from typing import List
import sys, importlib, inspect
import bpy

from rigify import feature_sets
from bpy.utils import register_class, unregister_class

from . import operators, rigs, utils, rig_features, ui

rigify_info = {
    'name': "NebysseFacer"
    ,'author': "Nebysse Studio"
    ,'version': (1, 1, 8)
    ,'blender': (4, 1, 0)  # 支持Blender 4.1+
    ,'description': "专业面部绑定Feature Set，为Rigify提供高级面部控制器"
    ,'doc_url': "https://github.com/nebysse/NebysseFacer"
    ,'link': "https://github.com/nebysse/NebysseFacer"
}

max_blender_version = (4, 3, 0)  # 最大支持版本

bl_info = {
    'name' : "NebysseFacer - 面部绑定Feature Set"
    ,'version' : (1, 0, 0)
    ,'blender' : (4, 1, 0)
    ,'description' : "应该作为Feature Set安装到Rigify插件中"
    ,'location': "插件->Rigify->Feature Sets->从文件安装Feature Set"
    ,'category': 'Rigging'
    ,'doc_url' : "https://github.com/nebysse/NebysseFacer"
}

# 注意：加载顺序很重要！
modules = [
    rig_features,
    ui,
    operators,
    rigs,
    utils
]

def register_unregister_modules(modules: List, register: bool):
    """递归注册或注销模块，通过查找un/register()函数或名为'registry'的列表
    registry应该是可注册类的列表。
    """
    register_func = register_class if register else unregister_class

    for m in modules:
        if register:
            importlib.reload(m)
        
        # 处理registry列表中的类
        if hasattr(m, 'registry'):
            for c in m.registry:
                try:
                    if register:
                        # 检查类是否已经注册
                        if hasattr(bpy.types, c.__name__):
                            print(f"警告: 类 {c.__name__} 已经注册，跳过注册")
                            continue
                    register_func(c)
                except Exception as e:
                    un = 'un' if not register else ''
                    print(f"警告: NebysseFacer无法{un}注册类: {c.__name__}")
                    print(f"错误详情: {e}")

        # 递归处理子模块
        if hasattr(m, 'modules'):
            register_unregister_modules(m.modules, register)

def register():
    """当安装或启用NebysseFacer时由Rigify调用。"""
    caller_name = inspect.stack()[2].function
    trying_to_install_as_addon = caller_name == 'execute'
    assert not trying_to_install_as_addon, "NebysseFacer不是插件。请将其作为Feature Set安装到Rigify插件中。"

    feature_sets.NebysseFacer = sys.modules[__name__]

    register_unregister_modules(modules, True)

def unregister():
    """当卸载或禁用NebysseFacer时由Rigify调用。"""
    register_unregister_modules(modules, False)
    try:
        del feature_sets.NebysseFacer
    except AttributeError:
        pass 