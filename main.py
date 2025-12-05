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
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="股票分析程序")
    
    # 配置文件参数
    parser.add_argument("-c", "--config", type=str, help="配置文件路径")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 获取股票数据命令
    fetch_parser = subparsers.add_parser("fetch", help="获取股票数据")
    fetch_parser.add_argument("stock_code", type=str, help="股票代码")
    fetch_parser.add_argument("start_date", type=str, help="开始日期 (YYYY-MM-DD)")
    fetch_parser.add_argument("end_date", type=str, help="结束日期 (YYYY-MM-DD)")
    fetch_parser.add_argument("-f", "--frequency", type=str, default="d", 
                            choices=["d", "w", "m"], help="数据频率 (d: 日线, w: 周线, m: 月线)")
    
    # 分析股票命令
    analyze_parser = subparsers.add_parser("analyze", help="分析股票")
    analyze_parser.add_argument("stock_code", type=str, help="股票代码")
    analyze_parser.add_argument("start_date", type=str, help="开始日期 (YYYY-MM-DD)")
    analyze_parser.add_argument("end_date", type=str, help="结束日期 (YYYY-MM-DD)")
    
    # 批量分析命令
    batch_parser = subparsers.add_parser("batch", help="批量分析股票")
    batch_parser.add_argument("start_date", type=str, help="开始日期 (YYYY-MM-DD)")
    batch_parser.add_argument("end_date", type=str, help="结束日期 (YYYY-MM-DD)")
    batch_parser.add_argument("-l", "--list", type=str, help="股票代码列表文件路径")
    
    # 获取所有股票代码命令
    subparsers.add_parser("get_codes", help="获取所有股票代码")
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    logger.info("股票分析程序启动")
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 创建股票分析器实例
    analyzer = StockAnalyzer(args.config)
    
    # 根据命令执行相应操作
    if args.command == "fetch":
        # 获取股票数据
        analyzer.fetch_stock_data(args.stock_code, args.start_date, args.end_date, args.frequency)
    
    elif args.command == "analyze":
        # 分析股票
        analyzer.analyze_stock(args.stock_code, args.start_date, args.end_date)
    
    elif args.command == "batch":
        # 批量分析股票
        if args.list:
            # 从文件读取股票代码列表
            with open(args.list, 'r', encoding='utf-8') as f:
                stock_codes = [line.strip() for line in f if line.strip()]
        else:
            # 获取所有股票代码
            stock_list = analyzer.fetch_all_stock_codes()
            stock_codes = [stock[0] for stock in stock_list]
        
        analyzer.batch_analyze(stock_codes, args.start_date, args.end_date)
    
    elif args.command == "get_codes":
        # 获取所有股票代码
        stock_list = analyzer.fetch_all_stock_codes()
        logger.info(f"获取到 {len(stock_list)} 只股票代码")
        for stock in stock_list:
            print(f"{stock[0]} - {stock[1]}")
    
    else:
        # 没有指定命令，显示帮助信息
        print("请指定命令，使用 --help 查看帮助")
    
    logger.info("股票分析程序结束")


if __name__ == "__main__":
    main()
