"""
NebOffset骨骼配置文件
用于管理NebysseFacer系统中的NebOffset骨骼名单和映射关系
"""

# NebOffset骨骼属性名列表（用于bones.wei属性）
NEBOFFSET_BONE_ATTRIBUTES = [
    # 眉毛NebOffset骨骼
    'brow.T.L.003', 'brow.T.L.002', 'brow.T.L.001',       # 左眉上部
    'brow.T.R.003', 'brow.T.R.002', 'brow.T.R.001',       # 右眉上部
    
    # 下颌NebOffset骨骼
    'jaw_master',                                         # 下颌主控
    'lid.B.L.002', 'lid.B.R.002', 'lid.T.L.002', 'lid.T.R.002', # 眼睑
    
    'jaw_master_mouth',
    # 嘴唇NebOffset骨骼 - 左侧
    'lip.T.L.001', 'lip.T.L.002',                         # 左上唇
    'lip.B.L.001', 'lip.B.L.002',                         # 左下唇
    'lips.L',                                             # 左嘴角
    'lip_end.L.001', 'lip_end.L.002',                         # 左嘴角

    # 嘴唇NebOffset骨骼 - 右侧
    'lip.T.R.001', 'lip.T.R.002',                         # 右上唇
    'lip.B.R.001', 'lip.B.R.002',                         # 右下唇
    'lips.R',                                             # 右嘴角
    'lip_end.R.001', 'lip_end.R.002',                         # 右嘴角
    
    # 嘴唇NebOffset骨骼 - 中央
    'lip.T', 'lip.B'                                      # 中央上下唇
]

# NebOffset骨骼名称映射（属性名 -> 完整骨骼名）
NEBOFFSET_BONE_MAPPING = {
    # 眉毛NebOffset骨骼 - 左侧
    'brow.T.L.003': 'NebOffset-brow.T.L.003',        # 左眉上部003
    'brow.T.L.002': 'NebOffset-brow.T.L.002',        # 左眉上部002
    'brow.T.L.001': 'NebOffset-brow.T.L.001',        # 左眉上部001
    
    # 眉毛NebOffset骨骼 - 右侧（对称）
    'brow.T.R.003': 'NebOffset-brow.T.R.003',        # 右眉上部003
    'brow.T.R.002': 'NebOffset-brow.T.R.002',        # 右眉上部002
    'brow.T.R.001': 'NebOffset-brow.T.R.001',        # 右眉上部001
    
    # 下颌NebOffset骨骼
    'jaw_master': 'NebOffset-jaw_master', 
    'jaw_master_mouth': 'NebOffset-jaw_master_mouth',
    'lid.B.L.002': 'NebOffset-lid.B.L.002',
    'lid.B.R.002': 'NebOffset-lid.B.R.002',
    'lid.T.L.002': 'NebOffset-lid.T.L.002',
    'lid.T.R.002': 'NebOffset-lid.T.R.002',
    
    # 嘴唇NebOffset骨骼 - 左侧
    'lip.T.L.001': 'NebOffset-lip.T.L.001',          # 左上唇001
    'lip.T.L.002': 'NebOffset-lip.T.L.002',          # 左上唇002
    'lip.B.L.001': 'NebOffset-lip.B.L.001',          # 左下唇001
    'lip.B.L.002': 'NebOffset-lip.B.L.002',          # 左下唇002
    'lips.L': 'NebOffset-lips.L',   
    'lip_end.L.001': 'NebOffset-lip_end.L.001',
    'lip_end.L.002': 'NebOffset-lip_end.L.002',
    
    
    # 嘴唇NebOffset骨骼 - 右侧（对称）
    'lip.T.R.001': 'NebOffset-lip.T.R.001',          # 右上唇001
    'lip.T.R.002': 'NebOffset-lip.T.R.002',          # 右上唇002
    'lip.B.R.001': 'NebOffset-lip.B.R.001',          # 右下唇001
    'lip.B.R.002': 'NebOffset-lip.B.R.002',          # 右下唇002
    'lips.R': 'NebOffset-lips.R',
    'lip_end.R.001': 'NebOffset-lip_end.R.001',
    'lip_end.R.002': 'NebOffset-lip_end.R.002',
    
    # 嘴唇NebOffset骨骼 - 中央
    'lip.T': 'NebOffset-lip.T',                      # 上唇中央
    'lip.B': 'NebOffset-lip.B',                      # 下唇中央
}

# 坐标对应关系映射（用户指定的特殊对应关系）
POSITION_MAPPINGS = [
    # 眉毛骨骼映射 - 直接对应
    ('brow.T.L.003', 'brow.T.L.003'),      # brow.T.L.003 = brow.T.L.003
    ('brow.T.L.002', 'brow.T.L.002'), 
    ('brow.T.L.001', 'brow.T.L.001'),
    ('brow.T.R.003', 'brow.T.R.003'),
    ('brow.T.R.002', 'brow.T.R.002'),
    ('brow.T.R.001', 'brow.T.R.001'),
    ('lid.B.L.002', 'lid.B.L.002'),
    ('lid.B.R.002', 'lid.B.R.002'),
    ('lid.T.L.002', 'lid.T.L.002'),
    ('lid.T.R.002', 'lid.T.R.002'),
    # 下颌骨骼映射
    ('jaw_master', 'jaw_master'),          # jaw_master = jaw_master
    ('jaw_master_mouth', 'jaw_master'),
    # 嘴唇骨骼映射 - 根据用户指定的对应关系
    ('lip.T', 'lip.T.L'),                  # lip.T = lip.T.L (修改)
    ('lip.B', 'lip.B.L'),                  # lip.B = lip.B.L (修改)
    ('lip.T.L.001', 'lip.T.L.001'),        # lip.T.L.001 = lip.T.L.001 (保持)
    ('lip.B.L.001', 'lip.B.L.001'),        # lip.B.L.001 = lip.B.L.001 (保持)
    ('lips.L', 'cheek.B.L'),
    ('lip_end.L.001', 'cheek.B.L'),
    ('lip_end.L.002', 'cheek.B.L'),
    
    # 右侧对称骨骼 - 保持原有逻辑
    ('lip.T.R.001', 'lip.T.R.001'),
    ('lip.B.R.001', 'lip.B.R.001'),
    ('lips.R', 'cheek.B.R'),
    ('lip_end.R.001', 'cheek.B.R'),
    ('lip_end.R.002', 'cheek.B.R'),
    
    # 扩展嘴唇骨骼映射 - 保持原有逻辑
    ('lip.T.L.002', 'lip.T.L.002'),
    ('lip.B.L.002', 'lip.B.L.002'),
    ('lip.T.R.002', 'lip.T.R.002'),
    ('lip.B.R.002', 'lip.B.R.002'),
]

# 复制变换约束映射（源骨骼 -> 目标NebOffset骨骼）
CONSTRAINT_MAPPINGS = [
    # 眉毛骨骼约束映射
    ('brow.T.L.003', 'NebOffset-brow.T.L.003'),
    ('brow.T.L.002', 'NebOffset-brow.T.L.002'),
    ('brow.T.L.001', 'NebOffset-brow.T.L.001'),
    ('brow.T.R.003', 'NebOffset-brow.T.R.003'),
    ('brow.T.R.002', 'NebOffset-brow.T.R.002'),
    ('brow.T.R.001', 'NebOffset-brow.T.R.001'),
    ('lid.B.L.002', 'NebOffset-lid.B.L.002'),
    ('lid.B.R.002', 'NebOffset-lid.B.R.002'),
    ('lid.T.L.002', 'NebOffset-lid.T.L.002'),
    ('lid.T.R.002', 'NebOffset-lid.T.R.002'),
    
    # 下颌骨骼约束映射
    ('jaw_master', 'NebOffset-jaw_master'),
    ('jaw_master_mouth', 'NebOffset-jaw_master_mouth'),
    # 嘴唇骨骼约束映射 - 左侧
    ('lip.T.L.001', 'NebOffset-lip.T.L.001'),
    ('lip.T.L.002', 'NebOffset-lip.T.L.002'),
    ('lip.B.L.001', 'NebOffset-lip.B.L.001'),
    ('lip.B.L.002', 'NebOffset-lip.B.L.002'),
    ('lips.L', 'NebOffset-lips.L'),
    ('lip_end.L.001', 'NebOffset-lip_end.L.001'),
    ('lip_end.L.002', 'NebOffset-lip_end.L.002'),
    
    # 嘴唇骨骼约束映射 - 右侧
    ('lip.T.R.001', 'NebOffset-lip.T.R.001'),
    ('lip.T.R.002', 'NebOffset-lip.T.R.002'),
    ('lip.B.R.001', 'NebOffset-lip.B.R.001'),
    ('lip.B.R.002', 'NebOffset-lip.B.R.002'),
    ('lips.R', 'NebOffset-lips.R'),
    ('lip_end.R.001', 'NebOffset-lip_end.R.001'),
    ('lip_end.R.002', 'NebOffset-lip_end.R.002'),
    # 嘴唇骨骼约束映射 - 中央
    ('lip.T', 'NebOffset-lip.T'),
    ('lip.B', 'NebOffset-lip.B'),
]

# 骨骼分组配置
BONE_GROUPS = {
    'eyebrow_left': [
        'brow.T.L.003', 'brow.T.L.002', 'brow.T.L.001'
    ],
    'eyebrow_right': [
        'brow.T.R.003', 'brow.T.R.002', 'brow.T.R.001'
    ],
    'lip_upper_left': [
        'lip.T.L.001', 'lip.T.L.002',
    ],
    'lip_lower_left': [
        'lip.B.L.001', 'lip.B.L.002',
    ],
    'lip_upper_right': [
        'lip.T.R.001', 'lip.T.R.002',
    ],
    'lip_lower_right': [
        'lip.B.R.001', 'lip.B.R.002',
    ],
    'lip_corners': [
        'lips.L', 'lips.R',
        'lip_end.L.001', 'lip_end.L.002',
        'lip_end.R.001', 'lip_end.R.002'
    ],
    'lip_center': [
        'lip.T', 'lip.B'
    ]
}

def get_neboffset_bone_count():
    """获取NebOffset骨骼总数"""
    return len(NEBOFFSET_BONE_ATTRIBUTES)

def get_bone_group_info():
    """获取骨骼分组信息"""
    info = {}
    for group_name, bones in BONE_GROUPS.items():
        info[group_name] = {
            'count': len(bones),
            'bones': bones
        }
    return info

def get_constraint_count():
    """获取约束映射总数"""
    return len(CONSTRAINT_MAPPINGS)

def get_position_mapping_count():
    """获取位置映射总数"""
    return len(POSITION_MAPPINGS)

def validate_bone_lists():
    """验证骨骼列表的一致性"""
    errors = []
    
    # 检查属性列表和映射字典的一致性
    attrs_set = set(NEBOFFSET_BONE_ATTRIBUTES)
    mapping_set = set(NEBOFFSET_BONE_MAPPING.keys())
    
    if attrs_set != mapping_set:
        missing_in_mapping = attrs_set - mapping_set
        extra_in_mapping = mapping_set - attrs_set
        
        if missing_in_mapping:
            errors.append(f"映射中缺少的属性: {missing_in_mapping}")
        if extra_in_mapping:
            errors.append(f"映射中多余的属性: {extra_in_mapping}")
    
    # 检查约束映射中的目标骨骼是否都在NEBOFFSET_BONE_MAPPING中
    constraint_targets = {target for _, target in CONSTRAINT_MAPPINGS}
    mapping_values = set(NEBOFFSET_BONE_MAPPING.values())
    
    missing_targets = constraint_targets - mapping_values
    if missing_targets:
        errors.append(f"约束映射中未定义的目标骨骼: {missing_targets}")
    
    return errors

def get_summary():
    """获取配置摘要"""
    return {
        'total_bones': get_neboffset_bone_count(),
        'constraint_mappings': get_constraint_count(),
        'position_mappings': get_position_mapping_count(),
        'bone_groups': len(BONE_GROUPS),
        'validation_errors': validate_bone_lists()
    }

# 使用示例和测试
if __name__ == "__main__":
    print("=== NebOffset骨骼配置摘要 ===")
    summary = get_summary()
    
    print(f"📊 总骨骼数: {summary['total_bones']} 个")
    print(f"🔗 约束映射: {summary['constraint_mappings']} 个")
    print(f"📍 位置映射: {summary['position_mappings']} 个")
    print(f"👥 骨骼分组: {summary['bone_groups']} 个")
    
    if summary['validation_errors']:
        print(f"❌ 验证错误: {len(summary['validation_errors'])} 个")
        for error in summary['validation_errors']:
            print(f"   - {error}")
    else:
        print("✅ 配置验证通过")
    
    print("\n=== 骨骼分组详情 ===")
    group_info = get_bone_group_info()
    for group_name, info in group_info.items():
        print(f"{group_name}: {info['count']} 个骨骼")
        for bone in info['bones']:
            print(f"  - {bone}") 