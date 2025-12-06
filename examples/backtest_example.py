#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测示例脚本

演示如何使用回测系统运行双均线策略
"""

import sys
import os
import pandas as pd
import numpy as np

# 确保项目根目录在Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入模块
from backtest_engine import BacktestEngine
from performance_analyzer import PerformanceAnalyzer
from backtest_visualizer import BacktestVisualizer
from examples.simple_ma_strategy import SimpleMAStrategy
from log_utils import setup_logger, get_logger
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
    
    # 应用参数优先级：函数参数 > 配置文件 > 硬编码默认值
    start_date = start_date or config.get("sample_data.start_date", "2020-01-01")
    end_date = end_date or config.get("sample_data.end_date", "2023-12-31")
    symbol = symbol or config.get("sample_data.symbol", "600000.SH")
    
    logger.info(f"使用参数生成示例数据: symbol={symbol}, start_date={start_date}, end_date={end_date}")
    
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


def main():
    """
    主函数
    """
    # 初始化日志
    setup_logger()
    logger = get_logger("backtest_example")
    logger.info("开始运行回测示例")
    
    # 加载配置文件
    load_config("config.json")
    config = get_config()
    
    # 生成示例数据
    logger.info("生成示例数据")
    sample_data = generate_sample_data()
    logger.info(f"生成了 {len(sample_data)} 条示例数据")
    
    # 保存示例数据到CSV文件
    sample_data.to_csv("sample_stock_data.csv", index=False, encoding='utf-8')
    logger.info("示例数据已保存到 sample_stock_data.csv")
    
    # 创建策略实例
    logger.info("创建双均线策略实例")
    strategy = SimpleMAStrategy()
    
    # 设置策略参数
    strategy_params = {
        "ma_short": 10,
        "ma_long": 20,
        "initial_cash": config.get("backtest.initial_cash", 1000000),
        "transaction_cost": config.get("backtest.transaction_cost", 0.0003),
        "slippage": config.get("backtest.slippage", 0.0001)
    }
    strategy.set_strategy_params(strategy_params)
    logger.info(f"设置策略参数: {strategy_params}")
    
    # 创建回测引擎
    logger.info("创建回测引擎")
    backtester = BacktestEngine()
    
    # 从配置文件获取回测参数
    start_date = config.get("backtest.start_date", "2020-01-01")
    end_date = config.get("backtest.end_date", "2023-12-31")
    
    # 设置回测参数
    backtester.set_params({
        "initial_cash": config.get("backtest.initial_cash", 1000000),
        "start_date": start_date,
        "end_date": end_date,
        "frequency": config.get("backtest.frequency", "d"),
        "transaction_cost": config.get("backtest.transaction_cost", 0.0003),
        "slippage": config.get("backtest.slippage", 0.0001)
    })
    
    # 加载数据
    logger.info("加载回测数据")
    backtester.load_data(sample_data)
    
    # 设置策略
    logger.info("设置策略")
    backtester.set_strategy(strategy)
    
    # 初始化回测
    logger.info("初始化回测")
    backtester.initialize()
    
    # 运行回测
    logger.info("开始回测")
    backtester.run()
    logger.info("回测完成")
    
    # 获取回测结果
    logger.info("获取回测结果")
    results = backtester.get_results()
    
    # 打印性能指标
    logger.info("打印性能指标")
    performance_metrics = results["performance_metrics"]
    logger.info(f"性能指标: {performance_metrics}")
    
    # 创建性能分析器
    logger.info("创建性能分析器")
    performance_analyzer = PerformanceAnalyzer()
    
    # 分析回测结果
    logger.info("分析回测结果")
    account_history = pd.DataFrame(results["account_history"])
    trades = pd.DataFrame(results["trades"])
    analysis_results = performance_analyzer.analyze(account_history, trades)
    
    # 生成性能分析报告
    logger.info("生成性能分析报告")
    performance_analyzer.generate_report(output_format="html", file_path="backtest_performance_report.html")
    logger.info("性能分析报告已生成")
    
    # 创建可视化器
    logger.info("创建可视化器")
    visualizer = BacktestVisualizer()
    
    # 从数据中提取实际股票信息，而非硬编码
    actual_stock_code = sample_data['code'].iloc[0]
    actual_start_date = sample_data['date'].min().strftime('%Y-%m-%d')
    actual_end_date = sample_data['date'].max().strftime('%Y-%m-%d')
    
    # 准备股票信息
    stock_info = {
        "symbol": actual_stock_code,
        "name": actual_stock_code,  # 简化处理，实际应用中可以从数据源获取股票名称
        "start_date": actual_start_date,
        "end_date": actual_end_date,
        "frequency": config.get("backtest.frequency", "d")  # 日线数据
    }
    
    logger.info(f"准备可视化报告，使用实际股票信息: {stock_info}")
    
    # 生成完整可视化报告
    logger.info("生成完整可视化报告")
    visualizer.generate_report(results, save_dir="visualization_results", stock_info=stock_info)
    
    logger.info("回测示例运行完成")
    
    # 打印最终结果
    print("\n=== 回测结果 ===")
    print(f"股票代码: {actual_stock_code}")
    print(f"回测日期范围: {actual_start_date} 至 {actual_end_date}")
    print(f"总收益率: {performance_metrics['total_return']:.2f}%")
    print(f"年化收益率: {performance_metrics['annual_return']:.2f}%")
    print(f"夏普比率: {performance_metrics['sharpe_ratio']:.2f}")
    print(f"最大回撤: {performance_metrics['max_drawdown']:.2f}%")
    print(f"胜率: {performance_metrics['win_rate']:.2f}%")
    print(f"总交易次数: {performance_metrics['total_trades']}")
    print(f"平均每笔交易收益率: {performance_metrics['avg_trade_return']:.4f}%")
    
    print("\n回测结果已保存到当前目录")
    print("性能分析报告: backtest_performance_report.html")
    print("完整可视化报告目录: visualization_results")


if __name__ == "__main__":
    main()
