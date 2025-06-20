# Blender模板加载系统使用指南

## 概述

新的通用Blender模板加载系统允许您直接从`.blend`文件加载骨骼数据、自定义属性和驱动器，为其他项目提供可复用的模板管理方案。

## 核心优势

- 🎨 **直观编辑**: 直接在Blender中编辑模板，所见即所得
- 🔄 **通用设计**: 可被多个项目和绑定类型共享使用
- 📊 **完整支持**: 支持自定义属性、驱动器、约束等所有数据
- 🛡️ **向后兼容**: 保持与现有JSON模板的完全兼容
- 🧹 **自动清理**: 智能的资源管理和临时数据清理

## 快速开始

### 1. 基本使用

```python
from NebysseFacer.rigs.utils.blend_template_loader import BlendTemplateLoader

# 创建模板加载器
loader = BlendTemplateLoader(template_name="Nebysse_FaceUP_Tem.blend")

# 加载特定骨骼的数据
template_data = loader.load_template_data(target_bone_names=["face-root"])

# 检查加载结果
bone_data = template_data.get('bone_data', {})
if 'face-root' in bone_data:
    face_root_data = bone_data['face-root']
    print(f"自定义属性: {len(face_root_data['custom_properties'])} 个")
    print(f"驱动器: {len(face_root_data['drivers'])} 个")

# 清理资源
loader.cleanup()
```

### 2. 应用到绑定

```python
from NebysseFacer.rigs.utils.blend_template_loader import apply_template_to_rig

# 一步应用模板到目标绑定
success = apply_template_to_rig(
    target_rig=my_armature_object,
    template_name="Nebysse_FaceUP_Tem.blend",
    bone_mapping={"face-root": "face-root"},  # 可选的骨骼名称映射
    target_bone_names=["face-root"]  # 只加载指定骨骼
)

if success:
    print("✅ 模板应用成功")
else:
    print("❌ 模板应用失败")
```

### 3. 在自定义绑定中使用

```python
class MyCustomRig(BaseRig):
    def __init__(self, generator, pose_bone):
        super().__init__(generator, pose_bone)
        # 创建模板管理器
        from NebysseFacer.rigs.utils.blend_template_loader import BlendTemplateLoader
        self.template_loader = BlendTemplateLoader(template_name="my_template.blend")
    
    def generate_bones(self):
        # ... 生成骨骼逻辑
        pass
    
    def rig_bones(self):
        # 应用模板数据
        template_data = self.template_loader.load_template_data(
            target_bone_names=["control_bone"]
        )
        
        bone_data = template_data.get('bone_data', {})
        success = self.template_loader.apply_bone_data_to_rig(
            self.obj, 
            bone_data,
            bone_mapping={"control_bone": "my_control_bone"}
        )
        
        if success:
            print("✅ 模板数据应用成功")
    
    def finalize(self):
        # 清理模板资源
        if hasattr(self, 'template_loader'):
            self.template_loader.cleanup()
```

## 高级功能

### 1. 骨骼名称映射

当模板中的骨骼名与目标绑定中的骨骼名不同时，可以使用骨骼映射：

```python
bone_mapping = {
    "template_bone_name": "target_bone_name",
    "face-root": "my_face_control",
    "jaw_ctrl": "jaw_master"
}

loader.apply_bone_data_to_rig(target_rig, bone_data, bone_mapping)
```

### 2. 选择性加载

只加载需要的骨骼数据，提高性能：

```python
# 只加载face-root和jaw_ctrl的数据
template_data = loader.load_template_data(
    target_bone_names=["face-root", "jaw_ctrl"]
)
```

### 3. 自定义搜索路径

指定自定义的模板文件搜索路径：

```python
custom_search_dirs = [
    "/path/to/my/templates",
    "/another/template/directory"
]

template_path = loader.find_template_file(search_dirs=custom_search_dirs)
```

### 4. 直接指定模板路径

```python
loader = BlendTemplateLoader(template_path="/full/path/to/template.blend")
```

## 数据结构

### 骨骼数据格式

```python
bone_data = {
    'bone_name': {
        'name': '骨骼名称',
        'custom_properties': {
            'property_name': {
                'value': 0.5,  # 属性值
                'ui_data': {
                    'min': 0.0,
                    'max': 1.0,
                    'description': '属性描述'
                }
            }
        },
        'drivers': [
            {
                'data_path': 'pose.bones["bone_name"]["property"]',
                'array_index': 0,
                'driver_type': 'SCRIPTED',
                'expression': 'var * 2',
                'variables': [
                    {
                        'name': 'var',
                        'type': 'TRANSFORMS',
                        'targets': [
                            {
                                'id_type': 'OBJECT',
                                'id': 'Armature',
                                'bone_target': 'source_bone',
                                'transform_type': 'LOC_X',
                                'transform_space': 'LOCAL_SPACE'
                            }
                        ]
                    }
                ]
            }
        ],
        'constraints': [
            {
                'name': 'Copy Transforms',
                'type': 'COPY_TRANSFORMS',
                'target': 'Armature',
                'subtarget': 'target_bone'
            }
        ]
    }
}
```

## 与FaceUP系统的集成

新的模板加载系统已经完全集成到FaceUP绑定系统中：

1. **自动检测**: 系统会首先尝试加载Blender模板
2. **智能回退**: 如果Blender模板不可用，自动回退到JSON模板
3. **无缝切换**: 用户无需修改任何配置，系统自动选择最佳加载方式

### 在FaceUP中的使用

```python
# 在TemplateManager中
template_manager = TemplateManager(rig_instance)

# 自动选择最佳加载方式
template_data = template_manager.load_faceroot_template()

# 系统会自动：
# 1. 尝试从Blender模板加载
# 2. 如果失败，回退到JSON模板
# 3. 返回统一格式的结果
```

## 错误处理

模板加载系统提供了完善的错误处理：

```python
try:
    loader = BlendTemplateLoader(template_name="my_template.blend")
    template_data = loader.load_template_data()
    
    if not template_data:
        print("模板加载失败")
        return
    
    # 处理加载的数据
    success = loader.apply_bone_data_to_rig(target_rig, template_data['bone_data'])
    
except Exception as e:
    print(f"错误: {e}")
finally:
    # 确保资源清理
    loader.cleanup()
```

## 最佳实践

### 1. 资源管理

```python
# 推荐: 使用上下文管理器模式
class TemplateContextManager:
    def __init__(self, template_name):
        self.loader = BlendTemplateLoader(template_name=template_name)
    
    def __enter__(self):
        return self.loader
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.loader.cleanup()

# 使用方式
with TemplateContextManager("my_template.blend") as loader:
    template_data = loader.load_template_data()
    # 自动清理资源
```

### 2. 性能优化

```python
# 只加载需要的骨骼
target_bones = ["face-root", "jaw_ctrl"]
template_data = loader.load_template_data(target_bone_names=target_bones)

# 批量处理多个绑定
bone_data = template_data['bone_data']
for rig in target_rigs:
    loader.apply_bone_data_to_rig(rig, bone_data, bone_mapping)
```

### 3. 调试和日志

系统提供详细的日志输出，便于调试：

```python
# 启用详细日志
loader = BlendTemplateLoader(template_name="my_template.blend")
template_data = loader.load_template_data()

# 日志输出示例:
# 🔍 搜索模板文件: /path/to/template.blend
# ✓ 找到模板文件: /path/to/template.blend
# 📂 开始加载模板文件: my_template.blend
# ✓ 找到模板骨架: Armature
# 📋 提取 1 个骨骼的数据...
# ✓ 提取骨骼数据: face-root
# 📝 自定义属性: 25 个
# 🔄 驱动器: 15 个
```

## 故障排除

### 常见问题

1. **模板文件未找到**
   ```
   ❌ 未找到模板文件: my_template.blend
   ```
   - 检查文件名是否正确
   - 确认文件在搜索路径中
   - 使用绝对路径指定文件位置

2. **权限问题**
   ```
   ❌ 加载模板文件失败: Permission denied
   ```
   - 检查文件读取权限
   - 确认Blender有访问该路径的权限

3. **数据应用失败**
   ```
   ❌ 应用骨骼数据失败: Bone 'target_bone' not found
   ```
   - 检查目标骨骼是否存在
   - 验证骨骼名称映射是否正确

### 调试技巧

```python
# 启用详细调试
loader = BlendTemplateLoader(template_name="debug_template.blend")

# 检查模板文件
template_path = loader.find_template_file()
print(f"模板路径: {template_path}")

# 检查加载的数据
template_data = loader.load_template_data()
bone_data = template_data.get('bone_data', {})

for bone_name, data in bone_data.items():
    print(f"骨骼: {bone_name}")
    print(f"  属性: {len(data.get('custom_properties', {}))}")
    print(f"  驱动器: {len(data.get('drivers', []))}")
```

## 扩展开发

### 创建自定义模板加载器

```python
from NebysseFacer.rigs.utils.blend_template_loader import BlendTemplateLoader

class MyCustomTemplateLoader(BlendTemplateLoader):
    def __init__(self, template_name):
        super().__init__(template_name)
        # 自定义初始化
    
    def _extract_custom_data(self, armature_obj):
        """提取自定义数据"""
        # 实现自定义的数据提取逻辑
        pass
    
    def _apply_custom_data(self, target_rig, custom_data):
        """应用自定义数据"""
        # 实现自定义的数据应用逻辑
        pass
```

### 添加新的数据类型支持

```python
def _extract_shape_keys(self, mesh_obj):
    """提取形状键数据"""
    if not mesh_obj.data.shape_keys:
        return {}
    
    shape_keys = {}
    for key in mesh_obj.data.shape_keys.key_blocks:
        shape_keys[key.name] = {
            'value': key.value,
            'min': key.slider_min,
            'max': key.slider_max
        }
    
    return shape_keys
```

通过这个通用的模板加载系统，您可以轻松地为任何项目创建和管理Blender模板，大大提高开发效率和用户体验！ 