#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数优化程序入口

整合参数优化、版本管理、权限控制和可视化功能
"""

import sys
import os
import json
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
from config_manager import get_config, load_config




def generate_sample_data(start_date=None, end_date=None, symbol=None):
    """
    生成示例数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        symbol: 股票代码
        
    Returns:
        pd.DataFrame: 示例股票数据
        
    参数优先级：函数传入参数 > 配置文件参数 > 硬编码默认值
    """
    logger = get_logger("generate_sample_data")
    
    # 获取配置管理器实例
    config = get_config()
    
    # 记录原始参数
    logger.info(f"原始传入参数 - start_date: {start_date}, end_date: {end_date}, symbol: {symbol}")
    
    # 应用参数优先级：函数参数 > 配置文件 > 硬编码默认值
    original_start_date = start_date
    original_end_date = end_date
    original_symbol = symbol
    
    start_date = start_date or config.get("sample_data.start_date", "2020-01-01")
    end_date = end_date or config.get("sample_data.end_date", "2023-12-31")
    symbol = symbol or config.get("sample_data.symbol", "600000.SH")
    
    # 记录最终使用的参数及来源
    logger.info(f"最终使用参数 - start_date: {start_date} (来源: {'传入参数' if original_start_date else '配置文件' if config.get('sample_data.start_date') else '硬编码默认值'})")
    logger.info(f"最终使用参数 - end_date: {end_date} (来源: {'传入参数' if original_end_date else '配置文件' if config.get('sample_data.end_date') else '硬编码默认值'})")
    logger.info(f"最终使用参数 - symbol: {symbol} (来源: {'传入参数' if original_symbol else '配置文件' if config.get('sample_data.symbol') else '硬编码默认值'})")
    
    # 参数验证
    if pd.to_datetime(start_date) > pd.to_datetime(end_date):
        raise ValueError(f"开始日期 {start_date} 不能晚于结束日期 {end_date}")
    
    # 验证股票代码格式（简单验证，实际使用时可能需要更复杂的验证）
    if symbol and not isinstance(symbol, str):
        raise ValueError(f"股票代码必须是字符串类型，当前为 {type(symbol)}")
    
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
        
    Raises:
        ValueError: 当配置参数与实际数据不一致时抛出
    """
    logger = get_logger("run_backtest")
    
    # 提取数据中的实际股票代码（使用第一个股票代码）
    data_stock_code = data.get('code', data.get('symbol', None))
    if data_stock_code is not None:
        data_stock_code = data_stock_code.iloc[0] if isinstance(data_stock_code, pd.Series) else data_stock_code
        logger.info(f"数据中的实际股票代码: {data_stock_code}")
    
    # 提取数据的实际日期范围
    date_col = 'date' if 'date' in data.columns else 'datetime' if 'datetime' in data.columns else None
    if date_col is None:
        raise ValueError("数据中缺少日期列(date或datetime)")
    
    data_start_date = data[date_col].min().strftime('%Y-%m-%d')
    data_end_date = data[date_col].max().strftime('%Y-%m-%d')
    logger.info(f"数据的实际日期范围: {data_start_date} 至 {data_end_date}")
    
    # 创建策略实例
    strategy = SimpleMAStrategy()
    
    # 设置策略参数
    strategy.set_strategy_params(params)
    
    # 创建回测引擎
    backtester = BacktestEngine()
    
    # 获取配置管理器实例
    config = get_config()
    
    # 获取配置中的回测参数
    config_start_date = config.get("backtest.start_date", "2020-01-01")
    config_end_date = config.get("backtest.end_date", "2023-12-31")
    config_stock_code = config.get("sample_data.symbol", "600000.SH")
    
    logger.info(f"配置中的股票代码: {config_stock_code}")
    logger.info(f"配置中的回测日期范围: {config_start_date} 至 {config_end_date}")
    
    # 验证股票代码一致性
    if data_stock_code and config_stock_code and data_stock_code != config_stock_code:
        logger.warning(f"股票代码不一致 - 配置: {config_stock_code}, 数据: {data_stock_code}")
        # 可以选择抛出异常或使用数据中的股票代码
        # raise ValueError(f"股票代码不一致 - 配置: {config_stock_code}, 数据: {data_stock_code}")
    
    # 验证日期范围一致性
    if pd.to_datetime(config_start_date) > pd.to_datetime(data_end_date) or pd.to_datetime(config_end_date) < pd.to_datetime(data_start_date):
        raise ValueError(f"回测日期范围 {config_start_date} 至 {config_end_date} 与数据实际日期范围 {data_start_date} 至 {data_end_date} 无重叠")
    
    # 调用配置管理器的参数一致性校验函数
    config.validate_param_consistency(
        actual_stock_code=data_stock_code,
        actual_start_date=data_start_date,
        actual_end_date=data_end_date
    )
    
    # 设置回测参数，优先级：params > 配置文件 > 硬编码默认值
    # 使用数据的实际日期范围作为回测日期范围，确保一致性
    backtest_params = {
        "initial_cash": params.get("initial_cash", config.get("backtest.initial_cash", 1000000)),
        "start_date": config_start_date,
        "end_date": config_end_date,
        "frequency": config.get("backtest.frequency", "d"),
        "transaction_cost": params.get("transaction_cost", config.get("backtest.transaction_cost", 0.0003)),
        "slippage": params.get("slippage", config.get("backtest.slippage", 0.0001))
    }
    
    logger.info(f"设置回测参数: {backtest_params}")
    backtester.set_params(backtest_params)
    
    # 加载数据
    logger.info("开始加载回测数据")
    backtester.load_data(data)
    
    # 设置策略
    backtester.set_strategy(strategy)
    
    # 初始化回测
    backtester.initialize()
    
    # 运行回测
    logger.info("开始运行回测")
    backtester.run()
    
    # 获取回测结果
    results = backtester.get_results()
    
    # 在结果中添加关键参数信息，便于后续分析
    results["params_info"] = {
        "config_stock_code": config_stock_code,
        "data_stock_code": data_stock_code,
        "config_start_date": config_start_date,
        "config_end_date": config_end_date,
        "data_start_date": data_start_date,
        "data_end_date": data_end_date,
        "strategy_params": params
    }
    
    return results


def main():
    """
    主函数
    """
    # 初始化日志
    setup_logger()
    logger = get_logger("optimize")
    logger.info("开始运行参数优化程序")
    
    # 加载配置文件
    load_config("config.json")
    
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
    
    # 获取配置管理器实例
    config = get_config()
    
    # 设置回测参数，优先级：配置文件 > 硬编码默认值
    backtester.set_params({
        "initial_cash": config.get("backtest.initial_cash", 1000000),
        "start_date": config.get("backtest.start_date", "2020-01-01"),
        "end_date": config.get("backtest.end_date", "2023-12-31"),
        "frequency": config.get("backtest.frequency", "d"),
        "transaction_cost": config.get("backtest.transaction_cost", 0.0003),
        "slippage": config.get("backtest.slippage", 0.0001)
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
    print(f"优化算法: random_search")
    print(f"迭代次数: {len(optimization_results['all_results'])}")
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
