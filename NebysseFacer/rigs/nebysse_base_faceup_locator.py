from rigify.base_rig import BaseRig
from rigify.utils.naming import make_derived_name
from rigify.utils.bones import BoneDict
from rigify.utils.widgets import create_widget
from ..utils.face_utils import create_face_control_widget

class BaseFaceUPLocator(BaseRig):
    """FaceUP 系统定位器基类"""
    
    def __init__(self, generator, pose_bone):
        super().__init__(generator, pose_bone)
        self.control_bone = None
        self.locator_type = "unknown"
    
    def find_master_faceroot(self):
        """查找主控 faceroot"""
        # 向上查找 faceroot 类型的父级
        current = self.base_bone
        while current:
            parent_name = self.get_bone(current).parent
            if parent_name:
                parent_rig = self.generator.bone_owners.get(parent_name)
                if parent_rig and hasattr(parent_rig, 'rig_id'):
                    if parent_rig.rig_id == 'nebysse_faceup_con':
                        return parent_rig
                current = parent_name
            else:
                break
        return None
    
    def register_to_faceup_controller(self):
        """注册到主控FaceUP控制器"""
        try:
            # 查找当前骨架中所有的 nebysse_faceup_con 类型
            for bone_name, owner in self.generator.bone_owners.items():
                module_name = type(owner).__module__ if owner else ""
                # 检查是否是 nebysse_faceup_con 类型
                if owner and hasattr(owner, 'rig_id'):
                    if 'nebysse_faceup_con' in module_name:
                        # 注册当前定位器到主控器
                        if hasattr(owner, 'child_locators'):
                            owner.child_locators[self.base_bone] = self
                            print(f"✓ {self.base_bone} 已注册到 nebysse_faceup_con 主控器")
                            return
            print(f"⚠ 未找到 nebysse_faceup_con 主控器，{self.base_bone} 将独立运行")
        except Exception as e:
            print(f"❌ 注册过程出错: {e}")
    
    def register_to_faceroot(self):
        """向 faceroot 注册自己"""
        # 查找当前骨架中所有的 faceup_con 类型
        for bone_name, rig in self.generator.bone_owners.items():
            if hasattr(rig, '__class__') and rig.__class__.__name__ == 'Rig':
                # 检查是否是 faceup_con 类型
                module_name = rig.__class__.__module__
                if 'faceup_con' in module_name:
                    if not hasattr(rig, 'child_locators'):
                        rig.child_locators = {}
                    rig.child_locators[self.locator_type] = self
                    print(f"✓ {self.locator_type} 已注册到 faceUP 主控")
                    return True
        
        print(f"⚠ 未找到 faceUP 主控，{self.locator_type} 注册失败")
        return False
    
    def generate_bones(self):
        """生成定位控制骨骼"""
        bones = BoneDict()
        
        # 获取原始骨骼名称（使用第一个骨骼）
        org_bone_name = self.bones.org[0] if isinstance(self.bones.org, list) else self.bones.org
        
        # 创建控制骨骼
        self.control_bone = self.copy_bone(
            org_bone_name, 
            make_derived_name(org_bone_name, 'ctrl', self.locator_type)
        )
        bones.ctrl = self.control_bone
        
        return bones
    
    def parent_bones(self):
        """设置骨骼父子关系"""
        # 获取原始骨骼名称（使用第一个骨骼）
        org_bone_name = self.bones.org[0] if isinstance(self.bones.org, list) else self.bones.org
        self.set_bone_parent(self.control_bone, org_bone_name)
    
    def configure_bones(self):
        """配置骨骼属性"""
        pass
    
    def rig_bones(self):
        """设置约束和驱动器"""
        # 注册到 faceroot
        self.register_to_faceroot()
    
    def generate_widgets(self):
        """生成控制器形状"""
        if self.control_bone:
            create_face_control_widget(
                self.obj, 
                self.control_bone,
                size=0.5,
                widget_type=self.get_widget_type()
            )
    
    def get_widget_type(self):
        """获取控制器形状类型，由子类重写"""
        return 'SPHERE' 