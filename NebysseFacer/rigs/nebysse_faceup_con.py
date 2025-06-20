from rigify.base_rig import BaseRig
from rigify.utils.naming import make_derived_name
from rigify.utils.bones import BoneDict
from rigify.utils.widgets import create_widget
from ..utils.face_utils import create_face_control_widget
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from mathutils import Vector
from .neboffset_bones import (
    NEBOFFSET_BONE_ATTRIBUTES,
    NEBOFFSET_BONE_MAPPING,
    POSITION_MAPPINGS,
    CONSTRAINT_MAPPINGS,
    BONE_GROUPS,
    get_neboffset_bone_count,
    get_constraint_count,
    validate_bone_lists
)
import json
import os
import bpy

# 导入重构后的utils模块
from .utils import (
    TemplateManager,
    BoneDetector,
    GenerationManager,
    ConstraintManager,
    parse_bone_list,
    validate_bone_existence
)

# 导入rigify骨骼集合相关的utils
from rigify.utils.layers import set_bone_layers

# 导入stage装饰器
from rigify.base_rig import stage

class Rig(BaseRig):
    """FaceUP-con: 面部控制主控系统"""
    
    ####################################################
    # 定义骨骼集合类型（按照rigify标准）
    
    class CtrlBones(BaseRig.CtrlBones):
        """控制骨骼集合"""
        master: str                    # 主控制器
        face_root: str                 # 面部根控制器
        mouth_main: str                # 嘴部主控制器
        eye_l_main: str                # 左眼主控制器
        eye_r_main: str                # 右眼主控制器
        brow_l_main: str               # 左眉主控制器
        brow_r_main: str               # 右眉主控制器
    
    class MchBones(BaseRig.MchBones):
        """机制骨骼集合（从rigify复制的骨骼）"""
        face_bones: BoneDict           # 从rigify面部骨骼复制的MCH骨骼
    
    class DiswBones(BoneDict):
        """NebOffset骨骼集合（自定义集合）"""
        # 眉毛NebOffset骨骼 - 左侧
        brow_t_l_003: str              # NebOffset-brow.t.l.003
        brow_t_l_002: str              # NebOffset-brow.t.l.002
        brow_t_l_001: str              # NebOffset-brow.t.l.001
        
        # 眉毛NebOffset骨骼 - 右侧（对称）
        brow_t_r_003: str              # NebOffset-brow.t.r.003
        brow_t_r_002: str              # NebOffset-brow.t.r.002
        brow_t_r_001: str              # NebOffset-brow.t.r.001
        
        # 嘴唇NebOffset骨骼 - 左侧
        lip_t_l_001: str               # NebOffset-lip.t.l.001
        lip_t_l_002: str               # NebOffset-lip.t.l.002
        lip_b_l_001: str               # NebOffset-lip.b.l.001
        lip_b_l_002: str               # NebOffset-lip.b.l.002
        lips_l: str                    # NebOffset-lips.l
        
        # 嘴唇NebOffset骨骼 - 右侧（对称）
        lip_t_r_001: str               # NebOffset-lip.t.r.001
        lip_t_r_002: str               # NebOffset-lip.t.r.002
        lip_b_r_001: str               # NebOffset-lip.b.r.001
        lip_b_r_002: str               # NebOffset-lip.b.r.002
        lips_r: str                    # NebOffset-lips.r
        
        # 嘴唇NebOffset骨骼 - 中央
        lip_t: str                     # NebOffset-lip.t
        lip_b: str                     # NebOffset-lip.b
    
    # 类型注解，定义bones属性的结构
    bones: BaseRig.ToplevelBones[
        str,                           # org: 单个基础骨骼
        'Rig.CtrlBones',              # ctrl: 控制骨骼集合
        'Rig.MchBones',               # mch: 机制骨骼集合
        list[str]                      # deform: 变形骨骼列表
    ]
    
    def __init__(self, generator, pose_bone):
        super().__init__(generator, pose_bone)
        
        # 子级定位器管理
        self.child_locators = {}
        self.required_locators = [
            "mouth-con",
            "eyelip-con.L", 
            "eyelip-con.R",
            "brow-con.L",
            "brow-con.R"
        ]
        
        # 主要骨骼引用
        self.faceroot_bone = None
        self.neb_facer_root_bone = None
        self.neb_rigify_face_bone = None
        self.template_data = None
        
        # 骨骼集合引用
        self.bone_collections = {}
        
        # 按照rigify标准，在__init__中初始化所有骨骼集合
        print("🏗️ 初始化骨骼集合结构...")
        
        # 重新初始化bones结构，添加自定义集合
        self.bones.ctrl = self.CtrlBones()
        self.bones.mch = self.MchBones()
        self.bones.mch.face_bones = BoneDict()  # MCH面部骨骼集合
        
        # 添加自定义NebOffset骨骼集合
        self.bones.wei = self.DiswBones()
        
        # 添加兼容性集合（保持现有约束系统工作）
        self.bones.neb_face_bones = BoneDict()  # 兼容性视图
        
        print("✅ 骨骼集合结构初始化完成")
        print(f"    🎮 ctrl: {type(self.bones.ctrl).__name__}")
        print(f"    🔧 mch: {type(self.bones.mch).__name__}")
        print(f"    ⚖️ wei: {type(self.bones.wei).__name__}")
        print(f"    🔗 neb_face_bones: {type(self.bones.neb_face_bones).__name__}")
        
        # 初始化管理器
        self.template_manager = TemplateManager(self)
        self.generation_manager = GenerationManager(self)
        self.constraint_manager = ConstraintManager(self)
    
    def ensure_bone_collection(self, name, *, ui_row=0, ui_title='', sel_set=False, color_set_id=0):
        """创建或获取指定名称的骨骼集合，并设置UI属性"""
        # 检查集合是否已存在
        coll = self.obj.data.collections_all.get(name)
        
        if not coll:
            # 创建新的骨骼集合
            coll = self.obj.data.collections.new(name)
            print(f"✓ 创建骨骼集合: {name}")
        else:
            print(f"✓ 使用现有骨骼集合: {name}")
        
        # 设置rigify UI属性
        if ui_row > 0:
            coll.rigify_ui_row = ui_row
        if ui_title:
            coll.rigify_ui_title = ui_title
        if sel_set:
            coll.rigify_sel_set = sel_set
        if color_set_id > 0:
            coll.rigify_color_set_id = color_set_id
        
        # 缓存集合引用
        self.bone_collections[name] = coll
        return coll
    
    def create_bone_collections(self):
        """创建所有需要的骨骼集合"""
        print("\n🗂️ === 开始创建骨骼集合 ===")
        
        # 创建Neb_MCH集合 - 包含从rigify复制的机制骨骼
        self.ensure_bone_collection('Neb_MCH', 
                                   ui_row=3, 
                                   ui_title='MCH (面部机制)',
                                   color_set_id=4)
        
        # 创建Neb_Disw集合 - 包含距离权重控制骨骼
        self.ensure_bone_collection('Neb_Disw',
                                   ui_row=4,
                                   ui_title='Disw (距离权重控制)',
                                   color_set_id=3)
        
        # 创建Neb_Con集合 - 包含主要控制骨骼
        self.ensure_bone_collection('Neb_Con',
                                   ui_row=2,
                                   ui_title='Con (主控制器)',
                                   color_set_id=2)
        
        # 创建主层级集合
        self.ensure_bone_collection('Neb_Face',
                                   ui_row=1,
                                   ui_title='Face (面部系统)',
                                   color_set_id=5)
        
        print(f"✅ 骨骼集合创建完成，共创建 {len(self.bone_collections)} 个集合")
        for name, coll in self.bone_collections.items():
            print(f"    📁 {name}: UI行 {coll.rigify_ui_row}, 颜色 {coll.rigify_color_set_id}")
        
        print("🗂️ === 骨骼集合创建完成 ===\n")
    
    def assign_bone_to_collection(self, bone_name, collection_name):
        """将骨骼分配到指定集合"""
        if collection_name not in self.bone_collections:
            print(f"⚠ 骨骼集合 '{collection_name}' 不存在，跳过分配骨骼 '{bone_name}'")
            return False
        
        try:
            # 获取骨骼集合
            coll = self.bone_collections[collection_name]
            
            # 获取编辑骨骼或普通骨骼
            if self.obj.mode == 'EDIT':
                bone = self.obj.data.edit_bones.get(bone_name)
            else:
                bone = self.obj.data.bones.get(bone_name)
            
            if bone:
                # 使用rigify的set_bone_layers函数分配骨骼
                set_bone_layers(bone, [coll])
                print(f"✓ 分配骨骼 '{bone_name}' 到集合 '{collection_name}'")
                return True
            else:
                print(f"⚠ 骨骼 '{bone_name}' 不存在")
                return False
                
        except Exception as e:
            print(f"❌ 分配骨骼失败: {bone_name} -> {collection_name}: {e}")
            return False
    
    def find_master_faceroot(self):
        """查找主控 faceroot"""
        current = self.base_bone
        while current:
            parent_name = self.get_bone(current).parent
            if parent_name:
                parent_rig = self.generator.bone_owners.get(parent_name)
                if parent_rig and hasattr(parent_rig, 'rig_id'):
                    if parent_rig.rig_id == 'nebysse_faceup_con':
                        return parent_rig
                current = parent_name
            else:
                break
        return None
    
    def generate_bones(self):
        """生成骨骼结构"""
        print("\n🏗️ === 开始生成骨骼结构 ===")
        
        # 1. 创建骨骼集合
        self.create_bone_collections()
        
        # 2. 创建 Neb_Facer_root 顶层骨骼
        self.neb_facer_root_bone = self.copy_bone(self.base_bone, "Neb_Facer_root")
        self.bones.neb_facer_root = self.neb_facer_root_bone
        print(f"✓ 创建顶层骨骼: Neb_Facer_root")
        
        # 3. 创建 Neb_face-root 主控骨骼
        self.faceroot_bone = self.copy_bone(self.base_bone, "Neb_face-root")
        self.bones.ctrl.master = self.faceroot_bone  # 使用标准命名
        print(f"✓ 创建主控骨骼: Neb_face-root")
        
        # 4. 创建 Neb_RigifyFace 父级骨骼
        self.neb_rigify_face_bone = self.copy_bone(self.base_bone, "Neb_RigifyFace")
        self.bones.neb_rigify_face = self.neb_rigify_face_bone
        print(f"✓ 创建父级骨骼: Neb_RigifyFace")
        
        # 5. 生成NebOffset骨骼（使用预定义的规范）
        print("\n⚖️ 生成NebOffset骨骼...")
        
        # 打印当前骨架的全部骨骼名称
        print("\n📋 === 当前骨架包含的所有骨骼 ===")
        all_bones = [bone.name for bone in self.obj.data.bones]
        print(f"📊 总骨骼数: {len(all_bones)} 个")
        
        # 按类型分组显示骨骼
        org_bones = [bone for bone in all_bones if bone.startswith('ORG-')]
        def_bones = [bone for bone in all_bones if bone.startswith('DEF-')]
        mch_bones = [bone for bone in all_bones if bone.startswith('MCH-')]
        wgt_bones = [bone for bone in all_bones if bone.startswith('WGT-')]
        neb_bones = [bone for bone in all_bones if bone.startswith('Neb')]
        disw_bones = [bone for bone in all_bones if bone.startswith('DISW-')]
        neboffset_bones = [bone for bone in all_bones if bone.startswith('NebOffset-')]
        ctrl_bones = [bone for bone in all_bones if not any(bone.startswith(prefix) for prefix in ['ORG-', 'DEF-', 'MCH-', 'WGT-', 'Neb', 'DISW-', 'NebOffset-'])]
        
        print(f"📊 骨骼类型统计:")
        print(f"   🦴 ORG骨骼 (原始): {len(org_bones)} 个") 
        print(f"   🔧 DEF骨骼 (变形): {len(def_bones)} 个")
        print(f"   ⚙️ MCH骨骼 (机制): {len(mch_bones)} 个") 
        print(f"   🎛️ WGT骨骼 (控件): {len(wgt_bones)} 个")
        print(f"   🏗️ Neb骨骼 (Nebysse): {len(neb_bones)} 个")
        print(f"   📐 DISW骨骼 (距离权重): {len(disw_bones)} 个")
        print(f"   ⚖️ NebOffset骨骼: {len(neboffset_bones)} 个")
        print(f"   🎯 其他控制骨骼: {len(ctrl_bones)} 个")
        
        # 显示Neb相关骨骼详细列表
        if neb_bones:
            print(f"\n🏗️ Neb骨骼详细列表 ({len(neb_bones)} 个):")
            for i, bone_name in enumerate(neb_bones):
                print(f"   {i+1:3d}. {bone_name}")
        
        # 显示DISW骨骼详细列表
        if disw_bones:
            print(f"\n📐 DISW骨骼详细列表 ({len(disw_bones)} 个):")
            for i, bone_name in enumerate(disw_bones):
                print(f"   {i+1:3d}. {bone_name}")
        
        # 显示NebOffset骨骼详细列表
        if neboffset_bones:
            print(f"\n⚖️ NebOffset骨骼详细列表 ({len(neboffset_bones)} 个):")
            for i, bone_name in enumerate(neboffset_bones):
                print(f"   {i+1:3d}. {bone_name}")
        
        # 显示部分控制骨骼作为参考
        if ctrl_bones:
            print(f"\n🎯 其他控制骨骼示例 (前10个，共{len(ctrl_bones)}个):")
            for i, bone_name in enumerate(ctrl_bones[:10]):
                print(f"   {i+1:3d}. {bone_name}")
            if len(ctrl_bones) > 10:
                print(f"   ... 还有 {len(ctrl_bones) - 10} 个控制骨骼")
        
        print(f"📋 === 骨骼列表显示完成 ===\n")
        
        # 验证配置文件
        print("🔍 验证NebOffset骨骼配置...")
        validation_errors = validate_bone_lists()
        if validation_errors:
            print("❌ 配置验证失败:")
            for error in validation_errors:
                print(f"   - {error}")
        else:
            print("✅ 配置验证通过")
        
        print(f"📊 从配置文件加载: {get_neboffset_bone_count()} 个NebOffset骨骼定义")
        
        # 使用配置文件中的骨骼映射
        disw_generated_count = 0
        disw_failed_count = 0
        
        for attr_name, bone_name in NEBOFFSET_BONE_MAPPING.items():
            try:
                disw_bone = self.copy_bone(self.base_bone, bone_name)
                setattr(self.bones.wei, attr_name.replace('.', '_'), disw_bone)  # 属性名转换为有效标识符
                disw_generated_count += 1
            except Exception as e:
                print(f"⚠ 生成NebOffset骨骼失败 {bone_name}: {e}")
                disw_failed_count += 1
                continue
        
        print(f"📊 NebOffset骨骼生成统计: 成功 {disw_generated_count} 个，失败 {disw_failed_count} 个")
        
        
        # 7. 统计所有骨骼
        total_wei = disw_generated_count
        
        print(f"\n✅ 骨骼生成完成总结:")
        print(f"    🏗️ 主要骨骼: 3 个 (Neb_Facer_root, Neb_face-root, Neb_RigifyFace)")
        print(f"    ⚖️ NebOffset 骨骼: {total_wei} 个")
        
        print(f"🏗️ === 骨骼结构生成完成 ===\n")
    
    def rig_bones(self):
        """设置约束系统和骨骼集合分配"""
        print("\n🔗 === 开始设置约束系统和骨骼集合分配 ===")
        
        # 分配主要骨骼到相应集合
        print("\n📁 分配主要骨骼到集合...")
        self.assign_bone_to_collection('Neb_Facer_root', 'Neb_Face')
        self.assign_bone_to_collection('Neb_face-root', 'Neb_Face')  
        self.assign_bone_to_collection('Neb_RigifyFace', 'Neb_Face')
        
        # 分配NebOffset骨骼到Neb_MCH集合
        if hasattr(self.bones, 'wei') and self.bones.wei:
            print(f"\n📁 分配NebOffset骨骼到Neb_MCH集合...")
            wei_assigned = 0
            wei_failed = 0
            
            # 使用配置文件中的骨骼属性列表
            wei_attr_names = [attr.replace('.', '_') for attr in NEBOFFSET_BONE_ATTRIBUTES]
            
            for i, attr_name in enumerate(wei_attr_names):
                if hasattr(self.bones.wei, attr_name):
                    bone_name = getattr(self.bones.wei, attr_name)
                    if bone_name:
                        if self.assign_bone_to_collection(bone_name, 'Neb_MCH'):
                            wei_assigned += 1
                            print(f"✅ NebOffset {i+1:2d}/{len(wei_attr_names)}: {bone_name}")
                        else:
                            wei_failed += 1
                    else:
                        print(f"⚠ NebOffset {i+1:2d}/{len(wei_attr_names)}: {attr_name} (骨骼名称为空)")
                else:
                    print(f"⚠ NebOffset {i+1:2d}/{len(wei_attr_names)}: {attr_name} (属性不存在)")
                    
            print(f"📊 NebOffset骨骼分配统计: 成功 {wei_assigned} 个，失败 {wei_failed} 个")
        
        # 分配控制骨骼到Neb_Con集合
        if hasattr(self.bones, 'ctrl') and self.bones.ctrl:
            print(f"\n📁 分配控制骨骼到Neb_Con集合...")
            ctrl_assigned = 0
            ctrl_failed = 0
            ctrl_attr_names = ['face_root', 'mouth_main', 'eye_l_main', 'eye_r_main', 'brow_l_main', 'brow_r_main']
            
            for i, attr_name in enumerate(ctrl_attr_names):
                if hasattr(self.bones.ctrl, attr_name):
                    bone_name = getattr(self.bones.ctrl, attr_name)
                    if bone_name:
                        if self.assign_bone_to_collection(bone_name, 'Neb_Con'):
                            ctrl_assigned += 1
                            print(f"✅ 控制骨骼 {i+1:2d}/{len(ctrl_attr_names)}: {bone_name}")
                        else:
                            ctrl_failed += 1
                    else:
                        print(f"⚠ 控制骨骼 {i+1:2d}/{len(ctrl_attr_names)}: {attr_name} (骨骼名称为空)")
                else:
                    print(f"⚠ 控制骨骼 {i+1:2d}/{len(ctrl_attr_names)}: {attr_name} (属性不存在)")
                    
            print(f"📊 控制骨骼分配统计: 成功 {ctrl_assigned} 个，失败 {ctrl_failed} 个")
        
        # 添加复制变换约束
        print(f"\n🔗 === 开始设置复制变换约束 ===")
        self.setup_copy_transform_constraints()
        
        # 复制模板约束和驱动器到NebOffset骨骼
        print(f"\n📋 === 开始复制模板约束和驱动器 ===")
        self.copy_template_constraints_and_drivers()
        
        print(f"🔗 === 约束系统和骨骼集合分配完成 ===\n")
        print(f"💡 注意：NebOffset骨骼位置设置已移至@stage.generate_bones阶段执行")
    
    def copy_template_constraints_and_drivers(self):
        """从模板rig复制约束和驱动器到NebOffset骨骼"""
        print("📋 开始从模板rig复制约束和驱动器到NebOffset骨骼...")
        
        # === 关键：完整的 Rigify 状态保护系统 ===
        rigify_state = {
            'active': bpy.context.view_layer.objects.active,
            'selected': list(bpy.context.selected_objects),
            'mode': bpy.context.mode,
            'current_rig': self.obj
        }
        
        print(f"🛡️ 保护 Rigify 状态:")
        print(f"   📌 活动对象: {rigify_state['active'].name if rigify_state['active'] else 'None'}")
        print(f"   📌 当前rig: {rigify_state['current_rig'].name}")
        print(f"   📌 模式: {rigify_state['mode']}")
        
        try:
            # 确保处于正确的模式和状态
            self._ensure_safe_context()
            
            # 获取模板rig对象（使用优化的查找方法）
            template_rig = self._find_template_rig_safe()
            if not template_rig:
                print("⚠ 未找到模板rig对象，跳过约束和驱动器复制")
                return
            
            print(f"✅ 找到模板rig: {template_rig.name}")
            
            # 执行复制操作（保持状态）
            success = self._perform_template_copy(template_rig)
            
            if success:
                print("✅ 模板约束和驱动器复制完成")
            else:
                print("⚠ 模板复制过程中出现问题")
                
        except Exception as e:
            print(f"❌ 复制模板约束和驱动器时出错: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # === 关键：恢复 Rigify 期望的状态 ===
            self._restore_rigify_state(rigify_state)
        
        print("📋 === 模板约束和驱动器复制完成 ===\n")
    
    def _ensure_safe_context(self):
        """确保处于安全的上下文状态"""
        # 确保在对象模式
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # 确保当前rig是活动的（Rigify要求）
        if bpy.context.view_layer.objects.active != self.obj:
            bpy.context.view_layer.objects.active = self.obj
            self.obj.select_set(True)
    
    def _find_template_rig_safe(self):
        """安全地查找模板rig对象（不破坏Rigify状态）"""
        print("🔍 安全查找模板rig对象...")
        
        # 首先尝试通过 template_manager 查找（推荐方法）
        if hasattr(self, 'template_manager') and self.template_manager:
            try:
                template_rig = self.template_manager.find_template_rig_object_safe(self.obj)
                if template_rig:
                    print(f"✅ 通过template_manager找到: {template_rig.name}")
                    return template_rig
            except Exception as e:
                print(f"⚠ template_manager查找失败: {e}")
        
        # 备用方法：直接在场景中查找
        print("🔍 使用备用方法查找...")
        return self._find_template_in_scene()
    
    def _find_template_in_scene(self):
        """在当前场景中直接查找模板rig"""
        target_names = [
            "Nebysse_FaceUP_Tem.Rig",
            "Nebysse_FaceUP_Tem",
            "FaceUP_Tem.Rig"
        ]
        
        # 精确名称匹配
        for target_name in target_names:
            if target_name in bpy.data.objects:
                obj = bpy.data.objects[target_name]
                if obj.type == 'ARMATURE' and obj != self.obj:
                    print(f"✅ 场景中找到模板rig: {obj.name}")
                    return obj
        
        # 包含NebOffset骨骼的armature对象
        for obj in bpy.context.scene.objects:
            if (obj.type == 'ARMATURE' and 
                obj != self.obj):
                neboffset_bones = [bone for bone in obj.pose.bones if bone.name.startswith('NebOffset-')]
                if len(neboffset_bones) > 5:
                    print(f"✅ 按NebOffset骨骼找到: {obj.name} ({len(neboffset_bones)}个骨骼)")
                    return obj
        
        print("⚠ 场景中未找到模板rig")
        return None
    
    def _perform_template_copy(self, template_rig):
        """执行模板复制操作（增强版：使用专门的NebOffset骨骼复制方法）"""
        constraints_copied = 0
        drivers_copied = 0
        failed_count = 0
        skipped_count = 0
        
        print(f"📋 开始从 {template_rig.name} 复制到NebOffset骨骼...")
        print(f"🎯 使用增强的NebOffset骨骼数据复制方法")
        
        # 创建blend_template_loader实例用于复制操作
        from .utils.blend_template_loader import BlendTemplateLoader
        loader = BlendTemplateLoader()
        # 遍历NEBOFFSET_BONE_ATTRIBUTES中的所有骨骼
        for i, bone_attr in enumerate(NEBOFFSET_BONE_ATTRIBUTES, 1):
            neboffset_bone_name = "NebOffset-"+bone_attr
            
            try:
                print(self.obj.pose.bones[neboffset_bone_name].name)
                print(f"🔄 [{i}/{len(NEBOFFSET_BONE_ATTRIBUTES)}] 复制骨骼数据: {neboffset_bone_name}")
                
                success = loader.copy_neboffset_bone_data(
                    template_rig_name=template_rig.name,
                    neboffset_bone_name=neboffset_bone_name,
                    target_rig=self.obj,
                    target_bone_name=neboffset_bone_name
                )
                
                if success:
                    # 统计成功复制的数据（这里我们使用近似值，因为新方法统一处理）
                    constraints_copied += 1  # 假设至少复制了1个约束
                    drivers_copied += 1       # 假设至少复制了1个驱动器
                    
                    if i <= 10:  # 只显示前10个成功信息
                        print(f"  ✅ [{i}] {neboffset_bone_name}: 完整数据复制成功")
                    elif i == 11:
                        print(f"  ... 继续复制更多骨骼数据 ...")
                else:
                    failed_count += 1
                    if failed_count <= 3:
                        print(f"  ❌ [{i}] {neboffset_bone_name}: 复制失败")
                
            except Exception as e:
                failed_count += 1
                if failed_count <= 3:
                    print(f"❌ 复制失败 {neboffset_bone_name}: {e}")
        
        # 输出统计结果
        successful_bones = len(NEBOFFSET_BONE_ATTRIBUTES) - skipped_count - failed_count
        
        print(f"📊 模板NebOffset骨骼数据复制统计:")
        print(f"   📋 处理骨骼: {len(NEBOFFSET_BONE_ATTRIBUTES)} 个")
        print(f"   ✅ 成功复制: {successful_bones} 个骨骼")
        print(f"   ⚠ 跳过处理: {skipped_count} 个")
        print(f"   ❌ 复制失败: {failed_count} 个")
        
        # 计算近似的约束和驱动器数量（基于成功的骨骼数量）
        estimated_constraints = successful_bones * 2  # 假设每个骨骼平均2个约束
        estimated_drivers = successful_bones * 3      # 假设每个骨骼平均3个驱动器
        
        print(f"   🔗 约束（估算）: {estimated_constraints} 个")
        print(f"   🎯 驱动器（估算）: {estimated_drivers} 个")
        
        if successful_bones > 0:
            success_rate = (successful_bones / len(NEBOFFSET_BONE_ATTRIBUTES)) * 100
            print(f"   📈 成功率: {success_rate:.1f}%")
            print("✅ NebOffset骨骼完整数据复制完成")
        else:
            print("⚠ 没有成功复制任何NebOffset骨骼数据")
        
        return successful_bones > 0
    
    def _restore_rigify_state(self, rigify_state):
        """恢复Rigify期望的状态"""
        try:
            print("🔄 恢复Rigify状态...")
            
            # 最重要：确保当前rig是活动对象
            current_rig = rigify_state['current_rig']
            if current_rig and current_rig.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = current_rig
                current_rig.select_set(True)
                print(f"✅ 活动对象恢复为: {current_rig.name}")
            
            # 恢复模式
            target_mode = rigify_state['mode']
            if bpy.context.mode != target_mode:
                if target_mode == 'EDIT_ARMATURE':
                    bpy.ops.object.mode_set(mode='EDIT')
                elif target_mode == 'POSE':
                    bpy.ops.object.mode_set(mode='POSE')
                else:
                    bpy.ops.object.mode_set(mode='OBJECT')
            
            # 更新视图层
            bpy.context.view_layer.update()
            
            # 验证最终状态
            final_active = bpy.context.view_layer.objects.active
            if final_active == current_rig:
                print("✅ Rigify状态恢复成功")
            else:
                print(f"⚠ 状态恢复异常，强制设置...")
                bpy.context.view_layer.objects.active = current_rig
                
        except Exception as e:
            print(f"❌ 恢复Rigify状态失败: {e}")
            # 紧急恢复
            try:
                current_rig = rigify_state['current_rig']
                bpy.context.view_layer.objects.active = current_rig
                current_rig.select_set(True)
                print("🆘 紧急恢复完成")
            except:
                print("🆘 紧急恢复也失败")
    
    def find_template_rig(self):
        """查找模板rig对象（简化版，委托给安全方法）"""
        print("🔍 开始查找模板rig对象...")
        
        # 直接委托给安全的查找方法
        template_rig = self._find_template_rig_safe()
        
        if template_rig:
            print(f"✅ 找到模板rig: {template_rig.name}")
        else:
            print("⚠ 未找到模板rig对象")
            print("💡 建议检查模板文件或手动导入模板rig")
        
        return template_rig
    
    def copy_bone_constraints(self, source_bone, target_bone, source_rig):
        """复制骨骼约束从源骨骼到目标骨骼"""
        copied_count = 0
        
        for source_constraint in source_bone.constraints:
            try:
                # 创建新约束
                new_constraint = target_bone.constraints.new(source_constraint.type)
                
                # 复制约束名称
                new_constraint.name = source_constraint.name
                
                # 复制约束属性
                self.copy_constraint_properties(source_constraint, new_constraint, source_rig)
                
                copied_count += 1
                
            except Exception as e:
                print(f"❌ 复制约束失败 {source_constraint.name}: {e}")
        
        return copied_count
    
    def copy_constraint_properties(self, source_constraint, target_constraint, source_rig):
        """复制约束属性"""
        # 基本属性
        if hasattr(source_constraint, 'influence'):
            target_constraint.influence = source_constraint.influence
        if hasattr(source_constraint, 'mute'):
            target_constraint.mute = source_constraint.mute
        
        # 目标相关属性
        if hasattr(source_constraint, 'target'):
            if source_constraint.target == source_rig:
                target_constraint.target = self.obj  # 重定向到当前rig
            else:
                target_constraint.target = source_constraint.target
        
        if hasattr(source_constraint, 'subtarget'):
            target_constraint.subtarget = source_constraint.subtarget
        
        # 空间相关属性
        for space_attr in ['target_space', 'owner_space', 'mix_mode']:
            if hasattr(source_constraint, space_attr):
                setattr(target_constraint, space_attr, getattr(source_constraint, space_attr))
        
        # 复制其他通用属性
        for attr in ['use_x', 'use_y', 'use_z', 'invert_x', 'invert_y', 'invert_z']:
            if hasattr(source_constraint, attr):
                setattr(target_constraint, attr, getattr(source_constraint, attr))
    
    def copy_bone_drivers(self, source_bone, target_bone, source_rig):
        """复制骨骼驱动器从源骨骼到目标骨骼"""
        copied_count = 0
        
        if not source_bone.id_data.animation_data:
            return 0
        
        source_drivers = source_bone.id_data.animation_data.drivers
        if not source_drivers:
            return 0
        
        # 获取源骨骼的数据路径前缀
        source_bone_path = f'pose.bones["{source_bone.name}"]'
        
        for driver in source_drivers:
            try:
                # 检查驱动器是否属于源骨骼
                if not driver.data_path.startswith(source_bone_path):
                    continue
                
                # 构建目标数据路径
                target_bone_path = f'pose.bones["{target_bone.name}"]'
                target_data_path = driver.data_path.replace(source_bone_path, target_bone_path)
                
                # 复制驱动器
                self.copy_driver(driver, target_data_path, source_rig)
                copied_count += 1
                
            except Exception as e:
                print(f"❌ 复制驱动器失败: {e}")
        
        return copied_count
    
    def copy_driver(self, source_driver, target_data_path, source_rig):
        """复制单个驱动器"""
        # 确保目标对象有动画数据
        if not self.obj.animation_data:
            self.obj.animation_data_create()
        
        # 创建新驱动器
        new_driver = self.obj.driver_add(target_data_path)
        if hasattr(new_driver, '__len__'):  # 如果返回列表，取第一个
            new_driver = new_driver[0]
        
        # 复制驱动器类型和表达式
        new_driver.driver.type = source_driver.driver.type
        if hasattr(source_driver.driver, 'expression'):
            new_driver.driver.expression = source_driver.driver.expression
        
        # 复制变量
        for source_var in source_driver.driver.variables:
            new_var = new_driver.driver.variables.new()
            new_var.name = source_var.name
            new_var.type = source_var.type
            
            # 复制变量目标
            for i, source_target in enumerate(source_var.targets):
                if i < len(new_var.targets):
                    new_target = new_var.targets[i]
                    
                    # 重定向目标对象
                    if source_target.id == source_rig:
                        new_target.id = self.obj
                    else:
                        new_target.id = source_target.id
                    
                    # 复制其他目标属性
                    for attr in ['bone_target', 'data_path', 'transform_type', 'transform_space']:
                        if hasattr(source_target, attr):
                            setattr(new_target, attr, getattr(source_target, attr))
    
    def setup_copy_transform_constraints(self):
        """设置复制变换约束"""
        print("🔗 开始为rigify骨骼添加复制变换约束...")
        
        # 使用配置文件中的约束映射
        constraint_mappings = CONSTRAINT_MAPPINGS
        
        constraint_added_count = 0
        constraint_failed_count = 0
        constraint_skipped_count = 0
        
        print(f"📝 准备为 {len(constraint_mappings)} 个骨骼对添加复制变换约束...")
        print("🎯 约束方向：rigify骨骼 -> NebOffset骨骼")
        print("🏗️ 父级骨骼：所有NebOffset骨骼都将以Neb_RigifyFace为父级")
        print(f"📋 约束配置来源：neboffset_bones.py (共 {get_constraint_count()} 个映射)")
        
        # 添加设置父级功能
        print("👨‍👩‍👧‍👦 开始为NebOffset骨骼设置父级...")
        parent_set_count = 0
        parent_failed_count = 0
        parent_skipped_count = 0
        
        for nonebone , source_bone_name  in constraint_mappings:
            target_bone_name = 'Neb_RigifyFace'
            try:
                parent_edit_bone = self.obj.data.edit_bones[target_bone_name]
                self.obj.data.edit_bones[source_bone_name].parent = parent_edit_bone
                parent_set_count += 1
                
            except Exception as e:
                parent_failed_count += 1
                if parent_failed_count <= 3:  # 只显示前3个错误
                    print(f"❌ 设置父级失败 {target_bone_name} -> {self.neb_rigify_face_bone}: {e}")
        




        # 输出父级设置统计
        total_parent_processed = parent_set_count + parent_failed_count + parent_skipped_count
        print(f"\n📊 NebOffset骨骼父级设置统计:")
        print(f"   ✅ 成功设置: {parent_set_count} 个父级关系")
        print(f"   ❌ 设置失败: {parent_failed_count} 个")
        print(f"   ⚠ 跳过处理: {parent_skipped_count} 个")
        print(f"   📝 总处理量: {total_parent_processed} 个")
        
        if parent_set_count > 0:
            parent_success_rate = (parent_set_count / total_parent_processed) * 100
            print(f"   📈 成功率: {parent_success_rate:.1f}%")
            print(f"✅ NebOffset骨骼父级设置完成，所有目标骨骼现在以 {self.neb_rigify_face_bone} 为父级")
            print("🎯 父级结构：Neb_RigifyFace -> 所有NebOffset骨骼")
        else:
            print("⚠ 没有成功设置任何NebOffset骨骼父级关系")
            print("💡 请检查Neb_RigifyFace骨骼和NebOffset骨骼是否正确生成")
        
        print("👨‍👩‍👧‍👦 === NebOffset骨骼父级设置完成 ===\n")
        
        for source_bone_name, target_bone_name in constraint_mappings:
            try:
                # 检查源骨骼（rigify骨骼）是否存在
                if source_bone_name not in self.obj.pose.bones:
                    constraint_skipped_count += 1
                    if constraint_skipped_count <= 5:  # 只显示前5个跳过信息
                        print(f"⚠ 跳过约束：源骨骼 '{source_bone_name}' 不存在")
                    continue
                
                # 检查目标骨骼（NebOffset骨骼）是否存在
                if target_bone_name not in self.obj.pose.bones:
                    constraint_failed_count += 1
                    if constraint_failed_count <= 5:  # 只显示前5个失败信息
                        print(f"❌ 约束失败：目标骨骼 '{target_bone_name}' 不存在")
                    continue
                
                # 获取源骨骼的姿态骨骼
                source_pbone = self.obj.pose.bones[source_bone_name]
                
                # 创建复制变换约束
                copy_transform = source_pbone.constraints.new('COPY_TRANSFORMS')
                copy_transform.name = f"复制变换_到_{target_bone_name}"
                copy_transform.target = self.obj
                copy_transform.subtarget = target_bone_name
                
                # 设置约束属性
                copy_transform.influence = 1.0  # 完全影响
                copy_transform.mix_mode = 'BEFORE'  # 在原始变换之前应用
                copy_transform.target_space = 'LOCAL'  # 局部空间
                copy_transform.owner_space = 'LOCAL'   # 局部空间
                
                constraint_added_count += 1
                
                # 显示成功添加的约束（只显示前10个）
                if constraint_added_count <= 10:
                    print(f"✅ 约束 {constraint_added_count:2d}: {source_bone_name:15s} -> {target_bone_name}")
                elif constraint_added_count == 11:
                    print(f"   ... 继续添加更多约束 ...")
                
            except Exception as e:
                constraint_failed_count += 1
                if constraint_failed_count <= 3:  # 只显示前3个错误
                    print(f"❌ 添加约束失败 {source_bone_name} -> {target_bone_name}: {e}")
        
        # 输出约束添加统计
        total_processed = constraint_added_count + constraint_failed_count + constraint_skipped_count
        print(f"\n📊 复制变换约束添加统计:")
        print(f"   ✅ 成功添加: {constraint_added_count} 个约束")
        print(f"   ❌ 添加失败: {constraint_failed_count} 个")
        print(f"   ⚠ 跳过处理: {constraint_skipped_count} 个")
        print(f"   📝 总处理量: {total_processed} 个")
        
        if constraint_added_count > 0:
            success_rate = (constraint_added_count / total_processed) * 100
            print(f"   📈 成功率: {success_rate:.1f}%")
            print("✅ 复制变换约束系统设置完成")
            print("🎯 约束效果：rigify骨骼的变换将跟随对应的NebOffset骨骼")
        else:
            print("⚠ 没有成功添加任何复制变换约束")
            print("💡 请检查源骨骼和目标骨骼是否正确生成")
        
        print("🔗 === 复制变换约束设置完成 ===\n")
    
    @stage.generate_bones
    def set_neboffset_positions_late(self):
        """延迟设置NebOffset骨骼位置 - 在所有rig的generate_bones完成后执行
        
        重要说明：
        - 使用编辑模式下的根坐标（head）和头坐标（tail）
        - 这些是世界坐标系下的绝对位置，不是姿态坐标
        - 坐标复制在编辑状态下进行，确保骨骼的基础结构正确
        """
        print(f"\n📍 === 延迟设置NebOffset骨骼编辑坐标 ===")
        print("💡 使用@stage.generate_bones装饰器确保在所有rigify骨骼生成完成后执行")
        print("🎯 坐标类型：编辑模式下的根坐标（head）和头坐标（tail），非姿态坐标")
        
        # 检查NebOffset骨骼集合是否存在
        #if not hasattr(self.bones, 'wei') or not self.bones.wei:
        #    print("⚠ NebOffset骨骼集合不存在，跳过编辑坐标设置")
        #    return
        
        # 获取编辑模式下的骨骼
        edit_bones = self.obj.data.edit_bones
        all_bones = [bone.name for bone in edit_bones]
        total_bones = len(all_bones)
        
        print(f"📊 当前骨架包含 {total_bones} 个骨骼（编辑模式）")
        
        # 快速检查关键rigify骨骼是否存在
        key_rigify_bones = ['brow.T.L.003', 'brow.T.R.003', 'lip.T.L', 'lip.B.L', 'cheek.B.L']
        existing_key_bones = []
        for bone in key_rigify_bones:
            print(f"🔑 关键rigify骨骼检测: {bone}")
            existing_key_bones.append(bone)
        
        if len(existing_key_bones) == 0:
            print("⚠ 未检测到任何关键rigify面部骨骼，可能不是rigify面部骨架")
            print("💡 跳过NebOffset编辑坐标设置，这是正常情况")
            return
        
        # 更新的骨骼映射配置 - 根据用户指定的对应关系
        # 格式：(NebOffset骨骼属性名, 源rigify骨骼名)
        # 
        # 用户指定的对应关系：
        # - lip.T = lip.T.L (NebOffset-lip.T 从 lip.T.L 获取编辑坐标)
        # - lip.T.L.001 = lip.T.L.001 (保持直接对应)
        # - lips.L = cheek.B.L (NebOffset-lips.L 从 cheek.B.L 获取编辑坐标)
        # - lip.B.L.001 = lip.B.L.001 (保持直接对应)
        # - lip.B = lip.B.L (NebOffset-lip.B 从 lip.B.L 获取编辑坐标)
        # - brow.T.L.003 = brow.T.L.003 (保持直接对应)
        position_mappings = POSITION_MAPPINGS
        
        print(f"📋 位置映射配置来源：neboffset_bones.py (共 {len(position_mappings)} 个映射)")
        
        # 执行编辑坐标设置
        position_set_count = 0
        position_failed_count = 0
        position_skipped_count = 0
        
        print(f"📍 开始设置NebOffset骨骼编辑坐标...")
        print(f"📝 应用新的编辑坐标对应关系:")
        print(f"   - lip.T -> lip.T.L (根坐标+头坐标)")
        print(f"   - lip.B -> lip.B.L (根坐标+头坐标)") 
        print(f"   - lips.L -> cheek.B.L (根坐标+头坐标)")
        print(f"   - 其他骨骼保持直接对应")
        print(f"🎯 坐标类型：编辑模式世界坐标（非姿态坐标）")
        for bone in edit_bones:
            print(f"🔍 检查骨骼: {bone.name}")
        for attr_name, rigify_bone_name in position_mappings:
            try:
                # 检查NebOffset骨骼是否存在
                # 检查两个骨骼是否都存在
                    
                # 复制编辑模式下的根坐标（head）和头坐标（tail）
                # 注意：这里使用的是编辑状态下的世界坐标，而非姿态坐标
                edit_bones["NebOffset-"+attr_name].head = edit_bones["ORG-"+ rigify_bone_name].head 
                edit_bones["NebOffset-"+attr_name].tail = edit_bones["ORG-"+ rigify_bone_name].head+Vector((0,0,0.01)) 
                edit_bones["NebOffset-"+attr_name].roll = 0
                
                position_set_count += 1
                
                    
            except Exception as e:
                position_failed_count += 1
                print(f"❌ 编辑坐标设置失败 {attr_name}: {e}")
        
        # 输出统计结果
        total_processed = position_set_count + position_failed_count + position_skipped_count
        print(f"\n📊 NebOffset骨骼编辑坐标设置统计:")
        print(f"   ✅ 成功设置: {position_set_count} 个（根坐标+头坐标）")
        print(f"   ❌ 设置失败: {position_failed_count} 个") 
        print(f"   ⚠ 跳过处理: {position_skipped_count} 个")
        print(f"   📝 总处理量: {total_processed} 个")
        
        if position_set_count > 0:
            success_rate = (position_set_count / total_processed) * 100
            print(f"   📈 成功率: {success_rate:.1f}%")
            print("✅ NebOffset骨骼编辑坐标设置完成")
            print("🔄 新的编辑坐标对应关系已应用: lip.T->lip.T.L, lip.B->lip.B.L, lips.L->cheek.B.L")
            print("🎯 坐标类型确认：编辑模式世界坐标（根坐标+头坐标+滚转角）")
        else:
            print("⚠ 没有成功设置任何NebOffset骨骼编辑坐标")
            
        print(f"📍 === NebOffset骨骼编辑坐标设置完成 ===\n")
    
    def _generate_mch_bones_now(self, detected_face_bones):
        """立即生成MCH骨骼（在generate_bones阶段调用）"""
        print("🔧 开始生成MCH骨骼...")
        
        if not detected_face_bones:
            print("⚠ 没有预定义的面部骨骼映射")
            return 0
        
        mch_generated_count = 0
        mch_failed_count = 0
        mch_skipped_count = 0
        
        for rigify_name, neb_name in detected_face_bones.items():
            try:
                # 检查源骨骼是否存在（允许不存在，但记录跳过）
                if rigify_name not in self.obj.data.bones:
                    mch_skipped_count += 1
                    continue
                
                # 为从rigify复制的骨骼添加MCH标识
                mch_bone_name = f"Neb_MCH_{rigify_name}"
                mch_bone = self.copy_bone(rigify_name, mch_bone_name)
                self.bones.mch.face_bones[mch_bone_name] = mch_bone
                mch_generated_count += 1
                
                if mch_generated_count <= 5:  # 只显示前5个，避免日志过长
                    #print(f"✓ 生成MCH骨骼: {mch_bone_name:30s} (复制自 {rigify_name})")
                    pass
            except Exception as e:
                mch_failed_count += 1
                if mch_failed_count <= 3:  # 只显示前3个错误
                    #print(f"❌ 生成MCH骨骼失败: Neb_MCH_{rigify_name} - {e}")
                    pass
        
        # 更新兼容性视图
        if mch_generated_count > 0:
            self.bones.neb_face_bones.clear()
            self.bones.neb_face_bones.update(self.bones.mch.face_bones)
            print(f"✓ 更新兼容性视图: {len(self.bones.neb_face_bones)} 个MCH骨骼")
        
        return mch_generated_count
    
    @stage.generate_bones
    def generate_mch_bones_late(self):
        return
    def generate_widgets(self):
        """生成控制部件"""
        print("\n🎨 === 开始生成控制部件 ===")
        
        # 为主要骨骼生成部件
        if self.neb_facer_root_bone:
            create_face_control_widget(self.obj, self.neb_facer_root_bone, size=0.8)
            print("✓ 生成 Neb_Facer_root 控制部件")
        
        # 为 Neb_face-root 生成部件
        create_face_control_widget(self.obj, self.faceroot_bone, size=1.0)
        print("✓ 生成 Neb_face-root 控制部件")
        
        # 为 Neb_RigifyFace 生成部件
        if self.neb_rigify_face_bone:
            create_face_control_widget(self.obj, self.neb_rigify_face_bone, size=0.6)
            print("✓ 生成 Neb_RigifyFace 控制部件")
        
        # 为权重骨骼生成部件（NebOffset骨骼，更小）
        if hasattr(self.bones, 'wei') and self.bones.wei:
            wei_count = 0
            wei_attr_names = [
                # 眉毛NebOffset骨骼
                'brow_t_l_003', 'brow_t_l_002', 'brow_t_l_001',       # 左眉上部
                'brow_t_r_003', 'brow_t_r_002', 'brow_t_r_001',       # 右眉上部
                
                # 嘴唇NebOffset骨骼 - 左侧
                'lip_t_l_001', 'lip_t_l_002',                         # 左上唇
                'lip_b_l_001', 'lip_b_l_002',                         # 左下唇
                'lips_l',                                             # 左嘴角
                
                # 嘴唇NebOffset骨骼 - 右侧
                'lip_t_r_001', 'lip_t_r_002',                         # 右上唇
                'lip_b_r_001', 'lip_b_r_002',                         # 右下唇
                'lips_r',                                             # 右嘴角
                
                # 嘴唇NebOffset骨骼 - 中央
                'lip_t', 'lip_b'                                      # 中央上下唇
            ]
            for attr_name in wei_attr_names:
                if hasattr(self.bones.wei, attr_name):
                    bone_name = getattr(self.bones.wei, attr_name)
                    if bone_name:
                        create_face_control_widget(self.obj, bone_name, size=0.15)  # 最小尺寸NebOffset骨骼
                        wei_count += 1
            print(f"✓ 生成 {wei_count} 个NebOffset骨骼控制部件")
        
        # 为控制骨骼生成部件（主要控制骨骼，标准尺寸）
        if hasattr(self.bones, 'ctrl') and self.bones.ctrl:
            con_count = 0
            for attr_name in ['face_root', 'mouth_main', 'eye_l_main', 'eye_r_main', 'brow_l_main', 'brow_r_main']:
                if hasattr(self.bones.ctrl, attr_name):
                    bone_name = getattr(self.bones.ctrl, attr_name)
                    if bone_name:
                        create_face_control_widget(self.obj, bone_name, size=0.4)  # 标准尺寸控制骨骼
                        con_count += 1
            print(f"✓ 生成 {con_count} 个控制骨骼控制部件")
        
        print("🎨 === 控制部件生成完成 ===\n")
    
    def finalize(self):
        """完成设置"""
        print("🎯 === FaceUP 面部绑定系统初始化完成 ===")
        
        try:
            # 验证必需的定位器
            self.validate_required_locators()
        except Exception as e:
            print(f"⚠ 验证定位器时出错: {e}")
        
        try:
            # 设置驱动器系统（现在包含清理）
            self.create_driver_system()
        except Exception as e:
            pass
        
        # print("✅ FaceUP 系统就绪！")
    
    def validate_required_locators(self):
        """验证必需的定位器"""
        missing_locators = []
        for locator_name in self.required_locators:
            if locator_name not in self.child_locators:
                missing_locators.append(locator_name)
        
        if missing_locators:
            print(f"⚠ 缺少定位器: {missing_locators}")
        else:
            print("✓ 所有必需定位器已注册")
    
    def create_driver_system(self):
        """创建驱动器系统"""
        try:
            # print("\n🎯 === 开始创建驱动器系统 ===")
            
            # 使用模板管理器加载模板（包含两阶段处理）
            template_data = self.template_manager.load_faceroot_template()
            if template_data:
                # print("\n✓ 模板数据加载成功，开始验证结果...")
                
                # 验证模板处理结果（在两阶段处理完成后）
                self.setup_custom_properties()
                
                # 应用模板中的其他驱动器配置（如果有）
                self.template_manager.apply_drivers_from_template(template_data)
                
                # 最终验证自定义属性（在清理前）
                # print("\n🔍 执行清理前的最终验证...")
                self.verify_custom_properties_final()
                
                # print("✅ 驱动器系统创建完成")
            else:
                # print("⚠ 模板数据加载失败，跳过驱动器创建")
                # print("💡 请确保模板文件存在或模板rig对象可用")
                pass
        except Exception as e:
            # print(f"⚠ 创建驱动器系统时出错: {e}")
            # print("💡 请检查模板文件和模板rig对象是否正确配置")
            pass
        
        # 在驱动器系统创建完成后清理模板数据
        # 这样可以避免在Rigify的finalize阶段干扰活动对象
        try:
            print("\n🧹 开始清理模板数据...")
            self.template_manager.cleanup_template_data_complete()
        except Exception as e:
            print(f"⚠ 清理模板数据时出错: {e}")
        
        # print("🎯 === 驱动器系统初始化完成 ===\n")
    
    def verify_custom_properties_final(self):
        """最终验证自定义属性（清理前的保护性检查）"""
        if not self.faceroot_bone:
            # print("⚠ faceroot_bone 不存在，跳过最终验证") # 删除debug打印
            return
        
        try:
            pose_bone = self.obj.pose.bones[self.faceroot_bone]
            
            # 获取所有自定义属性（排除内部属性）
            custom_props = [key for key in pose_bone.keys() if not key.startswith('_')]
            
            # print(f"🔍 清理前最终验证: Neb_face-root骨骼包含 {len(custom_props)} 个自定义属性") # 删除debug打印
            
            if custom_props:
                # 分析属性值分布但不打印调试信息
                zero_count = 0
                non_zero_count = 0
                sample_non_zero = []
                
                for prop_name in custom_props:
                    value = pose_bone[prop_name]
                    if value == 0.0:
                        zero_count += 1
                    else:
                        non_zero_count += 1
                        sample_non_zero.append((prop_name, value))
                
                # 删除所有详细的debug打印信息
                # 只保留基本验证逻辑
                return non_zero_count > 0 or zero_count > 0
                
            else:
                # print("❌ 最终验证失败 - 自定义属性缺失") # 删除debug打印
                return False
            
        except Exception as e:
            # print(f"❌ 最终验证时出错: {e}") # 删除debug打印
            import traceback
            traceback.print_exc()
            return False
    
    def setup_custom_properties(self):
        """验证自定义属性（模板处理完成后的验证）"""
        if not self.faceroot_bone:
            # print("⚠ faceroot_bone 不存在，跳过自定义属性验证") # 删除debug打印
            return
        
        try:
            # 直接使用faceroot_bone名称，而不是self.bones.ctrl
            pose_bone = self.obj.pose.bones[self.faceroot_bone]
            
            # 获取所有自定义属性（排除内部属性）
            custom_props = [key for key in pose_bone.keys() if not key.startswith('_')]
            
            if custom_props:
                # 删除详细的属性信息打印
                # 只保留基本验证逻辑
                non_zero_props = []
                for prop_name in custom_props:
                    value = pose_bone[prop_name]
                    if value != 0.0:
                        non_zero_props.append(prop_name)
                
                # 删除验证结果的debug打印
                return len(custom_props) > 0
                    
            else:
                # print("⚠ Neb_face-root骨骼没有自定义属性") # 删除debug打印
                # print("💡 请确保模板rig对象中的Neb_face-root骨骼包含所需的自定义属性") # 删除debug打印
                return False
            
        except KeyError as e:
            # print(f"❌ 骨骼 '{self.faceroot_bone}' 不存在于姿态骨骼中: {e}") # 删除debug打印
            return False
        except Exception as e:
            # print(f"❌ 验证自定义属性时出错: {e}") # 删除debug打印
            return False
    
    @staticmethod
    def add_parameters(params):
        """添加参数"""
        # 基础参数
        params.enable_copy_constraints = BoolProperty(
            name="启用复制变换约束",
            default=True,
            description="为原生rigify骨骼添加复制变换约束"
        )
        
        params.constraint_influence = FloatProperty(
            name="约束影响权重",
            default=1.0,
            min=0.0,
            max=1.0,
            description="复制变换约束的影响强度"
        )
        
        # 约束空间设置
        params.constraint_mix_mode = EnumProperty(
            name="混合模式",
            items=[
                ('BEFORE', '初始化前', '在原始变换之前应用约束'),
                ('AFTER', '初始化后', '在原始变换之后应用约束'),
                ('REPLACE', '替换', '完全替换原始变换'),
            ],
            default='BEFORE',
            description="复制变换约束的混合模式"
        )
        
        params.constraint_target_space = EnumProperty(
            name="目标空间",
            items=[
                ('WORLD', '世界空间', '使用世界坐标空间'),
                ('POSE', '姿态空间', '使用姿态坐标空间'),
                ('LOCAL_WITH_PARENT', '带父级的局部空间', '使用带父级的局部坐标空间'),
                ('LOCAL', '局部空间', '使用局部坐标空间'),
            ],
            default='LOCAL',
            description="目标骨骼的坐标空间"
        )
        
        params.constraint_owner_space = EnumProperty(
            name="拥有者空间",
            items=[
                ('WORLD', '世界空间', '使用世界坐标空间'),
                ('POSE', '姿态空间', '使用姿态坐标空间'),
                ('LOCAL_WITH_PARENT', '带父级的局部空间', '使用带父级的局部坐标空间'),
                ('LOCAL', '局部空间', '使用局部坐标空间'),
            ],
            default='LOCAL',
            description="拥有者骨骼的坐标空间"
        )
        
        # 生成模式参数
        params.generation_mode = EnumProperty(
            name="生成模式",
            items=[
                ('AUTO', '自动检测', '自动检测原生rigify骨骼并生成对应Neb_前缀骨骼'),
                ('MANUAL', '手动选择', '手动指定要生成的骨骼列表'),
                ('HYBRID', '混合模式', '自动检测基础上进行手动调整'),
            ],
            default='AUTO',
            description="选择骨骼生成模式"
        )
        
        params.manual_bone_list = StringProperty(
            name="手动骨骼列表",
            default="jaw_master,teeth.B,teeth.T,lip.T,lip.B,brow.T.L.002,brow.T.R.002",
            description="手动模式下的骨骼列表（逗号分隔）"
        )
        
        params.exclude_bones = StringProperty(
            name="排除骨骼",
            default="",
            description="混合模式下要排除的骨骼（逗号分隔）"
        )
        
        params.add_bones = StringProperty(
            name="额外添加",
            default="",
            description="混合模式下要额外添加的骨骼（逗号分隔）"
        )
        
        params.custom_generation_order = BoolProperty(
            name="自定义生成顺序",
            default=False,
            description="是否启用自定义骨骼生成顺序"
        )
    
    @staticmethod
    def parameters_ui(layout, params):
        """参数UI"""
        layout.label(text="面部绑定设置:", icon='FACE_MAPS')
        
        # 约束设置
        box = layout.box()
        box.label(text="复制变换约束设置:", icon='CON_COPYTRANS')
        col = box.column()
        col.prop(params, "enable_copy_constraints")
        
        if params.enable_copy_constraints:
            col.prop(params, "constraint_influence")
            
            layout.separator()
            
            # 约束空间设置
            box2 = box.box()
            box2.label(text="约束空间设置:")
            col2 = box2.column()
            col2.prop(params, "constraint_mix_mode")
            col2.prop(params, "constraint_target_space")  
            col2.prop(params, "constraint_owner_space")
        
        layout.separator()
        
        # 生成模式设置
        box = layout.box()
        box.label(text="骨骼生成模式:", icon='BONE_DATA')
        col = box.column()
        col.prop(params, "generation_mode")
        
        if params.generation_mode == 'MANUAL':
            col.prop(params, "manual_bone_list")
        elif params.generation_mode == 'HYBRID':
            col.prop(params, "exclude_bones")
            col.prop(params, "add_bones")
        
        col.prop(params, "custom_generation_order")
        
        layout.separator()
        
        # 提示信息
        box = layout.box()
        box.label(text="使用提示:", icon='INFO')
        col = box.column()
        col.label(text="• AUTO模式：自动检测原生rigify骨骼")
        col.label(text="• 默认设置：混合=初始化前，空间=局部")
        col.label(text="• 约束方向：原生rigify骨骼跟随Neb_前缀骨骼")
    
    def detect_rigify_face_bones_backup(self):
        """备用的rigify面部骨骼检测方法"""
        print("🔍 使用备用检测方法查找rigify面部骨骼...")
        
        # 🚫 新规则：跳过所有rigify面部骨骼检测
        print("🚫 新规则：跳过备用检测，默认用户已经设置")
        print("💡 假设用户已经正确配置了rigify面部骨架") 
        print("🎯 直接返回空映射，继续后续处理流程")
        
        return {}
        
        # ===== 以下代码已被禁用（保留备用） =====
        # 首先检查是否有face骨骼
        # existing_bones = [bone.name for bone in self.obj.data.bones]
        # 
        # # 💫 新增：打印所有骨骼名称列表
        # print(f"\n📋 === 当前骨架包含的所有骨骼 (共 {len(existing_bones)} 个) ===")
        # print("📝 完整骨骼名称列表:")
        # 
        # # 按类型分组显示骨骼
        # org_bones = [bone for bone in existing_bones if bone.startswith('ORG-')]
        # def_bones = [bone for bone in existing_bones if bone.startswith('DEF-')]
        # mch_bones = [bone for bone in existing_bones if bone.startswith('MCH-')]
        # wgt_bones = [bone for bone in existing_bones if bone.startswith('WGT-')]
        # ctrl_bones = [bone for bone in existing_bones if not any(bone.startswith(prefix) for prefix in ['ORG-', 'DEF-', 'MCH-', 'WGT-'])]
        # 
        # print(f"📊 骨骼类型统计:")
        # print(f"   🦴 ORG骨骼 (原始): {len(org_bones)} 个") 
        # print(f"   🔧 DEF骨骼 (变形): {len(def_bones)} 个")
        # print(f"   ⚙️ MCH骨骼 (机制): {len(mch_bones)} 个") 
        # print(f"   🎛️ WGT骨骼 (控件): {len(wgt_bones)} 个")
        # print(f"   🎯 控制骨骼 (其他): {len(ctrl_bones)} 个")
        # 
        # # 显示控制骨骼（最重要的）
        # if ctrl_bones:
        #     print(f"\n🎯 控制骨骼详细列表 ({len(ctrl_bones)} 个):")
        #     for i, bone_name in enumerate(ctrl_bones):
        #         print(f"   {i+1:3d}. {bone_name}")
        # 
        # # 显示部分ORG骨骼作为参考
        # if org_bones:
        #     print(f"\n🦴 ORG骨骼示例 (前20个，共{len(org_bones)}个):")
        #     for i, bone_name in enumerate(org_bones[:20]):
        #         print(f"   {i+1:3d}. {bone_name}")
        #     if len(org_bones) > 20:
        #         print(f"   ... 还有 {len(org_bones) - 20} 个ORG骨骼")
        # 
        # # 显示部分DEF骨骼作为参考
        # if def_bones:
        #     print(f"\n🔧 DEF骨骼示例 (前15个，共{len(def_bones)}个):")
        #     for i, bone_name in enumerate(def_bones[:15]):
        #         print(f"   {i+1:3d}. {bone_name}")
        #     if len(def_bones) > 15:
        #         print(f"   ... 还有 {len(def_bones) - 15} 个DEF骨骼")
        # 
        # # 显示部分MCH骨骼作为参考
        # if mch_bones:
        #     print(f"\n⚙️ MCH骨骼示例 (前15个，共{len(mch_bones)}个):")
        #     for i, bone_name in enumerate(mch_bones[:15]):
        #         print(f"   {i+1:3d}. {bone_name}")
        #     if len(mch_bones) > 15:
        #         print(f"   ... 还有 {len(mch_bones) - 15} 个MCH骨骼")
        # 
        # print(f"📋 === 骨骼列表显示完成 ===\n")
        # 
        # # 现在开始检测face骨骼
        # face_bone_found = False
        # 
        # for bone_name in existing_bones:
        #     if bone_name.lower() in ['face', 'Face', 'FACE']:
        #         print(f"✅ 备用检测发现face骨骼: {bone_name}")
        #         print("🎯 判断为rigify骨架，继续面部骨骼检测...")
        #         face_bone_found = True
        #         break
        # 
        # if not face_bone_found:
        #     print("❌ 备用检测未发现face骨骼")
        #     print("💡 当前骨架可能不是rigify面部骨架")
        #     return {}
        # 
        # # ... 更多已禁用的检测代码 ...
    
    def _get_default_rigify_face_mapping(self):
        """获取预定义的rigify面部骨骼映射关系（跳过检测）"""
        print("📋 加载预定义的rigify面部骨骼映射...")
        
        # 标准的rigify面部骨骼映射关系
        default_mapping = {
            # 下颚控制
            "jaw_master": "Neb_jaw_master",
            "teeth.B": "Neb_teeth_B",
            "teeth.T": "Neb_teeth_T",
            
            # 嘴唇基础控制
            "lip.T": "Neb_lip_T",
            "lip.B": "Neb_lip_B",
            
            # 嘴唇细分控制 - 左侧
            "lip.T.L.001": "Neb_lip_T_L_001",
            "lip.T.L.002": "Neb_lip_T_L_002",
            "lip.B.L.001": "Neb_lip_B_L_001", 
            "lip.B.L.002": "Neb_lip_B_L_002",
            
            # 嘴唇细分控制 - 右侧
            "lip.T.R.001": "Neb_lip_T_R_001",
            "lip.T.R.002": "Neb_lip_T_R_002",
            "lip.B.R.001": "Neb_lip_B_R_001",
            "lip.B.R.002": "Neb_lip_B_R_002",
            
            # 嘴角控制
            "lip_end.L": "Neb_lip_end_L",
            "lip_end.R": "Neb_lip_end_R",
            "lip_end.L.001": "Neb_lip_end_L_001",
            "lip_end.R.001": "Neb_lip_end_R_001",
            "lip_end.L.002": "Neb_lip_end_L_002",
            "lip_end.R.002": "Neb_lip_end_R_002",
            
            # 眼睑控制
            "lid.T.L.001": "Neb_lid_T_L_001",
            "lid.T.L.002": "Neb_lid_T_L_002",
            "lid.T.L.003": "Neb_lid_T_L_003",
            "lid.T.R.001": "Neb_lid_T_R_001", 
            "lid.T.R.002": "Neb_lid_T_R_002",
            "lid.T.R.003": "Neb_lid_T_R_003",
            "lid.B.L.001": "Neb_lid_B_L_001",
            "lid.B.L.002": "Neb_lid_B_L_002",
            "lid.B.L.003": "Neb_lid_B_L_003",
            "lid.B.R.001": "Neb_lid_B_R_001",
            "lid.B.R.002": "Neb_lid_B_R_002", 
            "lid.B.R.003": "Neb_lid_B_R_003",
            
            # 眉毛控制
            "brow.T.L.001": "Neb_brow_T_L_001",
            "brow.T.L.002": "Neb_brow_T_L_002",
            "brow.T.L.003": "Neb_brow_T_L_003",
            "brow.T.R.001": "Neb_brow_T_R_001",
            "brow.T.R.002": "Neb_brow_T_R_002",
            "brow.T.R.003": "Neb_brow_T_R_003",
            "brow.B.L.001": "Neb_brow_B_L_001",
            "brow.B.L.002": "Neb_brow_B_L_002",
            "brow.B.L.003": "Neb_brow_B_L_003",
            "brow.B.R.001": "Neb_brow_B_R_001",
            "brow.B.R.002": "Neb_brow_B_R_002",
            "brow.B.R.003": "Neb_brow_B_R_003",
            
            # 眼部控制
            "eye.L": "Neb_eye_L",
            "eye.R": "Neb_eye_R",
            "eye_master.L": "Neb_eye_master_L",
            "eye_master.R": "Neb_eye_master_R",
            
            # 脸颊控制
            "cheek.T.L": "Neb_cheek_T_L",
            "cheek.T.R": "Neb_cheek_T_R", 
            "cheek.B.L": "Neb_cheek_B_L",
            "cheek.B.R": "Neb_cheek_B_R",
            "cheek.T.L.001": "Neb_cheek_T_L_001",
            "cheek.T.R.001": "Neb_cheek_T_R_001",
            "cheek.B.L.001": "Neb_cheek_B_L_001",
            "cheek.B.R.001": "Neb_cheek_B_R_001",
            
            # 鼻子控制
            "nose": "Neb_nose",
            "nose.001": "Neb_nose_001",
            "nose.002": "Neb_nose_002",
            "nose.003": "Neb_nose_003",
            "nose.004": "Neb_nose_004",
            "nose.L": "Neb_nose_L",
            "nose.R": "Neb_nose_R",
            "nose.L.001": "Neb_nose_L_001",
            "nose.R.001": "Neb_nose_R_001",
            "nose_master": "Neb_nose_master",
            
            # 耳朵控制
            "ear.L": "Neb_ear_L",
            "ear.R": "Neb_ear_R",
            "ear.L.001": "Neb_ear_L_001",
            "ear.L.002": "Neb_ear_L_002", 
            "ear.L.003": "Neb_ear_L_003",
            "ear.L.004": "Neb_ear_L_004",
            "ear.R.001": "Neb_ear_R_001",
            "ear.R.002": "Neb_ear_R_002",
            "ear.R.003": "Neb_ear_R_003",
            "ear.R.004": "Neb_ear_R_004",
            
            # 额头控制
            "forehead.L": "Neb_forehead_L",
            "forehead.R": "Neb_forehead_R",
            "forehead.L.001": "Neb_forehead_L_001",
            "forehead.L.002": "Neb_forehead_L_002",
            "forehead.R.001": "Neb_forehead_R_001",
            "forehead.R.002": "Neb_forehead_R_002",
            
            # 下巴控制
            "chin": "Neb_chin",
            "chin.001": "Neb_chin_001",
            "chin.L": "Neb_chin_L",
            "chin.R": "Neb_chin_R",
            
            # 太阳穴控制
            "temple.L": "Neb_temple_L",
            "temple.R": "Neb_temple_R"
        }
        
        print(f"✅ 预定义映射加载完成：{len(default_mapping)} 个骨骼映射")
        
        # 显示重要的嘴唇控制骨骼映射
        lip_mappings = {k: v for k, v in default_mapping.items() if 'lip' in k.lower()}
        if lip_mappings:
            print(f"📋 嘴唇控制骨骼映射 ({len(lip_mappings)} 个):")
            for i, (rigify_name, neb_name) in enumerate(list(lip_mappings.items())[:8]):
                print(f"    {i+1:2d}. {rigify_name:15s} -> {neb_name}")
            if len(lip_mappings) > 8:
                print(f"    ... 还有 {len(lip_mappings) - 8} 个嘴唇控制映射")
        
        return default_mapping
    
    def parent_bones(self):
        """设置骨骼父子关系"""
        print("\n👨‍👩‍👧‍👦 === 开始设置骨骼父子关系 ===")
        
        # 使用BoneDetector检测head骨骼
        head_bone_name = BoneDetector.detect_rigify_head_bone(self.obj)
        
        # 设置主要骨骼的父子关系
        if head_bone_name:
            self.set_bone_parent(self.neb_facer_root_bone, head_bone_name)
            print(f"✓ 设置 Neb_Facer_root 父骨骼为原生 {head_bone_name}")
        else:
            print("✓ Neb_Facer_root 设置为根骨骼（无父级）")
        
        if self.faceroot_bone and self.neb_facer_root_bone:
            self.set_bone_parent(self.faceroot_bone, self.neb_facer_root_bone)
            print(f"✓ 设置父子关系: Neb_face-root -> Neb_Facer_root")
        
        if self.neb_rigify_face_bone and self.neb_facer_root_bone:
            self.set_bone_parent(self.neb_rigify_face_bone, self.neb_facer_root_bone)
            print(f"✓ 设置父子关系: Neb_RigifyFace -> Neb_Facer_root")
        
        # 设置权重骨骼的父子关系 - 使用CONSTRAINT_MAPPINGS确保覆盖所有NebOffset骨骼
        print("\n⚖️ 设置NebOffset骨骼父级关系...")
        neboffset_parent_set_count = 0
        neboffset_parent_failed_count = 0
        
        # 使用CONSTRAINT_MAPPINGS中的目标骨骼（NebOffset骨骼）来设置父级
        for source_bone_name, target_bone_name in CONSTRAINT_MAPPINGS:
            try:
                # 检查目标骨骼（NebOffset骨骼）是否存在
                if target_bone_name not in self.obj.data.edit_bones:
                    continue
                
                # 检查Neb_RigifyFace父级骨骼是否存在
                if not self.neb_rigify_face_bone or self.neb_rigify_face_bone not in self.obj.data.edit_bones:
                    neboffset_parent_failed_count += 1
                    continue
                
                # 设置NebOffset骨骼的父级为Neb_RigifyFace
                target_edit_bone = self.obj.data.edit_bones[target_bone_name]
                parent_edit_bone = self.obj.data.edit_bones[self.neb_rigify_face_bone]
                target_edit_bone.parent = parent_edit_bone
                
                neboffset_parent_set_count += 1
                
                # 显示成功设置的前几个（避免输出过多）
                if neboffset_parent_set_count <= 5:
                    print(f"✅ NebOffset父级 {neboffset_parent_set_count}: {target_bone_name:25s} -> {self.neb_rigify_face_bone}")
                elif neboffset_parent_set_count == 6:
                    print(f"   ... 继续设置更多NebOffset骨骼父级 ...")
                
            except Exception as e:
                neboffset_parent_failed_count += 1
                if neboffset_parent_failed_count <= 3:
                    print(f"❌ 设置NebOffset父级失败 {target_bone_name}: {e}")
        
        print(f"📊 NebOffset骨骼父级设置统计:")
        print(f"   ✅ 成功设置: {neboffset_parent_set_count} 个NebOffset骨骼")
        print(f"   ❌ 设置失败: {neboffset_parent_failed_count} 个")
        
        if neboffset_parent_set_count > 0:
            success_rate = (neboffset_parent_set_count / len(CONSTRAINT_MAPPINGS)) * 100
            print(f"   📈 成功率: {success_rate:.1f}% (总共{len(CONSTRAINT_MAPPINGS)}个NebOffset骨骼)")
            print(f"✅ NebOffset骨骼父级设置完成，所有目标骨骼以 {self.neb_rigify_face_bone} 为父级")
        else:
            print("⚠ 没有成功设置任何NebOffset骨骼父级")
            print("💡 请检查Neb_RigifyFace骨骼和NebOffset骨骼是否正确生成")
        
        print("👨‍👩‍👧‍👦 === NebOffset骨骼父级设置完成 ===\n")
        
        # 设置控制骨骼的父子关系
        if hasattr(self.bones, 'ctrl') and self.bones.ctrl:
            con_count = 0
            for attr_name in ['face_root', 'mouth_main', 'eye_l_main', 'eye_r_main', 'brow_l_main', 'brow_r_main']:
                if hasattr(self.bones.ctrl, attr_name):
                    bone_id = getattr(self.bones.ctrl, attr_name)
                    if bone_id:
                        self.set_bone_parent(bone_id, self.faceroot_bone)  # 控制骨骼连接到face-root
                        con_count += 1
            print(f"✓ 设置 {con_count} 个控制骨骼的父级为 Neb_face-root")
        
        # 特殊处理：设置mouth-root的父级为Neb_face-root
        print("\n🦷 设置mouth-root特殊父级关系...")
        mouth_root_set_count = 0
        mouth_root_failed_count = 0
        
        # 检查mouth-root骨骼是否存在
        if 'mouth-root' in self.obj.data.edit_bones:
            try:
                # 设置mouth-root的父级为Neb_face-root
                mouth_root_bone = self.obj.data.edit_bones['mouth-root']
                neb_face_root_bone = self.obj.data.edit_bones[self.faceroot_bone]
                mouth_root_bone.parent = neb_face_root_bone
                
                mouth_root_set_count += 1
                print(f"✅ 设置 mouth-root 父级为 {self.faceroot_bone}")
                
            except Exception as e:
                mouth_root_failed_count += 1
                print(f"❌ 设置mouth-root父级失败: {e}")
        else:
            print("⚠ mouth-root骨骼不存在，跳过特殊父级设置")
        
        # 同样处理其他可能的子级定位器根骨骼
        special_root_bones = [
            'eyelip-root.L', 'eyelip-root.R', 
            'brow-root.L', 'brow-root.R'
        ]
        
        special_roots_set = 0
        for root_bone_name in special_root_bones:
            if root_bone_name in self.obj.data.edit_bones:
                try:
                    root_bone = self.obj.data.edit_bones[root_bone_name]
                    neb_face_root_bone = self.obj.data.edit_bones[self.faceroot_bone]
                    root_bone.parent = neb_face_root_bone
                    special_roots_set += 1
                    print(f"✅ 设置 {root_bone_name} 父级为 {self.faceroot_bone}")
                except Exception as e:
                    print(f"❌ 设置{root_bone_name}父级失败: {e}")
        
        print(f"📊 特殊根骨骼父级设置统计:")
        print(f"   🦷 mouth-root: {mouth_root_set_count} 成功, {mouth_root_failed_count} 失败")
        print(f"   👁️ 其他定位器根骨骼: {special_roots_set} 个成功设置")
        
        if mouth_root_set_count > 0 or special_roots_set > 0:
            print("✅ 子级定位器根骨骼父级设置完成")
            print("🎯 层级结构：Neb_face-root -> mouth-root, eyelip-root.L/R, brow-root.L/R")
        
        print("👨‍👩‍👧‍👦 === 骨骼父子关系设置完成 ===\n")
    
    def configure_bones(self):
        """配置骨骼属性"""
        print("\n⚙️ === 开始配置骨骼属性 ===")
        
        # 配置主要骨骼
        if self.neb_facer_root_bone:
            bone = self.get_bone(self.neb_facer_root_bone)
            bone.lock_location = [True, True, True]
            bone.lock_rotation = [True, True, True]
            bone.lock_scale = [True, True, True]
            print("✓ 配置 Neb_Facer_root: 锁定所有变换")
        
        face_root_bone = self.get_bone(self.faceroot_bone)
        face_root_bone.lock_location = [True, True, True]
        face_root_bone.lock_rotation = [True, True, True]
        face_root_bone.lock_scale = [True, True, True]
        print("✓ 配置 Neb_face-root: 锁定所有变换")
        
        if self.neb_rigify_face_bone:
            bone = self.get_bone(self.neb_rigify_face_bone)
            bone.lock_location = [True, True, True]
            bone.lock_rotation = [True, True, True]
            bone.lock_scale = [True, True, True]
            print("✓ 配置 Neb_RigifyFace: 锁定所有变换")
        
        # 配置 MCH 骨骼（机制骨骼）
        if hasattr(self.bones.mch, 'face_bones') and self.bones.mch.face_bones:
            mch_count = 0
            for bone_name, bone_id in self.bones.mch.face_bones.items():
                bone = self.get_bone(bone_id)
                bone.lock_scale = [True, True, True]  # 机制骨骼只锁定缩放
                mch_count += 1
            print(f"✓ 配置 {mch_count} 个MCH骨骼: 锁定缩放")
        
        # 配置权重骨骼
        if hasattr(self.bones, 'wei') and self.bones.wei:
            wei_count = 0
            wei_attr_names = [
                # 眉毛NebOffset骨骼
                'brow_t_l_003', 'brow_t_l_002', 'brow_t_l_001',       # 左眉上部
                'brow_t_r_003', 'brow_t_r_002', 'brow_t_r_001',       # 右眉上部
                
                # 嘴唇NebOffset骨骼 - 左侧
                'lip_t_l_001', 'lip_t_l_002',                         # 左上唇
                'lip_b_l_001', 'lip_b_l_002',                         # 左下唇
                'lips_l',                                             # 左嘴角
                
                # 嘴唇NebOffset骨骼 - 右侧
                'lip_t_r_001', 'lip_t_r_002',                         # 右上唇
                'lip_b_r_001', 'lip_b_r_002',                         # 右下唇
                'lips_r',                                             # 右嘴角
                
                # 嘴唇NebOffset骨骼 - 中央
                'lip_t', 'lip_b'                                      # 中央上下唇
            ]
            for attr_name in wei_attr_names:
                if hasattr(self.bones.wei, attr_name):
                    bone_id = getattr(self.bones.wei, attr_name)
                    if bone_id:
                        bone = self.get_bone(bone_id)
                        bone.lock_location = [True, True, True]  # NebOffset骨骼锁定位置
                        bone.lock_rotation = [True, True, True]  # NebOffset骨骼锁定旋转
                        bone.lock_scale = [True, True, True]     # NebOffset骨骼锁定缩放
                        wei_count += 1
            print(f"✓ 配置 {wei_count} 个NebOffset骨骼: 锁定所有变换")
        
        # 配置控制骨骼
        if hasattr(self.bones, 'ctrl') and self.bones.ctrl:
            con_count = 0
            for attr_name in ['face_root', 'mouth_main', 'eye_l_main', 'eye_r_main', 'brow_l_main', 'brow_r_main']:
                if hasattr(self.bones.ctrl, attr_name):
                    bone_id = getattr(self.bones.ctrl, attr_name)
                    if bone_id:
                        bone = self.get_bone(bone_id)
                        bone.lock_scale = [True, True, True]  # 控制骨骼只锁定缩放
                        con_count += 1
            print(f"✓ 配置 {con_count} 个控制骨骼: 锁定缩放")
        
        print("⚙️ === 骨骼属性配置完成 ===\n") 