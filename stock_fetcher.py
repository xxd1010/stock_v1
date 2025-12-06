#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票数据获取程序

专门用于从数据源获取股票数据并存储
"""

import argparse
import sys
import os
from datetime import datetime

# 确保项目根目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from baostock_data_fetcher import BaoStockDataFetcher
from data_preprocessor import DataPreprocessor
from config_manager import get_config, load_config
from log_utils import setup_logger, get_logger

# 初始化日志
setup_logger()
logger = get_logger("stock_fetcher")


class StockFetcher:
    """
    股票数据获取器
    
    专门用于从数据源获取股票数据并存储
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化股票数据获取器
        
        Args:
            config_path: 配置文件路径
        """
        logger.info("初始化股票数据获取器")
        
        # 加载配置
        if config_path:
            load_config(config_path)
        
        # 获取配置
        self.config = get_config()
        
        # 验证配置
        if not self.config.validate_config():
            logger.error("配置验证失败，程序退出")
            sys.exit(1)
        
        # 初始化数据获取模块
        self.data_fetcher = BaoStockDataFetcher()
        self.data_preprocessor = DataPreprocessor()
        
        logger.info("股票数据获取器初始化完成")
    
    def fetch_stock_data(self, stock_code: str, start_date: str, end_date: str, frequency: str = "d"):
        """
        获取单只股票数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
        """
        logger.info(f"开始获取股票数据: {stock_code}, 时间范围: {start_date} 至 {end_date}")
        
        # 获取股票数据
        stock_data = self.data_fetcher.get_stock_data(stock_code, start_date, end_date, frequency)
        
        if stock_data.empty:
            logger.error(f"未获取到股票 {stock_code} 的数据")
            return None
        
        # 预处理数据
        processed_data = self.data_preprocessor.preprocess(stock_data)
        
        # 保存到数据库
        self.data_fetcher.save_stock_data_to_db(processed_data, stock_code)
        
        logger.info(f"股票数据获取完成: {stock_code}")
        return processed_data
    
    def fetch_all_stock_codes(self):
        """
        获取所有股票代码
        """
        logger.info("开始获取所有股票代码")
        return self.data_fetcher.get_stock_list()
    
    def batch_fetch(self, stock_codes: list, start_date: str, end_date: str, frequency: str = "d"):
        """
        批量获取多只股票数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
        """
        logger.info(f"开始批量获取 {len(stock_codes)} 只股票数据")
        
        results = {}
        success_count = 0
        
        for stock_code in stock_codes:
            try:
                result = self.fetch_stock_data(stock_code, start_date, end_date, frequency)
                results[stock_code] = result
                success_count += 1
                logger.info(f"股票 {stock_code} 数据获取完成")
            except Exception as e:
                logger.error(f"获取股票 {stock_code} 数据失败: {str(e)}")
                results[stock_code] = None
        
        logger.info(f"批量获取完成，成功获取 {success_count} 只股票数据，失败 {len(stock_codes) - success_count} 只股票数据")
        return results


def parse_arguments():
    """
    从配置文件读取参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    from argparse import Namespace
    
    # 从配置中读取参数
    config = get_config()
    
    # 创建参数命名空间
    args = Namespace()
    
    # 操作类型
    args.operation = config.get("operation", "fetch")
    
    # 股票相关参数（从sample_data或backtest节点读取）
    sample_data = config.get("sample_data", {})
    backtest = config.get("backtest", {})
    
    # 股票代码（优先从sample_data.symbol读取）
    args.stock_code = sample_data.get("symbol")
    
    # 日期范围（优先从backtest读取）
    args.start_date = backtest.get("start_date")
    args.end_date = backtest.get("end_date")
    
    # 频率（优先从backtest读取）
    args.frequency = backtest.get("frequency", "d")
    
    # 股票列表路径
    args.list = config.get("stock_list_path")
    
    logger.info(f"从配置文件读取参数: 操作={args.operation}, 股票代码={args.stock_code}, 日期范围={args.start_date} 至 {args.end_date}")
    
    return args


def main():
    """
    主函数
    """
    logger.info("股票数据获取程序启动")
    
    # 加载配置文件
    load_config("config.json")
    
    # 解析参数（从配置文件读取）
    args = parse_arguments()
    
    # 创建股票数据获取器实例
    fetcher = StockFetcher()
    
    # 根据配置文件中的操作类型执行相应操作
    if args.operation == "fetch":
        # 获取单只股票数据
        if not all([args.stock_code, args.start_date, args.end_date]):
            logger.error("fetch 操作需要在配置文件中提供 stock_code, start_date, end_date 参数")
            return
        fetcher.fetch_stock_data(args.stock_code, args.start_date, args.end_date, args.frequency)
    
    elif args.operation == "batch-fetch":
        # 批量获取股票数据
        if not all([args.start_date, args.end_date]):
            logger.error("batch-fetch 操作需要在配置文件中提供 start_date, end_date 参数")
            return
        
        if args.list:
            # 从文件读取股票代码列表
            with open(args.list, 'r', encoding='utf-8') as f:
                stock_codes = [line.strip() for line in f if line.strip()]
        else:
            # 获取所有股票代码
            stock_list = fetcher.fetch_all_stock_codes()
            stock_codes = [stock[0] for stock in stock_list]
        
        fetcher.batch_fetch(stock_codes, args.start_date, args.end_date, args.frequency)
    
    elif args.operation == "get-codes":
        # 获取所有股票代码
        stock_list = fetcher.fetch_all_stock_codes()
        logger.info(f"获取到 {len(stock_list)} 只股票代码")
        for stock in stock_list:
            print(f"{stock[0]} - {stock[1]}")
    
    else:
        logger.error(f"不支持的操作类型: {args.operation}")
    
    logger.info("股票数据获取程序结束")


if __name__ == "__main__":
    main()
