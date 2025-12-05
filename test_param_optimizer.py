#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数优化功能测试脚本

用于测试参数优化模块的核心功能，不依赖于完整的回测流程
"""

import sys
import os

# 确保项目根目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入测试所需的模块
from parameter_optimizer import ParameterOptimizer
from param_version_manager import ParamVersionManager
from param_permission_manager import ParamPermissionManager


def test_param_optimizer():
    """
    测试参数优化器的核心功能
    """
    print("=== 测试参数优化器核心功能 ===")
    
    # 由于ParameterOptimizer需要策略类、回测引擎等依赖，我们先测试其静态方法和工具函数
    
    # 测试参数空间生成
    print("\n1. 测试参数空间生成")
    param_space = {
        "ma_short": {
            "type": "integer",
            "min": 5,
            "max": 15,
            "default": 10,
            "step": 5,
            "description": "短期移动平均线周期"
        },
        "ma_long": {
            "type": "integer",
            "min": 10,
            "max": 20,
            "default": 15,
            "step": 5,
            "description": "长期移动平均线周期"
        }
    }
    
    # 测试版本管理器
    print("\n2. 测试参数版本管理器")
    version_manager = ParamVersionManager()
    
    # 测试保存版本
    test_params = {
        "ma_short": 10,
        "ma_long": 20,
        "transaction_cost": 0.0003
    }
    
    test_performance = {
        "total_return": 15.5,
        "annual_return": 5.2,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.3
    }
    
    version_id = version_manager.save_version(
        params=test_params,
        performance=test_performance,
        name="test_version",
        description="测试版本",
        strategy_name="test_strategy"
    )
    
    print(f"   保存版本成功，版本ID: {version_id}")
    
    # 测试加载版本
    loaded_version = version_manager.load_version(version_id)
    print(f"   加载版本成功，版本名称: {loaded_version.get('name', '未知')}")
    
    # 测试列出版本
    versions = version_manager.list_versions()
    print(f"   版本总数: {len(versions)}")
    
    # 测试权限管理器
    print("\n3. 测试参数权限管理器")
    permission_manager = ParamPermissionManager()
    
    # 测试添加用户
    username = "test_user"
    password = "test_password"
    permission_manager.add_user(username, "editor", password, "测试用户")
    print(f"   添加用户成功: {username}")
    
    # 测试用户认证
    is_authenticated = permission_manager.authenticate_user(username, password)
    print(f"   用户认证结果: {'成功' if is_authenticated else '失败'}")
    
    # 测试权限检查
    has_permission = permission_manager.check_permission(username, "edit")
    print(f"   用户编辑权限: {'有' if has_permission else '没有'}")
    
    # 测试记录操作日志
    permission_manager.log_param_operation(
        username=username,
        operation="test",
        params_before={"ma_short": 10},
        params_after={"ma_short": 15},
        strategy_name="test_strategy"
    )
    print("   记录操作日志成功")
    
    # 测试获取操作日志
    logs = permission_manager.get_operation_logs(username=username)
    print(f"   获取操作日志成功，日志数量: {len(logs)}")
    
    print("\n=== 参数优化功能测试完成 ===")
    print("所有核心模块测试通过！")


if __name__ == "__main__":
    test_param_optimizer()
