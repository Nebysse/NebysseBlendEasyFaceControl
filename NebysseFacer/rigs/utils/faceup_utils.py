"""
FaceUP Utils - 面部绑定实用工具模块

此模块包含从 faceup_con.py 抽取的所有功能性函数，
以提高代码的模块化和可维护性。

现在统一使用Blender原生.blend文件作为模板，提供更完整的数据支持。
JSON模板功能已移至 faceup_utils_json_legacy.py 作为备份。
"""

import os
import bpy
from rigify.utils.bones import BoneDict
from .blend_template_loader import BlendTemplateLoader, apply_template_to_rig


# ================================
# 模板管理类
# ================================

class TemplateManager:
    """模板管理器 - 处理所有模板相关功能"""
    
    def __init__(self, rig_instance):
        self.rig = rig_instance
        self.template_data_to_cleanup = None
        self.blend_loader = None
    
    def find_template_rig_object(self):
        """查找模板rig对象（增强版：支持主动加载）
        
        Returns:
            模板rig对象，如果没找到返回None
        """
        print("🔍 TemplateManager: 开始查找模板rig对象...")
        
        # 方法1: 查找场景中名称包含"template"或"Template"的armature对象
        print("🔍 方法1：按名称查找模板rig...")
        for obj in bpy.context.scene.objects:
            if (obj.type == 'ARMATURE' and 
                obj != self.rig.obj and
                ('template' in obj.name.lower() or 'Template' in obj.name)):
                print(f"✅ 找到模板rig（按名称）: {obj.name}")
                return obj
        
        # 方法2: 精确查找特定的模板rig名称
        print("🔍 方法2：精确名称匹配...")
        target_names = [
            "Nebysse_FaceUP_Tem.Rig",
            "Nebysse_FaceUP_Tem",
            "FaceUP_Tem.Rig", 
            "FaceUP_Tem"
        ]
        
        for target_name in target_names:
            if target_name in bpy.data.objects:
                obj = bpy.data.objects[target_name]
                if obj.type == 'ARMATURE':
                    print(f"✅ 找到模板rig（精确匹配）: {obj.name}")
                    return obj
        
        # 方法3: 查找场景中其他包含NebOffset骨骼的armature对象
        print("🔍 方法3：按NebOffset骨骼查找...")
        for obj in bpy.context.scene.objects:
            if (obj.type == 'ARMATURE' and 
                obj != self.rig.obj):
                # 检查是否包含NebOffset骨骼
                neboffset_bones = [bone for bone in obj.pose.bones if bone.name.startswith('NebOffset-')]
                if len(neboffset_bones) > 5:  # 至少有5个NebOffset骨骼才认为是模板
                    print(f"✅ 找到模板rig（按NebOffset骨骼）: {obj.name} (包含{len(neboffset_bones)}个NebOffset骨骼)")
                    return obj
        
        # 方法4: 从已有的blend_loader查找模板armature
        print("🔍 方法4：从blend_loader查找...")
        if hasattr(self, 'blend_loader') and self.blend_loader:
            template_obj = self.blend_loader.get_template_armature()
            if template_obj:
                print(f"✅ 找到模板rig（从blend文件）: {template_obj.name}")
                return template_obj
        
        # 方法5: 主动加载模板文件
        print("🔍 方法5：主动加载模板文件...")
        try:
            # 如果还没有blend_loader，创建一个
            if not hasattr(self, 'blend_loader') or not self.blend_loader:
                print("🔧 创建新的blend_loader...")
                self.blend_loader = BlendTemplateLoader(template_name="Nebysse_FaceUP_Tem.blend")
            
            # 尝试加载模板数据
            print("📂 加载模板数据...")
            template_data = self.blend_loader.load_template_data()
            
            if template_data and 'armature' in template_data:
                template_armature = template_data['armature']
                print(f"✅ 找到模板rig（主动加载）: {template_armature.name}")
                
                # 确保模板对象在场景中可见
                if template_armature.name not in bpy.context.scene.collection.objects:
                    try:
                        bpy.context.scene.collection.objects.link(template_armature)
                        print(f"🔗 将模板rig链接到场景: {template_armature.name}")
                    except Exception as link_error:
                        print(f"⚠ 链接模板rig到场景失败: {link_error}")
                
                return template_armature
            else:
                print("⚠ 模板数据加载失败或没有armature对象")
                
        except Exception as e:
            print(f"⚠ 主动加载模板文件失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("⚠ 未找到模板rig对象")
        
        # 显示调试信息
        current_armatures = [obj.name for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
        print(f"🔧 当前场景armature对象 ({len(current_armatures)} 个): {current_armatures}")
        
        return None
    
    def find_blend_template_file(self):
        """查找 Blender 模板文件路径"""
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        # 从 utils 文件夹向上两级到 NebysseFacer 根目录
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        template_path = os.path.join(parent_dir, "templates", "Nebysse_FaceUP_Tem.blend")
        
        print(f"查找 Blender 模板文件: {template_path}")
        
        if os.path.exists(template_path):
            print(f"✓ 找到 Blender 模板文件: {template_path}")
            return template_path
        else:
            print(f"✗ Blender 模板文件不存在: {template_path}")
            return None
    
    def load_faceroot_data_from_blend(self) -> bool:
        """
        从.blend模板文件加载face-root数据（推荐方法）
        
        Returns:
            加载是否成功
        """
        try:
            print("🎯 开始从Blender模板文件加载Neb_face-root数据...")
            
            # 创建blend模板加载器
            self.blend_loader = BlendTemplateLoader(template_name="Nebysse_FaceUP_Tem.blend")
            
            # 只加载Neb_face-root骨骼的数据
            template_data = self.blend_loader.load_template_data(target_bone_names=["Neb_face-root"])
            
            if not template_data or not template_data.get('bone_data'):
                print("⚠ 从Blender模板加载失败")
                return False
            
            bone_data = template_data['bone_data']
            
            if 'Neb_face-root' not in bone_data:
                print("⚠ 模板中没有Neb_face-root骨骼数据")
                return False
            
            face_root_data = bone_data['Neb_face-root']
            custom_props = face_root_data.get('custom_properties', {})
            drivers = face_root_data.get('drivers', [])
            
            print(f"✅ 从Blender模板加载成功:")
            print(f"   📝 自定义属性: {len(custom_props)} 个")
            # print(f"   🔄 驱动器: {len(drivers)} 个") # 删除debug打印
            
            # 应用到当前绑定
            return self._apply_blend_template_data(face_root_data)
            
        except Exception as e:
            print(f"❌ 从Blender模板加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_blend_template_data(self, face_root_data: dict) -> bool:
        """应用从Blender模板加载的数据"""
        if not hasattr(self.rig, 'faceroot_bone') or not self.rig.faceroot_bone:
            print("⚠ faceroot_bone 不存在，跳过数据应用")
            return False
        
        try:
            # 应用自定义属性
            success = self._apply_custom_properties_from_blend(face_root_data.get('custom_properties', {}))
            
            # 应用驱动器
            if success:
                success = self._apply_drivers_from_blend(face_root_data.get('drivers', []))
            
            return success
            
        except Exception as e:
            print(f"❌ 应用Blender模板数据失败: {e}")
            return False
    
    def _apply_custom_properties_from_blend(self, custom_props: dict) -> bool:
        """从Blender模板应用自定义属性"""
        if not custom_props:
            return True
        
        try:
            pose_bone = self.rig.obj.pose.bones[self.rig.faceroot_bone]
            
            applied_count = 0
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
                    
                    applied_count += 1
                    
                except Exception as e:
                    print(f"⚠ 设置属性失败 {prop_name}: {e}")
                    continue
            
            return applied_count > 0
            
        except Exception as e:
            print(f"❌ 应用自定义属性失败: {e}")
            return False
    
    def _apply_drivers_from_blend(self, drivers: list) -> bool:
        """从Blender模板应用驱动器"""
        if not drivers:
            return True
        
        try:
            pose_bone = self.rig.obj.pose.bones[self.rig.faceroot_bone]
            
            applied_count = 0
            for driver_data in drivers:
                try:
                    # 解析data_path，提取属性名
                    data_path = driver_data['data_path']
                    
                    # 提取属性名称
                    if '["' in data_path and '"]' in data_path:
                        start = data_path.find('["') + 2
                        end = data_path.find('"]', start)
                        prop_name = data_path[start:end]
                        
                        # 确保属性存在
                        if prop_name not in pose_bone.keys():
                            pose_bone[prop_name] = 0.0
                        
                        # 创建驱动器 - 自定义属性不需要array_index参数
                        driver = pose_bone.driver_add(f'["{prop_name}"]')
                        if driver:
                            driver.driver.type = driver_data.get('driver_type', 'SCRIPTED')
                            driver.driver.expression = driver_data.get('expression', '')
                            
                            # 清除现有变量 - 使用Rigify官方推荐的方法 (Blender 4.1+)
                            for var in list(driver.driver.variables):
                                driver.driver.variables.remove(var)
                            
                            # 添加变量
                            for var_data in driver_data.get('variables', []):
                                var = driver.driver.variables.new()
                                var.name = var_data['name']
                                var.type = var_data['type']
                                
                                for i, target_data in enumerate(var_data.get('targets', [])):
                                    if i >= len(var.targets):
                                        break
                                    
                                    target = var.targets[i]
                                    target.id = self.rig.obj
                                    target.bone_target = target_data.get('bone_target', '')
                                    target.data_path = target_data.get('data_path', '')
                                    target.transform_type = target_data.get('transform_type', 'LOC_X')
                                    target.transform_space = target_data.get('transform_space', 'LOCAL_SPACE')
                            
                            applied_count += 1
                    
                except Exception as e:
                    continue
            
            return applied_count > 0
            
        except Exception as e:
            # print(f"❌ 应用驱动器失败: {e}") # 删除debug打印
            return False
    
    def load_faceroot_template(self):
        """加载 Neb_face-root 模板数据（严格模式：失败直接报错，无回退机制）"""
        # 强制模式：只使用模板rig对象加载，失败直接抛出异常
        success = self.load_faceroot_data_from_template_rig()
        
        if success:
            print("✅ 使用模板rig对象加载成功")
            return {'source': 'template_rig', 'success': True}
        else:
            # 不再提供回退机制，直接报错
            error_msg = "❌ 模板rig对象加载失败，无法继续生成绑定"
            print(error_msg)
            print("💡 可能的解决方案：")
            print("   1. 检查模板文件是否存在且有效")
            print("   2. 确认模板rig对象名称正确")
            print("   3. 检查Blender版本兼容性")
            print("   4. 重新安装或修复模板文件")
            
            # 抛出异常终止生成过程
            raise RuntimeError(f"模板加载失败: {error_msg}")
    
    def load_faceroot_data_from_template_rig(self) -> bool:
        """
        从模板rig对象中的Neb_face-root骨骼复制自定义属性到Neb_face-root骨骼
        增强：防止重复加载，添加严格的错误检查
        
        执行顺序：
        1. 检查是否已加载模板（防止重复加载）
        2. 搜索自定义属性
        3. 获取自定义属性信息
        4. 复制自定义属性
        5. 验证自定义属性复制结果
        6. 处理驱动器（在自定义属性流程完成后）
        
        Returns:
            复制是否成功
        """
        try:
            print("🎯 开始从模板rig对象加载Neb_face-root数据...")
            
            # ==================== 防重复加载检查 ====================
            print("\n🔍 === 预检查阶段：防重复加载机制 ===")
            
            # 检查是否已经有blend模板加载器实例
            if hasattr(self, 'blend_loader') and self.blend_loader:
                print("⚠ 发现已存在的blend模板加载器，先清理...")
                try:
                    self.blend_loader.cleanup()
                    self.blend_loader = None
                    print("✓ 已清理现有的blend模板加载器")
                except Exception as e:
                    print(f"⚠ 清理现有加载器失败: {e}")
            
            # 检查场景中是否已存在模板对象
            existing_template_objects = []
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' and self._is_template_object(obj.name):
                    existing_template_objects.append(obj)
            
            if existing_template_objects:
                print(f"⚠ 发现 {len(existing_template_objects)} 个已存在的模板对象:")
                for obj in existing_template_objects:
                    print(f"  📍 {obj.name}")
                print("🧹 清理现有模板对象以防重复...")
                
                # 清理现有模板对象
                for obj in existing_template_objects:
                    try:
                        print(f"  🗑️ 清理现有模板对象: {obj.name}")
                        if obj == bpy.context.view_layer.objects.active:
                            bpy.context.view_layer.objects.active = None
                        obj.select_set(False)
                        bpy.data.objects.remove(obj)
                    except Exception as e:
                        print(f"  ⚠ 清理对象失败 {obj.name}: {e}")
                
                print("✓ 现有模板对象清理完成")
            else:
                print("✓ 未发现重复的模板对象")
            
            # 创建新的blend模板加载器
            print("🔧 创建新的blend模板加载器...")
            self.blend_loader = BlendTemplateLoader(template_name="Nebysse_FaceUP_Tem.blend")
            
            # ==================== 自定义属性处理流程 ====================
            print("\n📝 === 第一阶段：自定义属性处理流程 ===")
            
            # 1. 搜索和获取自定义属性信息
            print("🔍 1. 搜索自定义属性...")
            properties_success = self.blend_loader.copy_properties_from_template_rig(
                template_rig_name="Nebysse_FaceUP_Tem.Rig",
                source_bone_name="Neb_face-root", 
                target_rig=self.rig.obj,
                target_bone_name=self.rig.faceroot_bone
            )
            
            # 2. 验证自定义属性复制结果
            if properties_success:
                print("✅ 2. 自定义属性复制成功，验证结果...")
                self._verify_properties_after_copy()
            else:
                print("❌ 2. 自定义属性复制失败")
                
                # 严格模式：自定义属性复制失败直接报错
                error_msg = "自定义属性复制失败，模板rig对象可能不存在或无效"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            print("✅ 自定义属性处理流程完成\n")
            
            # ==================== 驱动器处理流程 ====================
            # print("🔄 === 第二阶段：驱动器处理流程（在自定义属性完成后）===") # 删除debug打印
            
            # 3. 处理驱动器（现在有属性保护机制）
            drivers_success = self.blend_loader.copy_drivers_from_template_rig(
                template_rig_name="Nebysse_FaceUP_Tem.Rig",
                source_bone_name="Neb_face-root",
                target_rig=self.rig.obj, 
                target_bone_name=self.rig.faceroot_bone
            )
            
            # 4. 驱动器处理后验证自定义属性是否被保护
            if drivers_success:
                self._verify_properties_after_drivers()
            else:
                pass
            
            # ==================== 最终结果 ====================
            if properties_success and drivers_success:
                return True
            elif properties_success:
                return True  # 自定义属性成功就算基本成功
            else:
                # 不应该到达这里，因为上面已经抛出异常了
                error_msg = "从模板rig对象复制数据完全失败"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
        except RuntimeError:
            # 重新抛出已知的运行时错误
            raise
        except Exception as e:
            error_msg = f"从模板rig对象加载过程中发生意外错误: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)
    
    def _verify_properties_after_copy(self):
        """自定义属性复制后的专门验证"""
        try:
            pose_bone = self.rig.obj.pose.bones[self.rig.faceroot_bone]
            custom_props = [key for key in pose_bone.keys() if not key.startswith('_')]
            
            print(f"✓ 自定义属性复制验证: 发现 {len(custom_props)} 个属性")
            
            if custom_props:
                # 显示属性值分布
                zero_count = 0
                non_zero_count = 0
                sample_props = []
                
                for prop_name in custom_props:
                    value = pose_bone[prop_name]
                    if value == 0.0:
                        zero_count += 1
                    else:
                        non_zero_count += 1
                        sample_props.append((prop_name, value))
                
                print(f"  📊 属性值分布: {non_zero_count} 个非零, {zero_count} 个零值")
                
                if sample_props:
                    print(f"  📝 非零属性示例:")
                    for prop_name, value in sample_props[:3]:
                        print(f"    • {prop_name}: {value}")
                    if len(sample_props) > 3:
                        print(f"    ... 还有 {len(sample_props) - 3} 个非零属性")
                
                print("✅ 自定义属性复制验证通过")
            else:
                print("❌ 自定义属性复制验证失败：没有发现属性")
                
        except Exception as e:
            print(f"⚠ 自定义属性复制验证失败: {e}")
    
    def _verify_properties_after_drivers(self):
        """驱动器复制后验证自定义属性完整性"""
        try:
            pose_bone = self.rig.obj.pose.bones[self.rig.faceroot_bone]
            custom_props = [key for key in pose_bone.keys() if not key.startswith('_')]
            
            # print(f"🔍 驱动器处理后验证: {len(custom_props)} 个自定义属性") # 删除debug打印
            
            if custom_props:
                # 统计数量分布但不输出调试信息
                zero_count = 0
                non_zero_count = 0
                
                for prop_name in custom_props:
                    prop_value = pose_bone[prop_name]
                    if prop_value == 0.0 or prop_value == 0:
                        zero_count += 1
                    else:
                        non_zero_count += 1
                
                # 不再输出统计结果的调试信息
                
                # 简单验证，不输出具体信息
                return True
            else:
                return False
                
        except Exception as e:
            # print(f"⚠ 驱动器后验证失败: {e}") # 删除debug打印
            return False
    
    def apply_drivers_from_template(self, template_data):
        """从模板数据应用驱动器到Neb_face-root骨骼"""
        if not template_data:
            # print("⚠ 模板数据为空，跳过驱动器应用") # 删除debug打印
            return
        
        # 获取 Neb_face-root 骨骼
        if not hasattr(self.rig, 'faceroot_bone') or not self.rig.faceroot_bone:
            return
        
        # 检查模板数据格式
        if isinstance(template_data, dict):
            # 处理 Blend 模板格式
            if 'Neb_face-root' in template_data:
                self._apply_drivers_from_blend(template_data['Neb_face-root'].get('drivers', []))
            elif 'bones' in template_data:
                # 处理 JSON 模板格式
                for bone_data in template_data['bones']:
                    if bone_data.get('name') == 'face-root':
                        self._apply_drivers_from_blend(bone_data.get('drivers', []))
        else:
            # print("⚠ 未知的模板格式，跳过驱动器应用") # 删除debug打印
            pass
    
    def find_existing_template_data(self):
        """查找已存在的模板数据"""
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and ("Nebysse_FaceUP_Tem" in obj.name or "FaceUP" in obj.name):
                return obj.data, obj
        return None
    
    def cleanup_template_data_complete(self):
        """完整清理所有模板数据"""
        print("🧹 执行完整的模板数据清理...")
        
        # 保存当前上下文状态
        original_active = bpy.context.view_layer.objects.active
        original_selected = list(bpy.context.selected_objects)
        original_mode = bpy.context.mode
        
        # 获取当前绑定对象（正在生成的rig，不是metarig）
        current_rig = self.rig.obj if hasattr(self.rig, 'obj') else None
        current_rig_name = current_rig.name if current_rig else None
        
        print(f"🛡️ 保护当前生成中的绑定对象: {current_rig_name}")
        print(f"📊 当前活动对象: {original_active.name if original_active else 'None'}")
        
        # 清理blend模板加载器
        if self.blend_loader:
            try:
                self.blend_loader.cleanup()
                self.blend_loader = None
                print("✓ Blend模板加载器已清理")
            except Exception as e:
                print(f"⚠ 清理blend模板加载器失败: {e}")
        
        cleaned_objects = 0
        cleaned_armatures = 0
        
        try:
            # 安全的清理所有模板相关的对象
            objects_to_remove = []
            for obj in bpy.data.objects:
                # 只清理明确的模板对象，保护当前正在生成的rig
                if (obj != current_rig and  # 不删除当前正在生成的rig对象
                    self._is_template_object(obj.name)):
                    objects_to_remove.append(obj)
            
            for obj in objects_to_remove:
                try:
                    print(f"  🗑️ 删除模板对象: {obj.name}")
                    # 如果对象是活动对象，先切换到当前rig对象
                    if obj == bpy.context.view_layer.objects.active:
                        if current_rig and current_rig.name in bpy.data.objects:
                            bpy.context.view_layer.objects.active = current_rig
                            print(f"    🔄 活动对象切换到当前rig: {current_rig.name}")
                        else:
                            bpy.context.view_layer.objects.active = None
                    
                    # 确保对象未被选中
                    obj.select_set(False)
                    
                    # 删除对象
                    bpy.data.objects.remove(obj)
                    cleaned_objects += 1
                except Exception as e:
                    print(f"⚠ 删除对象失败 {obj.name}: {e}")
            
            # 安全的清理所有模板相关的骨架数据
            armatures_to_remove = []
            for armature in bpy.data.armatures:
                # 只清理明确的模板骨架，保护当前rig的骨架
                if (armature != (current_rig.data if current_rig else None) and
                    self._is_template_armature(armature.name)):
                    armatures_to_remove.append(armature)
            
            for armature in armatures_to_remove:
                try:
                    print(f"  🗑️ 删除模板骨架: {armature.name}")
                    bpy.data.armatures.remove(armature)
                    cleaned_armatures += 1
                except Exception as e:
                    print(f"⚠ 删除骨架失败 {armature.name}: {e}")
            
            print(f"✓ 清理完成: {cleaned_objects} 个对象, {cleaned_armatures} 个骨架")
            
            # 清理损坏的驱动器
            self._cleanup_broken_drivers()
            
        except Exception as e:
            print(f"⚠ 清理模板数据时出错: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 智能恢复上下文：优先确保Rigify期望的活动对象状态
            try:
                # 最重要：确保当前正在生成的rig对象是活动的
                if current_rig and current_rig.name in bpy.data.objects:
                    # 设置当前rig为活动对象（Rigify生成过程的要求）
                    bpy.context.view_layer.objects.active = current_rig
                    current_rig.select_set(True)
                    print(f"✅ 确保当前rig为活动对象: {current_rig.name}")
                elif original_active and original_active.name in bpy.data.objects:
                    # 如果当前rig不存在，恢复原始活动对象
                    bpy.context.view_layer.objects.active = original_active
                    print(f"🔄 恢复原始活动对象: {original_active.name}")
                
                # 恢复选择状态（但不影响活动对象）
                for obj in original_selected:
                    # 安全检查：确保对象仍然存在且有效
                    try:
                        if obj and hasattr(obj, 'name') and obj.name in bpy.data.objects:
                            obj_ref = bpy.data.objects[obj.name]
                            obj_ref.select_set(True)
                    except (ReferenceError, AttributeError):
                        # 对象已被删除或引用已失效，跳过
                        pass
                    except Exception as e:
                        print(f"⚠ 恢复对象选择状态时出错: {e}")
                        pass
                
                # 更新视图层
                bpy.context.view_layer.update()
                
                final_active = bpy.context.view_layer.objects.active
                print(f"✓ 最终活动对象: {final_active.name if final_active else 'None'}")
                
            except Exception as restore_error:
                print(f"⚠ 清理后恢复上下文时出错: {restore_error}")
                import traceback
                traceback.print_exc()
                
                # 最后的安全措施：确保有活动对象且是当前rig
                try:
                    if current_rig and current_rig.name in bpy.data.objects:
                        bpy.context.view_layer.objects.active = current_rig
                        current_rig.select_set(True)
                        print(f"🆘 紧急确保rig为活动对象: {current_rig.name}")
                    elif not bpy.context.view_layer.objects.active:
                        # 如果没有活动对象，找一个骨架作为活动对象
                        for obj in bpy.data.objects:
                            if obj.type == 'ARMATURE':
                                bpy.context.view_layer.objects.active = obj
                                obj.select_set(True)
                                print(f"🆘 紧急设置活动对象: {obj.name}")
                                break
                except:
                    pass

    def _cleanup_broken_drivers(self):
        """清理损坏的驱动器（基于Blender社区最佳实践）"""
        try:
            # print("🔧 开始清理损坏的驱动器...") # 删除debug打印
            
            # 获取所有包含bpy_prop_collection的数据集合
            from bpy.types import bpy_prop_collection
            colls = [
                p for p in dir(bpy.data)
                if isinstance(getattr(bpy.data, p), bpy_prop_collection)
            ]
            
            total_removed = 0
            processed_objects = 0
            
            for collection_name in colls:
                collection = getattr(bpy.data, collection_name, [])
                for obj in collection:
                    animation_data = getattr(obj, "animation_data", None)
                    if not animation_data:
                        continue
                    
                    processed_objects += 1
                    broken_drivers = []
                    
                    # 查找损坏的驱动器
                    for driver in animation_data.drivers:
                        try:
                            # 尝试解析驱动器的数据路径
                            obj.path_resolve(driver.data_path)
                        except ValueError:
                            # 路径解析失败，说明驱动器已损坏
                            broken_drivers.append(driver)
                    
                    # 删除损坏的驱动器
                    while broken_drivers:
                        broken_driver = broken_drivers.pop()
                        animation_data.drivers.remove(broken_driver)
                        total_removed += 1
            
            if total_removed > 0:
                # print(f"🧹 清理完成: 删除了 {total_removed} 个损坏的驱动器") # 删除debug打印
                # print(f"📊 检查了 {processed_objects} 个包含动画数据的对象") # 删除debug打印
                pass
            else:
                # print(f"✓ 驱动器检查完成: 未发现损坏的驱动器") # 删除debug打印
                # print(f"📊 检查了 {processed_objects} 个包含动画数据的对象") # 删除debug打印
                pass
                
        except Exception as e:
            # print(f"⚠ 清理损坏驱动器时出错: {e}") # 删除debug打印
            import traceback
            traceback.print_exc()

    def _is_template_object(self, obj_name: str) -> bool:
        """判断是否为模板对象"""
        template_patterns = [
            "Nebysse_FaceUP_Tem",      # 主要模板模式
            "Nebysse_FaceUP_Tem.Rig",  # 特定的rig对象
            "TemplateFaceRig",         # 备用模板模式  
            "FaceUP_Tem",              # 简化模板模式
            "FaceUP_Template",         # 完整模板模式
        ]
        
        for pattern in template_patterns:
            if pattern in obj_name:
                return True
        return False
    
    def _is_template_armature(self, armature_name: str) -> bool:
        """判断是否为模板骨架"""
        template_patterns = [
            "Nebysse_FaceUP_Tem",      # 主要模板模式
            "FaceUP_Tem",              # 简化模板模式
            "FaceUP_Template",         # 完整模板模式
        ]
        
        for pattern in template_patterns:
            if pattern in armature_name:
                return True
        return False

    def find_template_rig_object_safe(self, current_rig_obj):
        """安全地查找模板rig对象（专为Rigify生成过程设计）
        
        Args:
            current_rig_obj: 当前正在生成的rig对象（用于排除）
            
        Returns:
            模板rig对象，如果没找到返回None
        """
        print("🔍 TemplateManager: 安全查找模板rig对象...")
        
        # === 保护当前状态 ===
        original_active = bpy.context.view_layer.objects.active
        original_mode = bpy.context.mode
        
        try:
            # 方法1: 在当前场景中查找已存在的模板rig
            print("🔍 方法1：在当前场景查找已存在模板...")
            
            # 精确名称匹配
            target_names = [
                "Nebysse_FaceUP_Tem.Rig",
                "Nebysse_FaceUP_Tem",
                "FaceUP_Tem.Rig"
            ]
            
            for target_name in target_names:
                if target_name in bpy.data.objects:
                    obj = bpy.data.objects[target_name]
                    if (obj.type == 'ARMATURE' and 
                        obj != current_rig_obj and
                        obj.name in bpy.context.scene.collection.objects):
                        print(f"✅ 找到现有模板rig: {obj.name}")
                        return obj
            
            # 方法2: 按NebOffset骨骼数量判断
            print("🔍 方法2：按NebOffset骨骼查找...")
            for obj in bpy.context.scene.objects:
                if (obj.type == 'ARMATURE' and 
                    obj != current_rig_obj):
                    try:
                        neboffset_bones = [bone for bone in obj.pose.bones if bone.name.startswith('NebOffset-')]
                        if len(neboffset_bones) > 5:
                            print(f"✅ 找到模板rig（按NebOffset骨骼）: {obj.name} ({len(neboffset_bones)}个)")
                            return obj
                    except:
                        continue
            
            # 方法3: 尝试从已加载的blend_loader获取（如果存在）
            print("🔍 方法3：从blend_loader查找...")
            if hasattr(self, 'blend_loader') and self.blend_loader:
                try:
                    template_obj = self.blend_loader.get_template_armature()
                    if template_obj and template_obj != current_rig_obj:
                        print(f"✅ 从blend_loader找到: {template_obj.name}")
                        return template_obj
                except Exception as e:
                    print(f"⚠ blend_loader查找失败: {e}")
            
            # 方法4: 作为最后手段，尝试安全地加载模板文件
            print("🔍 方法4：安全加载模板文件...")
            return self._safe_load_template_file(current_rig_obj)
            
        except Exception as e:
            print(f"❌ 安全查找过程出错: {e}")
            return None
            
        finally:
            # === 确保恢复原始状态 ===
            try:
                # 优先确保当前rig是活动的
                if current_rig_obj and current_rig_obj.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = current_rig_obj
                elif original_active and original_active.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = original_active
                
                # 恢复模式
                if bpy.context.mode != original_mode:
                    if original_mode == 'EDIT_ARMATURE':
                        bpy.ops.object.mode_set(mode='EDIT')
                    elif original_mode == 'POSE':
                        bpy.ops.object.mode_set(mode='POSE')
                    else:
                        bpy.ops.object.mode_set(mode='OBJECT')
                
                # 更新视图层
                bpy.context.view_layer.update()
                
            except Exception as restore_error:
                print(f"⚠ 恢复状态时出错: {restore_error}")
                # 紧急恢复
                try:
                    bpy.context.view_layer.objects.active = current_rig_obj
                except:
                    pass
    
    def _safe_load_template_file(self, current_rig_obj):
        """安全地加载模板文件（最小化状态影响）"""
        try:
            print("📂 尝试安全加载模板文件...")
            
            # 确保在对象模式
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # 如果还没有blend_loader，创建一个
            if not hasattr(self, 'blend_loader') or not self.blend_loader:
                self.blend_loader = BlendTemplateLoader(template_name="Nebysse_FaceUP_Tem.blend")
            
            # 尝试加载模板数据，但设置安全模式
            template_data = self.blend_loader.load_template_data_safe()
            
            if template_data and 'armature' in template_data:
                template_armature = template_data['armature']
                
                # 确保模板对象在场景中（但不激活）
                if template_armature.name not in bpy.context.scene.collection.objects:
                    try:
                        bpy.context.scene.collection.objects.link(template_armature)
                        print(f"🔗 模板rig已链接到场景: {template_armature.name}")
                    except:
                        print("⚠ 链接模板rig到场景失败")
                
                print(f"✅ 安全加载成功: {template_armature.name}")
                return template_armature
            else:
                print("⚠ 模板文件加载失败或无效")
                return None
                
        except Exception as e:
            print(f"⚠ 安全加载模板文件失败: {e}")
            return None
        
        finally:
            # 确保当前rig保持活动状态
            try:
                if current_rig_obj and current_rig_obj.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = current_rig_obj
                    current_rig_obj.select_set(True)
            except:
                pass


# ================================
# 骨骼检测类
# ================================

class BoneDetector:
    """骨骼检测器 - 处理原生rigify骨骼检测"""
    
    @staticmethod
    def get_default_face_bone_mapping():
        """获取默认的面部骨骼映射关系"""
        return {
            # 下颚控制
            "jaw_master": "Neb_jaw_master",
            "teeth.B": "Neb_teeth.B",
            "teeth.T": "Neb_teeth.T",
            
            # 嘴唇基础控制
            "lip.T": "Neb_lip.T",
            "lip.B": "Neb_lip.B",
            
            # 嘴唇细分控制
            "lip.B.L.001": "Neb_lip.B.L.001",
            "lip.B.L.002": "Neb_lip.B.L.002",
            "lip.B.R.001": "Neb_lip.B.R.001", 
            "lip.B.R.002": "Neb_lip.B.R.002",
            "lip.T.L.001": "Neb_lip.T.L.001",
            "lip.T.L.002": "Neb_lip.T.L.002", 
            "lip.T.R.001": "Neb_lip.T.R.001",
            "lip.T.R.002": "Neb_lip.T.R.002",
            
            # 嘴角控制
            "lip_end.L": "Neb_lip_end.L",
            "lip_end.R": "Neb_lip_end.R",
            "lip_end.L.002": "Neb_lip_end.L.002",
            "lip_end.R.002": "Neb_lip_end.R.002",
            
            # 眼睑控制
            "lid.B.L.002": "Neb_lid.B.L.002",
            "lid.T.L.002": "Neb_lid.T.L.002", 
            "lid.B.R.002": "Neb_lid.B.R.002",
            "lid.T.R.002": "Neb_lid.T.R.002",
            
            # 眉毛控制
            "brow.T.L.001": "Neb_brow.T.L.001",
            "brow.T.L.002": "Neb_brow.T.L.002",
            "brow.T.L.003": "Neb_brow.T.L.003",
            "brow.T.R.001": "Neb_brow.T.R.001",
            "brow.T.R.002": "Neb_brow.T.R.002",
            "brow.T.R.003": "Neb_brow.T.R.003",
        }
    
    @staticmethod
    def detect_face_bone_existence(armature_obj):
        """检测是否存在face骨骼，用于判断是否为rigify骨架"""
        if not armature_obj or armature_obj.type != 'ARMATURE':
            return False
        
        # 🚫 新规则：跳过face骨骼存在性检测，默认用户已经设置
        print("🚫 新规则：跳过face骨骼存在性检测")
        print("💡 假设用户已经正确设置了face骨骼")
        print("✅ 直接返回True，判断为rigify骨架")
        
        return True
    
    @staticmethod
    def detect_rigify_face_bones(armature_obj):
        """检测骨架中是否存在原生rigify face骨骼，并返回映射关系"""
        print("🔍 开始检测原生rigify face骨骼...")
        
        if not armature_obj or armature_obj.type != 'ARMATURE':
            print("❌ 当前对象不是骨架或为空")
            return {}
        
        # 🚫 新规则：跳过所有rigify面部骨骼检测
        print("🚫 新规则：跳过rigify面部骨骼检测，默认用户已经设置")
        print("💡 假设用户已经正确配置了rigify面部骨架")
        print("🎯 直接返回空映射，继续后续处理流程")
        
        return {}
    
    @staticmethod
    def smart_face_bone_detection(armature_obj, existing_bones):
        """智能面部骨骼检测方法"""
        detected_bones = {}
        
        # 1. 首先尝试标准映射
        print("🔍 尝试标准rigify面部骨骼映射...")
        rigify_face_mapping = BoneDetector.get_default_face_bone_mapping()
        missing_bones = []
        
        for rigify_name, neb_name in rigify_face_mapping.items():
            if rigify_name in existing_bones:
                detected_bones[rigify_name] = neb_name
                print(f"✓ 检测到标准骨骼: {rigify_name} -> 将生成: {neb_name}")
            else:
                missing_bones.append(rigify_name)
        
        # 2. 如果标准映射找到了骨骼，直接返回
        if detected_bones:
            print(f"✅ 标准映射成功，发现 {len(detected_bones)} 个骨骼")
            if missing_bones[:5]:
                print(f"  缺失示例: {', '.join(missing_bones[:5])}")
            return detected_bones
        
        # 3. 如果标准映射失败，使用智能模式检测
        print("🧠 标准映射未找到骨骼，启用智能检测模式...")
        return BoneDetector.intelligent_pattern_detection(existing_bones)
    
    @staticmethod
    def intelligent_pattern_detection(existing_bones):
        """智能模式检测 - 基于模式匹配"""
        detected_bones = {}
        
        # 定义面部骨骼模式
        face_patterns = {
            # 下颚和牙齿模式
            'jaw': [r'^jaw', r'jaw_master', r'mandible'],
            'teeth': [r'^teeth', r'tooth'],
            
            # 嘴唇模式
            'lip': [r'^lip\.', r'lip_'],
            
            # 眉毛模式  
            'brow': [r'^brow\.', r'eyebrow', r'brow_'],
            
            # 眼睑模式
            'lid': [r'^lid\.', r'eyelid', r'lid_'],
            
            # 眼部模式
            'eye': [r'^eye\.', r'eye_'],
            
            # 鼻子模式
            'nose': [r'^nose', r'nose\.'],
            
            # 脸颊模式
            'cheek': [r'^cheek\.', r'cheek_'],
            
            # 下巴模式
            'chin': [r'^chin', r'chin\.'],
            
            # 耳朵模式
            'ear': [r'^ear\.', r'ear_'],
            
            # 额头模式
            'forehead': [r'^forehead', r'forehead\.'],
            
            # 太阳穴模式
            'temple': [r'^temple', r'temple\.']
        }
        
        import re
        
        for bone_name in existing_bones:
            bone_lower = bone_name.lower()
            
            # 排除带前缀的骨骼（ORG-, DEF-, MCH-, WGT-）
            if any(prefix in bone_name for prefix in ['ORG-', 'DEF-', 'MCH-', 'WGT-']):
                continue
            
            # 检查每个模式
            for category, patterns in face_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, bone_lower):
                        # 生成对应的Neb_前缀名称
                        neb_name = f"Neb_{bone_name.replace('.', '_').replace('-', '_')}"
                        detected_bones[bone_name] = neb_name
                        print(f"✓ 智能检测到: {bone_name} -> {neb_name} (类别: {category})")
                        break
                if bone_name in [k for k in detected_bones.keys()]:
                    break
        
        if detected_bones:
            print(f"🧠 智能检测完成，发现 {len(detected_bones)} 个面部骨骼")
        else:
            print("❌ 智能检测也未找到面部骨骼")
        
        return detected_bones
    
    @staticmethod
    def detect_rigify_head_bone(armature_obj):
        """检测原生rigify的head骨骼"""
        if not armature_obj or armature_obj.type != 'ARMATURE':
            return None
        
        possible_head_bones = ["head", "Head", "head.001", "spine.006"]
        
        for bone_name in possible_head_bones:
            if bone_name in armature_obj.data.bones:
                print(f"✓ 检测到原生rigify head骨骼: {bone_name}")
                return bone_name
        
        print("⚠ 未检测到原生rigify head骨骼")
        return None


# ================================
# 生成管理类
# ================================

class GenerationManager:
    """生成管理器 - 处理骨骼生成逻辑"""
    
    def __init__(self, rig_instance):
        self.rig = rig_instance
    
    def get_manual_generation_mapping(self):
        """根据参数获取手动生成的骨骼映射"""
        print("\n🎯 === 手动生成模式 ===")
        
        # 🚫 新规则：跳过所有rigify面部骨骼检测
        print("🚫 新规则：跳过rigify面部骨骼检测，默认用户已经设置")
        print("💡 假设用户已经正确配置了rigify面部骨架")
        print("🎯 直接返回空映射，继续后续处理流程")
        
        return {}
        
        # ===== 以下代码已被禁用（保留备用） =====
        # generation_mode = getattr(self.rig.params, 'generation_mode', 'AUTO')
        # custom_order = getattr(self.rig.params, 'custom_generation_order', False)
        # 
        # print(f"📊 生成模式: {generation_mode}")
        # print(f"🔄 自定义顺序: {'启用' if custom_order else '禁用'}")
        # 
        # if generation_mode == 'AUTO':
        #     print("✓ 使用自动检测模式")
        #     return BoneDetector.detect_rigify_face_bones(self.rig.obj)
        # 
        # elif generation_mode == 'MANUAL':
        #     return self.get_manual_bone_mapping()
        # 
        # elif generation_mode == 'HYBRID':
        #     return self.get_hybrid_bone_mapping()
        # 
        # else:
        #     print(f"⚠ 未知的生成模式: {generation_mode}，回退到自动模式")
        #     return BoneDetector.detect_rigify_face_bones(self.rig.obj)
    
    def get_manual_bone_mapping(self):
        """获取手动模式的骨骼映射"""
        print("📝 使用手动选择模式")
        
        manual_list = getattr(self.rig.params, 'manual_bone_list', "")
        if not manual_list.strip():
            print("⚠ 手动骨骼列表为空，使用默认列表")
            manual_list = "jaw_master,teeth.B,teeth.T,lip.T,lip.B,brow.T.L.002,brow.T.R.002"
        
        bone_names = parse_bone_list(manual_list)
        print(f"📋 手动指定的骨骼列表 ({len(bone_names)} 个):")
        for i, name in enumerate(bone_names):
            print(f"  {i+1:2d}. {name}")
        
        manual_mapping = {}
        existing_bones = set(self.rig.obj.data.bones.keys())
        
        for rigify_name in bone_names:
            if rigify_name in existing_bones:
                neb_name = f"Neb_{rigify_name}"
                manual_mapping[rigify_name] = neb_name
                print(f"✓ 映射: {rigify_name} -> {neb_name}")
            else:
                print(f"⚠ 跳过不存在的骨骼: {rigify_name}")
        
        print(f"✅ 手动模式映射完成：{len(manual_mapping)} 个有效映射")
        return manual_mapping
    
    def get_hybrid_bone_mapping(self):
        """获取混合模式的骨骼映射"""
        print("🔄 使用混合模式")
        
        auto_mapping = BoneDetector.detect_rigify_face_bones(self.rig.obj)
        print(f"📊 自动检测到 {len(auto_mapping)} 个骨骼")
        
        # 处理排除列表
        exclude_list = getattr(self.rig.params, 'exclude_bones', "")
        if exclude_list.strip():
            exclude_bones = parse_bone_list(exclude_list)
            print(f"🚫 排除骨骼列表 ({len(exclude_bones)} 个): {exclude_bones}")
            
            for exclude_name in exclude_bones:
                if exclude_name in auto_mapping:
                    del auto_mapping[exclude_name]
                    print(f"  ✓ 已排除: {exclude_name}")
                else:
                    print(f"  ⚠ 排除失败（不存在）: {exclude_name}")
        
        # 处理额外添加列表
        add_list = getattr(self.rig.params, 'add_bones', "")
        if add_list.strip():
            add_bones = parse_bone_list(add_list)
            print(f"➕ 额外添加列表 ({len(add_bones)} 个): {add_bones}")
            
            existing_bones = set(self.rig.obj.data.bones.keys())
            for add_name in add_bones:
                if add_name in existing_bones and add_name not in auto_mapping:
                    neb_name = f"Neb_{add_name}"
                    auto_mapping[add_name] = neb_name
                    print(f"  ✓ 已添加: {add_name} -> {neb_name}")
                elif add_name in auto_mapping:
                    print(f"  ⚠ 已存在，跳过: {add_name}")
                else:
                    print(f"  ⚠ 添加失败（不存在）: {add_name}")
        
        print(f"✅ 混合模式映射完成：{len(auto_mapping)} 个有效映射")
        return auto_mapping


# ================================
# 约束管理类
# ================================

class ConstraintManager:
    """约束管理器 - 处理复制变换约束"""
    
    def __init__(self, rig_instance):
        self.rig = rig_instance
    
    def setup_copy_transform_constraints(self, bone_mapping):
        """为原生rigify骨骼设置复制变换约束到对应的Neb_前缀骨骼"""
        print("\n🔗 开始设置复制变换约束系统...")
        
        # 检查输入
        if not bone_mapping:
            print("❌ 骨骼映射表为空，无法设置约束")
            return
        
        # 获取约束参数
        params = getattr(self.rig, 'params', None)
        constraint_influence = getattr(params, 'constraint_influence', 1.0)
        mix_mode = getattr(params, 'constraint_mix_mode', 'BEFORE')
        target_space = getattr(params, 'constraint_target_space', 'LOCAL')
        owner_space = getattr(params, 'constraint_owner_space', 'LOCAL')
        
        print(f"⚙️ 约束参数设置:")
        print(f"   🎯 影响权重: {constraint_influence}")
        print(f"   🔀 混合模式: {mix_mode}")
        print(f"   📍 目标空间: {target_space}")
        print(f"   🏠 拥有者空间: {owner_space}")
        
        # 统计信息
        total_mapping = len(bone_mapping)
        print(f"🗂️ 骨骼映射表包含 {total_mapping} 个映射关系")
        print(f"🎯 约束方向：原生rigify骨骼 跟随 -> Neb_前缀骨骼")
        print(f"🛠️ 策略：使用rigify标准API，直接创建约束对象")
        
        # 预检查阶段：验证骨骼存在性
        print(f"\n🔍 === 预检查阶段：分析骨骼可用性 ===")
        
        # 检查生成的Neb_前缀骨骼
        neb_bones_count = len(self.rig.bones.neb_face_bones)
        print(f"🏗️ 已生成 {neb_bones_count} 个Neb_前缀骨骼")
        
        # 验证映射中的骨骼可用性
        valid_mappings = []
        missing_rigify_bones = []
        missing_neb_bones = []
        
        for rigify_name, neb_name in bone_mapping.items():
            # 检查原生rigify骨骼
            if rigify_name not in self.rig.obj.data.bones:
                missing_rigify_bones.append(rigify_name)
                continue
            
            # 检查Neb_前缀骨骼是否在生成的列表中
            if neb_name not in self.rig.bones.neb_face_bones:
                missing_neb_bones.append(neb_name)
                continue
                
            valid_mappings.append((rigify_name, neb_name))
        
        valid_count = len(valid_mappings)
        missing_rigify_count = len(missing_rigify_bones)
        missing_neb_count = len(missing_neb_bones)
        
        print(f"\n🔍 预检查结果：")
        print(f"   ✅ 可用映射: {valid_count} 个")
        print(f"   ❌ 缺失原生骨骼: {missing_rigify_count} 个")
        print(f"   ❌ 缺失目标骨骼: {missing_neb_count} 个")
        
        if missing_rigify_bones:
            print(f"   📋 缺失的原生骨骼: {missing_rigify_bones[:5]}")
            if len(missing_rigify_bones) > 5:
                print(f"       ... 还有 {len(missing_rigify_bones) - 5} 个")
        
        if missing_neb_bones:
            print(f"   �� 缺失的目标骨骼: {missing_neb_bones[:5]}")
            if len(missing_neb_bones) > 5:
                print(f"       ... 还有 {len(missing_neb_bones) - 5} 个")
        
        if valid_count == 0:
            print("❌ 没有可用的映射关系，跳过约束设置")
            return
        
        print(f"\n✅ 将为 {valid_count} 个有效映射设置约束")
        expected_success_rate = (valid_count / total_mapping) * 100
        print(f"🎯 预期成功率: {valid_count}/{total_mapping} ({expected_success_rate:.1f}%)")
        
        # 约束设置阶段：使用rigify标准API
        print(f"\n🔗 === 约束设置阶段：使用rigify标准API ===")
        
        constraint_count = 0
        updated_count = 0
        failed_count = 0
        
        for i, (rigify_name, neb_name) in enumerate(valid_mappings, 1):
            print(f"\n  🔸 [{i}/{valid_count}] 处理映射: {rigify_name} -> {neb_name}")
            
            try:
                # 获取姿态骨骼
                rigify_pbone = self.rig.obj.pose.bones[rigify_name]
                neb_bone_name = self.rig.bones.neb_face_bones[neb_name]
                
                print(f"    📌 原生骨骼: {rigify_pbone.name}")
                print(f"    📌 目标骨骼: {neb_bone_name}")
                
                # 检查现有约束
                existing_constraint = self._find_existing_constraint(rigify_pbone, neb_bone_name)
                
                if existing_constraint:
                    # 更新现有约束的所有参数
                    old_influence = existing_constraint.influence
                    existing_constraint.influence = constraint_influence
                    existing_constraint.mix_mode = mix_mode
                    existing_constraint.target_space = target_space
                    existing_constraint.owner_space = owner_space
                    updated_count += 1
                    print(f"    ✅ 更新现有约束: 影响权重 {old_influence:.2f} -> {constraint_influence:.2f}")
                    print(f"       混合模式: {mix_mode}")
                    print(f"       目标空间: {target_space}")
                    print(f"       拥有者空间: {owner_space}")
                    continue
                
                # 使用rigify标准API直接创建约束
                constraint = rigify_pbone.constraints.new('COPY_TRANSFORMS')
                constraint.name = f"Copy_{neb_name}"
                constraint.target = self.rig.obj
                constraint.subtarget = neb_bone_name
                constraint.mix_mode = mix_mode
                constraint.target_space = target_space
                constraint.owner_space = owner_space
                constraint.influence = constraint_influence
                
                constraint_count += 1
                print(f"    ✅ 新建约束: '{constraint.name}'")
                print(f"       目标: {constraint.target.name}.{constraint.subtarget}")
                print(f"       权重: {constraint.influence:.2f}")
                print(f"       混合模式: {constraint.mix_mode}")
                print(f"       目标空间: {constraint.target_space}")
                print(f"       拥有者空间: {constraint.owner_space}")
                
            except Exception as e:
                print(f"    ❌ 约束设置失败: {e}")
                print(f"    🔧 跳过当前骨骼，继续处理下一个骨骼...")
                import traceback
                traceback.print_exc()
                failed_count += 1
                continue
        
        # 最终结果统计
        successful_constraints = constraint_count + updated_count
        processed_mappings = successful_constraints + failed_count
        actual_success_rate = (successful_constraints / valid_count) * 100 if valid_count > 0 else 0
        overall_success_rate = (successful_constraints / total_mapping) * 100
        
        print(f"\n📊 === 约束设置结果汇总 ===")
        print(f"   🆕 新建约束: {constraint_count} 个")
        print(f"   🔄 更新约束: {updated_count} 个")
        print(f"   ❌ 设置失败: {failed_count} 个")
        print(f"   ⚠ 跳过骨骼: {total_mapping - valid_count} 个（骨骼缺失）")
        print(f"   📋 总计映射: {total_mapping} 个")
        print(f"   ✅ 有效处理成功率: {successful_constraints}/{valid_count} ({actual_success_rate:.1f}%)")
        print(f"   📊 总体成功率: {successful_constraints}/{total_mapping} ({overall_success_rate:.1f}%)")
        
        print(f"\n⚙️ 最终约束参数:")
        print(f"   📐 混合模式: {mix_mode}")
        print(f"   🎯 目标空间: {target_space}")
        print(f"   🏠 拥有者空间: {owner_space}")
        
        if successful_constraints > 0:
            print(f"\n✅ 约束系统激活：{successful_constraints} 个原生rigify骨骼现在会跟随Neb_前缀骨骼的变换")
            
            if failed_count > 0:
                print(f"⚠ 注意：{failed_count} 个映射在约束设置时失败")
                print(f"💡 建议检查失败骨骼的具体错误信息")
            
            if total_mapping - valid_count > 0:
                skipped_due_to_missing = total_mapping - valid_count
                print(f"💡 兼容提示：{skipped_due_to_missing} 个映射由于骨骼缺失而被跳过")
                print(f"   这是正常的兼容性行为，不影响已设置约束的正常运行")
                
        else:
            print(f"\n⚠ 警告：没有成功设置任何约束")
            print(f"💡 可能原因：")
            print(f"   1. 所有目标骨骼都缺失或无效")
            print(f"   2. 约束设置过程中发生技术错误")
            print(f"   3. Rigify系统或FaceUP系统生成不完整")
        
        print(f"\n🎯 约束设置完成！rigify标准API确保了最大兼容性。")
    
    def _find_existing_constraint(self, pose_bone, target_bone_name):
        """查找现有的复制变换约束"""
        for constraint in pose_bone.constraints:
            if (constraint.type == 'COPY_TRANSFORMS' and 
                hasattr(constraint, 'target') and 
                constraint.target == self.rig.obj and
                hasattr(constraint, 'subtarget') and
                constraint.subtarget == target_bone_name):
                return constraint
        return None


# ================================
# 实用函数
# ================================

def find_blend_template_file():
    """查找 Blender 模板文件路径（独立函数版本）"""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    template_path = os.path.join(parent_dir, "templates", "Nebysse_FaceUP_Tem.blend")
    
    if os.path.exists(template_path):
        return template_path
    return None


def detect_rigify_head_bone(armature_obj):
    """检测原生rigify的head骨骼（独立函数版本）"""
    return BoneDetector.detect_rigify_head_bone(armature_obj)


def parse_bone_list(bone_list_str):
    """解析骨骼列表字符串"""
    if not bone_list_str or not bone_list_str.strip():
        return []
    
    return [name.strip() for name in bone_list_str.split(',') if name.strip()]


def validate_bone_existence(armature_obj, bone_names):
    """验证骨骼是否存在于骨架中"""
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return {}
    
    existing_bones = set(armature_obj.data.bones.keys())
    result = {}
    
    for bone_name in bone_names:
        result[bone_name] = bone_name in existing_bones
    
    return result


def copy_bone_transforms_from_rigify(rig_instance, bone_mapping):
    """从原生rigify骨骼复制变换到对应的Neb_前缀骨骼"""
    if not hasattr(rig_instance.bones, 'neb_face_bones'):
        print("⚠ Neb_前缀骨骼未生成")
        return
    
    print("📍 开始复制原生rigify骨骼变换到Neb_前缀骨骼...")
    
    armature = rig_instance.obj
    copied_count = 0
    
    for rigify_name, neb_name in bone_mapping.items():
        if neb_name in rig_instance.bones.neb_face_bones:
            try:
                if rigify_name not in armature.data.bones:
                    print(f"⚠ 跳过不存在的原生骨骼: {rigify_name}")
                    continue
                
                rigify_bone = armature.data.bones[rigify_name]
                neb_bone_id = rig_instance.bones.neb_face_bones[neb_name]
                neb_bone = rig_instance.get_bone(neb_bone_id)
                
                if neb_bone:
                    neb_bone.head = rigify_bone.head.copy()
                    neb_bone.tail = rigify_bone.tail.copy()
                    neb_bone.roll = rigify_bone.roll
                    
                    copied_count += 1
                    
            except Exception as e:
                print(f"❌ 复制变换失败 {rigify_name} -> {neb_name}: {e}")
    
    print(f"📍 变换复制完成：成功复制 {copied_count} 个骨骼的变换") 