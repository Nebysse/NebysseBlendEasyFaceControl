"""
NebysseFacer 骨骼工具函数
提供骨骼操作相关的实用工具
"""

import bpy
from mathutils import Vector, Matrix
from rigify.utils.naming import make_derived_name
from rigify.utils.bones import align_bone_orientation, put_bone


def create_control_bone(rig, org_bone, suffix='ctrl', scale=1.0):
    """
    创建控制骨骼
    
    Args:
        rig: 绑定生成器
        org_bone: 原始骨骼名称
        suffix: 后缀
        scale: 缩放比例
    """
    
    ctrl_name = make_derived_name(org_bone, suffix)
    ctrl_bone = rig.copy_bone(org_bone, ctrl_name)
    
    # 设置骨骼属性
    eb = rig.get_bone(ctrl_bone)
    eb.use_deform = False
    
    # 调整大小
    if scale != 1.0:
        length = eb.length
        eb.length = length * scale
    
    return ctrl_bone


def create_mechanism_bone(rig, org_bone, suffix='mch', scale=0.5):
    """
    创建机制骨骼
    
    Args:
        rig: 绑定生成器
        org_bone: 原始骨骼名称
        suffix: 后缀
        scale: 缩放比例
    """
    
    mch_name = make_derived_name(org_bone, suffix)
    mch_bone = rig.copy_bone(org_bone, mch_name)
    
    # 设置骨骼属性
    eb = rig.get_bone(mch_bone)
    eb.use_deform = False
    
    # 调整大小
    if scale != 1.0:
        length = eb.length
        eb.length = length * scale
    
    return mch_bone


def create_deform_bone(rig, org_bone, suffix='def'):
    """
    创建变形骨骼
    
    Args:
        rig: 绑定生成器
        org_bone: 原始骨骼名称
        suffix: 后缀
    """
    
    def_name = make_derived_name(org_bone, suffix)
    def_bone = rig.copy_bone(org_bone, def_name)
    
    # 设置骨骼属性
    eb = rig.get_bone(def_bone)
    eb.use_deform = True
    
    return def_bone


def create_helper_bone(rig, org_bone, suffix='helper', offset=Vector((0, 0, 0))):
    """
    创建辅助骨骼
    
    Args:
        rig: 绑定生成器
        org_bone: 原始骨骼名称
        suffix: 后缀
        offset: 位置偏移
    """
    
    helper_name = make_derived_name(org_bone, suffix)
    helper_bone = rig.copy_bone(org_bone, helper_name)
    
    # 设置骨骼属性
    eb = rig.get_bone(helper_bone)
    eb.use_deform = False
    
    # 应用偏移
    if offset != Vector((0, 0, 0)):
        eb.head += offset
        eb.tail += offset
    
    return helper_bone


def align_bone_to_axis(rig, bone_name, axis='Y', length=None):
    """
    将骨骼对齐到指定轴
    
    Args:
        rig: 绑定生成器
        bone_name: 骨骼名称
        axis: 对齐轴 ('X', 'Y', 'Z')
        length: 新长度（可选）
    """
    
    eb = rig.get_bone(bone_name)
    
    if axis == 'X':
        direction = Vector((1, 0, 0))
    elif axis == 'Y':
        direction = Vector((0, 1, 0))
    elif axis == 'Z':
        direction = Vector((0, 0, 1))
    else:
        return
    
    # 设置新的尾部位置
    if length is None:
        length = eb.length
    
    eb.tail = eb.head + direction * length
    eb.roll = 0


def position_bone_relative(rig, bone_name, reference_bone, offset=Vector((0, 0, 0))):
    """
    相对于参考骨骼定位骨骼
    
    Args:
        rig: 绑定生成器
        bone_name: 要定位的骨骼名称
        reference_bone: 参考骨骼名称
        offset: 偏移量
    """
    
    target_eb = rig.get_bone(bone_name)
    ref_eb = rig.get_bone(reference_bone)
    
    # 计算新位置
    new_head = ref_eb.head + offset
    bone_length = target_eb.length
    bone_direction = (target_eb.tail - target_eb.head).normalized()
    
    target_eb.head = new_head
    target_eb.tail = new_head + bone_direction * bone_length


def create_bone_chain(rig, base_name, positions, parent=None):
    """
    创建骨骼链
    
    Args:
        rig: 绑定生成器
        base_name: 基础名称
        positions: 位置列表 [(head, tail), ...]
        parent: 父骨骼名称
    
    Returns:
        list: 创建的骨骼名称列表
    """
    
    bones = []
    
    for i, (head, tail) in enumerate(positions):
        bone_name = f"{base_name}.{i:03d}" if i > 0 else base_name
        
        # 创建骨骼
        eb = rig.obj.data.edit_bones.new(bone_name)
        eb.head = head
        eb.tail = tail
        eb.use_deform = False
        
        # 设置父子关系
        if i == 0 and parent:
            eb.parent = rig.get_bone(parent)
        elif i > 0:
            eb.parent = rig.get_bone(bones[i-1])
        
        bones.append(bone_name)
    
    return bones


def setup_bone_constraints(rig, bone_name, constraints_data):
    """
    为骨骼设置约束
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
        constraints_data: 约束数据列表
            [{'type': 'COPY_TRANSFORMS', 'target': 'bone_name', 'influence': 1.0}, ...]
    """
    
    if bone_name not in rig.pose.bones:
        return
    
    bone = rig.pose.bones[bone_name]
    
    for constraint_data in constraints_data:
        constraint_type = constraint_data.get('type')
        if not constraint_type:
            continue
        
        # 创建约束
        constraint = bone.constraints.new(type=constraint_type)
        constraint.target = rig
        
        # 设置约束属性
        for key, value in constraint_data.items():
            if key != 'type' and hasattr(constraint, key):
                setattr(constraint, key, value)


def lock_bone_transforms(rig, bone_name, location=None, rotation=None, scale=None):
    """
    锁定骨骼变换
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
        location: 位置锁定 (x, y, z) 布尔元组
        rotation: 旋转锁定 (x, y, z) 布尔元组
        scale: 缩放锁定 (x, y, z) 布尔元组
    """
    
    if bone_name not in rig.pose.bones:
        return
    
    bone = rig.pose.bones[bone_name]
    
    if location:
        bone.lock_location = location
    
    if rotation:
        bone.lock_rotation = rotation
    
    if scale:
        bone.lock_scale = scale


def assign_bone_to_face_collection(rig, bone_name, collection_name):
    """
    将骨骼分配到面部集合 (Blender 4.1+)
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
        collection_name: 集合名称 ('Face Primary', 'Face Secondary', 'Face Detail', 'Face Mechanism', 'Face Deform')
    
    Returns:
        bool: 是否成功分配
    """
    from .blender_compatibility import assign_bone_to_collection, create_all_face_collections
    
    if bone_name not in rig.data.bones:
        print(f"警告: 骨骼 {bone_name} 不存在")
        return False
    
    # 确保所有面部集合已创建
    create_all_face_collections(rig)
    
    # 分配骨骼到集合
    return assign_bone_to_collection(rig, bone_name, collection_name)


def assign_bone_to_primary_controls(rig, bone_name):
    """将骨骼分配到主要控制器集合"""
    return assign_bone_to_face_collection(rig, bone_name, 'Face Primary')


def assign_bone_to_secondary_controls(rig, bone_name):
    """将骨骼分配到次要控制器集合"""
    return assign_bone_to_face_collection(rig, bone_name, 'Face Secondary')


def assign_bone_to_detail_controls(rig, bone_name):
    """将骨骼分配到细节控制器集合"""
    return assign_bone_to_face_collection(rig, bone_name, 'Face Detail')


def assign_bone_to_mechanism(rig, bone_name):
    """将骨骼分配到机制骨骼集合"""
    return assign_bone_to_face_collection(rig, bone_name, 'Face Mechanism')


def assign_bone_to_deform(rig, bone_name):
    """将骨骼分配到变形骨骼集合"""
    return assign_bone_to_face_collection(rig, bone_name, 'Face Deform')


def set_bone_collection(rig, bone_name, collection_name):
    """
    将骨骼分配到指定集合
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
        collection_name: 集合名称
    
    Returns:
        bool: 是否成功分配
    """
    return assign_bone_to_face_collection(rig, bone_name, collection_name)


def create_custom_property(rig, bone_name, prop_name, default_value, min_value=None, max_value=None, description=""):
    """
    为骨骼创建自定义属性
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
        prop_name: 属性名称
        default_value: 默认值
        min_value: 最小值
        max_value: 最大值
        description: 描述
    """
    
    if bone_name not in rig.pose.bones:
        return
    
    bone = rig.pose.bones[bone_name]
    
    # 创建自定义属性
    bone[prop_name] = default_value
    
    # 设置属性范围和描述
    if hasattr(bone, '_RNA_UI'):
        if bone._RNA_UI is None:
            bone._RNA_UI = {}
    else:
        bone._RNA_UI = {}
    
    bone._RNA_UI[prop_name] = {
        "description": description,
        "default": default_value
    }
    
    if min_value is not None:
        bone._RNA_UI[prop_name]["min"] = min_value
    
    if max_value is not None:
        bone._RNA_UI[prop_name]["max"] = max_value


def get_bone_world_matrix(rig, bone_name):
    """
    获取骨骼的世界矩阵
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
    
    Returns:
        Matrix: 世界矩阵
    """
    
    if bone_name in rig.pose.bones:
        bone = rig.pose.bones[bone_name]
        return rig.matrix_world @ bone.matrix
    
    return Matrix.Identity(4)


def calculate_bone_distance(rig, bone1_name, bone2_name):
    """
    计算两个骨骼之间的距离
    
    Args:
        rig: 绑定对象
        bone1_name: 第一个骨骼名称
        bone2_name: 第二个骨骼名称
    
    Returns:
        float: 距离
    """
    
    if bone1_name in rig.pose.bones and bone2_name in rig.pose.bones:
        bone1 = rig.pose.bones[bone1_name]
        bone2 = rig.pose.bones[bone2_name]
        
        pos1 = rig.matrix_world @ bone1.head
        pos2 = rig.matrix_world @ bone2.head
        
        return (pos1 - pos2).length
    
    return 0.0 