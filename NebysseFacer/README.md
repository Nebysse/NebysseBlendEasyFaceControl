# NebysseFacer - 专业面部绑定Feature Set

NebysseFacer是一个专为Blender Rigify设计的面部绑定Feature Set，提供专业级的面部控制器系统。

## 🎯 主要特性

### 🎭 面部绑定类型
- **基础面部绑定**: 提供基本的面部控制器功能
- **高级面部控制**: 支持复杂的面部表情控制
- **模块化设计**: 可扩展的绑定组件系统

### 🛠️ 工具功能
- **骨骼组管理**: 自动创建和管理面部骨骼组
- **自定义属性**: 为面部控制器创建自定义属性
- **镜像工具**: 自动镜像左右对称的面部设置
- **控制器形状**: 多种预设的控制器形状

### 🎨 用户界面
- **直观的工具面板**: 集成在3D视图侧边栏
- **实时信息显示**: 显示绑定和骨骼信息
- **帮助系统**: 内置使用指南

## 📦 安装方法

### 方法1: 作为Rigify Feature Set安装（推荐）

1. 确保Blender中已启用Rigify插件
2. 将整个`NebysseFacer`文件夹复制到以下位置：
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\[版本]\scripts\addons\rigify\feature_sets\`
   - **macOS**: `~/Library/Application Support/Blender/[版本]/scripts/addons/rigify/feature_sets/`
   - **Linux**: `~/.config/blender/[版本]/scripts/addons/rigify/feature_sets/`

3. 重启Blender
4. 在Rigify面板中，你应该能看到NebysseFacer的绑定类型

### 方法2: 通过Rigify界面安装

1. 打开Blender，确保Rigify插件已启用
2. 在3D视图中，进入骨架编辑模式
3. 在Rigify面板中找到"Feature Sets"部分
4. 点击"Install Feature Set from File"
5. 选择NebysseFacer文件夹
6. 重启Blender

## 🚀 使用方法

### 基础使用流程

1. **创建骨架**: 在Blender中创建一个新的骨架对象
2. **设置Rigify类型**: 为骨骼设置NebysseFacer的绑定类型
3. **配置参数**: 在Rigify面板中调整绑定参数
4. **生成绑定**: 点击"Generate Rig"生成面部控制器

### 工具面板使用

1. **进入姿态模式**: 选择生成的绑定，进入姿态模式
2. **打开工具面板**: 在3D视图侧边栏找到"NebysseFacer"标签
3. **使用工具**:
   - 创建面部骨骼组
   - 为骨骼分配到相应组
   - 创建自定义属性
   - 镜像面部设置

## 🎮 绑定类型说明

### nebysse_faceup_con
面部控制主控系统，提供：
- 层级化的面部骨骼结构
- 模板库系统支持
- 复制变换约束系统
- 多种生成模式（AUTO/MANUAL/HYBRID）

#### 参数说明
- **启用复制变换约束**: 为原生rigify骨骼添加复制变换约束
- **约束影响权重**: 复制变换约束的影响强度
- **生成模式**: 选择骨骼生成模式（自动检测/手动选择/混合模式）
- **手动骨骼列表**: 手动模式下的骨骼列表
- **排除骨骼**: 混合模式下要排除的骨骼
- **额外添加**: 混合模式下要额外添加的骨骼

## 🔧 开发者信息

### 文件结构
```
NebysseFacer/
├── __init__.py              # 主初始化文件
├── rigs/                    # 绑定类型定义
│   ├── __init__.py
│   ├── nebysse_faceup_con.py       # 面部控制主控系统
│   ├── nebysse_mouth_con.py        # 嘴部控制器
│   ├── nebysse_brow_con_l.py       # 左眉控制器
│   ├── nebysse_brow_con_r.py       # 右眉控制器
│   ├── nebysse_eyelip_con_l.py     # 左眼睑控制器
│   ├── nebysse_eyelip_con_r.py     # 右眼睑控制器
│   ├── nebysse_base_faceup_locator.py  # 基础面部定位器
│   └── utils/              # 实用工具模块
│       ├── __init__.py
│       ├── faceup_utils.py # 面部绑定工具函数
│       └── README.md       # 工具模块文档
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── face_utils.py
│   └── bone_utils.py
├── operators/               # 操作器
│   ├── __init__.py
│   └── face_operators.py
├── ui/                      # 用户界面
│   ├── __init__.py
│   └── face_rig_ui.py
├── rig_features/            # 绑定特性
│   └── __init__.py
├── metarigs/                # 元绑定
│   └── __init__.py
└── README.md
```

### 扩展开发
要添加新的绑定类型：
1. 在`rigs/`目录下创建新的Python文件
2. 继承`BaseRig`类
3. 实现必要的方法
4. 在`rigs/__init__.py`中注册新类型

## 🐛 故障排除

### 常见问题

**Q: 安装后在Rigify面板中看不到NebysseFacer**
A: 确保文件夹放置在正确位置，并重启Blender

**Q: 生成绑定时出现错误**
A: 检查控制台输出，确保所有依赖项正确导入

**Q: 工具面板不显示**
A: 确保在姿态模式下，并且选中了骨架对象

**Q: 出现"already registered as a subclass"错误**
A: 这通常是重复注册导致的，请：
1. 重启Blender
2. 确保只有一个NebysseFacer副本在feature_sets目录中
3. 如果问题持续，删除NebysseFacer文件夹，重启Blender，然后重新安装

**Q: 扩展加载失败**
A: 检查以下几点：
1. 确保Blender版本为4.1或更高
2. 确保Rigify插件已启用
3. 检查控制台是否有错误信息
4. 运行`install_test.py`脚本进行诊断

### 诊断工具

可以在Blender的脚本编辑器中运行`install_test.py`来检查扩展状态：

```python
# 在Blender脚本编辑器中运行
exec(open("path/to/NebysseFacer/install_test.py").read())
```

### 获取帮助
- GitHub: https://github.com/nebysse/NebysseFacer
- 问题反馈: 请在GitHub上提交Issue

## 📄 许可证

本项目采用GPL-2.0-or-later许可证。

## 🙏 致谢

感谢Blender Animation Studio的CloudRig项目提供的架构参考。

---

**版本**: 1.0.0  
**作者**: Nebysse Studio  
**兼容性**: Blender 4.1+ 