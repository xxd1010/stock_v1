#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票分析程序主入口

整合所有模块，提供完整的股票分析功能
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
logger = get_logger("main")


class StockAnalyzer:
    """
    股票分析器主类
    
    整合所有功能模块，提供完整的股票分析功能
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化股票分析器
        
        Args:
            config_path: 配置文件路径
        """
        logger.info("初始化股票分析器")
        
        # 加载配置
        if config_path:
            load_config(config_path)
        
        # 获取配置
        self.config = get_config()
        
        # 验证配置
        if not self.config.validate_config():
            logger.error("配置验证失败，程序退出")
            sys.exit(1)
        
        # 初始化各模块
        self.data_fetcher = BaoStockDataFetcher()
        self.data_preprocessor = DataPreprocessor()
        from technical_indicators import TechnicalIndicators
        self.technical_indicators = TechnicalIndicators()
        from trend_analysis import TrendAnalysis
        self.trend_analyzer = TrendAnalysis()
        from visualization import Visualization
        self.visualizer = Visualization()
        from report_generator import ReportGenerator
        self.report_generator = ReportGenerator()
        
        logger.info("股票分析器初始化完成")
    
    def fetch_stock_data(self, stock_code: str, start_date: str, end_date: str, frequency: str = "d"):
        """
        获取股票数据
        
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
    
    def analyze_stock(self, stock_code: str, start_date: str, end_date: str):
        """
        完整的股票分析流程
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        logger.info(f"开始完整的股票分析: {stock_code}")
        
        # 1. 获取数据
        stock_data = self.fetch_stock_data(stock_code, start_date, end_date)
        
        if stock_data is None:
            logger.error(f"股票分析失败: 未获取到数据")
            return None
        
        # 2. 计算技术指标
        logger.info(f"开始计算股票 {stock_code} 的技术指标")
        stock_data_with_indicators = self.technical_indicators.calculate_all_indicators(stock_data)
        logger.info(f"股票 {stock_code} 的技术指标计算完成")
        
        # 3. 趋势分析
        logger.info(f"开始分析股票 {stock_code} 的趋势")
        stock_data_with_trend, support_levels, resistance_levels, latest_trend = self.trend_analyzer.analyze_trend(stock_data_with_indicators)
        logger.info(f"股票 {stock_code} 的趋势分析完成，当前趋势: {latest_trend}")
        logger.info(f"支撑位: {support_levels}, 阻力位: {resistance_levels}")
        
        # 4. 可视化
        logger.info(f"开始生成股票 {stock_code} 的可视化图表")
        chart_paths = self.visualizer.generate_all_charts(stock_data_with_trend, stock_code)
        logger.info(f"股票 {stock_code} 的可视化图表生成完成，共生成 {len(chart_paths)} 个图表")
        
        # 5. 生成报告
        logger.info(f"开始生成股票 {stock_code} 的趋势分析报告")
        trend_report = self.trend_analyzer.generate_trend_report(stock_data_with_trend, stock_code)
        logger.info(f"股票 {stock_code} 的趋势分析报告生成完成")
        
        # 将图表路径添加到报告中
        trend_report['chart_paths'] = chart_paths
        
        # 6. 生成并导出完整报告
        logger.info(f"开始生成并导出股票 {stock_code} 的完整分析报告")
        report_results = self.report_generator.generate_and_export_report(stock_data_with_trend, trend_report)
        logger.info(f"股票 {stock_code} 的完整分析报告生成和导出完成")
        
        # 打印报告摘要
        logger.info(f"报告摘要: 股票 {stock_code}，当前趋势: {trend_report['latest_trend']}，投资建议: {trend_report['investment_suggestion']}")
        
        # 打印导出结果
        for fmt, path in report_results['export_results'].items():
            if path and isinstance(path, str) and not path.startswith("Error"):
                logger.info(f"报告已导出为 {fmt} 格式: {path}")
            else:
                logger.error(f"报告导出为 {fmt} 格式失败: {path}")
        
        logger.info(f"股票分析完成: {stock_code}")
        
        # 返回分析结果和报告
        return {
            "stock_data": stock_data_with_trend,
            "trend_report": trend_report,
            "full_report": report_results['report'],
            "export_results": report_results['export_results'],
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "latest_trend": latest_trend
        }
    
    def batch_analyze(self, stock_codes: list, start_date: str, end_date: str):
        """
        批量分析多只股票
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        logger.info(f"开始批量分析 {len(stock_codes)} 只股票")
        
        results = {}
        success_count = 0
        
        for stock_code in stock_codes:
            try:
                result = self.analyze_stock(stock_code, start_date, end_date)
                results[stock_code] = result
                success_count += 1
                logger.info(f"股票 {stock_code} 分析完成")
            except Exception as e:
                logger.error(f"分析股票 {stock_code} 失败: {str(e)}")
                results[stock_code] = {
                    "error": str(e),
                    "stock_data": None,
                    "trend_report": None,
                    "support_levels": [],
                    "resistance_levels": [],
                    "latest_trend": "Unknown"
                }
        
        logger.info(f"批量分析完成，成功分析 {success_count} 只股票，失败 {len(stock_codes) - success_count} 只股票")
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
    
    # 股票相关参数
    args.stock_code = config.get("stock_code")
    args.start_date = config.get("start_date")
    args.end_date = config.get("end_date")
    args.frequency = config.get("frequency", "d")
    args.list = config.get("stock_list_path")
    
    logger.info(f"从配置文件读取参数: 操作={args.operation}, 股票代码={args.stock_code}, 日期范围={args.start_date} 至 {args.end_date}")
    
    return args


def main():
    """
    主函数
    """
    logger.info("股票分析程序启动")
    
    # 加载配置文件
    load_config("config.json")
    
    # 解析参数（从配置文件读取）
    args = parse_arguments()
    
    # 创建股票分析器实例
    analyzer = StockAnalyzer()
    
    # 根据配置文件中的操作类型执行相应操作
    if args.operation == "fetch":
        # 获取股票数据
        if not all([args.stock_code, args.start_date, args.end_date]):
            logger.error("fetch 操作需要在配置文件中提供 stock_code, start_date, end_date 参数")
            return
        analyzer.fetch_stock_data(args.stock_code, args.start_date, args.end_date, args.frequency)
    
    elif args.operation == "analyze":
        # 分析股票
        if not all([args.stock_code, args.start_date, args.end_date]):
            logger.error("analyze 操作需要在配置文件中提供 stock_code, start_date, end_date 参数")
            return
        analyzer.analyze_stock(args.stock_code, args.start_date, args.end_date)
    
    elif args.operation == "batch":
        # 批量分析股票
        if not all([args.start_date, args.end_date]):
            logger.error("batch 操作需要在配置文件中提供 start_date, end_date 参数")
            return
        
        if args.list:
            # 从文件读取股票代码列表
            with open(args.list, 'r', encoding='utf-8') as f:
                stock_codes = [line.strip() for line in f if line.strip()]
        else:
            # 获取所有股票代码
            stock_list = analyzer.fetch_all_stock_codes()
            stock_codes = [stock[0] for stock in stock_list]
        
        analyzer.batch_analyze(stock_codes, args.start_date, args.end_date)
    
    elif args.operation == "get-codes":
        # 获取所有股票代码
        stock_list = analyzer.fetch_all_stock_codes()
        logger.info(f"获取到 {len(stock_list)} 只股票代码")
        for stock in stock_list:
            print(f"{stock[0]} - {stock[1]}")
    
    else:
        logger.error(f"不支持的操作类型: {args.operation}")
    
    logger.info("股票分析程序结束")


if __name__ == "__main__":
    main()
