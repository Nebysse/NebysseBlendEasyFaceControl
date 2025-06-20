# NebOffset骨骼配置系统

## 📁 文件结构

### `neboffset_bones.py` - 配置文件
集中管理所有NebOffset骨骼相关的配置数据，包括：

- **NEBOFFSET_BONE_ATTRIBUTES**: 骨骼属性名列表（18个）
- **NEBOFFSET_BONE_MAPPING**: 属性名到完整骨骼名的映射
- **POSITION_MAPPINGS**: 坐标对应关系映射（18个）
- **CONSTRAINT_MAPPINGS**: 复制变换约束映射（18个）
- **BONE_GROUPS**: 骨骼分组配置（8个分组）

### `nebysse_faceup_con.py` - 主要实现
使用配置文件中的数据来实现NebOffset骨骼系统。

## 🎯 优势

### 1. **集中管理**
- 所有骨骼配置集中在一个文件中
- 便于维护和修改
- 减少代码重复

### 2. **配置验证**
```python
validation_errors = validate_bone_lists()
if validation_errors:
    print("❌ 配置验证失败")
else:
    print("✅ 配置验证通过")
```

### 3. **分组管理**
- 左眉毛 (3个骨骼)
- 右眉毛 (3个骨骼)  
- 左上唇 (2个骨骼)
- 左下唇 (2个骨骼)
- 右上唇 (2个骨骼)
- 右下唇 (2个骨骼)
- 嘴角 (2个骨骼)
- 中央嘴唇 (2个骨骼)

## 📊 配置摘要

运行配置验证：
```bash
python neboffset_bones.py
```

输出示例：
```
=== NebOffset骨骼配置摘要 ===
📊 总骨骼数: 18 个
🔗 约束映射: 18 个
📍 位置映射: 18 个
👥 骨骼分组: 8 个
✅ 配置验证通过
```

## 🔧 使用方法

### 导入配置
```python
from .neboffset_bones import (
    NEBOFFSET_BONE_ATTRIBUTES,
    NEBOFFSET_BONE_MAPPING,
    POSITION_MAPPINGS,
    CONSTRAINT_MAPPINGS,
    BONE_GROUPS
)
```

### 获取信息
```python
# 获取骨骼总数
total_bones = get_neboffset_bone_count()

# 获取约束数量
constraint_count = get_constraint_count()

# 获取配置摘要
summary = get_summary()
```

## ⚙️ 配置修改

### 添加新骨骼
1. 在 `NEBOFFSET_BONE_ATTRIBUTES` 中添加属性名
2. 在 `NEBOFFSET_BONE_MAPPING` 中添加映射
3. 在 `POSITION_MAPPINGS` 中添加位置映射
4. 在 `CONSTRAINT_MAPPINGS` 中添加约束映射
5. 在适当的 `BONE_GROUPS` 中分组

### 修改映射关系
直接编辑对应的列表或字典即可，系统会自动验证一致性。

## 🔍 验证功能

配置文件包含内置的验证功能：

- **一致性检查**: 确保所有列表和映射的一致性
- **完整性检查**: 确保约束映射中的目标骨骼都已定义
- **错误报告**: 详细的错误信息和修复建议

## 📝 维护说明

1. **修改前验证**: 修改配置后运行验证脚本
2. **备份配置**: 重要修改前备份配置文件
3. **测试生成**: 在测试环境中验证修改效果
4. **文档更新**: 重要修改后更新相关文档

---

**创建时间**: 2024年
**版本**: NebysseFacer 1.1.8+
**维护者**: Nebysse Studio 