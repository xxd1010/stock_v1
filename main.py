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
    operation = config.get("operation", "fetch")
    
    logger.info(f"当前操作: {operation}")
    
    try:
        # 根据操作类型调用不同的程序
        if operation in ["fetch", "batch-fetch", "get-codes"]:
            # 数据获取相关操作，调用 stock_fetcher.py
            logger.info("调用股票数据获取程序")
            from stock_fetcher import main as fetcher_main
            fetcher_main()
        elif operation in ["analyze", "batch-analyze"]:
            # 数据分析相关操作，调用 stock_analyzer.py
            logger.info("调用股票分析程序")
            from stock_analyzer import main as analyzer_main
            analyzer_main()
        else:
            logger.error(f"不支持的操作类型: {operation}")
            logger.error("支持的操作类型: fetch, batch-fetch, get-codes, analyze, batch-analyze")
            sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("股票分析程序结束")


if __name__ == "__main__":
    main()
