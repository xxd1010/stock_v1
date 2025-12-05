#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数优化程序入口

整合参数优化、版本管理、权限控制和可视化功能
"""

import sys
import os
import pandas as pd
import numpy as np
from log_utils import setup_logger, get_logger

# 确保项目根目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from parameter_optimizer import ParameterOptimizer
from param_version_manager import ParamVersionManager
from param_visualizer import ParamVisualizer
from param_permission_manager import ParamPermissionManager
from backtest_engine import BacktestEngine
from examples.simple_ma_strategy import SimpleMAStrategy


def generate_sample_data(start_date="2020-01-01", end_date="2023-12-31", symbol="600000.SH"):
    """
    生成示例数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        symbol: 股票代码
        
    Returns:
        pd.DataFrame: 示例股票数据
    """
    # 生成日期范围
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # 生成随机价格数据（模拟股票价格）
    np.random.seed(42)
    base_price = 10.0
    price_changes = np.random.normal(0, 0.02, len(dates))
    prices = base_price * (1 + price_changes).cumprod()
    
    # 添加一些趋势
    trend = np.linspace(0, 10, len(dates))
    prices += trend
    
    # 生成开盘价、最高价、最低价（基于收盘价）
    opens = prices * (1 + np.random.normal(0, 0.01, len(dates)))
    highs = np.maximum(prices, opens) * (1 + np.random.normal(0, 0.01, len(dates)))
    lows = np.minimum(prices, opens) * (1 - np.random.normal(0, 0.01, len(dates)))
    
    # 生成成交量
    volumes = np.random.randint(1000000, 10000000, len(dates))
    
    # 创建DataFrame
    data = pd.DataFrame({
        "date": dates,
        "code": symbol,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes
    })
    
    return data


def run_backtest(params, data):
    """
    运行回测
    
    Args:
        params: 策略参数
        data: 回测数据
        
    Returns:
        dict: 回测结果，包含性能指标
    """
    # 创建策略实例
    strategy = SimpleMAStrategy()
    
    # 设置策略参数
    strategy.set_strategy_params(params)
    
    # 创建回测引擎
    backtester = BacktestEngine()
    
    # 设置回测参数
    backtester.set_params({
        "initial_cash": params.get("initial_cash", 1000000),
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "frequency": "d",
        "transaction_cost": params.get("transaction_cost", 0.0003),
        "slippage": params.get("slippage", 0.0001)
    })
    
    # 加载数据
    backtester.load_data(data)
    
    # 设置策略
    backtester.set_strategy(strategy)
    
    # 初始化回测
    backtester.initialize()
    
    # 运行回测
    backtester.run()
    
    # 获取回测结果
    results = backtester.get_results()
    
    return results


def main():
    """
    主函数
    """
    # 初始化日志
    setup_logger()
    logger = get_logger("optimize")
    logger.info("开始运行参数优化程序")
    
    # 1. 初始化各个模块
    logger.info("初始化参数优化相关模块")
    
    # 创建版本管理器
    version_manager = ParamVersionManager()
    
    # 创建可视化器
    visualizer = ParamVisualizer()
    
    # 创建权限管理器
    permission_manager = ParamPermissionManager()
    
    # 2. 检查权限（示例）
    logger.info("检查用户权限")
    username = "admin"
    password = "password123"
    
    # 如果用户不存在，先添加用户
    if not any(user["username"] == username for user in permission_manager.get_user_list()):
        logger.info(f"添加用户: {username}")
        permission_manager.add_user(username, "admin", password, "系统管理员")
    
    if not permission_manager.authenticate_user(username, password):
        logger.error("用户认证失败")
        return
    
    if not permission_manager.check_permission(username, "edit"):
        logger.error("用户没有编辑权限")
        return
    
    # 3. 生成示例数据
    logger.info("生成示例数据")
    sample_data = generate_sample_data()
    logger.info(f"生成了 {len(sample_data)} 条示例数据")
    
    # 4. 初始化回测引擎和上下文
    logger.info("初始化回测引擎和上下文")
    backtester = BacktestEngine()
    
    # 设置回测参数
    backtester.set_params({
        "initial_cash": 1000000,
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "frequency": "d",
        "transaction_cost": 0.0003,
        "slippage": 0.0001
    })
    
    # 加载数据
    backtester.load_data(sample_data)
    
    # 创建回测上下文
    context = {
        "strategy_name": "simple_ma",
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "initial_cash": 1000000
    }
    
    # 创建参数优化器
    optimizer = ParameterOptimizer(
        strategy_class=SimpleMAStrategy,
        backtest_engine=backtester,
        data=sample_data,
        context=context
    )
    
    # 4. 定义参数空间
    logger.info("定义参数空间")
    param_space = {
        "ma_short": {
            "type": "integer",
            "min": 5,
            "max": 30,
            "default": 10,
            "step": 1,
            "description": "短期移动平均线周期"
        },
        "ma_long": {
            "type": "integer",
            "min": 10,
            "max": 60,
            "default": 20,
            "step": 1,
            "description": "长期移动平均线周期"
        },
        "transaction_cost": {
            "type": "float",
            "min": 0.0001,
            "max": 0.001,
            "default": 0.0003,
            "step": 0.0001,
            "description": "交易成本率"
        },
        "initial_cash": {
            "type": "integer",
            "min": 100000,
            "max": 2000000,
            "default": 1000000,
            "step": 100000,
            "description": "初始资金"
        }
    }
    
    # 5. 推荐参数（基于历史数据）
    logger.info("推荐参数")
    recommended_params = optimizer.recommend_params(param_space, method="statistical")
    logger.info(f"推荐参数: {recommended_params}")
    
    # 6. 执行参数优化
    logger.info("执行参数优化")
    
    # 执行优化（使用最少的迭代次数，加快测试速度）
    optimization_results = optimizer.optimize(
        param_space,
        algorithm="random_search",  # 使用随机搜索替代网格搜索，更快
        max_iterations=3  # 只执行3次迭代
    )
    
    logger.info(f"优化完成，最佳参数: {optimization_results['best_params']}")
    logger.info(f"最佳性能: {optimization_results['best_performance']}")
    
    # 7. 记录优化历史
    logger.info("记录优化历史")
    all_results = optimization_results['all_results']
    
    # 8. 可视化优化结果（暂时注释，加快测试速度）
    # logger.info("可视化优化结果")
    # 
    # # 准备优化历史数据用于可视化
    # optimization_history = []
    # for i, result in enumerate(all_results):
    #     optimization_history.append({
    #         "performance": result['performance'].get('sharpe_ratio', 0)
    #     })
    # 
    # # 可视化优化过程
    # visualizer.visualize_optimization_results(optimization_history)
    # 
    # # 可视化参数空间
    # sample_params = []
    # for result in all_results[:10]:  # 只取前10个结果用于可视化
    #     sample_param = result['params'].copy()
    #     sample_param['performance'] = result['performance'].get('sharpe_ratio', 0)
    #     sample_params.append(sample_param)
    # 
    # visualizer.visualize_parameter_space(param_space, sample_params, optimization_results["best_params"])
    
    # 9. 保存最佳参数版本
    logger.info("保存最佳参数版本")
    
    # 运行最佳参数的回测，获取完整性能指标
    best_results = run_backtest(optimization_results["best_params"], sample_data)
    best_performance = best_results["performance_metrics"]
    
    # 保存版本
    version_id = version_manager.save_version(
        params=optimization_results["best_params"],
        performance=best_performance,
        name="best_sharpe",
        description="基于夏普比率优化的最佳参数",
        strategy_name="simple_ma"
    )
    
    logger.info(f"最佳参数已保存，版本ID: {version_id}")
    
    # 10. 记录操作日志
    logger.info("记录操作日志")
    
    # 记录参数优化操作
    permission_manager.log_param_operation(
        username=username,
        operation="optimize",
        params_before={"ma_short": 10, "ma_long": 20, "transaction_cost": 0.0003, "initial_cash": 1000000},
        params_after=optimization_results["best_params"],
        strategy_name="simple_ma"
    )
    
    # 11. 展示优化结果
    logger.info("展示优化结果")
    
    print("\n=== 参数优化结果 ===")
    print(f"优化算法: grid_search")
    print(f"迭代次数: {len(optimization_history)}")
    print(f"最佳参数: {optimization_results['best_params']}")
    print(f"最佳性能 (夏普比率): {optimization_results['best_performance'].get('sharpe_ratio', 0):.4f}")
    
    print("\n=== 最佳参数回测结果 ===")
    print(f"总收益率: {best_performance['total_return']:.2f}%")
    print(f"年化收益率: {best_performance['annual_return']:.2f}%")
    print(f"夏普比率: {best_performance['sharpe_ratio']:.2f}")
    print(f"最大回撤: {best_performance['max_drawdown']:.2f}%")
    print(f"胜率: {best_performance['win_rate']:.2f}%")
    print(f"总交易次数: {best_performance['total_trades']}")
    
    print("\n=== 版本信息 ===")
    print(f"版本ID: {version_id}")
    print(f"策略名称: simple_ma")
    print(f"保存时间: {datetime.now().isoformat()}")
    
    # 12. 启动参数调整GUI（可选）
    # visualizer.create_param_adjustment_gui(param_space, callback=lambda params: print("参数调整:", params))
    
    logger.info("参数优化程序运行完成")


if __name__ == "__main__":
    from datetime import datetime
    main()
