import os
import bpy
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty
from .nebysse_base_faceup_locator import BaseFaceUPLocator
from .nebysse_collection_utils import BaseFaceUPCollectionMixin
from rigify.utils.bones import BoneDict
from rigify.utils.naming import make_derived_name

class Rig(BaseFaceUPLocator, BaseFaceUPCollectionMixin):
    """右眉毛控制定位器"""
    
    def __init__(self, generator, pose_bone):
        super().__init__(generator, pose_bone)
        self.locator_type = "brow-con.R"
        self.rig_id = "nebysse_brow_con_r"
        self.disw_bones = []  # 存储 DISW 骨骼列表
        # 模板骨骼名称（在模板文件中的原始名称）
        self.template_bones = [
            "DISW-brow.T.R.001",
            "DISW-brow.T.R.002",
            "DISW-brow.T.R",
            "DISW-brow.B.R",
            "DISW-brow.B.R.001"
        ]
        # 目标骨骼名称（复制到当前骨架时使用的名称）
        self.target_bone_names = [
            "DISW-Neb_brow.T.R.001",
            "DISW-Neb_brow.T.R.002",
            "DISW-Neb_brow.T.R",
            "DISW-Neb_brow.B.R",
            "DISW-Neb_brow.B.R.001"
        ]
        
        # 初始化DISW骨骼位置
        self.disw_positions = self.get_disw_positions_from_params()
        
        # 调试信息：显示自定义坐标状态
        use_custom = getattr(self.params, 'use_custom_positions', True)
        print(f"🔧 右眉毛控制器初始化: use_custom_positions={use_custom}")
        
        if use_custom:
            # 显示一些关键坐标作为验证
            sample_coords = self.disw_positions.get("DISW-brow.T.R.001")
            print(f"📍 样本坐标 DISW-brow.T.R.001: {sample_coords}")
            
            # 显示参数读取状态
            x_val = getattr(self.params, 'disw_t_001_x', 'MISSING')
            y_val = getattr(self.params, 'disw_t_001_y', 'MISSING')
            z_val = getattr(self.params, 'disw_t_001_z', 'MISSING')
            print(f"📊 参数值检查: X={x_val}, Y={y_val}, Z={z_val}")
        else:
            print("📍 使用默认坐标位置")
    def rig_bones(self):
        """设置约束和驱动器"""
        # 调用父类方法
        super().rig_bones()
        
        # 创建 DISW 骨骼集合
        self.create_disw_bone_collection()
        
        # 根据参数决定是否为DISW骨骼添加约束
        if getattr(self.params, 'enable_disw_constraints', False):
            # 为每个DISW骨骼添加复制位置约束
            for disw_bone in self.disw_bones:
                con = self.make_constraint(disw_bone, 'COPY_LOCATION', self.control_bone)
                con.name = f"Copy Location from {self.control_bone}"
                con.use_offset = True
                print(f"✓ 为 {disw_bone} 添加了复制位置约束")
            print(f"✓ 右眉骨骼约束和驱动器设置完成（包含约束）")
        else:
            # DISW骨骼不添加任何约束修改器
            # 它们将通过父子关系和位置偏移来实现正确的变形
            print(f"✓ 右眉骨骼约束和驱动器设置完成（无约束修改器）")
    def get_widget_type(self):
        return 'ARROW'
    
    def get_disw_positions_from_params(self):
        """从参数中获取 DISW 骨骼的局部坐标"""
        try:
            # 检查是否启用自定义坐标
            if getattr(self.params, 'use_custom_positions', True):
                # 从参数中读取自定义坐标
                return {
                    "DISW-brow.T.R.001": Vector((
                        getattr(self.params, 'disw_t_001_x', 0.015),
                        getattr(self.params, 'disw_t_001_y', 0.005),
                        getattr(self.params, 'disw_t_001_z', 0.02)
                    )),
                    "DISW-brow.T.R.002": Vector((
                        getattr(self.params, 'disw_t_002_x', 0.025),
                        getattr(self.params, 'disw_t_002_y', 0.005),
                        getattr(self.params, 'disw_t_002_z', 0.015)
                    )),
                    "DISW-brow.T.R": Vector((
                        getattr(self.params, 'disw_t_x', 0.035),
                        getattr(self.params, 'disw_t_y', 0.005),
                        getattr(self.params, 'disw_t_z', 0.01)
                    )),
                    "DISW-brow.B.R": Vector((
                        getattr(self.params, 'disw_b_x', 0.03),
                        getattr(self.params, 'disw_b_y', 0.003),
                        getattr(self.params, 'disw_b_z', -0.005)
                    )),
                    "DISW-brow.B.R.001": Vector((
                        getattr(self.params, 'disw_b_001_x', 0.02),
                        getattr(self.params, 'disw_b_001_y', 0.003),
                        getattr(self.params, 'disw_b_001_z', -0.01)
                    ))
                }
            else:
                # 使用默认坐标
                return self.get_default_disw_positions()
        except Exception as e:
            print(f"⚠ 读取自定义坐标参数失败，使用默认值: {e}")
            return self.get_default_disw_positions()
    
    def get_default_disw_positions(self):
        """获取默认的DISW骨骼位置"""
        return {
            "DISW-brow.T.R.001": Vector((0.015, 0.005, 0.02)),
            "DISW-brow.T.R.002": Vector((0.025, 0.005, 0.015)),
            "DISW-brow.T.R": Vector((0.035, 0.005, 0.01)),
            "DISW-brow.B.R": Vector((0.03, 0.003, -0.005)),
            "DISW-brow.B.R.001": Vector((0.02, 0.003, -0.01))
        }
    
    def generate_bones(self):
        """生成右眉毛控制骨骼层级结构
        
        层级结构：
        brow-root.R (根骨骼)
        ├── brow-con.R (控制器)
        ├── DISW-brow.T.R.001 (权重骨骼)
        ├── DISW-brow.T.R.002
        ├── DISW-brow.T.R
        ├── DISW-brow.B.R.001
        └── DISW-brow.B.R
        """
        bones = BoneDict()
        
        # 1. 创建根骨骼 brow-root.R
        self.root_bone = self.copy_bone(self.base_bone, "brow-root.R")
        bones.root = self.root_bone
        
        # 2. 创建控制器骨骼 brow-con.R
        self.control_bone = self.copy_bone(self.base_bone, "brow-con.R")
        bones.ctrl = self.control_bone
        
        # 3. 创建权重骨骼
        self.disw_bones = []
        disw_bone_specs = [
            "DISW-brow.T.R.001",   # 上眉1
            "DISW-brow.T.R.002",   # 上眉2
            "DISW-brow.T.R",       # 上眉主要
            "DISW-brow.B.R.001",   # 下眉1
            "DISW-brow.B.R"        # 下眉主要
        ]
        
        for bone_name in disw_bone_specs:
            disw_bone = self.copy_bone(self.base_bone, bone_name)
            self.disw_bones.append(disw_bone)
            
            # 设置权重骨骼的位置（相对于控制器骨骼 brow-con.R）
            if bone_name in self.disw_positions:
                bone_obj = self.get_bone(disw_bone)
                control_bone_obj = self.get_bone(self.control_bone)  # 使用控制器骨骼而不是根骨骼
                
                # 计算权重骨骼的位置（相对于控制器骨骼）
                offset = self.disw_positions[bone_name]
                bone_obj.head = control_bone_obj.head + offset
                bone_obj.tail = bone_obj.head + Vector((0, 0.005, 0))  # 设置小的尾部偏移
                
                print(f"✓ 创建权重骨骼: {bone_name} 位置偏移: {offset} (相对于 {self.control_bone})")
            else:
                # 如果没有自定义位置，使用默认位置
                print(f"⚠ 权重骨骼 {bone_name} 没有找到自定义位置，使用默认位置")
        
        # 将权重骨骼添加到bones字典
        bones.disw = self.disw_bones
        
        # 注册到父级控制器（nebysse_faceup_con）
        self.register_to_faceup_controller()
        
        print(f"✓ 右眉骨骼层级生成完成: root={self.root_bone}, ctrl={self.control_bone}, disw={len(self.disw_bones)}个")
        
        return bones
    
    def create_disw_bones_from_positions(self):
        """根据自定义坐标创建 DISW 骨骼"""
        try:
            for target_name, position in self.disw_positions.items():
                # 创建 DISW 骨骼
                disw_bone = self.copy_bone(self.base_bone, target_name)
                
                # 设置骨骼位置（相对于主控制器）
                bone_obj = self.get_bone(disw_bone)
                base_head = self.get_bone(self.base_bone).head
                bone_obj.head = base_head + position
                bone_obj.tail = bone_obj.head + Vector((0, 0, 0.01))  # 设置小的尾部偏移
                
                self.disw_bones.append(disw_bone)
                print(f"✓ 创建 DISW 骨骼: {target_name} at {position}")
            
            print(f"✓ 从自定义坐标创建了 {len(self.disw_bones)} 个 DISW 骨骼")
            
        except Exception as e:
            print(f"✗ 创建 DISW 骨骼失败: {e}")
            import traceback
            traceback.print_exc()
    
    def append_disw_bones_from_template(self):
        """从模板文件追加 DISW 骨骼"""
        try:
            # 获取当前文件的绝对路径
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            parent_dir = os.path.dirname(current_dir)
            template_path = os.path.join(parent_dir, "templates", "wei_brow_r.json")
            
            if not os.path.exists(template_path):
                print(f"✗ 模板文件不存在: {template_path}")
                return
            
            import json
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 从模板数据创建骨骼
            for i, bone_data in enumerate(template_data.get('bones', [])):
                if i < len(self.target_bone_names):
                    target_name = self.target_bone_names[i]
                    disw_bone = self.copy_bone(self.base_bone, target_name)
                    
                    # 应用模板数据
                    bone_obj = self.get_bone(disw_bone)
                    if 'head' in bone_data:
                        bone_obj.head = Vector(bone_data['head'])
                    if 'tail' in bone_data:
                        bone_obj.tail = Vector(bone_data['tail'])
                    
                    self.disw_bones.append(disw_bone)
                    print(f"✓ 从模板创建 DISW 骨骼: {target_name}")
            
            print(f"✓ 从模板文件创建了 {len(self.disw_bones)} 个 DISW 骨骼")
            
        except Exception as e:
            print(f"✗ 从模板追加 DISW 骨骼失败: {e}")
            import traceback
            traceback.print_exc()
    
    def parent_bones(self):
        """设置骨骼父子关系
        
        层级结构：
        brow-root.R (根骨骼)
        ├── brow-con.R (控制器)
        ├── DISW-brow.T.R.001 (权重骨骼)
        ├── DISW-brow.T.R.002
        ├── DISW-brow.T.R
        ├── DISW-brow.B.R.001
        └── DISW-brow.B.R
        """
        # 调用父类方法设置基础父子关系（这会处理到faceup系统的连接）
        super().parent_bones()
        
        # 设置控制器骨骼为根骨骼的子级
        if hasattr(self, 'control_bone') and hasattr(self, 'root_bone'):
            self.set_bone_parent(self.control_bone, self.root_bone)
            print(f"✓ 设置 {self.control_bone} 父骨骼为 {self.root_bone}")
        
        # 设置所有DISW骨骼为根骨骼的子级（与brow-con.R同级）
        if hasattr(self, 'disw_bones') and hasattr(self, 'root_bone'):
            for disw_bone in self.disw_bones:
                self.set_bone_parent(disw_bone, self.root_bone)
                print(f"✓ 设置 {disw_bone} 父骨骼为 {self.root_bone}")
        
        print(f"✓ 右眉骨骼层级关系设置完成")
    
    def configure_bones(self):
        """配置眉毛控制骨骼"""
        bone = self.get_bone(self.control_bone)
        
        # 眉毛控制主要是 X, Z 轴移动
        bone.lock_location = [False, True, False]
        bone.lock_rotation = [True, True, True]
        bone.lock_scale = [True, True, True]
        
        # 配置 DISW 骨骼
        for disw_bone in self.disw_bones:
            disw_bone_obj = self.get_bone(disw_bone)
            disw_bone_obj.lock_location = [False, False, False]
            disw_bone_obj.lock_rotation = [True, True, True]
            disw_bone_obj.lock_scale = [True, True, True]
    
    @staticmethod
    def add_parameters(params):
        """添加参数"""
        # 基础参数
        params.brow_control_size = FloatProperty(
            name="控制器大小",
            default=0.7,
            min=0.1,
            max=2.0,
            description="眉毛控制器的大小"
        )
        
        params.enable_brow_rotation = BoolProperty(
            name="启用旋转",
            default=False,
            description="启用眉毛控制器的旋转功能"
        )
        
        params.enable_disw_bones = BoolProperty(
            name="启用 DISW 骨骼",
            default=True,
            description="生成 DISW 子骨骼"
        )
        
        params.disw_bone_size = FloatProperty(
            name="DISW 骨骼大小",
            default=0.3,
            min=0.1,
            max=1.0,
            description="DISW 骨骼的大小"
        )
        
        # 约束设置
        params.enable_disw_constraints = BoolProperty(
            name="启用 DISW 约束",
            default=False,
            description="为 DISW 骨骼添加复制位置约束（通常不需要）"
        )
        
        # 坐标模式选择
        params.use_custom_positions = BoolProperty(
            name="使用自定义坐标",
            default=True,
            description="使用自定义坐标而不是模板文件"
        )
        
        # DISW-brow.T.R.001 坐标参数
        params.disw_t_001_x = FloatProperty(
            name="T.001 X",
            default=0.015,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R.001 的 X 坐标（相对于 brow-con.R）"
        )
        
        params.disw_t_001_y = FloatProperty(
            name="T.001 Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R.001 的 Y 坐标（相对于 brow-con.R）"
        )
        
        params.disw_t_001_z = FloatProperty(
            name="T.001 Z",
            default=0.02,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R.001 的 Z 坐标（相对于 brow-con.R）"
        )
        
        # DISW-brow.T.R.002 坐标参数
        params.disw_t_002_x = FloatProperty(
            name="T.002 X",
            default=0.025,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R.002 的 X 坐标（相对于 brow-con.R）"
        )
        
        params.disw_t_002_y = FloatProperty(
            name="T.002 Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R.002 的 Y 坐标（相对于 brow-con.R）"
        )
        
        params.disw_t_002_z = FloatProperty(
            name="T.002 Z",
            default=0.015,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R.002 的 Z 坐标（相对于 brow-con.R）"
        )
        
        # DISW-brow.T.R 坐标参数
        params.disw_t_x = FloatProperty(
            name="T X",
            default=0.035,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R 的 X 坐标（相对于 brow-con.R）"
        )
        
        params.disw_t_y = FloatProperty(
            name="T Y",
            default=0.005,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R 的 Y 坐标（相对于 brow-con.R）"
        )
        
        params.disw_t_z = FloatProperty(
            name="T Z",
            default=0.01,
            min=-0.1,
            max=0.1,
            description="DISW-brow.T.R 的 Z 坐标（相对于 brow-con.R）"
        )
        
        # DISW-brow.B.R 坐标参数
        params.disw_b_x = FloatProperty(
            name="B X",
            default=0.03,
            min=-0.1,
            max=0.1,
            description="DISW-brow.B.R 的 X 坐标（相对于 brow-con.R）"
        )
        
        params.disw_b_y = FloatProperty(
            name="B Y",
            default=0.003,
            min=-0.1,
            max=0.1,
            description="DISW-brow.B.R 的 Y 坐标（相对于 brow-con.R）"
        )
        
        params.disw_b_z = FloatProperty(
            name="B Z",
            default=-0.005,
            min=-0.1,
            max=0.1,
            description="DISW-brow.B.R 的 Z 坐标（相对于 brow-con.R）"
        )
        
        # DISW-brow.B.R.001 坐标参数
        params.disw_b_001_x = FloatProperty(
            name="B.001 X",
            default=0.02,
            min=-0.1,
            max=0.1,
            description="DISW-brow.B.R.001 的 X 坐标（相对于 brow-con.R）"
        )
        
        params.disw_b_001_y = FloatProperty(
            name="B.001 Y",
            default=0.003,
            min=-0.1,
            max=0.1,
            description="DISW-brow.B.R.001 的 Y 坐标（相对于 brow-con.R）"
        )
        
        params.disw_b_001_z = FloatProperty(
            name="B.001 Z",
            default=-0.01,
            min=-0.1,
            max=0.1,
            description="DISW-brow.B.R.001 的 Z 坐标（相对于 brow-con.R）"
        )
    
    @staticmethod
    def parameters_ui(layout, params):
        """参数界面"""
        layout.label(text="右眉毛控制器:")
        
        # 基础参数
        row = layout.row()
        row.prop(params, "brow_control_size", text="控制器大小")
        
        row = layout.row()
        row.prop(params, "enable_brow_rotation", text="启用旋转")
        
        # DISW 骨骼设置
        layout.separator()
        layout.label(text="DISW 骨骼设置:")
        
        row = layout.row()
        row.prop(params, "enable_disw_bones", text="启用 DISW 骨骼")
        
        if params.enable_disw_bones:
            row = layout.row()
            row.prop(params, "disw_bone_size", text="DISW 骨骼大小")
            
            row = layout.row()
            row.prop(params, "enable_disw_constraints", text="启用 DISW 约束")
            
            row = layout.row()
            row.prop(params, "use_custom_positions", text="使用自定义坐标")
            
            if params.use_custom_positions:
                layout.separator()
                layout.label(text="DISW 骨骼坐标 (相对于 brow-con.R):")
                
                # DISW-brow.T.R.001 坐标
                box = layout.box()
                box.label(text="T.R.001 (上眉内侧):")
                row = box.row()
                row.prop(params, "disw_t_001_x", text="X")
                row.prop(params, "disw_t_001_y", text="Y") 
                row.prop(params, "disw_t_001_z", text="Z")
                
                # DISW-brow.T.R.002 坐标
                box = layout.box()
                box.label(text="T.R.002 (上眉中部):")
                row = box.row()
                row.prop(params, "disw_t_002_x", text="X")
                row.prop(params, "disw_t_002_y", text="Y")
                row.prop(params, "disw_t_002_z", text="Z")
                
                # DISW-brow.T.R 坐标
                box = layout.box()
                box.label(text="T.R (上眉外侧):")
                row = box.row()
                row.prop(params, "disw_t_x", text="X")
                row.prop(params, "disw_t_y", text="Y")
                row.prop(params, "disw_t_z", text="Z")
                
                # DISW-brow.B.R 坐标
                box = layout.box()
                box.label(text="B.R (下眉外侧):")
                row = box.row()
                row.prop(params, "disw_b_x", text="X")
                row.prop(params, "disw_b_y", text="Y")
                row.prop(params, "disw_b_z", text="Z")
                
                # DISW-brow.B.R.001 坐标
                box = layout.box()
                box.label(text="B.R.001 (下眉内侧):")
                row = box.row()
                row.prop(params, "disw_b_001_x", text="X")
                row.prop(params, "disw_b_001_y", text="Y")
                row.prop(params, "disw_b_001_z", text="Z") 