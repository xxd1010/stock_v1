#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票分析程序主入口（控制器）

根据配置调用不同的程序，实现功能解耦
"""

import sys
import os

# 确保项目根目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from config_manager import load_config
from log_utils import setup_logger, get_logger

# 初始化日志
setup_logger()
logger = get_logger("main")

# 支持的操作选项
SUPPORTED_OPERATIONS = {
    "fetch": "获取单只股票数据",
    "batch-fetch": "批量获取股票数据",
    "get-codes": "获取股票代码列表",
    "analyze": "分析单只股票",
    "batch-analyze": "批量分析股票",
    "backtest": "执行回测",
    "optimize": "参数优化"
}

# 操作选项分类
FETCH_OPERATIONS = ["fetch", "batch-fetch", "get-codes"]
ANALYZE_OPERATIONS = ["analyze", "batch-analyze"]
BACKTEST_OPERATIONS = ["backtest", "optimize"]


def main():
    """
    主函数
    
    根据配置文件中的操作类型，调用不同的程序
    """
    logger.info("股票分析程序启动")

    # 加载配置文件
    load_config("config.json")

    # 从配置中读取操作类型
    from config_manager import get_config
    config = get_config()
    # 获取操作类型，默认值为fetch
    operation = config.get("operation", "fetch")

    logger.info(
        f"当前操作: {operation} ({SUPPORTED_OPERATIONS.get(operation, '未知操作')})")

    try:
        # 根据操作类型调用不同的程序
        if operation in FETCH_OPERATIONS:
            # 数据获取相关操作，调用 stock_fetcher.py
            logger.info("调用股票数据获取程序")
            from stock_fetcher import main as fetcher_main
            fetcher_main()
        elif operation in ANALYZE_OPERATIONS:
            # 数据分析相关操作，调用 stock_analyzer.py
            logger.info("调用股票分析程序")
            from stock_analyzer import main as analyzer_main
            analyzer_main()
        elif operation in BACKTEST_OPERATIONS:
            # 回测相关操作，调用回测模块
            logger.info("调用回测程序")
            if operation == "backtest":
                # 执行回测
                logger.info("执行回测")
                # 这里可以直接调用回测示例脚本，或者创建一个专门的回测入口
                from examples.backtest_example import main as backtest_main
                backtest_main()
            elif operation == "optimize":
                # 执行参数优化
                logger.info("执行参数优化")
                # 调用参数优化模块
                from optimize import main as optimize_main
                optimize_main()
        else:
            logger.error(f"不支持的操作类型: {operation}")
            supported_ops = ", ".join(SUPPORTED_OPERATIONS.keys())
            logger.error(f"支持的操作类型: {supported_ops}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

    logger.info("股票分析程序结束")


if __name__ == "__main__":
    main()
