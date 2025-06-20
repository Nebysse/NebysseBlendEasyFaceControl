"""
Blender 4.1+ 骨骼集合模块
专为 Blender 4.1 及以上版本设计的骨骼集合 API
"""

import bpy

# 颜色主题映射
BONE_COLLECTION_COLORS = {
    'face_primary': 'THEME01',      # 红色 - 主要面部控制器
    'face_secondary': 'THEME02',    # 橙色 - 次要面部控制器  
    'face_detail': 'THEME03',       # 黄色 - 细节控制器
    'face_mechanism': 'THEME06',    # 绿色 - 机制骨骼
    'face_deform': 'THEME09',       # 蓝色 - 变形骨骼
}

# 面部骨骼集合配置
FACE_BONE_COLLECTIONS = {
    'Face Primary': {
        'color': BONE_COLLECTION_COLORS['face_primary'],
        'description': '主要面部控制器'
    },
    'Face Secondary': {
        'color': BONE_COLLECTION_COLORS['face_secondary'],
        'description': '次要面部控制器'
    },
    'Face Detail': {
        'color': BONE_COLLECTION_COLORS['face_detail'],
        'description': '细节面部控制器'
    },
    'Face Mechanism': {
        'color': BONE_COLLECTION_COLORS['face_mechanism'],
        'description': '面部机制骨骼'
    },
    'Face Deform': {
        'color': BONE_COLLECTION_COLORS['face_deform'],
        'description': '面部变形骨骼'
    }
}

def set_bone_collection_color(collection, color_theme):
    """设置骨骼集合的颜色
    
    Args:
        collection: 骨骼集合对象
        color_theme: 颜色主题 (如 'THEME01', 'THEME02' 等)
    """
    if hasattr(collection, 'color_set'):
        collection.color_set = color_theme
    else:
        print(f"警告: 无法为集合 {collection.name} 设置颜色")

def create_bone_collection_with_color(rig, name, color_theme):
    """创建带颜色的骨骼集合
    
    Args:
        rig: 骨架对象
        name: 集合名称
        color_theme: 颜色主题
    
    Returns:
        创建的骨骼集合对象
    """
    # 检查集合是否已存在
    collection = rig.data.collections.get(name)
    if collection:
        return collection
    
    # 创建新集合
    collection = rig.data.collections.new(name=name)
    
    # 设置颜色
    set_bone_collection_color(collection, color_theme)
    
    return collection

def assign_bone_to_collection(rig, bone_name, collection_name):
    """将骨骼分配到指定集合
    
    Args:
        rig: 骨架对象
        bone_name: 骨骼名称
        collection_name: 集合名称
    
    Returns:
        bool: 是否成功分配
    """
    try:
        # 检查骨骼是否存在
        if bone_name not in rig.data.bones:
            print(f"警告: 骨骼 {bone_name} 不存在")
            return False
        
        # 获取或创建骨骼集合
        collection = rig.data.collections.get(collection_name)
        if not collection:
            # 从预定义配置中获取颜色
            color = FACE_BONE_COLLECTIONS.get(collection_name, {}).get('color', 'THEME01')
            collection = create_bone_collection_with_color(rig, collection_name, color)
        
        # 分配骨骼到集合
        bone = rig.data.bones[bone_name]
        
        # 检查骨骼是否已在集合中
        if collection not in bone.collections:
            collection.assign(bone)
            print(f"✓ 成功分配骨骼 '{bone_name}' 到集合 '{collection_name}'")
        else:
            print(f"ℹ 骨骼 '{bone_name}' 已在集合 '{collection_name}' 中")
        
        return True
        
    except Exception as e:
        print(f"❌ 分配骨骼失败: {bone_name} -> {collection_name}: {e}")
        return False

def get_bones_in_collection(rig, collection):
    """获取集合中的所有骨骼
    
    Args:
        rig: 骨架对象
        collection: 骨骼集合对象
    
    Returns:
        list: 集合中的骨骼列表
    """
    bones_in_collection = []
    
    try:
        # 使用正确的 Blender 4.1+ API
        for bone in rig.data.bones:
            if collection in bone.collections:
                bones_in_collection.append(bone)
        return bones_in_collection
    except Exception as e:
        print(f"获取集合中的骨骼时出错: {e}")
    
    return bones_in_collection

def print_bone_collections_info(rig):
    """打印骨骼集合信息（调试用）
    
    Args:
        rig: 骨架对象
    """
    print(f"骨架 {rig.name} 的骨骼集合信息:")
    
    if hasattr(rig.data, 'collections'):
        print(f"骨骼集合数量: {len(rig.data.collections)}")
        for i, collection in enumerate(rig.data.collections):
            bones_count = len(get_bones_in_collection(rig, collection))
            print(f"  {i+1}. {collection.name}: {bones_count} 个骨骼")
    else:
        print("错误: Blender 版本不支持骨骼集合")

def create_all_face_collections(rig):
    """创建所有面部骨骼集合
    
    Args:
        rig: 骨架对象
    """
    for collection_name, config in FACE_BONE_COLLECTIONS.items():
        create_bone_collection_with_color(rig, collection_name, config['color']) 