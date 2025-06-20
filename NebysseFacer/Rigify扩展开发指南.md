# Rigify 扩展开发指南

## 目录
1. [开发前准备](#开发前准备)
2. [核心注意事项](#核心注意事项)
3. [项目结构规范](#项目结构规范)
4. [核心功能函数详解](#核心功能函数详解)
5. [参数系统使用](#参数系统使用)
6. [约束和驱动器管理](#约束和驱动器管理)
7. [调试和错误处理](#调试和错误处理)
8. [最佳实践](#最佳实践)

---

## 开发前准备

### 环境要求
- **Blender版本**: 4.1+
- **Python版本**: 3.10+
- **必需插件**: Rigify (已启用)

### 基础知识要求
- Python 面向对象编程
- Blender API (bpy) 基础
- Rigify 框架结构理解
- 骨骼系统和约束原理

---

## 核心注意事项

### 1. 目录结构严格要求

```
你的扩展名/
├── rigs/                    # 必需 - 主要绑定模块
│   ├── 主控制器.py           # 命名规范: 功能_用途.py
│   ├── 子控制器_l.py         # 左右分离时使用 _l/_r 后缀
│   ├── 子控制器_r.py
│   ├── 基础类.py             # 共享基础类
│   └── utils/               # 工具模块目录
├── templates/               # 可选 - 模板文件
│   └── 模板.blend
└── utils/                   # 可选 - 全局工具
```

⚠️ **重要**: `rigs/` 目录是Rigify识别的关键，必须存在且结构正确

### 2. 类继承关系

```python
from rigify.base_rig import BaseRig

# 主控制器 - 必须继承BaseRig
class Rig(BaseRig):
    """主控制器类"""
    
# 子控制器 - 可以继承自定义基类
class BaseFaceUPLocator(BaseRig):
    """自定义基础定位器类"""
    
class Rig(BaseFaceUPLocator):
    """子控制器继承自定义基类"""
```

⚠️ **注意**: 每个绑定文件必须包含名为 `Rig` 的主类

### 3. 文件命名规范

- **主控制器**: `项目名_主要功能.py`
- **左右对称**: `功能名_l.py` / `功能名_r.py`
- **工具类**: `功能_utils.py` 或 `工具名.py`

### 4. Blender环境特殊性

由于Blender的特殊运行环境：
- **不需要生成测试脚本** (除非用户强制要求)
- **无法通过控制台直接调试**
- **需要手动在Blender内运行测试**
- **错误信息主要通过控制台输出**

---

## 项目结构规范

### 模块化设计原则

```python
# 主控制器 - 统一管理
class Rig(BaseRig):
    def __init__(self, generator, obj, bone_name, **params):
        super().__init__(generator, obj, bone_name, **params)
        # 注册子定位器
        self.child_rigs = []
        
    def register_child_rig(self, child_rig):
        """注册子控制器"""
        self.child_rigs.append(child_rig)

# 子控制器 - 独立功能
class BaseFaceUPLocator(BaseRig):
    def register_to_faceup_controller(self):
        """向主控制器注册自己"""
        # 查找并注册到主控制器
```

### 集合管理系统

```python
def create_bone_collections(self):
    """创建骨骼集合 - 组织和分类骨骼"""
    collections = {
        'Neb_Face': {'ui_row': 1, 'color_set_id': 5},  # 主要面部系统
        'Neb_Con': {'ui_row': 2, 'color_set_id': 2},   # 主控制器
        'Neb_MCH': {'ui_row': 3, 'color_set_id': 4},   # 机制骨骼
        'Neb_Disw': {'ui_row': 4, 'color_set_id': 3}   # 距离权重控制
    }
    
    for name, props in collections.items():
        coll = self.generator.collection_manager.create_collection(name)
        coll.ui_row = props['ui_row']
        coll.color_set_id = props['color_set_id']
```

---

## 核心功能函数详解

### 1. `generate_bones()` - 骨骼生成函数

**作用**: 创建绑定所需的所有骨骼结构

```python
def generate_bones(self):
    """骨骼生成阶段 - Rigify生成流程第一步"""
    
    # 1. 创建根骨骼
    root_name = self.copy_bone(self.bones.org, "主根骨骼")
    
    # 2. 创建控制骨骼
    control_name = self.copy_bone(self.bones.org, "控制器骨骼")
    
    # 3. 创建机制骨骼 (MCH)
    mch_name = self.copy_bone(self.bones.org, "MCH-机制骨骼")
    
    # 4. 创建变形骨骼 (DEF) - 可选
    def_name = self.copy_bone(self.bones.org, "DEF-变形骨骼")
    
    # 5. 保存骨骼引用以供后续使用
    self.bones.ctrl = control_name
    self.bones.mch = mch_name
    
    # 6. 设置骨骼基本属性
    self.get_bone(control_name).use_deform = False  # 控制骨骼不参与变形
    self.get_bone(mch_name).use_deform = False      # 机制骨骼不参与变形
```

**关键要点**:
- 必须在所有绑定类中实现
- 只创建骨骼，不设置约束或父子关系
- 使用 `self.copy_bone()` 复制现有骨骼
- 骨骼命名要有意义且唯一

### 2. `rig_bones()` - 骨骼装配函数

**作用**: 设置约束系统、骨骼分配和属性配置

```python
def rig_bones(self):
    """骨骼装配阶段 - 设置约束和骨骼行为"""
    
    # 1. 分配骨骼到集合
    self.generator.collection_manager.assign_bone(
        self.bones.ctrl, 'Neb_Con'  # 控制器骨骼 -> 控制器集合
    )
    
    # 2. 设置复制变换约束
    if self.params.enable_copy_constraints:
        self.setup_copy_transform_constraints()
    
    # 3. 从模板加载约束
    if hasattr(self.params, 'load_constraints_from_template'):
        if self.params.load_constraints_from_template:
            self.load_constraints_from_template()
    
    # 4. 设置驱动器
    self.setup_drivers()
    
    # 5. 配置骨骼锁定/解锁
    self.configure_bone_locks()

def setup_copy_transform_constraints(self):
    """设置复制变换约束的具体实现"""
    for source_bone, target_bone in self.constraint_mappings:
        # 获取目标骨骼的姿态骨骼
        pose_bone = self.obj.pose.bones.get(target_bone)
        if pose_bone:
            # 创建复制变换约束
            constraint = pose_bone.constraints.new('COPY_TRANSFORMS')
            constraint.target = self.obj
            constraint.subtarget = source_bone
            constraint.influence = self.params.constraint_influence
            constraint.mix_mode = self.params.constraint_mix_mode
```

**关键要点**:
- 在`generate_bones()`之后执行
- 负责设置所有约束和驱动器
- 管理骨骼的集合分配
- 配置骨骼的可见性和锁定状态

### 3. `parent_bones()` - 父子关系函数

**作用**: 建立骨骼之间的层级关系

```python
def parent_bones(self):
    """设置骨骼父子关系 - 建立骨骼层级结构"""
    
    # 1. 设置主要层级结构
    self.set_bone_parent(self.bones.ctrl, self.bones.root)  # 控制器 -> 根骨骼
    
    # 2. 设置机制骨骼层级
    for mch_bone in self.mch_bones:
        self.set_bone_parent(mch_bone, self.bones.mch_root)
    
    # 3. 特殊的权重骨骼父级设置
    for constraint_mapping in self.constraint_mappings:
        source_bone, neboffset_bone = constraint_mapping
        if self.get_bone(neboffset_bone):
            # 设置NebOffset骨骼的父级为特定根骨骼
            self.set_bone_parent(neboffset_bone, 'Neb_RigifyFace')
    
    # 4. 子控制器层级
    for child_rig in self.child_rigs:
        child_rig.setup_parent_hierarchy()
```

**层级结构示例**:
```
Neb_Facer_root (项目根)
├── Neb_face-root (面部根)
├── Neb_RigifyFace (Rigify面部)
│   └── NebOffset-* (所有权重骨骼)
└── brow-root.L/R (眉毛根)
    └── eyelip-root.L/R (眼睑根)
        └── mouth-root (嘴部根)
```

### 4. `configure_bones()` - 骨骼配置函数

**作用**: 配置骨骼的显示属性、锁定状态等

```python
def configure_bones(self):
    """配置骨骼属性和显示"""
    
    # 1. 设置控制器骨骼属性
    ctrl_bone = self.get_bone(self.bones.ctrl)
    ctrl_bone.lock_location = (True, True, False)  # 锁定X,Y轴移动
    ctrl_bone.lock_rotation = (False, False, True) # 锁定Z轴旋转
    ctrl_bone.lock_scale = (True, True, True)      # 锁定所有缩放
    
    # 2. 设置骨骼颜色和形状
    pose_bone = self.obj.pose.bones.get(self.bones.ctrl)
    if pose_bone:
        pose_bone.custom_shape = self.load_widget('控制器形状')
        pose_bone.bone_group_index = 1  # 设置骨骼组
    
    # 3. 隐藏机制骨骼
    for mch_bone in self.mch_bones:
        bone = self.get_bone(mch_bone)
        bone.hide = True  # 在编辑模式隐藏
        
        pose_bone = self.obj.pose.bones.get(mch_bone)
        if pose_bone:
            pose_bone.bone.hide = True  # 在姿态模式隐藏
```

### 5. 模板和工具函数

#### 模板加载函数
```python
def copy_template_constraints_and_drivers(self):
    """从模板文件复制约束和驱动器"""
    
    # 1. 加载模板数据
    template_data = TemplateManager.load_faceroot_template()
    if not template_data:
        print("警告: 无法加载模板数据")
        return
    
    # 2. 复制驱动器
    if 'drivers' in template_data:
        self.apply_drivers_from_template(template_data['drivers'])
    
    # 3. 复制约束
    if 'constraints' in template_data:
        self.apply_constraints_from_template(template_data['constraints'])

def apply_drivers_from_template(self, drivers_data):
    """应用驱动器数据"""
    for driver_info in drivers_data:
        target_bone = driver_info.get('target_bone')
        if target_bone and self.get_bone(target_bone):
            # 创建并配置驱动器
            self.create_driver(target_bone, driver_info)
```

---

## 参数系统使用

### 参数定义
```python
@staticmethod
def add_parameters(params):
    """添加用户可配置参数"""
    
    # 基础开关参数
    params.enable_copy_constraints = BoolProperty(
        name="启用复制约束",
        description="是否启用复制变换约束",
        default=True
    )
    
    # 数值参数
    params.constraint_influence = FloatProperty(
        name="约束影响",
        description="约束的影响权重",
        default=1.0,
        min=0.0,
        max=1.0
    )
    
    # 枚举参数
    params.constraint_mix_mode = EnumProperty(
        name="混合模式",
        description="约束的混合模式",
        items=[
            ('BEFORE', "之前", "在现有变换之前应用"),
            ('AFTER', "之后", "在现有变换之后应用"),
            ('REPLACE', "替换", "替换现有变换")
        ],
        default='BEFORE'
    )
    
    # 坐标参数 (用于DISW骨骼等)
    params.disw_t_001_x = FloatProperty(name="T.001 X坐标", default=-0.015)
    params.disw_t_001_y = FloatProperty(name="T.001 Y坐标", default=0.005)
    params.disw_t_001_z = FloatProperty(name="T.001 Z坐标", default=0.02)
```

### 参数使用
```python
def generate_bones(self):
    # 读取用户参数
    if self.params.enable_copy_constraints:
        # 执行约束相关逻辑
        pass
    
    # 使用数值参数
    influence = self.params.constraint_influence
    
    # 使用坐标参数
    if hasattr(self.params, 'use_custom_positions') and self.params.use_custom_positions:
        custom_pos = Vector((
            self.params.disw_t_001_x,
            self.params.disw_t_001_y,
            self.params.disw_t_001_z
        ))
```

---

## 约束和驱动器管理

### 约束创建和配置
```python
def create_constraint(self, bone_name, constraint_type, **kwargs):
    """创建约束的通用方法"""
    pose_bone = self.obj.pose.bones.get(bone_name)
    if not pose_bone:
        print(f"警告: 骨骼 {bone_name} 不存在")
        return None
    
    constraint = pose_bone.constraints.new(constraint_type)
    
    # 设置约束属性
    for prop, value in kwargs.items():
        if hasattr(constraint, prop):
            setattr(constraint, prop, value)
    
    return constraint

# 使用示例
def setup_limit_constraints(self):
    """设置限制约束"""
    self.create_constraint(
        self.bones.ctrl,
        'LIMIT_LOCATION',
        use_min_x=True, min_x=-0.1,
        use_max_x=True, max_x=0.1,
        owner_space='LOCAL'
    )
```

### 驱动器管理
```python
def create_driver(self, target_bone, property_path, expression=""):
    """创建驱动器"""
    driver = self.obj.pose.bones[target_bone].driver_add(property_path)
    
    if expression:
        driver.driver.expression = expression
    
    return driver

# 使用示例
def setup_facial_drivers(self):
    """设置面部驱动器"""
    # 眉毛高度驱动器
    driver = self.create_driver(
        'brow-control.L',
        'location',
        'ctrl_influence * 0.5'
    )
    
    # 添加驱动器变量
    var = driver.driver.variables.new()
    var.name = 'ctrl_influence'
    var.targets[0].id = self.obj
    var.targets[0].bone_target = 'main-control'
    var.targets[0].transform_type = 'LOC_Z'
```

---

## 调试和错误处理

### 调试信息输出
```python
def debug_print(self, message, level="INFO"):
    """统一的调试信息输出"""
    prefix = f"[{self.__class__.__name__}] {level}: "
    print(f"{prefix}{message}")

# 使用示例
def generate_bones(self):
    self.debug_print("开始生成骨骼")
    
    # 详细的进度信息
    self.debug_print(f"参数状态: enable_copy_constraints={self.params.enable_copy_constraints}")
    
    bone_count = len(self.bones_to_create)
    self.debug_print(f"计划创建 {bone_count} 个骨骼")
```

### 错误处理最佳实践
```python
def safe_bone_operation(self, bone_name, operation):
    """安全的骨骼操作包装器"""
    try:
        bone = self.get_bone(bone_name)
        if not bone:
            self.debug_print(f"骨骼 {bone_name} 不存在", "WARNING")
            return False
        
        operation(bone)
        return True
        
    except Exception as e:
        self.debug_print(f"骨骼 {bone_name} 操作失败: {str(e)}", "ERROR")
        return False

# 使用示例
def configure_bones(self):
    def set_bone_locks(bone):
        bone.lock_location = (True, True, False)
    
    self.safe_bone_operation(self.bones.ctrl, set_bone_locks)
```

### 验证函数
```python
def validate_generation(self):
    """验证生成结果"""
    errors = []
    
    # 检查必需骨骼
    required_bones = [self.bones.root, self.bones.ctrl]
    for bone_name in required_bones:
        if not self.get_bone(bone_name):
            errors.append(f"缺少必需骨骼: {bone_name}")
    
    # 检查约束
    ctrl_pose_bone = self.obj.pose.bones.get(self.bones.ctrl)
    if ctrl_pose_bone and not ctrl_pose_bone.constraints:
        errors.append("控制器骨骼缺少约束")
    
    # 输出验证结果
    if errors:
        self.debug_print("验证失败:", "ERROR")
        for error in errors:
            self.debug_print(f"  - {error}", "ERROR")
    else:
        self.debug_print("验证通过", "SUCCESS")
    
    return len(errors) == 0
```

---

## 最佳实践

### 1. 代码组织
- **单一职责**: 每个函数只做一件事
- **模块化**: 相关功能组织在一起
- **可扩展**: 设计时考虑未来的扩展需求

### 2. 性能优化
```python
# 缓存经常访问的对象
def __init__(self, generator, obj, bone_name, **params):
    super().__init__(generator, obj, bone_name, **params)
    self._pose_bones_cache = {}

def get_pose_bone_cached(self, bone_name):
    """缓存姿态骨骼访问"""
    if bone_name not in self._pose_bones_cache:
        self._pose_bones_cache[bone_name] = self.obj.pose.bones.get(bone_name)
    return self._pose_bones_cache[bone_name]
```

### 3. 用户体验
- **有意义的参数名称和描述**
- **合理的默认值**
- **清晰的错误信息**
- **进度反馈**

### 4. 兼容性考虑
```python
def ensure_blender_compatibility(self):
    """确保Blender版本兼容性"""
    import bpy
    
    if bpy.app.version < (4, 1, 0):
        raise Exception("需要Blender 4.1或更高版本")
    
    # 检查必需的插件
    if 'rigify' not in bpy.context.preferences.addons:
        raise Exception("需要启用Rigify插件")
```

### 5. 文档和注释
```python
class Rig(BaseRig):
    """眉毛控制定位器
    
    功能:
    - 生成左/右眉毛控制骨骼
    - 创建DISW权重骨骼
    - 支持自定义坐标设置
    
    使用:
    在Rigify元骨骼中选择此绑定类型，配置参数后生成绑定
    """
    
    def generate_bones(self):
        """生成眉毛控制骨骼结构
        
        生成的骨骼:
        - brow-root.L/R: 根骨骼
        - brow-con.L/R: 控制器骨骼  
        - DISW-brow.*: 距离权重骨骼
        
        坐标系统:
        所有DISW骨骼坐标相对于控制器骨骼设置
        """
```

---

## 总结

开发Rigify扩展需要掌握：

1. **核心函数流程**: `generate_bones()` → `rig_bones()` → `parent_bones()` → `configure_bones()`
2. **参数系统**: 为用户提供灵活的配置选项
3. **约束管理**: 正确设置骨骼约束和驱动器
4. **错误处理**: 优雅地处理各种异常情况
5. **调试技巧**: 有效的调试和验证方法

遵循这些指导原则，您就能开发出稳定、可靠的Rigify扩展。记住，Blender环境的特殊性要求我们更加重视代码的健壮性和调试信息的完整性。 