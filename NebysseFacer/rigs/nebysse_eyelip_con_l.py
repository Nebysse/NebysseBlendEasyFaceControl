import os
import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .nebysse_base_faceup_locator import BaseFaceUPLocator

class Rig(BaseFaceUPLocator):
    """左眼睑控制定位器"""
    
    def __init__(self, generator, pose_bone):
        super().__init__(generator, pose_bone)
        self.locator_type = "eyelip-con.L"
        self.rig_id = "nebysse_eyelip_con_l"
    
    def get_widget_type(self):
        return 'CIRCLE'
    
    def find_blend_template_file(self):
        """查找 Blender 模板文件路径"""
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(current_dir)
        template_path = os.path.join(parent_dir, "templates", "Nebysse_FaceUP_Tem.blend")
        
        if os.path.exists(template_path):
            print(f"✓ 找到 Blender 模板文件: {template_path}")
            return template_path
        else:
            print(f"✗ Blender 模板文件不存在: {template_path}")
            return None
    
    def load_constraints_from_template(self):
        """从模板文件加载约束（增强诊断版本）"""
        template_path = self.find_blend_template_file()
        if not template_path:
            return False
        
        try:
            print(f"🔄 开始加载模板约束，路径: {template_path}")
            
            # 记录加载前的骨架和对象数量
            armatures_before = set(bpy.data.armatures.keys())
            objects_before = set(bpy.data.objects.keys())
            print(f"📊 加载前状态: {len(armatures_before)} 个骨架, {len(objects_before)} 个对象")
            
            # 使用 Blender API 追加骨架
            with bpy.data.libraries.load(template_path) as (data_from, data_to):
                armature_name = "Nebysse_FaceUP_Tem.Rig"
                print(f"🔍 模板文件中可用的骨架: {data_from.armatures}")
                
                if armature_name in data_from.armatures:
                    data_to.armatures = [armature_name]
                    print(f"✓ 找到模板骨架: {armature_name}")
                else:
                    print(f"✗ 未找到模板骨架: {armature_name}")
                    print(f"📋 可用骨架列表: {list(data_from.armatures)}")
                    return False
            
            # 检查加载后的变化
            armatures_after = set(bpy.data.armatures.keys())
            objects_after = set(bpy.data.objects.keys())
            new_armatures = armatures_after - armatures_before
            new_objects = objects_after - objects_before
            
            print(f"📊 加载后状态: {len(armatures_after)} 个骨架, {len(objects_after)} 个对象")
            print(f"📊 新增内容: {len(new_armatures)} 个骨架, {len(new_objects)} 个对象")
            
            if new_armatures:
                print(f"🔍 新增骨架: {list(new_armatures)}")
            if new_objects:
                print(f"🔍 新增对象: {list(new_objects)}")
            
            # 获取追加的骨架和对象（改进的查找逻辑）
            template_armature_data = None
            template_object = None
            
            # 方法1：直接查找新增的骨架
            for armature_name in new_armatures:
                if "Nebysse_FaceUP_Tem" in armature_name:
                    template_armature_data = bpy.data.armatures[armature_name]
                    print(f"✓ 通过新增列表找到模板骨架数据: {armature_name}")
                    break
            
            # 方法2：如果方法1失败，使用原始方法
            if not template_armature_data:
                for armature in bpy.data.armatures:
                    if armature.name.startswith("Nebysse_FaceUP_Tem.Rig"):
                        template_armature_data = armature
                        print(f"✓ 通过遍历找到模板骨架数据: {armature.name}")
                        break
            
            # 查找对应的对象
            if template_armature_data:
                # 方法1：在新增对象中查找
                for obj_name in new_objects:
                    obj = bpy.data.objects[obj_name]
                    if obj.type == 'ARMATURE' and obj.data == template_armature_data:
                        template_object = obj
                        print(f"✓ 通过新增列表找到模板对象: {obj_name}")
                        break
                
                # 方法2：如果没有新增对象，说明只加载了骨架数据，需要创建对象
                if not template_object:
                    print("⚠ 未在新增对象中找到模板对象，尝试创建临时对象...")
                    
                    # 创建临时对象
                    temp_obj_name = f"TempTemplate_{template_armature_data.name}"
                    template_object = bpy.data.objects.new(temp_obj_name, template_armature_data)
                    
                    # 将对象链接到场景
                    bpy.context.scene.collection.objects.link(template_object)
                    print(f"✓ 创建并链接临时模板对象: {temp_obj_name}")
                
                # 方法3：最后的遍历查找
                if not template_object:
                    for obj in bpy.data.objects:
                        if obj.type == 'ARMATURE' and obj.data == template_armature_data:
                            template_object = obj
                            print(f"✓ 通过遍历找到模板对象: {obj.name}")
                            break
            
            # 诊断结果
            if not template_armature_data:
                print("❌ 诊断失败：未能获取模板骨架数据")
                print("🔍 详细诊断:")
                print(f"   - 模板文件路径: {template_path}")
                print(f"   - 预期骨架名: Nebysse_FaceUP_Tem.Rig")
                print(f"   - 实际新增骨架: {list(new_armatures)}")
                return False
            
            if not template_object:
                print("❌ 诊断失败：未能获取模板对象")
                print("🔍 详细诊断:")
                print(f"   - 骨架数据存在: {template_armature_data.name}")
                print(f"   - 新增对象: {list(new_objects)}")
                print(f"   - 尝试创建临时对象: 失败")
                
                # 清理骨架数据
                bpy.data.armatures.remove(template_armature_data)
                return False
            
            print(f"✅ 成功获取模板资源:")
            print(f"   📁 骨架数据: {template_armature_data.name}")
            print(f"   🎯 对象: {template_object.name}")
            
            # 复制约束
            success = self.copy_constraints_from_template(template_object)
            
            # 智能清理临时数据
            try:
                print("🧹 开始清理模板数据...")
                
                # 先从场景中移除对象
                if template_object.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(template_object)
                    print(f"   🔗 从场景中取消链接: {template_object.name}")
                
                # 删除对象
                bpy.data.objects.remove(template_object)
                print(f"   🗑️ 删除对象: {template_object.name}")
                
                # 删除骨架数据
                bpy.data.armatures.remove(template_armature_data)
                print(f"   🗑️ 删除骨架数据: {template_armature_data.name}")
                
                print("✓ 模板数据清理完成")
                
            except Exception as cleanup_error:
                print(f"⚠ 清理模板数据时出错: {cleanup_error}")
                # 清理错误不影响主要功能的成功
            
            return success
            
        except Exception as e:
            print(f"❌ 从模板加载约束失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 增强错误诊断
            print("🔍 错误诊断信息:")
            print(f"   - 模板文件存在: {os.path.exists(template_path) if template_path else False}")
            print(f"   - 当前工作目录: {os.getcwd()}")
            print(f"   - Blender版本: {bpy.app.version_string}")
            
            return False
    
    def copy_constraints_from_template(self, template_object):
        """从模板对象复制约束"""
        try:
            # 首先验证模板对象的有效性
            if not template_object:
                print(f"❌ 模板对象为空")
                return False
            
            if template_object.type != 'ARMATURE':
                print(f"❌ 模板对象不是骨架类型: {template_object.type}")
                return False
            
            # 确保对象有有效的姿态数据
            if not template_object.pose:
                print(f"⚠ 模板对象缺少姿态数据，尝试更新...")
                
                # 尝试刷新对象数据
                import bpy
                bpy.context.view_layer.update()
                
                # 如果还是没有姿态数据，尝试切换到姿态模式再切回来
                if not template_object.pose:
                    print(f"🔧 尝试通过模式切换初始化姿态数据...")
                    
                    # 保存当前状态
                    original_active = bpy.context.view_layer.objects.active
                    original_mode = bpy.context.mode
                    
                    try:
                        # 设置模板对象为活动对象
                        bpy.context.view_layer.objects.active = template_object
                        
                        # 尝试进入姿态模式来初始化姿态数据
                        if bpy.context.mode != 'POSE':
                            bpy.ops.object.mode_set(mode='POSE')
                            bpy.context.view_layer.update()
                        
                        # 再次检查姿态数据
                        if template_object.pose:
                            print(f"✓ 通过模式切换成功初始化姿态数据")
                        else:
                            print(f"❌ 仍无法获取姿态数据")
                            return False
                    
                    except Exception as mode_error:
                        print(f"⚠ 模式切换时出错: {mode_error}")
                        return False
                    
                    finally:
                        # 恢复原始状态
                        try:
                            if original_active:
                                bpy.context.view_layer.objects.active = original_active
                            if original_mode != 'POSE':
                                bpy.ops.object.mode_set(mode='OBJECT')
                        except:
                            pass
            
            # 最终检查姿态数据
            if not template_object.pose:
                print(f"❌ 无法获取模板对象的姿态数据")
                return False
            
            if not template_object.pose.bones:
                print(f"❌ 模板对象没有姿态骨骼")
                return False
            
            print(f"✓ 模板对象姿态数据验证通过，包含 {len(template_object.pose.bones)} 个姿态骨骼")
            
            # 查找模板中的对应骨骼
            template_bone_name = "eyelip-con.L"
            
            if template_bone_name not in template_object.pose.bones:
                print(f"✗ 模板中未找到骨骼: {template_bone_name}")
                print(f"🔍 模板中可用的骨骼: {list(template_object.pose.bones.keys())[:10]}...")  # 显示前10个
                return False
            
            template_bone = template_object.pose.bones[template_bone_name]
            local_bone = self.obj.pose.bones[self.control_bone]
            
            print(f"✓ 找到模板骨骼: {template_bone_name}")
            print(f"✓ 目标骨骼: {self.control_bone}")
            
            # 复制约束
            constraints_count = 0
            for template_constraint in template_bone.constraints:
                # 创建新约束
                new_constraint = local_bone.constraints.new(type=template_constraint.type)
                
                # 复制约束属性
                self.copy_constraint_properties(template_constraint, new_constraint)
                
                # 应用用户参数
                self.apply_constraint_parameters(new_constraint, template_constraint.type)
                
                constraints_count += 1
                print(f"✓ 复制约束: {template_constraint.type}")
            
            print(f"✓ 复制了 {constraints_count} 个约束")
            return True
            
        except Exception as e:
            print(f"✗ 复制约束时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 增强错误诊断
            print(f"🔍 错误诊断信息:")
            try:
                print(f"   - 模板对象类型: {template_object.type if template_object else 'None'}")
                print(f"   - 模板对象名称: {template_object.name if template_object else 'None'}")
                print(f"   - 姿态数据存在: {bool(template_object.pose) if template_object else 'N/A'}")
                if template_object and template_object.pose:
                    print(f"   - 姿态骨骼数量: {len(template_object.pose.bones)}")
                print(f"   - 目标控制骨骼: {self.control_bone}")
                print(f"   - 当前对象: {self.obj.name}")
            except Exception as diag_error:
                print(f"   - 诊断信息获取失败: {diag_error}")
            
            return False
    
    def copy_constraint_properties(self, source_constraint, target_constraint):
        """复制约束属性"""
        # 根据约束类型复制特定属性（不是所有约束都有target属性）
        
        if source_constraint.type == 'LIMIT_LOCATION':
            # 位置限制约束不需要target，只需要复制限制设置
            target_constraint.use_min_x = source_constraint.use_min_x
            target_constraint.use_max_x = source_constraint.use_max_x
            target_constraint.use_min_y = source_constraint.use_min_y
            target_constraint.use_max_y = source_constraint.use_max_y
            target_constraint.use_min_z = source_constraint.use_min_z
            target_constraint.use_max_z = source_constraint.use_max_z
            target_constraint.owner_space = source_constraint.owner_space
            
        elif source_constraint.type == 'LIMIT_ROTATION':
            # 旋转限制约束不需要target
            target_constraint.use_limit_x = source_constraint.use_limit_x
            target_constraint.use_limit_y = source_constraint.use_limit_y
            target_constraint.use_limit_z = source_constraint.use_limit_z
            target_constraint.owner_space = source_constraint.owner_space
            
        elif source_constraint.type == 'LIMIT_DISTANCE':
            # 距离限制约束需要target
            if hasattr(source_constraint, 'target') and source_constraint.target:
                target_constraint.target = self.obj  # 使用本地对象
                if hasattr(source_constraint, 'subtarget'):
                    target_constraint.subtarget = source_constraint.subtarget
            target_constraint.distance = source_constraint.distance
            target_constraint.limit_mode = source_constraint.limit_mode
            target_constraint.owner_space = source_constraint.owner_space
            
        elif source_constraint.type in ['COPY_LOCATION', 'COPY_ROTATION', 'COPY_TRANSFORMS']:
            # 这些约束需要target
            if hasattr(source_constraint, 'target') and source_constraint.target:
                target_constraint.target = self.obj  # 使用本地对象
                if hasattr(source_constraint, 'subtarget'):
                    target_constraint.subtarget = source_constraint.subtarget
            # 复制其他相关属性
            if hasattr(source_constraint, 'target_space'):
                target_constraint.target_space = source_constraint.target_space
            if hasattr(source_constraint, 'owner_space'):
                target_constraint.owner_space = source_constraint.owner_space
    
    def apply_constraint_parameters(self, constraint, constraint_type):
        """应用用户参数到约束"""
        params = self.params
        
        if constraint_type == 'LIMIT_LOCATION':
            # 应用位置限制参数
            constraint.min_x = getattr(params, 'limit_location_min_x', -0.1)
            constraint.max_x = getattr(params, 'limit_location_max_x', 0.1)
            constraint.min_y = getattr(params, 'limit_location_min_y', -0.1)
            constraint.max_y = getattr(params, 'limit_location_max_y', 0.1)
            constraint.min_z = getattr(params, 'limit_location_min_z', -0.1)
            constraint.max_z = getattr(params, 'limit_location_max_z', 0.1)
            
        elif constraint_type == 'LIMIT_ROTATION':
            # 应用旋转限制参数（主要是Y轴）
            constraint.min_y = getattr(params, 'limit_rotation_min_y', -0.5)
            constraint.max_y = getattr(params, 'limit_rotation_max_y', 0.5)
            
        elif constraint_type == 'LIMIT_DISTANCE':
            # 应用距离限制参数
            constraint.distance = getattr(params, 'limit_distance_value', 0.1)
    
    def configure_bones(self):
        """配置眼睑控制骨骼"""
        bone = self.get_bone(self.control_bone)
        
        # 主要控制 Z 轴移动（闭眼/睁眼）
        bone.lock_location = [False, True, False]
        bone.lock_rotation = [True, True, True]
        bone.lock_scale = [True, True, True]
    
    def rig_bones(self):
        """设置约束"""
        # 调用父类方法
        super().rig_bones()
        
        # 根据参数决定是否加载约束
        if getattr(self.params, 'load_constraints_from_template', True):
            self.load_constraints_from_template()
    
    @staticmethod  
    def add_parameters(params):
        """添加参数"""
        # 基础参数
        params.eyelid_control_size = FloatProperty(
            name="控制器大小",
            default=0.5,
            min=0.1,
            max=2.0,
            description="眼睑控制器的大小"
        )
        
        params.enable_eyelid_x_motion = BoolProperty(
            name="启用X轴运动",
            default=True,
            description="启用眼睑控制器的X轴运动"
        )
        
        # 约束加载选项
        params.load_constraints_from_template = BoolProperty(
            name="从模板加载约束",
            default=True,
            description="从 Nebysse_FaceUP_Tem.blend 文件加载约束"
        )
        
        # Limit Location 参数
        params.limit_location_min_x = FloatProperty(
            name="位置限制最小X",
            default=-0.1,
            min=-1.0,
            max=0.0,
            description="位置限制约束的最小X值"
        )
        
        params.limit_location_max_x = FloatProperty(
            name="位置限制最大X",
            default=0.1,
            min=0.0,
            max=1.0,
            description="位置限制约束的最大X值"
        )
        
        params.limit_location_min_y = FloatProperty(
            name="位置限制最小Y",
            default=-0.1,
            min=-1.0,
            max=0.0,
            description="位置限制约束的最小Y值"
        )
        
        params.limit_location_max_y = FloatProperty(
            name="位置限制最大Y",
            default=0.1,
            min=0.0,
            max=1.0,
            description="位置限制约束的最大Y值"
        )
        
        params.limit_location_min_z = FloatProperty(
            name="位置限制最小Z",
            default=-0.1,
            min=-1.0,
            max=0.0,
            description="位置限制约束的最小Z值"
        )
        
        params.limit_location_max_z = FloatProperty(
            name="位置限制最大Z",
            default=0.1,
            min=0.0,
            max=1.0,
            description="位置限制约束的最大Z值"
        )
        
        # Limit Rotation Y轴参数
        params.limit_rotation_min_y = FloatProperty(
            name="旋转限制最小Y",
            default=-0.5,
            min=-3.14159,
            max=0.0,
            description="旋转限制约束的最小Y值（弧度）"
        )
        
        params.limit_rotation_max_y = FloatProperty(
            name="旋转限制最大Y",
            default=0.5,
            min=0.0,
            max=3.14159,
            description="旋转限制约束的最大Y值（弧度）"
        )
        
        # Limit Distance 参数
        params.limit_distance_value = FloatProperty(
            name="距离限制值",
            default=0.1,
            min=0.01,
            max=1.0,
            description="距离限制约束的距离值"
        )
    
    @staticmethod
    def parameters_ui(layout, params):
        """参数界面"""
        layout.label(text="左眼睑控制器:")
        
        # 基础参数
        row = layout.row()
        row.prop(params, "eyelid_control_size", text="控制器大小")
        
        row = layout.row()
        row.prop(params, "enable_eyelid_x_motion", text="启用X轴运动")
        
        # 约束设置
        layout.separator()
        layout.label(text="约束设置:")
        
        row = layout.row()
        row.prop(params, "load_constraints_from_template", text="从模板加载约束")
        
        if params.load_constraints_from_template:
            # Limit Location 参数
            box = layout.box()
            box.label(text="位置限制 (Limit Location):", icon='CON_LOCLIMIT')
            
            col = box.column()
            row = col.row()
            row.prop(params, "limit_location_min_x", text="最小X")
            row.prop(params, "limit_location_max_x", text="最大X")
            
            row = col.row()
            row.prop(params, "limit_location_min_y", text="最小Y")
            row.prop(params, "limit_location_max_y", text="最大Y")
            
            row = col.row()
            row.prop(params, "limit_location_min_z", text="最小Z")
            row.prop(params, "limit_location_max_z", text="最大Z")
            
            # Limit Rotation Y轴参数
            box = layout.box()
            box.label(text="旋转限制 Y轴 (Limit Rotation):", icon='CON_ROTLIMIT')
            
            col = box.column()
            row = col.row()
            row.prop(params, "limit_rotation_min_y", text="最小Y")
            row.prop(params, "limit_rotation_max_y", text="最大Y")
            
            # Limit Distance 参数
            box = layout.box()
            box.label(text="距离限制 (Limit Distance):", icon='CON_DISTLIMIT')
            
            col = box.column()
            col.prop(params, "limit_distance_value", text="距离值") 