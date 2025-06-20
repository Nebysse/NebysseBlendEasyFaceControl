# NebysseFacer Operators Module
# 操作器定义

from .face_operators import *

registry = [
    NEBYSSE_OT_create_face_bone_collections,
    NEBYSSE_OT_assign_bone_to_face_group,
    NEBYSSE_OT_create_face_custom_property,
    NEBYSSE_OT_mirror_face_bones,
] 