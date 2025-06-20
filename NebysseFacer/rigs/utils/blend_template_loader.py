"""
Blender模板加载器 - 通用模块

此模块提供从Blender模板文件(.blend)加载骨骼数据、自定义属性、驱动器等功能的通用解决方案。
可以被多个项目和绑定类型共享使用。

主要功能：
- 从.blend文件加载骨架和骨骼数据
- 复制自定义属性和驱动器（包括自定义属性上的驱动器）
- 支持选择性加载指定骨骼
- 提供完整的错误处理和日志

特别强化：
- 自定义属性上的驱动器完整复制
- 驱动器变量和表达式的精确复制
- 支持复杂的驱动器系统
"""

import os
import bpy
from typing import Dict, List, Optional, Tuple, Any


class BlendTemplateLoader:
    """Blender模板文件加载器"""
    
    def __init__(self, template_name: str = None, template_path: str = None):
        """
        初始化模板加载器
        
        Args:
            template_name: 模板文件名（不含路径）
            template_path: 完整的模板文件路径（优先使用）
        """
        self.template_name = template_name
        self.template_path = template_path
        self.loaded_objects = []
        self.original_context = None
        
    def get_template_armature(self):
        """获取已加载的模板armature对象
        
        Returns:
            模板armature对象，如果没有则返回None
        """
        # 查找已加载的armature对象
        for obj in self.loaded_objects:
            if obj and obj.type == 'ARMATURE':
                return obj
        
        # 如果没有已加载的对象，尝试查找场景中的模板armature
        if self.template_name:
            template_base_name = os.path.splitext(self.template_name)[0]
            for obj in bpy.data.objects:
                if (obj.type == 'ARMATURE' and 
                    (template_base_name in obj.name or
                     "Nebysse_FaceUP_Tem" in obj.name or
                     "FaceUP_Tem" in obj.name)):
                    return obj
        
        return None
    
    def find_template_file(self, search_dirs: List[str] = None) -> Optional[str]:
        """
        查找模板文件路径
        
        Args:
            search_dirs: 搜索目录列表，如果为None则使用默认搜索路径
            
        Returns:
            找到的模板文件完整路径，未找到返回None
        """
        if self.template_path and os.path.exists(self.template_path):
            print(f"✓ 使用指定的模板路径: {self.template_path}")
            return self.template_path
        
        if not self.template_name:
            print("❌ 未指定模板名称")
            return None
        
        # 默认搜索路径
        if not search_dirs:
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            # 从 utils 目录向上找到项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            
            search_dirs = [
                os.path.join(project_root, "templates"),
                os.path.join(project_root, "NebysseFacer", "templates"),
                os.path.join(current_dir, "templates"),
                os.path.join(current_dir, "..", "templates"),
                os.path.join(current_dir, "..", "..", "templates"),
            ]
        
        # 在搜索目录中查找模板文件
        for search_dir in search_dirs:
            template_path = os.path.join(search_dir, self.template_name)
            template_path = os.path.normpath(template_path)
            
            print(f"🔍 搜索模板文件: {template_path}")
            
            if os.path.exists(template_path):
                print(f"✓ 找到模板文件: {template_path}")
                self.template_path = template_path
                return template_path
        
        print(f"❌ 未找到模板文件: {self.template_name}")
        return None
    
    def load_template_data(self, target_bone_names: List[str] = None) -> Dict[str, Any]:
        """
        从模板文件加载数据（防重复加载版本）
        
        Args:
            target_bone_names: 要加载的目标骨骼名称列表，None表示加载所有骨骼
            
        Returns:
            包含加载数据的字典
        """
        template_path = self.find_template_file()
        if not template_path:
            return {}
        
        print(f"📂 开始加载模板文件: {os.path.basename(template_path)}")
        
        try:
            # 保存当前上下文
            self.original_context = {
                'active_object': bpy.context.view_layer.objects.active,
                'selected_objects': list(bpy.context.selected_objects),
                'mode': bpy.context.mode
            }
            
            # 确保在对象模式
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # ==================== 防重复加载检查 ====================
            print("🔍 检查是否存在重复的模板对象...")
            
            # 检查当前场景中是否已有同名的模板对象
            existing_template_objects = []
            template_base_name = os.path.splitext(os.path.basename(template_path))[0]  # 不含扩展名的文件名
            
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    # 检查对象名称是否包含模板基础名称
                    if (template_base_name in obj.name or 
                        "Nebysse_FaceUP_Tem" in obj.name or
                        "FaceUP_Tem" in obj.name):
                        existing_template_objects.append(obj)
            
            if existing_template_objects:
                print(f"⚠ 发现 {len(existing_template_objects)} 个可能重复的模板对象:")
                for obj in existing_template_objects:
                    print(f"  📍 {obj.name}")
                
                print("🤔 选择处理策略...")
                
                # 策略1：尝试重用现有对象（如果名称匹配度高）
                best_match = None
                for obj in existing_template_objects:
                    # 寻找最匹配的对象（名称包含"Rig"且没有多余的后缀）
                    if "Rig" in obj.name and not any(suffix in obj.name for suffix in [".001", ".002", ".003", ".004"]):
                        best_match = obj
                        break
                
                if best_match:
                    print(f"✓ 重用现有的最佳匹配模板对象: {best_match.name}")
                    
                    # 将现有对象添加到已加载对象列表中，以便后续清理
                    if best_match not in self.loaded_objects:
                        self.loaded_objects.append(best_match)
                    
                    # 提取骨骼数据
                    bone_data = self._extract_bone_data(best_match, target_bone_names)
                    
                    return {
                        'armature': best_match,
                        'bone_data': bone_data,
                        'loaded_objects': self.loaded_objects,
                        'template_path': template_path,
                        'reused_existing': True
                    }
                else:
                    # 策略2：清理所有现有对象，重新加载
                    print("🧹 清理现有对象，准备重新加载...")
                    for obj in existing_template_objects:
                        try:
                            print(f"  🗑️ 清理现有对象: {obj.name}")
                            if obj == bpy.context.view_layer.objects.active:
                                bpy.context.view_layer.objects.active = None
                            obj.select_set(False)
                            bpy.data.objects.remove(obj)
                        except Exception as e:
                            print(f"  ⚠ 清理对象失败 {obj.name}: {e}")
                    
                    print("✓ 现有对象清理完成，继续新加载...")
            else:
                print("✓ 未发现重复对象，可以安全加载")
            
            # ==================== 开始加载模板文件 ====================
            print("📦 开始从文件加载模板对象...")
            
            # 记录加载前的对象
            objects_before = set(bpy.data.objects.keys())
            
            # 加载模板文件
            with bpy.data.libraries.load(template_path, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
                data_to.armatures = data_from.armatures
            
            # 查找新加载的对象
            objects_after = set(bpy.data.objects.keys())
            new_objects = objects_after - objects_before
            
            print(f"📊 成功加载了 {len(new_objects)} 个新对象")
            
            # 找到骨架对象
            template_armature = None
            loaded_armatures = []
            
            for obj_name in new_objects:
                obj = bpy.data.objects[obj_name]
                if obj.type == 'ARMATURE':
                    loaded_armatures.append(obj)
                    # 选择最佳的骨架对象（优先没有后缀的）
                    if not template_armature or (not any(suffix in obj.name for suffix in [".001", ".002", ".003"]) and "Rig" in obj.name):
                        template_armature = obj
                    self.loaded_objects.append(obj)
            
            if not template_armature:
                print("❌ 模板中未找到骨架对象")
                return {}
            
            print(f"✓ 找到主模板骨架: {template_armature.name}")
            if len(loaded_armatures) > 1:
                print(f"⚠ 注意：加载了 {len(loaded_armatures)} 个骨架对象，使用主骨架: {template_armature.name}")
                for arm in loaded_armatures:
                    if arm != template_armature:
                        print(f"  📋 其他骨架: {arm.name}")
            
            # 将骨架添加到场景（如果还没有）
            if template_armature.name not in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.link(template_armature)
                print(f"🔗 已将模板骨架链接到场景: {template_armature.name}")
            
            # 提取骨骼数据
            bone_data = self._extract_bone_data(template_armature, target_bone_names)
            
            return {
                'armature': template_armature,
                'bone_data': bone_data,
                'loaded_objects': self.loaded_objects,
                'template_path': template_path,
                'reused_existing': False
            }
            
        except Exception as e:
            print(f"❌ 加载模板文件失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_bone_data(self, armature_obj, target_bone_names: List[str] = None) -> Dict[str, Dict]:
        """
        提取骨骼数据，包括自定义属性和驱动器
        
        Args:
            armature_obj: 骨架对象
            target_bone_names: 目标骨骼名称列表
            
        Returns:
            骨骼数据字典
        """
        bone_data = {}
        
        try:
            # 确保骨架是活动对象
            bpy.context.view_layer.objects.active = armature_obj
            
            # 获取要处理的骨骼列表
            bones_to_process = target_bone_names if target_bone_names else armature_obj.pose.bones.keys()
            
            print(f"📋 提取 {len(bones_to_process)} 个骨骼的数据...")
            
            for bone_name in bones_to_process:
                if bone_name not in armature_obj.pose.bones:
                    print(f"⚠ 跳过不存在的骨骼: {bone_name}")
                    continue
                
                pose_bone = armature_obj.pose.bones[bone_name]
                bone = armature_obj.data.bones[bone_name]
                
                # 提取骨骼基本信息
                bone_info = {
                    'name': bone_name,
                    'custom_properties': {},
                    'drivers': [],
                    'constraints': [],
                    'bone_properties': {
                        'head': list(bone.head_local),
                        'tail': list(bone.tail_local),
                        'parent': bone.parent.name if bone.parent else None,
                        'use_deform': bone.use_deform,
                        'layers': list(bone.layers) if hasattr(bone, 'layers') else None,
                    },
                    'pose_properties': {
                        'location': list(pose_bone.location),
                        'rotation_quaternion': list(pose_bone.rotation_quaternion),
                        'rotation_euler': list(pose_bone.rotation_euler),
                        'scale': list(pose_bone.scale),
                        'rotation_mode': pose_bone.rotation_mode,
                        'lock_location': list(pose_bone.lock_location),
                        'lock_rotation': list(pose_bone.lock_rotation),
                        'lock_scale': list(pose_bone.lock_scale),
                    }
                }
                
                # 提取自定义属性
                custom_props = self._extract_custom_properties(pose_bone)
                bone_info['custom_properties'] = custom_props
                
                # 提取驱动器（包括自定义属性上的驱动器）
                drivers = self._extract_drivers(armature_obj, bone_name)
                bone_info['drivers'] = drivers
                
                # 提取约束
                constraints = self._extract_constraints(pose_bone)
                bone_info['constraints'] = constraints
                
                bone_data[bone_name] = bone_info
                
                print(f"  ✓ 提取骨骼数据: {bone_name}")
                print(f"    🔄 自定义属性: {len(custom_props)}")
                # print(f"    🔄 驱动器: {len(drivers)}") # 删除debug打印
                print(f"    🔗 约束: {len(constraints)}")
                
                # 详细报告自定义属性上的驱动器
                custom_prop_drivers = [d for d in drivers if self._is_custom_property_driver(d)]
                if custom_prop_drivers:
                    # print(f"    🎯 自定义属性驱动器: {len(custom_prop_drivers)}") # 删除debug打印
                    pass
            
            print(f"✅ 骨骼数据提取完成: {len(bone_data)} 个骨骼")
            return bone_data
            
        except Exception as e:
            print(f"❌ 提取骨骼数据失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_custom_properties(self, pose_bone) -> Dict[str, Any]:
        """提取自定义属性"""
        custom_props = {}
        
        for key in pose_bone.keys():
            if not key.startswith('_'):
                value = pose_bone[key]
                
                # 获取属性的UI设置
                ui_data = {}
                try:
                    if key in pose_bone.keys():
                        id_props_ui = pose_bone.id_properties_ui(key)
                        ui_data = {
                            'min': getattr(id_props_ui, 'min', None),
                            'max': getattr(id_props_ui, 'max', None),
                            'description': getattr(id_props_ui, 'description', ''),
                            'default': getattr(id_props_ui, 'default', None),
                        }
                except:
                    pass
                
                custom_props[key] = {
                    'value': value,
                    'ui_data': ui_data
                }
        
        return custom_props
    
    def _extract_drivers(self, armature_obj, bone_name: str) -> List[Dict]:
        """
        提取驱动器（增强版：包括自定义属性和约束属性上的驱动器）
        """
        drivers = []
        
        if not armature_obj.animation_data or not armature_obj.animation_data.drivers:
            return drivers
        
        # 构建该骨骼的所有可能的数据路径模式
        bone_path_patterns = [
            f'pose.bones["{bone_name}"]',
            f"pose.bones['{bone_name}']",
        ]
        
        # print(f"    🔍 搜索驱动器，骨骼路径模式: {bone_path_patterns}") # 删除debug打印
        
        for fcurve in armature_obj.animation_data.drivers:
            data_path = fcurve.data_path
            
            # 检查是否是该骨骼的驱动器
            is_bone_driver = any(pattern in data_path for pattern in bone_path_patterns)
            
            if is_bone_driver:
                driver_data = {
                    'data_path': data_path,
                    'array_index': fcurve.array_index,
                    'driver_type': fcurve.driver.type,
                    'expression': fcurve.driver.expression,
                    'variables': []
                }
                
                # 检查驱动器类型
                if self._is_constraint_property_driver_data(data_path):
                    # print(f"      🔗 发现约束属性驱动器: {data_path}") # 删除debug打印
                    pass
                elif self._is_custom_property_driver(driver_data):
                    # print(f"      🎯 发现自定义属性驱动器: {data_path}") # 删除debug打印
                    pass
                else:
                    # print(f"      🔄 发现变换驱动器: {data_path}") # 删除debug打印
                    pass
                
                # 提取变量
                for var in fcurve.driver.variables:
                    var_data = {
                        'name': var.name,
                        'type': var.type,
                        'targets': []
                    }
                    
                    for target in var.targets:
                        target_data = {
                            'id_type': target.id_type,
                            'id': target.id.name if target.id else None,
                            'data_path': target.data_path,
                            'bone_target': target.bone_target,
                            'transform_type': target.transform_type,
                            'transform_space': target.transform_space,
                        }
                        var_data['targets'].append(target_data)
                    
                    driver_data['variables'].append(var_data)
                
                drivers.append(driver_data)
                # print(f"      ✓ 提取驱动器: {data_path} -> 表达式: {fcurve.driver.expression}") # 删除debug打印
        
        return drivers
    
    def _is_constraint_property_driver_data(self, data_path: str) -> bool:
        """检查是否是约束属性驱动器（基于数据路径）"""
        # 检查路径是否包含 constraints["name"].property 格式
        import re
        constraint_pattern = r'\.constraints\[["\'][^"\']+["\']\]\.[a-zA-Z_]+'
        return bool(re.search(constraint_pattern, data_path))
    
    def _is_custom_property_driver(self, driver_data: Dict) -> bool:
        """检查是否是自定义属性驱动器"""
        data_path = driver_data.get('data_path', '')
        # 自定义属性驱动器的路径包含 ["property_name"] 格式，但不是约束属性
        has_custom_prop_pattern = '["' in data_path and '"]' in data_path
        is_constraint_prop = self._is_constraint_property_driver_data(data_path)
        return has_custom_prop_pattern and not is_constraint_prop
    
    def _extract_constraints(self, pose_bone) -> List[Dict]:
        """提取约束"""
        constraints = []
        
        for constraint in pose_bone.constraints:
            constraint_data = {
                'name': constraint.name,
                'type': constraint.type,
                'mute': constraint.mute,
                'influence': constraint.influence,
                'properties': {}
            }
            
            # 提取特定约束类型的属性
            if constraint.type == 'COPY_TRANSFORMS':
                constraint_data['properties'] = {
                    'target': constraint.target.name if constraint.target else None,
                    'subtarget': constraint.subtarget,
                    'mix_mode': constraint.mix_mode,
                    'target_space': constraint.target_space,
                    'owner_space': constraint.owner_space,
                }
            elif constraint.type == 'ACTION':
                # ACTION 约束属性提取
                constraint_data['properties'] = {
                    'action': constraint.action.name if constraint.action else None,
                    'frame_start': constraint.frame_start,
                    'frame_end': constraint.frame_end,
                    'use_eval_time': constraint.use_eval_time,
                    'eval_time': getattr(constraint, 'eval_time', 0.0),
                    'transform_channel': constraint.transform_channel,
                    'target_space': constraint.target_space,
                    'mix_mode': getattr(constraint, 'mix_mode', 'REPLACE'),
                    'target': constraint.target.name if constraint.target else None,
                    'subtarget': constraint.subtarget if hasattr(constraint, 'subtarget') else '',
                }
            elif constraint.type == 'LIMIT_ROTATION':
                # 限制旋转约束
                constraint_data['properties'] = {
                    'use_limit_x': constraint.use_limit_x,
                    'use_limit_y': constraint.use_limit_y,
                    'use_limit_z': constraint.use_limit_z,
                    'min_x': constraint.min_x,
                    'min_y': constraint.min_y,
                    'min_z': constraint.min_z,
                    'max_x': constraint.max_x,
                    'max_y': constraint.max_y,
                    'max_z': constraint.max_z,
                    'owner_space': constraint.owner_space,
                }
            elif constraint.type == 'LIMIT_LOCATION':
                # 限制位置约束
                constraint_data['properties'] = {
                    'use_min_x': constraint.use_min_x,
                    'use_min_y': constraint.use_min_y,
                    'use_min_z': constraint.use_min_z,
                    'use_max_x': constraint.use_max_x,
                    'use_max_y': constraint.use_max_y,
                    'use_max_z': constraint.use_max_z,
                    'min_x': constraint.min_x,
                    'min_y': constraint.min_y,
                    'min_z': constraint.min_z,
                    'max_x': constraint.max_x,
                    'max_y': constraint.max_y,
                    'max_z': constraint.max_z,
                    'owner_space': constraint.owner_space,
                }
            elif constraint.type == 'DAMPED_TRACK':
                # 阻尼跟踪约束
                constraint_data['properties'] = {
                    'target': constraint.target.name if constraint.target else None,
                    'subtarget': constraint.subtarget,
                    'track_axis': constraint.track_axis,
                    'head_tail': getattr(constraint, 'head_tail', 0.0),
                    'use_deform_preserve_volume': getattr(constraint, 'use_deform_preserve_volume', False),
                }
            else:
                # 对于未明确支持的约束类型，尝试通用属性提取
                constraint_data['properties'] = {}
                
                # 常见的约束属性
                common_attrs = ['target', 'subtarget', 'target_space', 'owner_space', 
                              'mix_mode', 'head_tail', 'use_bone_envelopes']
                
                for attr in common_attrs:
                    if hasattr(constraint, attr):
                        try:
                            value = getattr(constraint, attr)
                            # 如果是对象引用，获取名称
                            if hasattr(value, 'name'):
                                constraint_data['properties'][attr] = value.name
                            else:
                                constraint_data['properties'][attr] = value
                        except:
                            pass
            # 可以根据需要添加更多约束类型
            
            constraints.append(constraint_data)
        
        return constraints
    
    def apply_bone_data_to_rig(self, target_rig, bone_data: Dict[str, Dict], 
                              bone_mapping: Dict[str, str] = None) -> bool:
        """
        将骨骼数据应用到目标绑定
        
        Args:
            target_rig: 目标绑定对象
            bone_data: 骨骼数据字典
            bone_mapping: 骨骼名称映射 {模板骨骼名: 目标骨骼名}
            
        Returns:
            应用是否成功
        """
        if not bone_data:
            print("⚠ 骨骼数据为空")
            return False
        
        print("🔄 开始应用骨骼数据到目标绑定...")
        
        success_count = 0
        error_count = 0
        
        for template_bone_name, data in bone_data.items():
            # 确定目标骨骼名称
            target_bone_name = bone_mapping.get(template_bone_name, template_bone_name) if bone_mapping else template_bone_name
            
            try:
                # 应用自定义属性
                if self._apply_custom_properties(target_rig, target_bone_name, data.get('custom_properties', {})):
                    print(f"  ✓ 应用自定义属性: {template_bone_name} -> {target_bone_name}")
                
                # 应用驱动器（包括自定义属性上的驱动器）
                if drivers:
                    self._apply_drivers(target_rig, target_bone_name, drivers, bone_mapping)
                
                success_count += 1
                
            except Exception as e:
                print(f"❌ 应用骨骼数据失败 {template_bone_name}: {e}")
                error_count += 1
                continue
        
        print(f"📊 骨骼数据应用完成:")
        print(f"   ✅ 成功: {success_count} 个")
        print(f"   ❌ 失败: {error_count} 个")
        
        return error_count == 0
    
    def _apply_custom_properties(self, target_rig, bone_name: str, custom_props: Dict) -> bool:
        """应用自定义属性"""
        if bone_name not in target_rig.pose.bones:
            print(f"⚠ 目标骨骼不存在: {bone_name}")
            return False
        
        pose_bone = target_rig.pose.bones[bone_name]
        
        for prop_name, prop_data in custom_props.items():
            try:
                # 设置属性值
                pose_bone[prop_name] = prop_data['value']
                
                # 设置UI属性
                ui_data = prop_data.get('ui_data', {})
                if ui_data and prop_name in pose_bone.keys():
                    id_props_ui = pose_bone.id_properties_ui(prop_name)
                    
                    if 'min' in ui_data and ui_data['min'] is not None:
                        id_props_ui.update(min=ui_data['min'])
                    if 'max' in ui_data and ui_data['max'] is not None:
                        id_props_ui.update(max=ui_data['max'])
                    if 'description' in ui_data and ui_data['description']:
                        id_props_ui.update(description=ui_data['description'])
                
                print(f"    📝 设置属性: {prop_name} = {prop_data['value']}")
                
            except Exception as e:
                print(f"⚠ 设置属性失败 {prop_name}: {e}")
                continue
        
        return True
    
    def _apply_drivers(self, target_rig, bone_name: str, drivers: List[Dict], 
                      bone_mapping: Dict[str, str] = None) -> bool:
        """
        应用驱动器（强化版：包括自定义属性上的驱动器）
        """
        if not drivers:
            return True
        
        if bone_name not in target_rig.pose.bones:
            print(f"⚠ 目标骨骼不存在: {bone_name}")
            return False
        
        pose_bone = target_rig.pose.bones[bone_name]
        
        custom_prop_drivers = 0
        transform_drivers = 0
        
        for driver_data in drivers:
            try:
                # 解析data_path，替换骨骼名称
                data_path = driver_data['data_path']
                original_data_path = data_path
                
                # 替换骨骼名称（支持多种引号格式）
                import re
                pattern = r'pose\.bones\[(["\'])([^"\']+)\1\]'
                def replace_bone_name(match):
                    quote = match.group(1)
                    old_bone_name = match.group(2)
                    if bone_mapping and old_bone_name in bone_mapping:
                        new_bone_name = bone_mapping[old_bone_name]
                    else:
                        new_bone_name = bone_name
                    return f'pose.bones[{quote}{new_bone_name}{quote}]'
                
                data_path = re.sub(pattern, replace_bone_name, data_path)
                
                array_index = driver_data.get('array_index', 0)
                
                # 检查是否是自定义属性驱动器
                is_custom_prop = self._is_custom_property_driver(driver_data)
                
                if is_custom_prop:
                    # 自定义属性驱动器处理 - 不传递array_index参数
                    success = self._apply_custom_property_driver(
                        pose_bone, data_path, driver_data, bone_mapping, target_rig
                    )
                    if success:
                        custom_prop_drivers += 1
                else:
                    # 常规变换驱动器处理
                    success = self._apply_transform_driver(
                        pose_bone, data_path, array_index, driver_data, bone_mapping, target_rig
                    )
                    if success:
                        transform_drivers += 1
                
            except Exception as e:
                continue
        
        if custom_prop_drivers > 0 or transform_drivers > 0:
            pass
        
        return True
    
    def _apply_custom_property_driver(self, pose_bone, data_path: str, 
                                    driver_data: Dict, bone_mapping: Dict, target_rig) -> bool:
        """应用自定义属性驱动器（增强版）"""
        try:
            # 修复：正确提取自定义属性名称
            # 路径格式: pose.bones["骨骼名"]["属性名"]
            # 需要找到最后一个[""]部分，那才是属性名称
            prop_name = None
            
            # 使用正则表达式更精确地匹配属性名称
            import re
            # 匹配 pose.bones["骨骼名"]["属性名"] 格式
            pattern = r'pose\.bones\["[^"]+"\]\["([^"]+)"\]'
            match = re.search(pattern, data_path)
            
            if match:
                prop_name = match.group(1)
            else:
                # 备用方案：查找最后一个[""]部分
                parts = data_path.split('["')
                if len(parts) >= 3:  # pose.bones, 骨骼名, 属性名
                    last_part = parts[-1]
                    if '"]' in last_part:
                        prop_name = last_part.split('"]')[0]
            
            if not prop_name:
                return False
                
            # 确保属性存在 - 修复：保护已存在的属性值
            if prop_name not in pose_bone.keys():
                pose_bone[prop_name] = 0.0
            else:
                # 属性已存在，保留原值
                existing_value = pose_bone[prop_name]
            
            # 验证属性创建成功
            if prop_name not in pose_bone.keys():
                return False
            
            # 创建驱动器 - 自定义属性不需要array_index参数
            driver = pose_bone.driver_add(f'["{prop_name}"]')
            
            if not driver:
                return False
            
            # 验证驱动器基本结构
            if not hasattr(driver, 'driver') or not driver.driver:
                return False
            
            # 配置驱动器
            self._configure_driver(driver, driver_data, bone_mapping, target_rig)
            
            # 验证最终结果
            return self._verify_driver_creation(pose_bone, prop_name, driver, driver_data)
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def _verify_driver_creation(self, pose_bone, prop_name: str, driver, driver_data: Dict) -> bool:
        """验证驱动器创建结果"""
        try:
            # print(f"      🔍 验证驱动器创建结果...") # 删除debug打印
            
            # 检查属性是否仍然存在
            if prop_name not in pose_bone.keys():
                # print(f"      ❌ 属性丢失: {prop_name}") # 删除debug打印
                return False
            
            # 检查驱动器是否存在
            if not driver or not driver.driver:
                # print(f"      ❌ 驱动器对象无效") # 删除debug打印
                return False
            
            # 检查骨架是否有动画数据
            armature = pose_bone.id_data
            if not armature.animation_data:
                # print(f"      ❌ 骨架缺少动画数据") # 删除debug打印
                return False
            
            # 查找对应的FCurve
            target_path = f'pose.bones["{pose_bone.name}"]["{prop_name}"]'
            found_fcurve = None
            
            for fcurve in armature.animation_data.drivers:
                if fcurve.data_path == target_path:
                    found_fcurve = fcurve
                    break
            
            if not found_fcurve:
                # print(f"      ❌ 未找到对应的FCurve: {target_path}") # 删除debug打印
                return False
            
            # print(f"      ✓ 找到FCurve: {found_fcurve.data_path}") # 删除debug打印
            
            # 检查驱动器表达式
            expression = driver.driver.expression
            expected_expression = driver_data.get('expression', '')
            
            if expression != expected_expression:
                # print(f"      ⚠ 表达式不匹配:") # 删除debug打印
                # print(f"        期望: '{expected_expression}'") # 删除debug打印
                # print(f"        实际: '{expression}'") # 删除debug打印
                pass
            else:
                # print(f"      ✓ 表达式匹配: '{expression}'") # 删除debug打印
                pass
            
            # 检查变量数量
            variables_count = len(driver.driver.variables)
            expected_count = len(driver_data.get('variables', []))
            
            if variables_count != expected_count:
                # print(f"      ⚠ 变量数量不匹配: 期望 {expected_count}, 实际 {variables_count}") # 删除debug打印
                pass
            else:
                # print(f"      ✓ 变量数量正确: {variables_count} 个") # 删除debug打印
                pass
            
            # 检查属性值是否受保护
            current_value = pose_bone[prop_name]
            # print(f"      📝 当前属性值: {prop_name} = {current_value}") # 删除debug打印
            
            # print(f"      ✅ 驱动器验证通过") # 删除debug打印
            return True
            
        except Exception as e:
            # print(f"      ❌ 验证驱动器创建失败: {e}") # 删除debug打印
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_transform_driver(self, pose_bone, data_path: str, array_index: int,
                              driver_data: Dict, bone_mapping: Dict, target_rig) -> bool:
        """应用变换驱动器"""
        try:
            # 提取变换属性名称（如 location, rotation_euler 等）
            parts = data_path.split('.')
            if len(parts) >= 2:
                transform_prop = parts[-1]
                
                # 创建驱动器
                driver = pose_bone.driver_add(transform_prop, array_index)
                if driver:
                    self._configure_driver(driver, driver_data, bone_mapping, target_rig)
                    return True
                    
        except Exception as e:
            # print(f"⚠ 应用变换驱动器失败: {e}") # 删除debug打印
            return False
        
        return False
    
    def _configure_driver(self, driver, driver_data: Dict, bone_mapping: Dict, target_rig):
        """配置驱动器的通用方法（增强版）"""
        try:
            # print(f"        🔧 开始配置驱动器...") # 删除debug打印
            # print(f"        📄 驱动器数据: {driver_data.get('data_path', 'unknown')}") # 删除debug打印
            
            # 设置驱动器类型和表达式
            driver_type = driver_data.get('driver_type', 'SCRIPTED')
            expression = driver_data.get('expression', '')
            
            driver.driver.type = driver_type
            driver.driver.expression = expression
            
            # print(f"        ⚙️ 驱动器类型: {driver_type}") # 删除debug打印
            # print(f"        📝 表达式: '{expression}'") # 删除debug打印
            
            # 清除现有变量 - 使用Rigify官方推荐的方法 (Blender 4.1+)
            existing_vars = list(driver.driver.variables)
            # print(f"        🧹 清理现有变量: {len(existing_vars)} 个")
            for var in existing_vars:
                driver.driver.variables.remove(var)
            
            # 添加变量
            variables_data = driver_data.get('variables', [])
            # print(f"        ➕ 添加变量: {len(variables_data)} 个")
            
            for i, var_data in enumerate(variables_data):
                try:
                    var = driver.driver.variables.new()
                    var_name = var_data.get('name', f'var_{i}')
                    var_type = var_data.get('type', 'SINGLE_PROP')
                    
                    var.name = var_name
                    var.type = var_type
                    
                    # print(f"          🔸 变量 {i+1}: {var_name} (类型: {var_type})")
                    
                    # 配置变量目标
                    targets_data = var_data.get('targets', [])
                    for j, target_data in enumerate(targets_data):
                        if j >= len(var.targets):
                    #        print(f"            ⚠ 跳过多余的目标 {j+1}")
                            break
                        
                        target = var.targets[j]
                        target.id = target_rig
                        
                        # 处理骨骼名称映射
                        bone_target = target_data.get('bone_target', '')
                        if bone_target and bone_mapping:
                            original_bone = bone_target
                            bone_target = bone_mapping.get(bone_target, bone_target)
                            if original_bone != bone_target:
                                # print(f"            🔄 骨骼映射: {original_bone} -> {bone_target}")
                                pass
                        
                        target.bone_target = bone_target
                        target.data_path = target_data.get('data_path', '')
                        target.transform_type = target_data.get('transform_type', 'LOC_X')
                        target.transform_space = target_data.get('transform_space', 'LOCAL_SPACE')
                        
                        # print(f"            🎯 目标 {j+1}: 骨骼='{bone_target}', 路径='{target.data_path}'")
                        # print(f"              变换类型: {target.transform_type}, 空间: {target.transform_space}")
                        
                except Exception as var_error:
                    # print(f"          ❌ 配置变量 {i+1} 失败: {var_error}")
                    continue
            
            # 验证驱动器配置
            self._validate_driver_configuration(driver, driver_data)
            
            # print(f"        ✅ 驱动器配置完成") # 删除debug打印
            
        except Exception as e:
            # print(f"        ❌ 配置驱动器失败: {e}") # 删除debug打印
            import traceback
            traceback.print_exc()
            raise
    
    def _validate_driver_configuration(self, driver, driver_data: Dict):
        """验证驱动器配置是否正确"""
        try:
            # print(f"        🔍 验证驱动器配置...") # 删除debug打印
            
            # 检查基本配置
            if not driver or not driver.driver:
                # print(f"        ❌ 驱动器对象无效") # 删除debug打印
                return False
            
            # 检查表达式
            expression = driver.driver.expression
            if not expression or expression.strip() == '':
                # print(f"        ⚠ 驱动器表达式为空") # 删除debug打印
                pass
            else:
                # print(f"        ✓ 表达式有效: '{expression}'") # 删除debug打印
                pass
            
            # 检查变量
            variables_count = len(driver.driver.variables)
            expected_count = len(driver_data.get('variables', []))
            
            if variables_count != expected_count:
                # print(f"        ⚠ 变量数量不匹配: 期望 {expected_count}, 实际 {variables_count}") # 删除debug打印
                pass
            else:
                # print(f"        ✓ 变量数量匹配: {variables_count}") # 删除debug打印
                pass
            
            # 检查变量配置但不打印调试信息
            for i, variable in enumerate(driver.driver.variables):
                # print(f"          变量 {i+1}: 名称='{variable.name}', 类型='{variable.type}'") # 删除debug打印
                
                for j, target in enumerate(variable.targets):
                    if target.id:
                        # print(f"            目标 {j+1}: 对象='{target.id.name}', 骨骼='{target.bone_target}'") # 删除debug打印
                        pass
                    else:
                        # print(f"            目标 {j+1}: 无目标对象") # 删除debug打印
                        pass
            
            # print(f"        ✅ 驱动器验证完成") # 删除debug打印
            return True
            
        except Exception as e:
            # print(f"        ❌ 验证驱动器配置失败: {e}") # 删除debug打印
            return False
    
    def cleanup(self):
        """清理加载的模板数据"""
        print("🧹 清理模板数据...")
        
        # 保存当前上下文信息
        current_active = bpy.context.view_layer.objects.active
        current_selected = list(bpy.context.selected_objects)
        
        # 统计要清理的对象
        template_rig_objects = []
        other_objects = []
        
        for obj in self.loaded_objects:
            if "Nebysse_FaceUP_Tem.Rig" in obj.name:
                template_rig_objects.append(obj)
            else:
                other_objects.append(obj)
        
        if template_rig_objects:
            print(f"  🎯 发现模板rig对象: {len(template_rig_objects)} 个")
            for obj in template_rig_objects:
                print(f"    📍 {obj.name}")
        
        if other_objects:
            print(f"  📦 其他模板对象: {len(other_objects)} 个")
        
        # 清理加载的对象
        for obj in self.loaded_objects:
            try:
                # 安全检查：确保对象仍然存在且有效
                if obj and hasattr(obj, 'name') and obj.name in bpy.data.objects:
                    # 特别标注模板rig对象的删除
                    if "Nebysse_FaceUP_Tem.Rig" in obj.name:
                        print(f"  🗑️ 删除模板rig对象: {obj.name}")
                    else:
                        print(f"  🗑️ 删除对象: {obj.name}")
                    
                    # 如果要删除的对象是当前活动对象，先切换活动对象
                    if obj == current_active:
                        # 尝试找到一个不会被删除的对象作为活动对象
                        for alt_obj in bpy.data.objects:
                            if alt_obj not in self.loaded_objects:
                                bpy.context.view_layer.objects.active = alt_obj
                                print(f"    🔄 切换活动对象到: {alt_obj.name}")
                                break
                        else:
                            bpy.context.view_layer.objects.active = None
                    
                    # 确保对象未被选中
                    obj.select_set(False)
                    
                    # 删除对象
                    bpy.data.objects.remove(obj)
            except (ReferenceError, AttributeError):
                # 对象已被删除或引用已失效，跳过
                pass
            except Exception as e:
                print(f"⚠ 删除对象失败: {e}")
        
        self.loaded_objects.clear()
        print(f"  ✓ 已清理所有模板对象，包括 {len(template_rig_objects)} 个模板rig对象")
        
        # 智能恢复原始上下文
        if self.original_context:
            try:
                # 恢复活动对象
                original_active = self.original_context['active_object']
                if original_active and hasattr(original_active, 'name') and original_active.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = original_active
                    print(f"  ✓ 恢复活动对象: {original_active.name}")
                elif not bpy.context.view_layer.objects.active:
                    # 如果没有活动对象，尝试设置一个
                    for obj in bpy.data.objects:
                        if obj.type == 'ARMATURE':
                            bpy.context.view_layer.objects.active = obj
                            print(f"  🔄 设置活动对象为骨架: {obj.name}")
                            break
                
                # 恢复选择状态
                bpy.ops.object.select_all(action='DESELECT')
                for obj in self.original_context['selected_objects']:
                    # 安全检查：确保对象仍然存在且有效
                    try:
                        if obj and hasattr(obj, 'name') and obj.name in bpy.data.objects:
                            bpy.data.objects[obj.name].select_set(True)
                    except (ReferenceError, AttributeError):
                        # 对象已被删除或引用已失效，跳过
                        pass
                    except Exception as e:
                        print(f"⚠ 恢复对象选择状态时出错: {e}")
                        pass
                
                # 更新视图层
                bpy.context.view_layer.update()
                
                print(f"  ✓ 上下文恢复完成，活动对象: {bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else 'None'}")
                
            except Exception as e:
                print(f"⚠ 恢复上下文失败: {e}")
                
                # 紧急恢复：确保有活动对象
                try:
                    if not bpy.context.view_layer.objects.active:
                        for obj in bpy.data.objects:
                            if obj.type == 'ARMATURE':
                                bpy.context.view_layer.objects.active = obj
                                obj.select_set(True)
                                print(f"  🆘 紧急设置活动对象: {obj.name}")
                                break
                except:
                    pass
        
        print("✓ 清理完成")

    def copy_properties_from_template_rig(self, template_rig_name: str = "Nebysse_FaceUP_Tem.Rig", 
                                        source_bone_name: str = "Neb_face-root", 
                                        target_rig=None, target_bone_name: str = "Neb_face-root") -> bool:
        """
        从模板rig对象中的指定骨骼复制自定义属性到目标rig的指定骨骼
        
        Args:
            template_rig_name: 模板rig对象名称
            source_bone_name: 源骨骼名称
            target_rig: 目标rig对象
            target_bone_name: 目标骨骼名称
            
        Returns:
            复制是否成功
            
        Raises:
            RuntimeError: 如果模板rig对象不存在或其他关键错误
        """
        try:
            print(f"🎯 开始从模板rig复制自定义属性...")
            print(f"   📂 模板rig: {template_rig_name}")
            print(f"   🦴 源骨骼: {source_bone_name}")
            print(f"   🎯 目标骨骼: {target_bone_name}")
            
            # 查找模板rig对象（可能抛出异常）
            template_rig_obj = self._find_template_rig_object(template_rig_name)
            # 如果执行到这里，说明找到了模板rig对象
            
            # 检查源骨骼是否存在
            if source_bone_name not in template_rig_obj.pose.bones:
                error_msg = f"模板rig中不存在源骨骼: {source_bone_name}"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            source_pose_bone = template_rig_obj.pose.bones[source_bone_name]
            print(f"✓ 找到源骨骼: {source_pose_bone.name}")
            
            # 检查目标rig和骨骼
            if not target_rig:
                error_msg = "未指定目标rig对象"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            if target_bone_name not in target_rig.pose.bones:
                error_msg = f"目标rig中不存在目标骨骼: {target_bone_name}"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            target_pose_bone = target_rig.pose.bones[target_bone_name]
            print(f"✓ 找到目标骨骼: {target_pose_bone.name}")
            
            # 提取源骨骼的自定义属性
            source_custom_props = self._extract_custom_properties(source_pose_bone)
            print(f"📝 从源骨骼提取到 {len(source_custom_props)} 个自定义属性")
            
            if not source_custom_props:
                print("⚠ 源骨骼没有自定义属性")
                return True
            
            # 复制自定义属性到目标骨骼
            copied_count = 0
            for prop_name, prop_data in source_custom_props.items():
                try:
                    # 设置属性值
                    target_pose_bone[prop_name] = prop_data['value']
                    
                    # 设置UI属性
                    ui_data = prop_data.get('ui_data', {})
                    if ui_data and prop_name in target_pose_bone.keys():
                        id_props_ui = target_pose_bone.id_properties_ui(prop_name)
                        
                        if 'min' in ui_data and ui_data['min'] is not None:
                            id_props_ui.update(min=ui_data['min'])
                        if 'max' in ui_data and ui_data['max'] is not None:
                            id_props_ui.update(max=ui_data['max'])
                        if 'description' in ui_data and ui_data['description']:
                            id_props_ui.update(description=ui_data['description'])
                        if 'soft_min' in ui_data and ui_data['soft_min'] is not None:
                            id_props_ui.update(soft_min=ui_data['soft_min'])
                        if 'soft_max' in ui_data and ui_data['soft_max'] is not None:
                            id_props_ui.update(soft_max=ui_data['soft_max'])
                    
                    copied_count += 1
                    print(f"  ✓ 复制属性: {prop_name} = {prop_data['value']}")
                    
                except Exception as e:
                    print(f"⚠ 复制属性失败 {prop_name}: {e}")
                    continue
            
            print(f"✅ 自定义属性复制完成: {copied_count}/{len(source_custom_props)} 个成功")
            
            # 更新依赖图
            bpy.context.view_layer.update()
            
            return copied_count > 0
            
        except RuntimeError:
            # 重新抛出已知的运行时错误（如模板rig对象不存在）
            raise
        except Exception as e:
            error_msg = f"从模板rig复制自定义属性时发生意外错误: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)

    def copy_drivers_from_template_rig(self, template_rig_name: str = "Nebysse_FaceUP_Tem.Rig",
                                     source_bone_name: str = "Neb_face-root",
                                     target_rig=None, target_bone_name: str = "Neb_face-root") -> bool:
        """
        从模板rig对象中的指定骨骼复制驱动器到目标rig的指定骨骼
        
        Args:
            template_rig_name: 模板rig对象名称
            source_bone_name: 源骨骼名称
            target_rig: 目标rig对象
            target_bone_name: 目标骨骼名称
            
        Returns:
            复制是否成功
            
        Raises:
            RuntimeError: 如果模板rig对象不存在或其他关键错误
        """
        try:
            # print(f"🔄 开始从模板rig复制驱动器...") # 删除debug打印
            # print(f"  📌 模板rig: {template_rig_name}") # 删除debug打印
            # print(f"  📌 源骨骼: {source_bone_name}") # 删除debug打印
            # print(f"  📌 目标骨骼: {target_bone_name}") # 删除debug打印
            
            # 查找模板rig对象
            template_rig_obj = self._find_template_rig_object(template_rig_name)
            if not template_rig_obj:
                # print(f"❌ 找不到模板rig对象: {template_rig_name}") # 删除debug打印
                return False
            
            # 提取源骨骼的驱动器
            source_drivers = self._extract_drivers(template_rig_obj, source_bone_name)
            
            if not source_drivers:
                # print("⚠ 源骨骼没有驱动器") # 删除debug打印
                return True  # 没有驱动器也算成功
            
            # print(f"🔄 从源骨骼提取到 {len(source_drivers)} 个驱动器") # 删除debug打印
            
            # 应用驱动器到目标骨骼
            success = self._apply_drivers(target_rig, target_bone_name, source_drivers)
            
            if success:
                # print(f"✅ 驱动器复制完成") # 删除debug打印
                return True
            else:
                # print(f"⚠ 驱动器复制部分失败") # 删除debug打印
                return False
            
        except RuntimeError:
            # 重新抛出已知的运行时错误（如模板rig对象不存在）
            raise
        except Exception as e:
            error_msg = f"从模板rig复制驱动器时发生意外错误: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)

    def _find_template_rig_object(self, template_rig_name: str):
        """
        查找模板rig对象（严格模式：找不到直接抛出异常）
        
        Args:
            template_rig_name: 模板rig对象名称
            
        Returns:
            找到的rig对象
            
        Raises:
            RuntimeError: 如果未找到模板rig对象
        """
        try:
            print(f"🔍 智能查找模板rig对象: {template_rig_name}")
            
            # 第一步：尝试直接根据名称查找
            if template_rig_name in bpy.data.objects:
                obj = bpy.data.objects[template_rig_name]
                if obj.type == 'ARMATURE':
                    print(f"✓ 直接找到模板rig对象: {obj.name}")
                    return obj
            
            # 第二步：智能查找包含基础名称的对象（处理.001, .002等后缀）
            base_name = template_rig_name
            template_candidates = []
            
            for obj in bpy.data.objects:
                if obj.type != 'ARMATURE':
                    continue
                
                obj_name = obj.name
                
                # 检查是否是带后缀的同名对象
                if obj_name.startswith(base_name):
                    # 检查后缀格式：.001, .002 等
                    suffix = obj_name[len(base_name):]
                    if suffix == "" or (suffix.startswith('.') and suffix[1:].isdigit()):
                        template_candidates.append(obj)
                        print(f"  📋 发现候选对象: {obj_name}")
            
            # 第三步：如果找到候选对象，选择最佳匹配
            if template_candidates:
                # 优先选择没有后缀的原始名称
                for obj in template_candidates:
                    if obj.name == base_name:
                        print(f"✓ 找到原始名称的模板rig: {obj.name}")
                        return obj
                
                # 如果没有原始名称，选择后缀数字最小的
                template_candidates.sort(key=lambda x: self._extract_suffix_number(x.name))
                best_match = template_candidates[0]
                print(f"✓ 找到最佳匹配的模板rig: {best_match.name}")
                print(f"  💡 注意：由于Blender重名机制，使用了带后缀的对象")
                return best_match
            
            # 第四步：扩展搜索 - 查找包含关键词的对象
            print(f"🔍 扩展搜索包含关键词的对象...")
            keyword_matches = []
            keywords = ["FaceUP", "Tem", "Rig", "Template"]
            
            for obj in bpy.data.objects:
                if obj.type != 'ARMATURE':
                    continue
                
                obj_name = obj.name
                keyword_count = sum(1 for keyword in keywords if keyword in obj_name)
                
                if keyword_count >= 2:  # 至少包含2个关键词
                    keyword_matches.append((obj, keyword_count))
                    print(f"  📋 关键词匹配: {obj_name} (匹配 {keyword_count} 个关键词)")
            
            if keyword_matches:
                # 按匹配的关键词数量排序，选择最佳匹配
                keyword_matches.sort(key=lambda x: x[1], reverse=True)
                best_match = keyword_matches[0][0]
                print(f"✓ 通过关键词找到模板rig: {best_match.name}")
                return best_match
            
            # 第五步：尝试从当前加载的对象中查找（如果是刚加载的）
            if hasattr(self, 'loaded_objects') and self.loaded_objects:
                print(f"🔍 在已加载对象中查找...")
                for obj in self.loaded_objects:
                    if obj.type == 'ARMATURE' and template_rig_name in obj.name:
                        print(f"✓ 在已加载对象中找到: {obj.name}")
                        return obj
            
            # 第六步：如果还没找到，尝试从模板文件加载
            print(f"⚠ 场景中未找到模板rig对象: {template_rig_name}")
            print(f"🔄 尝试从模板文件加载...")
            
            template_data = self.load_template_data()
            if template_data and 'armature' in template_data:
                template_armature = template_data['armature']
                if template_rig_name in template_armature.name or template_armature.name in template_rig_name:
                    print(f"✓ 从模板文件加载到rig对象: {template_armature.name}")
                    return template_armature
            
            # 所有方法都失败了，抛出详细的异常
            error_msg = f"无法找到模板rig对象: {template_rig_name}"
            print(f"❌ {error_msg}")
            print(f"💡 详细诊断信息：")
            print(f"   1. 直接名称查找：失败")
            print(f"   2. 后缀名称查找：找到 {len(template_candidates)} 个候选对象")
            print(f"   3. 关键词匹配：找到 {len(keyword_matches)} 个匹配对象")
            print(f"   4. 已加载对象查找：{len(self.loaded_objects) if hasattr(self, 'loaded_objects') else 0} 个对象")
            print(f"   5. 模板文件加载：{'成功' if template_data else '失败'}")
            
            print(f"🔧 可能的解决方案：")
            print(f"   1. 检查模板文件是否存在且有效")
            print(f"   2. 确认模板rig对象名称为: {template_rig_name}")
            print(f"   3. 检查Blender版本兼容性")
            print(f"   4. 重新安装或修复模板文件")
            print(f"   5. 手动导入模板文件到场景中")
            
            # 列出当前场景中的所有骨架对象
            armature_objects = [obj.name for obj in bpy.data.objects if obj.type == 'ARMATURE']
            if armature_objects:
                print(f"📋 当前场景中的骨架对象:")
                for arm_name in armature_objects:
                    print(f"   • {arm_name}")
            else:
                print(f"📋 当前场景中没有骨架对象")
            
            raise RuntimeError(error_msg)
            
        except RuntimeError:
            # 重新抛出已知的运行时错误
            raise
        except Exception as e:
            error_msg = f"查找模板rig对象时发生意外错误: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)
    
    def _extract_suffix_number(self, name: str) -> int:
        """提取名称后缀中的数字，用于排序"""
        try:
            # 查找最后一个点的位置
            last_dot = name.rfind('.')
            if last_dot == -1:
                return 0  # 没有后缀
            
            suffix = name[last_dot + 1:]
            if suffix.isdigit():
                return int(suffix)
            else:
                return 0  # 后缀不是数字
        except:
            return 0

    def load_template_data_safe(self):
        """安全地加载模板数据（专为Rigify生成过程设计）
        
        Returns:
            模板数据字典，失败返回None
        """
        print("📂 BlendTemplateLoader: 安全加载模板数据...")
        
        # 保护当前状态
        original_active = bpy.context.view_layer.objects.active
        original_selected = list(bpy.context.selected_objects)
        original_mode = bpy.context.mode
        
        try:
            # 确保在对象模式
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # 调用原有的加载方法，但更加小心
            return self._load_template_data_protected()
            
        except Exception as e:
            print(f"❌ 安全加载失败: {e}")
            return None
            
        finally:
            # 恢复原始状态
            try:
                if original_active and original_active.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = original_active
                
                # 恢复选择状态
                for obj in original_selected:
                    try:
                        if obj and obj.name in bpy.data.objects:
                            obj.select_set(True)
                    except:
                        pass
                
                # 恢复模式
                if bpy.context.mode != original_mode:
                    try:
                        if original_mode == 'EDIT_ARMATURE':
                            bpy.ops.object.mode_set(mode='EDIT')
                        elif original_mode == 'POSE':
                            bpy.ops.object.mode_set(mode='POSE')
                        else:
                            bpy.ops.object.mode_set(mode='OBJECT')
                    except:
                        pass
                
                # 更新视图层
                bpy.context.view_layer.update()
                
                print(f"  ✓ 上下文恢复完成，活动对象: {bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else 'None'}")
                
            except Exception as e:
                print(f"⚠ 安全加载后恢复状态失败: {e}")
    
    def _load_template_data_protected(self):
        """受保护的模板数据加载（内部方法）"""
        if not self.template_path and self.template_name:
            # 查找模板文件路径
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            self.template_path = os.path.join(parent_dir, "templates", self.template_name)
        
        if not self.template_path or not os.path.exists(self.template_path):
            print(f"⚠ 模板文件不存在: {self.template_path}")
            return None
        
        try:
            print(f"📁 加载模板文件: {self.template_path}")
            
            # 检查模板文件是否已经被链接
            existing_template = None
            for obj in bpy.data.objects:
                if (obj.type == 'ARMATURE' and 
                    ('Nebysse_FaceUP_Tem' in obj.name or 'FaceUP_Tem' in obj.name)):
                    existing_template = obj
                    break
            
            if existing_template:
                print(f"✅ 使用已存在的模板对象: {existing_template.name}")
                return {'armature': existing_template}
            
            # 使用append模式加载（而不是link，避免依赖问题）
            with bpy.data.libraries.load(self.template_path, link=False) as (data_from, data_to):
                # 查找armature
                armature_names = [name for name in data_from.objects if any(
                    pattern in name for pattern in ['Nebysse_FaceUP_Tem', 'FaceUP_Tem']
                )]
                
                if armature_names:
                    data_to.objects = armature_names
                    print(f"📦 准备加载armature: {armature_names}")
                else:
                    print("⚠ 模板文件中未找到armature对象")
                    return None
            
            # 获取加载的对象
            loaded_armature = None
            for obj in data_to.objects:
                if obj and obj.type == 'ARMATURE':
                    loaded_armature = obj
                    self.loaded_objects.append(obj)
                    break
            
            if loaded_armature:
                print(f"✅ 模板armature加载成功: {loaded_armature.name}")
                return {'armature': loaded_armature}
            else:
                print("❌ 加载的对象中没有有效的armature")
                return None
                
        except Exception as e:
            print(f"❌ 受保护加载失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def copy_neboffset_bone_data(self, template_rig_name: str, 
                                 neboffset_bone_name: str,
                                 target_rig, target_bone_name: str = None) -> bool:
        """
        复制模板rig中指定NebOffset骨骼的约束、修改器和驱动器到目标rig的同名骨骼
        
        Args:
            template_rig_name: 模板rig对象名称
            neboffset_bone_name: NebOffset骨骼名称（如: "NebOffset-brow.T.L.003"）
            target_rig: 目标rig对象
            target_bone_name: 目标骨骼名称，如果为None则使用与源骨骼相同的名称
            
        Returns:
            复制是否成功
            
        Raises:
            RuntimeError: 如果模板rig对象或骨骼不存在
        """
        try:
            if target_bone_name is None:
                target_bone_name = neboffset_bone_name
                
            print(f"🎯 开始复制NebOffset骨骼数据:")
            print(f"   📂 模板rig: {template_rig_name}")
            print(f"   🦴 源骨骼: {neboffset_bone_name}")
            print(f"   🎯 目标骨骼: {target_bone_name}")
            
            # 查找模板rig对象
            template_rig_obj = self._find_template_rig_object(template_rig_name)
            
            # 检查源骨骼是否存在
            if neboffset_bone_name not in template_rig_obj.pose.bones:
                error_msg = f"模板rig中不存在NebOffset骨骼: {neboffset_bone_name}"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            # 检查目标骨骼是否存在
            if target_bone_name not in target_rig.pose.bones:
                error_msg = f"目标rig中不存在目标骨骼: {target_bone_name}"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            # 提取源骨骼的完整数据
            bone_data = self._extract_bone_data(template_rig_obj, [neboffset_bone_name])
            
            if neboffset_bone_name not in bone_data:
                error_msg = f"提取骨骼数据失败: {neboffset_bone_name}"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            source_bone_data = bone_data[neboffset_bone_name]
            print(f"✅ 成功提取源骨骼数据")
            
            # 应用数据到目标骨骼
            success = self._apply_neboffset_bone_data(target_rig, target_bone_name, source_bone_data, template_rig_obj)
            
            if success:
                print(f"✅ NebOffset骨骼数据复制完成: {neboffset_bone_name} -> {target_bone_name}")
            else:
                print(f"⚠ NebOffset骨骼数据复制部分失败")
            
            return success
            
        except RuntimeError:
            # 重新抛出已知的运行时错误
            raise
        except Exception as e:
            error_msg = f"复制NebOffset骨骼数据时发生意外错误: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)
    
    def _apply_neboffset_bone_data(self, target_rig, target_bone_name: str, 
                                  source_bone_data: Dict, template_rig_obj) -> bool:
        """
        将提取的NebOffset骨骼数据应用到目标骨骼
        
        Args:
            target_rig: 目标rig对象
            target_bone_name: 目标骨骼名称
            source_bone_data: 源骨骼数据字典
            template_rig_obj: 模板rig对象（用于约束目标重定向）
            
        Returns:
            应用是否成功
        """
        try:
            target_pose_bone = target_rig.pose.bones[target_bone_name]
            print(f"📋 开始应用NebOffset骨骼数据到: {target_bone_name}")
            
            success_count = 0
            total_operations = 0
            
            # 1. 应用约束
            constraints_data = source_bone_data.get('constraints', [])
            if constraints_data:
                print(f"🔗 应用约束: {len(constraints_data)} 个")
                total_operations += len(constraints_data)
                
                for constraint_data in constraints_data:
                    if self._apply_single_constraint(target_pose_bone, constraint_data, template_rig_obj, target_rig):
                        success_count += 1
                        print(f"  ✅ 约束: {constraint_data.get('name', 'unknown')}")
                    else:
                        print(f"  ❌ 约束失败: {constraint_data.get('name', 'unknown')}")
            
            # 2. 应用驱动器
            drivers_data = source_bone_data.get('drivers', [])
            if drivers_data:
                print(f"🔄 应用驱动器: {len(drivers_data)} 个")
                total_operations += len(drivers_data)
                
                # 创建骨骼映射（源骨骼名称 -> 目标骨骼名称）
                bone_mapping = {source_bone_data['name']: target_bone_name}
                
                for driver_data in drivers_data:
                    if self._apply_single_driver(target_rig, target_bone_name, driver_data, bone_mapping):
                        success_count += 1
                        print(f"  ✅ 驱动器: {driver_data.get('data_path', 'unknown')}")
                    else:
                        print(f"  ❌ 驱动器失败: {driver_data.get('data_path', 'unknown')}")
            
            # 3. 应用自定义属性（如果有）
            custom_props = source_bone_data.get('custom_properties', {})
            if custom_props:
                print(f"📝 应用自定义属性: {len(custom_props)} 个")
                total_operations += len(custom_props)
                
                for prop_name, prop_data in custom_props.items():
                    if self._apply_single_custom_property(target_pose_bone, prop_name, prop_data):
                        success_count += 1
                        print(f"  ✅ 属性: {prop_name} = {prop_data.get('value', 'unknown')}")
                    else:
                        print(f"  ❌ 属性失败: {prop_name}")
            
            print(f"📊 NebOffset骨骼数据应用统计:")
            print(f"   ✅ 成功: {success_count}/{total_operations} 个操作")
            print(f"   📈 成功率: {(success_count/total_operations*100):.1f}%" if total_operations > 0 else "   📈 成功率: 100%")
            
            # 更新依赖图
            bpy.context.view_layer.update()
            
            return success_count > 0 or total_operations == 0
            
        except Exception as e:
            print(f"❌ 应用NebOffset骨骼数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_single_constraint(self, target_pose_bone, constraint_data: Dict, 
                                template_rig_obj, target_rig) -> bool:
        """应用单个约束"""
        try:
            constraint_type = constraint_data.get('type')
            constraint_name = constraint_data.get('name', f"约束_{constraint_type}")
            
            # 创建约束
            new_constraint = target_pose_bone.constraints.new(constraint_type)
            new_constraint.name = constraint_name
            
            # 设置基本属性
            new_constraint.mute = constraint_data.get('mute', False)
            new_constraint.influence = constraint_data.get('influence', 1.0)
            
            # 设置特定约束类型的属性
            properties = constraint_data.get('properties', {})
            
            if constraint_type == 'COPY_TRANSFORMS':
                # 重定向目标对象
                if properties.get('target'):
                    new_constraint.target = target_rig  # 重定向到当前rig
                    new_constraint.subtarget = properties.get('subtarget', '')
                
                new_constraint.mix_mode = properties.get('mix_mode', 'BEFORE')
                new_constraint.target_space = properties.get('target_space', 'LOCAL')
                new_constraint.owner_space = properties.get('owner_space', 'LOCAL')
                
            elif constraint_type == 'ACTION':
                # ACTION 约束（动作约束）
                print(f"      🎬 配置ACTION约束: {constraint_name}")
                
                # 设置动作
                action_name = properties.get('action')
                if action_name and action_name in bpy.data.actions:
                    new_constraint.action = bpy.data.actions[action_name]
                    print(f"        ✓ 动作: {action_name}")
                else:
                    print(f"        ⚠ 动作不存在或为空: {action_name}")
                
                # 设置帧范围
                if properties.get('frame_start') is not None:
                    new_constraint.frame_start = properties.get('frame_start')
                if properties.get('frame_end') is not None:
                    new_constraint.frame_end = properties.get('frame_end')
                if properties.get('use_eval_time') is not None:
                    new_constraint.use_eval_time = properties.get('use_eval_time')
                if properties.get('eval_time') is not None:
                    new_constraint.eval_time = properties.get('eval_time', 0.0)
                
                # 设置变换通道和空间
                if properties.get('transform_channel'):
                    new_constraint.transform_channel = properties.get('transform_channel')
                if properties.get('target_space'):
                    new_constraint.target_space = properties.get('target_space')
                
                # 设置目标对象
                if properties.get('target'):
                    new_constraint.target = target_rig  # 重定向到当前rig
                    new_constraint.subtarget = properties.get('subtarget', '')
                
                print(f"        ✓ ACTION约束配置完成")
                
            elif constraint_type == 'LIMIT_ROTATION':
                # 限制旋转约束
                for attr in ['use_limit_x', 'use_limit_y', 'use_limit_z',
                           'min_x', 'min_y', 'min_z', 'max_x', 'max_y', 'max_z']:
                    if attr in properties:
                        setattr(new_constraint, attr, properties[attr])
                if 'owner_space' in properties:
                    new_constraint.owner_space = properties['owner_space']
                        
            elif constraint_type == 'LIMIT_LOCATION':
                # 限制位置约束
                for attr in ['use_min_x', 'use_min_y', 'use_min_z',
                           'use_max_x', 'use_max_y', 'use_max_z',
                           'min_x', 'min_y', 'min_z', 'max_x', 'max_y', 'max_z']:
                    if attr in properties:
                        setattr(new_constraint, attr, properties[attr])
                if 'owner_space' in properties:
                    new_constraint.owner_space = properties['owner_space']
                        
            elif constraint_type == 'DAMPED_TRACK':
                # 阻尼跟踪约束
                if properties.get('target'):
                    new_constraint.target = target_rig
                    new_constraint.subtarget = properties.get('subtarget', '')
                new_constraint.track_axis = properties.get('track_axis', 'TRACK_Y')
                if 'head_tail' in properties:
                    new_constraint.head_tail = properties['head_tail']
                        
            else:
                # 通用约束处理
                for attr_name, attr_value in properties.items():
                    if hasattr(new_constraint, attr_name):
                        try:
                            if attr_name == 'target' and attr_value:
                                # 目标对象重定向
                                setattr(new_constraint, attr_name, target_rig)
                            else:
                                setattr(new_constraint, attr_name, attr_value)
                        except Exception as e:
                            print(f"        ⚠ 设置属性失败 {attr_name}: {e}")
            
            return True
            
        except Exception as e:
            print(f"    ❌ 应用约束失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_single_driver(self, target_rig, target_bone_name: str, 
                           driver_data: Dict, bone_mapping: Dict) -> bool:
        """应用单个驱动器（增强版：支持约束属性驱动器）"""
        try:
            data_path = driver_data.get('data_path', '')
            array_index = driver_data.get('array_index', 0)
            
            # 替换骨骼名称路径
            original_data_path = data_path
            
            # 使用正则表达式替换骨骼名称
            import re
            pattern = r'pose\.bones\[(["\'])([^"\']+)\1\]'
            def replace_bone_name(match):
                quote = match.group(1)
                old_bone_name = match.group(2)
                new_bone_name = bone_mapping.get(old_bone_name, target_bone_name)
                return f'pose.bones[{quote}{new_bone_name}{quote}]'
            
            data_path = re.sub(pattern, replace_bone_name, data_path)
            
            print(f"        📍 驱动器路径: {original_data_path}")
            if data_path != original_data_path:
                print(f"        🔄 重定向路径: {data_path}")
            
            # 检查驱动器类型
            if self._is_constraint_property_driver(data_path):
                # 约束属性驱动器（如 constraints["name"].influence）
                return self._apply_constraint_property_driver(
                    target_rig, target_bone_name, data_path, driver_data, bone_mapping
                )
            elif self._is_custom_property_driver(driver_data):
                # 自定义属性驱动器
                target_pose_bone = target_rig.pose.bones[target_bone_name]
                return self._apply_custom_property_driver(
                    target_pose_bone, data_path, driver_data, bone_mapping, target_rig
                )
            else:
                # 变换驱动器
                target_pose_bone = target_rig.pose.bones[target_bone_name]
                return self._apply_transform_driver(
                    target_pose_bone, data_path, array_index, driver_data, bone_mapping, target_rig
                )
                
        except Exception as e:
            print(f"    ❌ 应用驱动器失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _is_constraint_property_driver(self, data_path: str) -> bool:
        """检查是否是约束属性驱动器"""
        # 检查路径是否包含 constraints["name"].property 格式
        import re
        constraint_pattern = r'\.constraints\[["\'][^"\']+["\']\]\.[a-zA-Z_]+'
        return bool(re.search(constraint_pattern, data_path))
    
    def _apply_constraint_property_driver(self, target_rig, target_bone_name: str, 
                                        data_path: str, driver_data: Dict, bone_mapping: Dict) -> bool:
        """应用约束属性驱动器（如：约束的influence属性）"""
        try:
            print(f"        🔗 约束属性驱动器: {data_path}")
            
            # 解析约束名称和属性名称
            import re
            
            # 匹配模式：constraints["constraint_name"].property_name
            constraint_match = re.search(r'\.constraints\[(["\'])([^"\']+)\1\]\.([a-zA-Z_]+)', data_path)
            
            if not constraint_match:
                print(f"        ❌ 无法解析约束路径: {data_path}")
                return False
            
            constraint_name = constraint_match.group(2)
            property_name = constraint_match.group(3)
            
            print(f"        📋 约束名称: {constraint_name}")
            print(f"        🎯 属性名称: {property_name}")
            
            # 检查目标骨骼是否存在
            if target_bone_name not in target_rig.pose.bones:
                print(f"        ❌ 目标骨骼不存在: {target_bone_name}")
                return False
            
            target_pose_bone = target_rig.pose.bones[target_bone_name]
            
            # 检查约束是否存在
            target_constraint = None
            for constraint in target_pose_bone.constraints:
                if constraint.name == constraint_name:
                    target_constraint = constraint
                    break
            
            if not target_constraint:
                print(f"        ❌ 约束不存在: {constraint_name}")
                print(f"        📋 可用约束: {[c.name for c in target_pose_bone.constraints]}")
                return False
            
            # 检查属性是否存在
            if not hasattr(target_constraint, property_name):
                print(f"        ❌ 约束属性不存在: {property_name}")
                return False
            
            # 构建完整的驱动器路径（针对目标rig对象）
            # 格式：pose.bones["bone_name"].constraints["constraint_name"].property_name
            full_data_path = f'pose.bones["{target_bone_name}"].constraints["{constraint_name}"].{property_name}'
            
            print(f"        🎯 最终路径: {full_data_path}")
            
            # 创建驱动器
            try:
                driver = target_rig.driver_add(full_data_path)
                if hasattr(driver, '__len__'):  # 如果返回列表，取第一个
                    driver = driver[0]
                
                # 配置驱动器
                self._configure_driver(driver, driver_data, bone_mapping, target_rig)
                
                # 验证驱动器创建
                if self._validate_constraint_driver(target_constraint, property_name, driver, driver_data):
                    print(f"        ✅ 约束属性驱动器创建成功: {constraint_name}.{property_name}")
                    return True
                else:
                    print(f"        ⚠ 约束属性驱动器验证失败")
                    return False
                    
            except Exception as driver_error:
                print(f"        ❌ 创建约束驱动器失败: {driver_error}")
                return False
                
        except Exception as e:
            print(f"        ❌ 约束属性驱动器应用失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _validate_constraint_driver(self, constraint, property_name: str, driver, driver_data: Dict) -> bool:
        """验证约束驱动器创建是否成功"""
        try:
            # 检查驱动器基本配置
            if not driver or not driver.driver:
                return False
            
            # 检查驱动器类型
            expected_type = driver_data.get('driver_type', 'SCRIPTED')
            if driver.driver.type != expected_type:
                print(f"          ⚠ 驱动器类型不匹配: 期望 {expected_type}, 实际 {driver.driver.type}")
            
            # 检查表达式
            expected_expression = driver_data.get('expression', '')
            if driver.driver.expression != expected_expression:
                print(f"          ⚠ 表达式不匹配: 期望 '{expected_expression}', 实际 '{driver.driver.expression}'")
            
            # 检查变量数量
            expected_vars = len(driver_data.get('variables', []))
            actual_vars = len(driver.driver.variables)
            if actual_vars != expected_vars:
                print(f"          ⚠ 变量数量不匹配: 期望 {expected_vars}, 实际 {actual_vars}")
            
            # 基本验证：约束属性应该是可驱动的
            if hasattr(constraint, property_name):
                current_value = getattr(constraint, property_name)
                print(f"          📊 当前属性值: {property_name} = {current_value}")
                return True
            else:
                print(f"          ❌ 约束属性不存在: {property_name}")
                return False
                
        except Exception as e:
            print(f"          ❌ 验证约束驱动器失败: {e}")
            return False
    
    def _apply_single_custom_property(self, target_pose_bone, prop_name: str, prop_data: Dict) -> bool:
        """应用单个自定义属性"""
        try:
            # 设置属性值
            target_pose_bone[prop_name] = prop_data['value']
            
            # 设置UI属性
            ui_data = prop_data.get('ui_data', {})
            if ui_data and prop_name in target_pose_bone.keys():
                id_props_ui = target_pose_bone.id_properties_ui(prop_name)
                
                if 'min' in ui_data and ui_data['min'] is not None:
                    id_props_ui.update(min=ui_data['min'])
                if 'max' in ui_data and ui_data['max'] is not None:
                    id_props_ui.update(max=ui_data['max'])
                if 'description' in ui_data and ui_data['description']:
                    id_props_ui.update(description=ui_data['description'])
            
            return True
            
        except Exception as e:
            print(f"    ❌ 应用自定义属性失败: {e}")
            return False


# 便捷函数

def load_bone_data_from_template(template_name: str, bone_names: List[str] = None, 
                                search_dirs: List[str] = None) -> Dict[str, Dict]:
    """从模板文件加载骨骼数据的便捷函数"""
    loader = BlendTemplateLoader(template_name=template_name)
    template_data = loader.load_template_data(target_bone_names=bone_names)
    
    if template_data and 'bone_data' in template_data:
        return template_data['bone_data']
    return {}

def apply_template_to_rig(target_rig, template_name: str, bone_mapping: Dict[str, str] = None,
                         target_bone_names: List[str] = None) -> bool:
    """将模板数据应用到绑定的便捷函数"""
    loader = BlendTemplateLoader(template_name=template_name)
    template_data = loader.load_template_data(target_bone_names=target_bone_names)
    
    if template_data and 'bone_data' in template_data:
        return loader.apply_bone_data_to_rig(target_rig, template_data['bone_data'], bone_mapping)
    return False


# 测试和调试函数
def test_constraint_driver_parsing():
    """测试约束属性驱动器路径解析"""
    loader = BlendTemplateLoader()
    
    # 测试路径示例
    test_paths = [
        'pose.bones["NebOffset-lip.T"].constraints["lip_T.R"].influence',
        'pose.bones["NebOffset-brow.T.L.003"].constraints["ACTION_Constraint"].influence',
        'pose.bones["NebOffset-lip.B"].constraints["复制变换"].mute',
        'pose.bones["NebOffset-lip.T"].location',  # 不是约束属性
        'pose.bones["NebOffset-lip.T"]["custom_prop"]',  # 自定义属性
    ]
    
    print("🧪 测试约束属性驱动器路径解析:")
    
    for path in test_paths:
        is_constraint = loader._is_constraint_property_driver_data(path)
        is_custom = loader._is_custom_property_driver({'data_path': path})
        
        if is_constraint:
            # 解析约束名称和属性
            import re
            constraint_match = re.search(r'\.constraints\[(["\'])([^"\']+)\1\]\.([a-zA-Z_]+)', path)
            if constraint_match:
                constraint_name = constraint_match.group(2)
                property_name = constraint_match.group(3)
                print(f"  🔗 约束驱动器: {path}")
                print(f"      约束: {constraint_name}")
                print(f"      属性: {property_name}")
            else:
                print(f"  ❌ 约束路径解析失败: {path}")
        elif is_custom:
            print(f"  🎯 自定义属性驱动器: {path}")
        else:
            print(f"  🔄 变换驱动器: {path}")
    
    print("🧪 测试完成")

if __name__ == "__main__":
    # 运行测试
    test_constraint_driver_parsing()