# NebOffset骨骼坐标对应关系更新

## 🔄 更新说明

本次更新修改了NebOffset前缀骨骼在Rigify生成阶段的坐标读取机制，建立了新的坐标对应关系。

**重要说明：使用编辑模式下的根坐标（head）和头坐标（tail）**
- 这些是世界坐标系下的绝对位置，**不是姿态坐标**
- 坐标复制在编辑状态下进行，确保骨骼的基础结构正确
- 包含根坐标（骨骼起点）、头坐标（骨骼终点）和滚转角度

## 📍 新的坐标对应关系

### 已修改的对应关系

| NebOffset骨骼 | 原来读取自 | 现在读取自 | 坐标类型 | 说明 |
|---------------|------------|------------|----------|------|
| `lip.T` | `lip.T` | `lip.T.L` | 编辑坐标 | 上唇中央从左上唇获取根坐标+头坐标 |
| `lip.B` | `lip.B` | `lip.B.L` | 编辑坐标 | 下唇中央从左下唇获取根坐标+头坐标 |
| `lips.L` | `lips.L` | `cheek.B.L` | 编辑坐标 | 左嘴角从左下脸颊获取根坐标+头坐标 |

### 保持直接对应的关系

| NebOffset骨骼 | 读取自 | 坐标类型 | 说明 |
|---------------|--------|----------|------|
| `brow.T.L.003` | `brow.T.L.003` | 编辑坐标 | 左眉上部003保持直接对应 |
| `lip.T.L.001` | `lip.T.L.001` | 编辑坐标 | 左上唇001保持直接对应 |
| `lip.B.L.001` | `lip.B.L.001` | 编辑坐标 | 左下唇001保持直接对应 |

## 🛠️ 技术实现

### 修改的文件
- `NebysseFacer/rigs/nebysse_faceup_con.py`

### 修改的方法
- `set_neboffset_positions_late()` - 使用`@stage.generate_bones`装饰器确保在Rigify系统生成完成后执行

### 关键代码位置
```python
@stage.generate_bones
def set_neboffset_positions_late(self):
    """使用编辑模式下的根坐标（head）和头坐标（tail）"""
    
    # 获取编辑模式下的骨骼
    edit_bones = self.obj.data.edit_bones
    
    # 复制编辑模式下的根坐标和头坐标
    neboffset_bone.head = rigify_bone.head.copy()  # 根坐标（骨骼起点）
    neboffset_bone.tail = rigify_bone.tail.copy()  # 头坐标（骨骼终点）
    neboffset_bone.roll = rigify_bone.roll         # 骨骼滚转角度
```

## 🎯 功能特点

1. **编辑模式坐标**: 使用编辑模式下的世界坐标，而非姿态坐标
2. **完整坐标信息**: 包含根坐标、头坐标和滚转角度的完整骨骼信息
3. **在生成阶段调用**: 使用`@stage.generate_bones`装饰器确保在Rigify系统生成完成后执行
4. **智能骨骼检测**: 自动检测关键Rigify面部骨骼的存在
5. **错误处理**: 完善的错误处理和日志记录
6. **统计报告**: 详细的操作统计和成功率报告

## 📋 使用说明

### 1. 生成绑定时的日志输出

在生成Rigify绑定时，您会看到类似以下的日志输出：

```
📍 === 延迟设置NebOffset骨骼编辑坐标 ===
🎯 坐标类型：编辑模式下的根坐标（head）和头坐标（tail），非姿态坐标

📝 应用新的编辑坐标对应关系:
   - lip.T -> lip.T.L (根坐标+头坐标)
   - lip.B -> lip.B.L (根坐标+头坐标) 
   - lips.L -> cheek.B.L (根坐标+头坐标)
   - 其他骨骼保持直接对应
🎯 坐标类型：编辑模式世界坐标（非姿态坐标）

✅ 编辑坐标 01: NebOffset-lip.T <- lip.T.L 🔄
    📍 根坐标: (0.125, 0.048, 1.654)
    📍 头坐标: (0.137, 0.063, 1.672)
✅ 编辑坐标 02: NebOffset-lip.B <- lip.B.L 🔄
    📍 根坐标: (0.118, 0.045, 1.634)
    📍 头坐标: (0.132, 0.058, 1.648)
...

📊 NebOffset骨骼编辑坐标设置统计:
   ✅ 成功设置: 12 个（根坐标+头坐标）
   📈 成功率: 85.7%
🔄 新的编辑坐标对应关系已应用: lip.T->lip.T.L, lip.B->lip.B.L, lips.L->cheek.B.L
🎯 坐标类型确认：编辑模式世界坐标（根坐标+头坐标+滚转角）
```

### 2. 特殊标识

- 🔄 表示使用了新的对应关系
- ✅ 表示编辑坐标设置成功
- 📍 显示具体的根坐标和头坐标数值
- ⚠ 表示跳过处理（通常是源骨骼不存在）

## 🧪 验证方法

### 1. 检查骨骼位置（编辑模式）

生成绑定后，在编辑模式下检查：
1. `NebOffset-lip.T` 的根坐标和头坐标应该与 `lip.T.L` 相同
2. `NebOffset-lip.B` 的根坐标和头坐标应该与 `lip.B.L` 相同  
3. `NebOffset-lips.L` 的根坐标和头坐标应该与 `cheek.B.L` 相同

### 2. 坐标验证方法

```python
# 在Blender脚本编辑器中验证
import bpy

# 获取编辑模式下的骨骼
armature = bpy.context.object
edit_bones = armature.data.edit_bones

# 检查坐标是否一致
source_bone = edit_bones.get('lip.T.L')
target_bone = edit_bones.get('NebOffset-lip.T')

if source_bone and target_bone:
    print(f"源骨骼头坐标: {source_bone.head}")
    print(f"目标骨骼头坐标: {target_bone.head}")
    print(f"坐标一致: {source_bone.head == target_bone.head}")
```

### 3. 检查日志

查看Blender控制台输出，确认看到：
- "🎯 坐标类型确认：编辑模式世界坐标" 消息
- 具体的根坐标和头坐标数值显示
- 带有 🔄 标识的编辑坐标设置记录

## ⚠️ 注意事项

1. **坐标类型**: 使用的是编辑模式下的世界坐标，不是姿态模式的变换坐标
2. **Rigify版本兼容性**: 确保使用的Rigify版本包含所需的源骨骼（如`lip.T.L`、`cheek.B.L`等）
3. **生成顺序**: 新的坐标设置在`@stage.generate_bones`阶段执行，确保在其他Rigify组件完成后进行
4. **编辑模式**: 坐标复制必须在编辑模式下进行，确保骨骼基础结构正确
5. **错误处理**: 如果源骨骼不存在，系统会跳过对应的NebOffset骨骼，不会导致生成失败

## 📞 支持

如果在使用过程中遇到问题，请检查：
1. Blender控制台的错误输出
2. 是否使用了正确的Rigify面部绑定类型
3. NebOffset骨骼是否正确生成
4. 确认看到编辑坐标相关的日志输出

---

**更新时间**: 2024年
**版本**: NebysseFacer 1.1.8+
**兼容性**: Blender 4.1+
**坐标类型**: 编辑模式世界坐标（根坐标+头坐标+滚转角）