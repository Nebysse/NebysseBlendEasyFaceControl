import os
import bpy
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty
from .nebysse_base_faceup_locator import BaseFaceUPLocator
from .nebysse_collection_utils import BaseFaceUPCollectionMixin
from rigify.utils.bones import BoneDict
from rigify.utils.naming import make_derived_name

class Rig(BaseFaceUPLocator, BaseFaceUPCollectionMixin):
    """嘴部控制定位器"""
    
    def __init__(self, generator, pose_bone):
        super().__init__(generator, pose_bone)
        self.locator_type = "mouth-con"
        self.rig_id = "nebysse_mouth_con"
        self.disw_bones = []  # 存储 DISW 骨骼列表
        # 模板骨骼名称（在模板文件中的原始名称）
        self.template_bones = ["DISW-Lip_T.L", "DISW-Lip_B.L", "DISW-Lip_T.R", "DISW-Lip_B.R"]
        # 目标骨骼名称（包含Neb前缀）
        self.target_bone_names = ["DISW-Neb_Lip_T.L", "DISW-Neb_Lip_B.L", "DISW-Neb_Lip_T.R", "DISW-Neb_Lip_B.R"]
        
        # 安全获取用户自定义的坐标参数
        if hasattr(self, 'get_disw_positions_from_params'):
            try:
                self.disw_positions = self.get_disw_positions_from_params()
            except Exception as e:
                print(f"⚠ 获取DISW位置参数失败，使用默认值: {e}")
                self.disw_positions = self._get_default_disw_positions()
        else:
            print("⚠ get_disw_positions_from_params方法不存在，使用默认坐标")
            self.disw_positions = self._get_default_disw_positions()
    
    def _get_default_disw_positions(self):
        """获取默认的DISW骨骼位置"""
        return {
            "top_left": Vector((-0.01, 0.005, 0.015)),
            "top_right": Vector((0.01, 0.005, 0.015)),
            "bottom_left": Vector((-0.01, 0.005, -0.01)),
            "bottom_right": Vector((0.01, 0.005, -0.01))
        }
    
    def get_disw_positions_from_params(self):
        """从参数中获取 DISW 骨骼的局部坐标"""
        params = self.params
        
        # 默认坐标（如果参数不存在）
        default_positions = {
            "top_left": Vector((-0.01, 0.005, 0.015)),      # 左上
            "bottom_left": Vector((-0.01, 0.005, -0.01)),   # 左下  
            "top_right": Vector((0.01, 0.005, 0.015)),      # 右上
            "bottom_right": Vector((0.01, 0.005, -0.01))    # 右下
        }
        
        # 从参数中读取坐标，如果不存在则使用默认值
        positions = {}
        for key, default_pos in default_positions.items():
            x_attr = f"disw_{key}_x"
            y_attr = f"disw_{key}_y" 
            z_attr = f"disw_{key}_z"
            
            x = getattr(params, x_attr, default_pos.x)
            y = getattr(params, y_attr, default_pos.y)
            z = getattr(params, z_attr, default_pos.z)
            
            positions[key] = Vector((x, y, z))
        
        return positions
    
    def get_widget_type(self):
        return 'CUBE'
    
    def generate_bones(self):
        """生成嘴部控制骨骼层级结构"""
        bones = BoneDict()
        
        # 1. 创建根骨骼 mouth-root
        self.root_bone = self.copy_bone(self.base_bone, "mouth-root")
        bones.root = self.root_bone
        
        # 2. 创建控制器骨骼 mouth-con
        self.control_bone = self.copy_bone(self.base_bone, "mouth-con")
        bones.ctrl = self.control_bone
        
        # 3. 创建权重骨骼
        self.disw_bones = []
        disw_bone_specs = [
            ("DISW-Lip_T.L", "top_left"),      # 左上唇
            ("DISW-Lip_T.R", "top_right"),     # 右上唇  
            ("DISW-Lip_B.L", "bottom_left"),   # 左下唇
            ("DISW-Lip_B.R", "bottom_right")   # 右下唇
        ]
        
        for bone_name, pos_key in disw_bone_specs:
            disw_bone = self.copy_bone(self.base_bone, bone_name)
            self.disw_bones.append(disw_bone)
            
            # 设置权重骨骼的位置（相对于根骨骼）
            if pos_key in self.disw_positions:
                bone_obj = self.get_bone(disw_bone)
                root_bone_obj = self.get_bone(self.root_bone)
                
                # 计算权重骨骼的位置
                offset = self.disw_positions[pos_key]
                bone_obj.head = root_bone_obj.head + offset
                bone_obj.tail = bone_obj.head + Vector((0, 0.005, 0))  # 设置小的尾部偏移
                
                print(f"✓ 创建权重骨骼: {bone_name} 位置偏移: {offset}")
        
        # 将权重骨骼添加到bones字典
        bones.disw = self.disw_bones
        
        # 注册到父级控制器（nebysse_faceup_con）
        self.register_to_faceup_controller()
        
        print(f"✓ 嘴部骨骼层级生成完成: root={self.root_bone}, ctrl={self.control_bone}, disw={len(self.disw_bones)}个")
        
        return bones
    
    def parent_bones(self):
        """设置骨骼父子关系"""
        # 调用父类方法设置基础父子关系
        super().parent_bones()
        
        # 设置控制器骨骼为根骨骼的子级
        if hasattr(self, 'control_bone') and hasattr(self, 'root_bone'):
            self.set_bone_parent(self.control_bone, self.root_bone)
            print(f"✓ 设置 {self.control_bone} 父骨骼为 {self.root_bone}")
        
        # 设置所有DISW骨骼为根骨骼的子级
        if hasattr(self, 'disw_bones') and hasattr(self, 'root_bone'):
            for disw_bone in self.disw_bones:
                self.set_bone_parent(disw_bone, self.root_bone)
                print(f"✓ 设置 {disw_bone} 父骨骼为 {self.root_bone}")
        
        print(f"✓ 嘴部骨骼层级关系设置完成")
    
    def configure_bones(self):
        """配置嘴部控制骨骼和 DISW 骨骼"""
        # 配置主控制骨骼
        bone = self.get_bone(self.control_bone)
        bone.lock_location = [False, False, False]
        bone.lock_rotation = [False, False, False]  
        bone.lock_scale = [False, False, False]
        
        # 配置 DISW 骨骼
        for disw_bone in self.disw_bones:
            if disw_bone in self.obj.data.bones:
                disw_bone_obj = self.get_bone(disw_bone)
                disw_bone_obj.lock_location = [False, False, False]
                disw_bone_obj.lock_rotation = [False, False, False]
                disw_bone_obj.lock_scale = [False, False, False]
    
    def rig_bones(self):
        """设置约束和驱动器"""
        # 调用父类方法
        super().rig_bones()
        
        # 创建 DISW 骨骼集合
        self.create_disw_bone_collection()
    
    @staticmethod
    def add_parameters(params):
        """添加参数"""
        # 基础参数
        params.mouth_control_size = FloatProperty(
            name="控制器大小",
            default=1.0,
            min=0.1,
            max=5.0,
            description="嘴部控制器的大小"
        )
        
        params.enable_mouth_rotation = BoolProperty(
            name="启用旋转",
            default=True,
            description="启用嘴部控制器的旋转功能"
        )
        
        params.enable_mouth_scale = BoolProperty(
            name="启用缩放",
            default=True,
            description="启用嘴部控制器的缩放功能"
        )
        
        params.enable_disw_bones = BoolProperty(
            name="启用 DISW 骨骼",
            default=True,
            description="生成 DISW 子骨骼"
        )
        
        params.disw_bone_size = FloatProperty(
            name="DISW 骨骼大小",
            default=0.5,
            min=0.1,
            max=2.0,
            description="DISW 骨骼的大小"
        )
        
        # 坐标模式选择
        params.use_custom_positions = BoolProperty(
            name="使用自定义坐标",
            default=True,
            description="使用自定义坐标而不是模板文件"
        )
        
        # DISW 骨骼坐标参数 - 左上 (Top Left)
        params.disw_top_left_x = FloatProperty(
            name="左上 X",
            default=-0.01,
            min=-0.1,
            max=0.1,
            description="左上 DISW 骨骼的 X 坐标（相对于 mouth-con）"
        )
        
        params.disw_top_left_y = FloatProperty(
            name="左上 Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="左上 DISW 骨骼的 Y 坐标（相对于 mouth-con）"
        )
        
        params.disw_top_left_z = FloatProperty(
            name="左上 Z",
            default=0.015,
            min=-0.1,
            max=0.1,
            description="左上 DISW 骨骼的 Z 坐标（相对于 mouth-con）"
        )
        
        # DISW 骨骼坐标参数 - 左下 (Bottom Left)
        params.disw_bottom_left_x = FloatProperty(
            name="左下 X",
            default=-0.01,
            min=-0.1,
            max=0.1,
            description="左下 DISW 骨骼的 X 坐标（相对于 mouth-con）"
        )
        
        params.disw_bottom_left_y = FloatProperty(
            name="左下 Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="左下 DISW 骨骼的 Y 坐标（相对于 mouth-con）"
        )
        
        params.disw_bottom_left_z = FloatProperty(
            name="左下 Z",
            default=-0.01,
            min=-0.1,
            max=0.1,
            description="左下 DISW 骨骼的 Z 坐标（相对于 mouth-con）"
        )
        
        # DISW 骨骼坐标参数 - 右上 (Top Right)
        params.disw_top_right_x = FloatProperty(
            name="右上 X",
            default=0.01,
            min=-0.1,
            max=0.1,
            description="右上 DISW 骨骼的 X 坐标（相对于 mouth-con）"
        )
        
        params.disw_top_right_y = FloatProperty(
            name="右上 Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="右上 DISW 骨骼的 Y 坐标（相对于 mouth-con）"
        )
        
        params.disw_top_right_z = FloatProperty(
            name="右上 Z",
            default=0.015,
            min=-0.1,
            max=0.1,
            description="右上 DISW 骨骼的 Z 坐标（相对于 mouth-con）"
        )
        
        # DISW 骨骼坐标参数 - 右下 (Bottom Right)
        params.disw_bottom_right_x = FloatProperty(
            name="右下 X",
            default=0.01,
            min=-0.1,
            max=0.1,
            description="右下 DISW 骨骼的 X 坐标（相对于 mouth-con）"
        )
        
        params.disw_bottom_right_y = FloatProperty(
            name="右下 Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="右下 DISW 骨骼的 Y 坐标（相对于 mouth-con）"
        )
        
        params.disw_bottom_right_z = FloatProperty(
            name="右下 Z",
            default=-0.01,
            min=-0.1,
            max=0.1,
            description="右下 DISW 骨骼的 Z 坐标（相对于 mouth-con）"
        )
    
    @staticmethod
    def parameters_ui(layout, params):
        """参数界面"""
        layout.label(text="嘴部控制器:")
        
        row = layout.row()
        row.prop(params, "mouth_control_size", text="控制器大小")
        
        row = layout.row()
        row.prop(params, "enable_mouth_rotation", text="启用旋转")
        
        row = layout.row()
        row.prop(params, "enable_mouth_scale", text="启用缩放")
        
        layout.separator()
        layout.label(text="DISW 骨骼:")
        
        row = layout.row()
        row.prop(params, "enable_disw_bones", text="启用 DISW 骨骼")
        
        row = layout.row()
        row.prop(params, "disw_bone_size", text="DISW 骨骼大小")
        
        row = layout.row()
        row.prop(params, "use_custom_positions", text="使用自定义坐标")
        
        if params.use_custom_positions:
            layout.separator()
            layout.label(text="DISW 骨骼坐标 (相对于 mouth-con):")
            
            # 左上坐标
            box = layout.box()
            box.label(text="左上 (上唇左侧):")
            row = box.row()
            row.prop(params, "disw_top_left_x", text="X")
            row.prop(params, "disw_top_left_y", text="Y") 
            row.prop(params, "disw_top_left_z", text="Z")
            
            # 左下坐标
            box = layout.box()
            box.label(text="左下 (下唇左侧):")
            row = box.row()
            row.prop(params, "disw_bottom_left_x", text="X")
            row.prop(params, "disw_bottom_left_y", text="Y")
            row.prop(params, "disw_bottom_left_z", text="Z")
            
            # 右上坐标
            box = layout.box()
            box.label(text="右上 (上唇右侧):")
            row = box.row()
            row.prop(params, "disw_top_right_x", text="X")
            row.prop(params, "disw_top_right_y", text="Y")
            row.prop(params, "disw_top_right_z", text="Z")
            
            # 右下坐标
            box = layout.box()
            box.label(text="右下 (下唇右侧):")
            row = box.row()
            row.prop(params, "disw_bottom_right_x", text="X")
            row.prop(params, "disw_bottom_right_y", text="Y")
            row.prop(params, "disw_bottom_right_z", text="Z") 