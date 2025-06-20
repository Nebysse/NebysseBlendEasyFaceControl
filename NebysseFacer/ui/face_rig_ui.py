"""
NebysseFacer 面部绑定用户界面
提供面部绑定相关的UI面板
"""

import bpy
from bpy.types import Panel
from ..utils.blender_compatibility import get_bones_in_collection


class NEBYSSE_PT_face_rig_tools(Panel):
    """面部绑定工具面板"""
    bl_label = "NebysseFacer 工具"
    bl_idname = "NEBYSSE_PT_face_rig_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "NebysseFacer"
    bl_context = "posemode"
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE')
    
    def draw(self, context):
        layout = self.layout
        
        # 骨骼组工具
        box = layout.box()
        box.label(text="骨骼组管理", icon='GROUP_BONE')
        
        row = box.row()
        row.operator("nebysse.create_face_bone_collections", text="创建面部骨骼集合")
        
        if context.selected_pose_bones:
            row = box.row()
            row.operator("nebysse.assign_bone_to_face_group", text="分配到组")
        
        # 自定义属性工具
        box = layout.box()
        box.label(text="自定义属性", icon='PROPERTIES')
        
        if context.selected_pose_bones:
            row = box.row()
            row.operator("nebysse.create_face_custom_property", text="创建面部属性")
        
        # 镜像工具
        box = layout.box()
        box.label(text="镜像工具", icon='MOD_MIRROR')
        
        row = box.row()
        row.operator("nebysse.mirror_face_bones", text="镜像面部设置")


class NEBYSSE_PT_face_rig_info(Panel):
    """面部绑定信息面板"""
    bl_label = "绑定信息"
    bl_idname = "NEBYSSE_PT_face_rig_info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "NebysseFacer"
    bl_context = "posemode"
    bl_parent_id = "NEBYSSE_PT_face_rig_tools"
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE')
    
    def draw(self, context):
        layout = self.layout
        rig = context.active_object
        
        # 显示绑定基本信息
        col = layout.column(align=True)
        col.label(text=f"绑定名称: {rig.name}")
        col.label(text=f"骨骼数量: {len(rig.pose.bones)}")
        
        # 显示面部骨骼集合信息
        face_collections = [collection for collection in rig.data.collections if 'Face' in collection.name]
        if face_collections:
            col.separator()
            col.label(text="面部骨骼集合:")
            for collection in face_collections:
                bones_in_collection = get_bones_in_collection(rig, collection)
                col.label(text=f"  {collection.name}: {len(bones_in_collection)} 骨骼")
        
        # 显示选中骨骼信息
        if context.selected_pose_bones:
            col.separator()
            col.label(text=f"选中骨骼: {len(context.selected_pose_bones)}")
            
            # 显示活动骨骼的详细信息
            if context.active_pose_bone:
                active_bone = context.active_pose_bone
                col.separator()
                col.label(text=f"活动骨骼: {active_bone.name}")
                
                # 显示自定义属性
                custom_props = [key for key in active_bone.keys() if not key.startswith('_')]
                if custom_props:
                    col.label(text="自定义属性:")
                    for prop in custom_props:
                        col.label(text=f"  {prop}: {active_bone[prop]}")


class NEBYSSE_PT_face_rig_settings(Panel):
    """面部绑定设置面板"""
    bl_label = "绑定设置"
    bl_idname = "NEBYSSE_PT_face_rig_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "NebysseFacer"
    bl_context = "posemode"
    bl_parent_id = "NEBYSSE_PT_face_rig_tools"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE')
    
    def draw(self, context):
        layout = self.layout
        
        # 显示层设置
        box = layout.box()
        
        # 显示骨骼集合
        box.label(text="骨骼集合", icon='GROUP_BONE')
        
        # 显示当前骨骼集合
        armature = context.active_object.data
        if hasattr(armature, 'collections'):
            for collection in armature.collections:
                row = box.row()
                if hasattr(collection, 'is_visible'):
                    row.prop(collection, "is_visible", text=collection.name)
                else:
                    row.label(text=collection.name)


class NEBYSSE_PT_face_rig_help(Panel):
    """面部绑定帮助面板"""
    bl_label = "使用帮助"
    bl_idname = "NEBYSSE_PT_face_rig_help"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "NebysseFacer"
    bl_context = "posemode"
    bl_parent_id = "NEBYSSE_PT_face_rig_tools"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.label(text="NebysseFacer 使用指南:")
        col.separator()
        
        col.label(text="1. 创建面部骨骼组")
        col.label(text="   - 点击'创建面部骨骼组'按钮")
        col.separator()
        
        col.label(text="2. 分配骨骼到组")
        col.label(text="   - 选择骨骼")
        col.label(text="   - 点击'分配到组'")
        col.separator()
        
        col.label(text="3. 创建自定义属性")
        col.label(text="   - 选择骨骼")
        col.label(text="   - 点击'创建面部属性'")
        col.separator()
        
        col.label(text="4. 镜像设置")
        col.label(text="   - 设置左侧骨骼")
        col.label(text="   - 点击'镜像面部设置'")
        
        col.separator()
        col.label(text="更多信息请访问:")
        col.label(text="github.com/nebysse/NebysseFacer") 