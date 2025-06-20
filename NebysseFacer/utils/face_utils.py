"""
NebysseFacer 面部工具函数
提供面部绑定相关的实用工具
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
from rigify.utils.widgets import create_widget
from .blender_compatibility import (
    create_bone_collection_with_color,
    FACE_BONE_COLLECTIONS,
    create_all_face_collections,
    assign_bone_to_collection
)


def create_face_control_widget(rig, bone_name, size=1.0, widget_type='SPHERE'):
    """
    创建面部控制器形状
    
    Args:
        rig: 绑定对象
        bone_name: 骨骼名称
        size: 控制器大小
        widget_type: 控制器类型
    """
    
    if widget_type == 'SPHERE':
        return create_sphere_face_widget(rig, bone_name, size)
    elif widget_type == 'CUBE':
        return create_cube_face_widget(rig, bone_name, size)
    elif widget_type == 'CIRCLE':
        return create_circle_face_widget(rig, bone_name, size)
    elif widget_type == 'ARROW':
        return create_arrow_face_widget(rig, bone_name, size)
    else:
        return create_sphere_face_widget(rig, bone_name, size)


def create_sphere_face_widget(rig, bone_name, size=1.0):
    """创建球形控制器"""
    
    # 创建控制器对象
    obj = create_widget(rig, bone_name)
    if obj is None:
        return None
    
    # 创建球形网格
    mesh = obj.data
    bm = bmesh.new()
    
    # 创建UV球
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=size * 0.1)
    
    bm.to_mesh(mesh)
    bm.free()
    
    return obj


def create_cube_face_widget(rig, bone_name, size=1.0):
    """创建立方体控制器"""
    
    # 创建控制器对象
    obj = create_widget(rig, bone_name)
    if obj is None:
        return None
    
    mesh = obj.data
    bm = bmesh.new()
    
    # 创建立方体
    bmesh.ops.create_cube(bm, size=size * 0.1)
    
    bm.to_mesh(mesh)
    bm.free()
    
    return obj


def create_circle_face_widget(rig, bone_name, size=1.0):
    """创建圆形控制器"""
    
    # 创建控制器对象
    obj = create_widget(rig, bone_name)
    if obj is None:
        return None
    
    mesh = obj.data
    bm = bmesh.new()
    
    # 创建圆形
    bmesh.ops.create_circle(bm, cap_ends=False, radius=size * 0.1, segments=16)
    
    bm.to_mesh(mesh)
    bm.free()
    
    return obj


def create_arrow_face_widget(rig, bone_name, size=1.0):
    """创建箭头控制器"""
    
    # 创建控制器对象
    obj = create_widget(rig, bone_name)
    if obj is None:
        return None
    
    mesh = obj.data
    bm = bmesh.new()
    
    # 手动创建箭头形状
    verts = [
        (0.0, size * 0.1, 0.0),      # 箭头尖端
        (-size * 0.05, 0.0, 0.0),    # 左翼
        (-size * 0.02, 0.0, 0.0),    # 左内
        (-size * 0.02, -size * 0.08, 0.0),  # 左尾
        (size * 0.02, -size * 0.08, 0.0),   # 右尾
        (size * 0.02, 0.0, 0.0),     # 右内
        (size * 0.05, 0.0, 0.0),     # 右翼
    ]
    
    for v in verts:
        bm.verts.new(v)
    
    # 创建面
    bm.verts.ensure_lookup_table()
    faces = [
        [0, 1, 2, 3, 4, 5, 6]  # 箭头面
    ]
    
    for face in faces:
        bm.faces.new([bm.verts[i] for i in face])
    
    bm.to_mesh(mesh)
    bm.free()
    
    return obj


def create_face_bone_collections(rig):
    """创建面部骨骼集合"""
    
    # 确保在编辑模式或姿态模式
    if bpy.context.mode not in ['EDIT_ARMATURE', 'POSE']:
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
    
    # 创建所有面部骨骼集合
    create_all_face_collections(rig)


def assign_bone_to_face_collection(rig, bone_name, collection_name):
    """将骨骼分配到指定面部集合"""
    return assign_bone_to_collection(rig, bone_name, collection_name)


def create_face_constraints(rig, target_bone, source_bone, constraint_type='COPY_TRANSFORMS'):
    """创建面部约束"""
    
    if target_bone in rig.pose.bones and source_bone in rig.pose.bones:
        target = rig.pose.bones[target_bone]
        
        # 添加约束
        constraint = target.constraints.new(type=constraint_type)
        constraint.target = rig
        constraint.subtarget = source_bone
        
        return constraint
    
    return None


def setup_face_drivers(rig, control_bone, target_bone, property_name, driver_expression):
    """设置面部驱动器"""
    
    if target_bone in rig.pose.bones and control_bone in rig.pose.bones:
        target = rig.pose.bones[target_bone]
        
        # 创建驱动器
        driver = target.driver_add(property_name).driver
        driver.type = 'SCRIPTED'
        driver.expression = driver_expression
        
        # 添加变量
        var = driver.variables.new()
        var.name = "ctrl"
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = control_bone
        
        return driver
    
    return None


def mirror_face_setup(rig, left_bones, right_bones):
    """镜像面部设置"""
    
    for left_bone, right_bone in zip(left_bones, right_bones):
        if left_bone in rig.pose.bones and right_bone in rig.pose.bones:
            left = rig.pose.bones[left_bone]
            right = rig.pose.bones[right_bone]
            
            # 复制约束
            for constraint in left.constraints:
                new_constraint = right.constraints.new(type=constraint.type)
                
                # 复制约束属性
                for attr in dir(constraint):
                    if not attr.startswith('_') and hasattr(new_constraint, attr):
                        try:
                            setattr(new_constraint, attr, getattr(constraint, attr))
                        except:
                            pass
                
                # 镜像目标骨骼名称
                if hasattr(new_constraint, 'subtarget') and new_constraint.subtarget:
                    mirrored_name = mirror_bone_name(new_constraint.subtarget)
                    if mirrored_name in rig.pose.bones:
                        new_constraint.subtarget = mirrored_name


def mirror_bone_name(bone_name):
    """镜像骨骼名称"""
    
    if bone_name.endswith('.L'):
        return bone_name[:-2] + '.R'
    elif bone_name.endswith('.R'):
        return bone_name[:-2] + '.L'
    elif bone_name.endswith('_L'):
        return bone_name[:-2] + '_R'
    elif bone_name.endswith('_R'):
        return bone_name[:-2] + '_L'
    elif 'left' in bone_name.lower():
        return bone_name.lower().replace('left', 'right')
    elif 'right' in bone_name.lower():
        return bone_name.lower().replace('right', 'left')
    else:
        return bone_name  # 无法镜像的名称保持不变 