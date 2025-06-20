"""
FaceUP Utils - JSON模板加载功能（遗留/备份版本）

此文件包含原有的JSON模板加载功能，已不再使用，仅作为备份保存。
现在主要使用blend模板加载器（blend_template_loader.py）。

保存时间：2024年
替换原因：统一使用Blender原生.blend文件作为模板，提供更完整的数据支持
"""

import os
import json
import bpy


class JSONTemplateManagerLegacy:
    """JSON模板管理器（遗留版本）"""
    
    def __init__(self, rig_instance):
        self.rig = rig_instance
    
    def load_faceroot_template_json(self):
        """加载 face-root JSON 模板（备用方法）"""
        try:
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            
            template_path = os.path.join(parent_dir, "templates", "faceUP_faceroot.json")
            template_path = os.path.normpath(template_path)
            print(f"JSON模板文件路径: {template_path}")
            
            if not os.path.exists(template_path):
                print(f"✗ JSON模板文件不存在: {template_path}")
                # 尝试备用路径
                alternative_paths = [
                    os.path.join(current_dir, "templates", "faceUP_faceroot.json"),
                    os.path.join(parent_dir, "..", "templates", "faceUP_faceroot.json"),
                ]
                
                for alt_path in alternative_paths:
                    alt_path = os.path.normpath(alt_path)
                    print(f"尝试备用路径: {alt_path}")
                    if os.path.exists(alt_path):
                        template_path = alt_path
                        print(f"✓ 找到JSON模板文件: {template_path}")
                        break
                else:
                    raise FileNotFoundError(f"找不到JSON模板文件: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # print(f"✓ JSON模板加载成功: {len(template_data['bones'][0]['drivers'])} 个驱动器") # 删除debug打印
            return template_data
            
        except Exception as e:
            print(f"✗ JSON模板加载失败: {e}")
            return None

    def apply_drivers_from_json_template(self, template_data):
        """从JSON模板数据应用驱动器到face-root骨骼"""
        if not template_data:
            # print("⚠ 模板数据为空，跳过驱动器应用") # 删除debug打印
            return
        
        # 检查 faceroot_bone 是否存在
        if not hasattr(self.rig, 'faceroot_bone') or not self.rig.faceroot_bone:
            # print("⚠ faceroot_bone 不存在，跳过驱动器应用") # 删除debug打印
            return
        
        try:
            # print("🔄 开始应用JSON驱动器...") # 删除debug打印
            
            # 获取face-root骨骼
            faceroot_pose_bone = self.rig.obj.pose.bones[self.rig.faceroot_bone]
            
            # 获取模板中的驱动器数据
            # 检查是否是JSON模板格式
            bones_data = template_data.get('bones', [])
            if not bones_data:
                # print("⚠ 模板中没有骨骼数据") # 删除debug打印
                return
            
            # 查找 face-root 骨骼数据
            face_root_data = None
            for bone_data in bones_data:
                if bone_data.get('name') == 'face-root':
                    face_root_data = bone_data
                    break
            
            if not face_root_data:
                # print("⚠ 模板中没有face-root骨骼数据") # 删除debug打印
                return
            
            drivers = face_root_data.get('drivers', [])
            if not drivers:
                # print("⚠ 模板中没有驱动器数据") # 删除debug打印
                return
            
            # print(f"📊 找到 {len(drivers)} 个JSON驱动器定义") # 删除debug打印
            
            applied_count = 0
            skipped_count = 0
            
            for driver_data in drivers:
                try:
                    # 应用单个驱动器
                    if self._apply_single_json_driver(driver_data, faceroot_pose_bone):
                        applied_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    # print(f"❌ 应用驱动器失败: {e}") # 删除debug打印
                    skipped_count += 1
                    continue
            
            # print(f"✅ JSON驱动器应用完成:") # 删除debug打印
            # print(f"   ✓ 成功应用: {applied_count} 个") # 删除debug打印
            # print(f"   ⚠ 跳过: {skipped_count} 个") # 删除debug打印
            
            # 更新依赖图
            bpy.context.view_layer.update()
            
        except Exception as e:
            # print(f"❌ 应用JSON驱动器时出错: {e}") # 删除debug打印
            import traceback
            traceback.print_exc()
    
    def _apply_single_json_driver(self, driver_data, pose_bone):
        """应用单个JSON驱动器"""
        try:
            data_path = driver_data.get('data_path', '')
            array_index = driver_data.get('array_index', 0)
            expression = driver_data.get('expression', '')
            driver_type = driver_data.get('type', 'SCRIPTED')
            variables = driver_data.get('variables', [])
            
            # 解析自定义属性名称
            # data_path 格式: pose.bones["face-root"]["属性名"]
            if not data_path or '"' not in data_path:
                # print(f"⚠ 无效的data_path: {data_path}") # 删除debug打印
                return False
            
            # 提取属性名称
            parts = data_path.split('"')
            if len(parts) < 4:
                # print(f"⚠ 无法解析data_path: {data_path}") # 删除debug打印
                return False
            
            property_name = parts[3]  # 第四个引号内的内容是属性名
            
            # 确保自定义属性存在
            if property_name not in pose_bone.keys():
                pose_bone[property_name] = 0.0
            
            # 创建驱动器
            driver = pose_bone.driver_add('["{}"]'.format(property_name), array_index)
            if not driver:
                # print(f"❌ 无法创建驱动器: {property_name}") # 删除debug打印
                return False
            
            # 设置驱动器类型和表达式
            driver.driver.type = driver_type
            driver.driver.expression = expression
            
            # 清除现有变量 - 使用Rigify官方推荐的方法 (Blender 4.1+)
            for var in list(driver.driver.variables):
                driver.driver.variables.remove(var)
            
            # 添加变量
            for var_data in variables:
                var_name = var_data.get('name', 'var')
                var_type = var_data.get('type', 'TRANSFORMS')
                targets = var_data.get('targets', [])
                
                var = driver.driver.variables.new()
                var.name = var_name
                var.type = var_type
                
                # 设置目标
                for i, target_data in enumerate(targets):
                    if i >= len(var.targets):
                        break
                        
                    target = var.targets[i]
                    target.id = self.rig.obj
                    target.data_path = target_data.get('data_path', '')
                    target.transform_type = target_data.get('transform_type', 'LOC_X')
                    target.transform_space = target_data.get('transform_space', 'LOCAL_SPACE')
                    
                    bone_target = target_data.get('bone_target', '')
                    if bone_target:
                        target.bone_target = bone_target
            
            # print(f"  ✓ 应用JSON驱动器: {property_name}") # 删除debug打印
            return True
            
        except Exception as e:
            # print(f"❌ 应用单个JSON驱动器失败: {e}") # 删除debug打印
            return False


# 遗留的便捷函数

def load_faceroot_template_json_legacy():
    """加载face-root JSON模板（遗留函数）"""
    try:
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        
        template_path = os.path.join(parent_dir, "templates", "faceUP_faceroot.json")
        template_path = os.path.normpath(template_path)
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"JSON模板文件不存在: {template_path}")
            return None
            
    except Exception as e:
        print(f"加载JSON模板失败: {e}")
        return None


def apply_json_drivers_to_bone_legacy(armature_obj, bone_name, drivers_data):
    """将JSON驱动器数据应用到指定骨骼（遗留函数）"""
    if bone_name not in armature_obj.pose.bones:
        print(f"骨骼 {bone_name} 不存在")
        return False
    
    pose_bone = armature_obj.pose.bones[bone_name]
    
    for driver_data in drivers_data:
        try:
            # 解析属性名称和创建驱动器的逻辑
            data_path = driver_data.get('data_path', '')
            if '"' in data_path:
                parts = data_path.split('"')
                if len(parts) >= 4:
                    property_name = parts[3]
                    
                    # 确保属性存在
                    if property_name not in pose_bone.keys():
                        pose_bone[property_name] = 0.0
                    
                    # 创建驱动器
                    driver = pose_bone.driver_add(f'["{property_name}"]', 
                                                 driver_data.get('array_index', 0))
                    
                    if driver:
                        driver.driver.type = driver_data.get('type', 'SCRIPTED')
                        driver.driver.expression = driver_data.get('expression', '')
                        
                        # 设置变量 - 使用Rigify官方推荐的方法 (Blender 4.1+)
                        for var in list(driver.driver.variables):
                            driver.driver.variables.remove(var)
                        for var_data in driver_data.get('variables', []):
                            var = driver.driver.variables.new()
                            var.name = var_data.get('name', 'var')
                            var.type = var_data.get('type', 'TRANSFORMS')
                            
                            # 设置目标
                            for i, target_data in enumerate(var_data.get('targets', [])):
                                if i < len(var.targets):
                                    target = var.targets[i]
                                    target.id = armature_obj
                                    target.data_path = target_data.get('data_path', '')
                                    target.transform_type = target_data.get('transform_type', 'LOC_X')
                                    target.transform_space = target_data.get('transform_space', 'LOCAL_SPACE')
                                    if 'bone_target' in target_data:
                                        target.bone_target = target_data['bone_target']
                        
                        # print(f"✓ 应用JSON驱动器: {property_name}") # 删除debug打印
                    
        except Exception as e:
            # print(f"应用驱动器失败: {e}") # 删除debug打印
            continue
    
    return True


"""
使用示例（已弃用）:

# 加载JSON模板
template_data = load_faceroot_template_json_legacy()

# 应用到骨骼
if template_data:
    json_manager = JSONTemplateManagerLegacy(rig_instance)
    json_manager.apply_drivers_from_json_template(template_data)
""" 