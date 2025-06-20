"""
Nebysse FaceUP 集合管理工具类
提供优化的骨骼集合创建和管理功能
"""

class CollectionManager:
    """骨骼集合管理器 - 优化版本"""
    
    def __init__(self, armature_obj):
        """初始化集合管理器
        
        Args:
            armature_obj: 骨架对象
        """
        self.armature_obj = armature_obj
        self.armature = armature_obj.data
    
    def create_disw_bone_collection(self, bone_names, collection_name="Neb_Disw"):
        """创建 DISW 骨骼集合 - 优化版本
        
        Args:
            bone_names: 要添加到集合的骨骼名称列表
            collection_name: 集合名称，默认为 "Neb_Disw"
            
        Returns:
            bool: 操作是否成功
        """
        if not bone_names:
            print("⚠ 没有骨骼需要添加到集合")
            return False
        
        try:
            # 获取或创建骨骼集合
            target_collection = self._get_or_create_bone_collection(collection_name)
            
            # 批量处理骨骼
            valid_bones, invalid_bones = self._validate_bones(bone_names)
            
            if invalid_bones:
                print(f"⚠ 发现 {len(invalid_bones)} 个无效骨骼: {invalid_bones}")
            
            if not valid_bones:
                print("✗ 没有有效的骨骼可添加")
                return False
            
            # 添加骨骼到集合
            added_count = self._add_bones_to_collection(valid_bones, target_collection)
            
            print(f"✅ {collection_name} 集合操作完成: 添加了 {added_count}/{len(valid_bones)} 个骨骼")
            return added_count > 0
            
        except Exception as e:
            print(f"✗ 创建骨骼集合失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_or_create_bone_collection(self, collection_name):
        """获取或创建骨骼集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            骨骼集合对象
        """
        # 尝试找到现有集合
        for collection in self.armature.collections:
            if collection.name == collection_name:
                print(f"ℹ 使用现有的 {collection_name} 集合")
                return collection
        
        # 创建新集合
        new_collection = self.armature.collections.new(collection_name)
        print(f"✓ 创建新的 {collection_name} 集合")
        return new_collection
    
    def _validate_bones(self, bone_names):
        """验证骨骼的有效性
        
        Args:
            bone_names: 骨骼名称列表
            
        Returns:
            tuple: (有效骨骼列表, 无效骨骼列表)
        """
        valid_bones = []
        invalid_bones = []
        
        for bone_name in bone_names:
            # 确保骨骼名称是字符串
            if not isinstance(bone_name, str):
                invalid_bones.append(f"{bone_name}(类型错误:{type(bone_name).__name__})")
                continue
            
            # 检查骨骼是否存在
            if bone_name not in self.armature.bones:
                invalid_bones.append(f"{bone_name}(不存在)")
                continue
            
            valid_bones.append(bone_name)
        
        print(f"📋 骨骼验证完成: {len(valid_bones)} 个有效, {len(invalid_bones)} 个无效")
        return valid_bones, invalid_bones
    
    def _add_bones_to_collection(self, bone_names, target_collection):
        """将骨骼添加到集合中
        
        Args:
            bone_names: 有效骨骼名称列表
            target_collection: 目标集合对象
            
        Returns:
            int: 成功添加的骨骼数量
        """
        added_count = 0
        
        for bone_name in bone_names:
            bone = self.armature.bones[bone_name]
            
            # 检查骨骼是否已在目标集合中
            if target_collection in bone.collections:
                print(f"ℹ {bone_name} 已在集合中，跳过")
                continue
            
            # 添加骨骼到集合
            try:
                target_collection.assign(bone)
                added_count += 1
                print(f"✓ 已添加 {bone_name} 到集合")
            except Exception as e:
                print(f"✗ 添加 {bone_name} 失败: {e}")
        
        return added_count
    
    def remove_bones_from_collection(self, bone_names, collection_name):
        """从集合中移除骨骼
        
        Args:
            bone_names: 要移除的骨骼名称列表
            collection_name: 集合名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 查找集合
            target_collection = None
            for collection in self.armature.collections:
                if collection.name == collection_name:
                    target_collection = collection
                    break
            
            if not target_collection:
                print(f"⚠ 集合 {collection_name} 不存在")
                return False
            
            removed_count = 0
            for bone_name in bone_names:
                if bone_name in self.armature.bones:
                    bone = self.armature.bones[bone_name]
                    if target_collection in bone.collections:
                        target_collection.unassign(bone)
                        removed_count += 1
                        print(f"✓ 从集合中移除 {bone_name}")
            
            print(f"✅ 从 {collection_name} 集合移除了 {removed_count} 个骨骼")
            return removed_count > 0
            
        except Exception as e:
            print(f"✗ 移除骨骼失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_collection_bones(self, collection_name):
        """获取集合中的所有骨骼
        
        Args:
            collection_name: 集合名称
            
        Returns:
            list: 骨骼名称列表
        """
        try:
            for collection in self.armature.collections:
                if collection.name == collection_name:
                    return [bone.name for bone in collection.bones]
            
            print(f"⚠ 集合 {collection_name} 不存在")
            return []
            
        except Exception as e:
            print(f"✗ 获取集合骨骼失败: {e}")
            return []
    
    def collection_exists(self, collection_name):
        """检查集合是否存在
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 集合是否存在
        """
        for collection in self.armature.collections:
            if collection.name == collection_name:
                return True
        return False
    
    def delete_collection(self, collection_name):
        """删除集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            for collection in self.armature.collections:
                if collection.name == collection_name:
                    self.armature.collections.remove(collection)
                    print(f"✓ 删除集合 {collection_name}")
                    return True
            
            print(f"⚠ 集合 {collection_name} 不存在")
            return False
            
        except Exception as e:
            print(f"✗ 删除集合失败: {e}")
            return False


class BaseFaceUPCollectionMixin:
    """FaceUP 集合管理混入类
    
    为 FaceUP 定位器提供统一的集合管理功能
    """
    
    def get_collection_manager(self):
        """获取集合管理器实例
        
        Returns:
            CollectionManager: 集合管理器实例
        """
        if not hasattr(self, '_collection_manager'):
            self._collection_manager = CollectionManager(self.obj)
        return self._collection_manager
    
    def create_disw_bone_collection(self, collection_name="Neb_Disw"):
        """创建 DISW 骨骼集合 - 优化版本
        
        Args:
            collection_name: 集合名称，默认为 "Neb_Disw"
            
        Returns:
            bool: 操作是否成功
        """
        if not hasattr(self, 'disw_bones') or not self.disw_bones:
            print("⚠ 没有DISW骨骼需要添加到集合")
            return False
        
        manager = self.get_collection_manager()
        return manager.create_disw_bone_collection(self.disw_bones, collection_name)
    
    def remove_disw_bones_from_collection(self, collection_name="Neb_Disw"):
        """从集合中移除 DISW 骨骼
        
        Args:
            collection_name: 集合名称，默认为 "Neb_Disw"
            
        Returns:
            bool: 操作是否成功
        """
        if not hasattr(self, 'disw_bones') or not self.disw_bones:
            print("⚠ 没有DISW骨骼需要从集合移除")
            return False
        
        manager = self.get_collection_manager()
        return manager.remove_bones_from_collection(self.disw_bones, collection_name)