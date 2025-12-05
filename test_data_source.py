#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据源管理测试脚本

测试新添加的数据源管理功能，使用不同数据源获取数据并进行回测
"""

import sys
import os
from log_utils import get_logger, setup_logger
from backtest_engine import BacktestEngine
from examples.simple_ma_strategy import SimpleMAStrategy

# 初始化日志
setup_logger()
logger = get_logger("test_data_source")

def test_data_source():
    """
    测试数据源管理功能
    """
    logger.info("开始测试数据源管理功能")
    
    # 创建回测引擎
    backtest_engine = BacktestEngine()
    
    # 设置回测参数
    backtest_engine.set_params({
        "initial_cash": 1000000,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "transaction_cost": 0.0003,
        "slippage": 0.0001
    })
    
    # 测试从BaoStock获取数据
    logger.info("测试从BaoStock获取数据")
    result = backtest_engine.fetch_data(
        stock_code="sh.600000",
        start_date="2023-01-01",
        end_date="2023-12-31",
        frequency="d",
        source_name="baostock"
    )
    
    if not result:
        logger.error("从BaoStock获取数据失败")
        return
    
    logger.info(f"从BaoStock获取到数据，共 {len(backtest_engine.data)} 条记录")
    print(backtest_engine.data.head())
    
    # 设置策略
    strategy = SimpleMAStrategy()
    backtest_engine.set_strategy(strategy)
    
    # 运行回测
    logger.info("运行回测")
    backtest_engine.run()
    
    # 获取回测结果
    results = backtest_engine.get_results()
    performance_metrics = backtest_engine.get_performance_metrics()
    
    logger.info(f"回测完成，性能指标: {performance_metrics}")
    print(f"总收益率: {performance_metrics['total_return']}%")
    print(f"年化收益率: {performance_metrics['annual_return']}%")
    print(f"夏普比率: {performance_metrics['sharpe_ratio']}")
    print(f"最大回撤: {performance_metrics['max_drawdown']}%")
    
    logger.info("数据源管理功能测试完成")

if __name__ == "__main__":
    test_data_source()
