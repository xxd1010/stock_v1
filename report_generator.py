#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成与导出模块

生成股票分析报告并支持多种格式导出
"""

import pandas as pd
import os
import json
from datetime import datetime
from log_utils import get_logger
from config_manager import get_config

# 尝试导入必要的库
try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("reportlab库未安装，PDF导出功能将不可用")
    REPORTLAB_AVAILABLE = False

try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    logger.warning("jinja2库未安装，HTML报告生成功能将不可用")
    JINJA2_AVAILABLE = False

# 获取日志记录器
logger = get_logger("report_generator")


class ReportGenerator:
    """
    报告生成器类
    
    生成股票分析报告并支持多种格式导出
    """
    
    def __init__(self):
        """
        初始化报告生成器
        """
        logger.info("初始化报告生成模块")
        
        # 获取配置
        self.config = get_config()
        
        # 报告配置
        self.default_template = self.config.get("report_generator.default_template", "basic")
        self.export_formats = self.config.get("report_generator.export_formats", ["excel", "pdf", "html"])
        self.report_output_dir = self.config.get("report_generator.report_output_dir", "reports")
        
        # 确保输出目录存在
        os.makedirs(self.report_output_dir, exist_ok=True)
        
        # 初始化模板环境
        self.template_env = None
        if JINJA2_AVAILABLE:
            self._init_template_env()
        
        logger.info("报告生成模块初始化完成")
    
    def _init_template_env(self):
        """
        初始化模板环境
        """
        # 创建模板加载器
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        # 创建模板环境
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # 添加自定义过滤器
        self.template_env.filters['basename'] = os.path.basename
        
        # 检查基本模板是否存在，如果不存在则创建
        basic_template_path = os.path.join(template_dir, "basic_report.html")
        if not os.path.exists(basic_template_path):
            self._create_default_template(basic_template_path)
    
    def _create_default_template(self, template_path: str):
        """
        创建默认模板
        
        Args:
            template_path: 模板路径
        """
        default_template = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>{{ report.stock_code }} 股票分析报告</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                    border-bottom: 2px solid #333;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #555;
                    margin-top: 30px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }
                .info-section {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin: 20px 0;
                }
                .info-item {
                    flex: 1;
                    min-width: 200px;
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                }
                .info-label {
                    font-weight: bold;
                    color: #666;
                }
                .chart-section {
                    margin: 30px 0;
                    text-align: center;
                }
                .chart {
                    max-width: 100%;
                    height: auto;
                    margin: 20px 0;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                .analysis-section {
                    background-color: #f0f8ff;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .investment-suggestion {
                    background-color: #fff3cd;
                    padding: 20px;
                    border-left: 5px solid #ffc107;
                    margin: 20px 0;
                    font-weight: bold;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{{ report.stock_code }} 股票分析报告</h1>
                
                <div class="info-section">
                    <div class="info-item">
                        <div class="info-label">分析日期:</div>
                        <div>{{ report.analysis_date }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">最新数据日期:</div>
                        <div>{{ report.latest_date }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">最新价格:</div>
                        <div>{{ report.latest_price }} 元</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">当前趋势:</div>
                        <div>{{ report.latest_trend }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">趋势强度:</div>
                        <div>{{ report.trend_strength }}%</div>
                    </div>
                </div>
                
                <h2>一、技术指标分析</h2>
                <table>
                    <tr>
                        <th>指标名称</th>
                        <th>当前值</th>
                        <th>分析</th>
                    </tr>
                    <tr>
                        <td>RSI (12日)</td>
                        <td>{{ report.technical_indicators.rsi }}</td>
                        <td>{% if report.technical_indicators.rsi > 70 %}超买{% elif report.technical_indicators.rsi < 30 %}超卖{% else %}正常{% endif %}</td>
                    </tr>
                    <tr>
                        <td>MACD</td>
                        <td>{{ report.technical_indicators.macd }}</td>
                        <td>{% if report.technical_indicators.macd > 0 %}多头{% else %}空头{% endif %}</td>
                    </tr>
                    <tr>
                        <td>MACD柱状图</td>
                        <td>{{ report.technical_indicators.macd_hist }}</td>
                        <td>{% if report.technical_indicators.macd_hist > 0 %}上涨动能{% else %}下跌动能{% endif %}</td>
                    </tr>
                    <tr>
                        <td>布林带位置</td>
                        <td>{{ report.technical_indicators.bollinger_position | round(2) }}</td>
                        <td>{% if report.technical_indicators.bollinger_position > 0.8 %}接近上轨{% elif report.technical_indicators.bollinger_position < 0.2 %}接近下轨{% else %}中轨附近{% endif %}</td>
                    </tr>
                </table>
                
                <h2>二、支撑位与阻力位</h2>
                <div class="info-section">
                    <div class="info-item">
                        <div class="info-label">支撑位:</div>
                        <div>{{ report.support_levels | join(', ') }} 元</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">阻力位:</div>
                        <div>{{ report.resistance_levels | join(', ') }} 元</div>
                    </div>
                </div>
                
                <h2>三、K线形态分析</h2>
                <div class="info-section">
                    <div class="info-item">
                        <div class="info-label">最新K线形态:</div>
                        <div>{{ report.latest_candlestick_pattern }}</div>
                    </div>
                </div>
                
                <h2>四、图表分析</h2>
                {% for chart_path in report.chart_paths %}
                    <div class="chart-section">
                        <h3>{{ chart_path | basename }}</h3>
                        <img src="{{ chart_path }}" alt="图表" class="chart">
                    </div>
                {% endfor %}
                
                <h2>五、投资建议</h2>
                <div class="investment-suggestion">
                    {{ report.investment_suggestion }}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(default_template)
        
        logger.info(f"创建默认模板: {template_path}")
    
    def generate_report(self, stock_data: pd.DataFrame, trend_report: dict, template: str = "basic") -> dict:
        """
        生成完整的股票分析报告
        
        Args:
            stock_data: 股票数据
            trend_report: 趋势分析报告
            template: 报告模板名称
            
        Returns:
            dict: 完整的股票分析报告
        """
        logger.info(f"开始生成股票 {trend_report['stock_code']} 的分析报告")
        
        # 构建完整报告
        report = {
            **trend_report,
            "full_data": stock_data.to_dict(orient='records'),
            "report_generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "template": template
        }
        
        logger.info(f"股票 {trend_report['stock_code']} 的分析报告生成完成")
        return report
    
    def export_to_excel(self, report: dict, output_path: str = None) -> str:
        """
        导出报告为Excel格式
        
        Args:
            report: 完整的股票分析报告
            output_path: 输出路径，None表示自动生成
            
        Returns:
            str: 导出文件路径
        """
        logger.info(f"开始将股票 {report['stock_code']} 的报告导出为Excel格式")
        
        # 自动生成输出路径
        if output_path is None:
            output_path = os.path.join(
                self.report_output_dir,
                f"{report['stock_code']}_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建Excel写入器
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # 写入基本信息
            info_df = pd.DataFrame([{
                "股票代码": report['stock_code'],
                "分析日期": report['analysis_date'],
                "最新数据日期": report['latest_date'],
                "最新价格": report['latest_price'],
                "当前趋势": report['latest_trend'],
                "趋势强度": report['trend_strength'],
                "投资建议": report['investment_suggestion']
            }])
            info_df.to_excel(writer, sheet_name='基本信息', index=False)
            
            # 写入技术指标
            indicators_df = pd.DataFrame([report['technical_indicators']])
            indicators_df.to_excel(writer, sheet_name='技术指标', index=False)
            
            # 写入支撑位和阻力位
            levels_df = pd.DataFrame({
                "支撑位": report['support_levels'],
                "阻力位": report['resistance_levels']
            })
            levels_df.to_excel(writer, sheet_name='支撑阻力位', index=False)
            
            # 写入完整数据
            full_data_df = pd.DataFrame(report['full_data'])
            full_data_df.to_excel(writer, sheet_name='完整数据', index=False)
        
        logger.info(f"股票 {report['stock_code']} 的报告已导出为Excel格式: {output_path}")
        return output_path
    
    def export_to_pdf(self, report: dict, output_path: str = None) -> str:
        """
        导出报告为PDF格式
        
        Args:
            report: 完整的股票分析报告
            output_path: 输出路径，None表示自动生成
            
        Returns:
            str: 导出文件路径或空字符串
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab库未安装，无法导出PDF")
            return ""
        
        logger.info(f"开始将股票 {report['stock_code']} 的报告导出为PDF格式")
        
        # 自动生成输出路径
        if output_path is None:
            output_path = os.path.join(
                self.report_output_dir,
                f"{report['stock_code']}_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建PDF文档
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        
        # 获取样式表
        styles = getSampleStyleSheet()
        
        # 创建自定义样式
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=24,
            alignment=1,  # 居中
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            spaceBefore=15,
            spaceAfter=10
        )
        
        heading2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=10,
            spaceAfter=5
        )
        
        normal_style = styles['Normal']
        normal_style.alignment = 0  # 左对齐
        normal_style.spaceAfter = 5
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold'
        )
        
        # 构建报告内容
        content = []
        
        # 添加标题
        content.append(Paragraph(f"{report['stock_code']} 股票分析报告", title_style))
        
        # 添加基本信息表格
        info_data = [
            ['分析日期:', report['analysis_date']],
            ['最新数据日期:', report['latest_date']],
            ['最新价格:', f"{report['latest_price']} 元"],
            ['当前趋势:', report['latest_trend']],
            ['趋势强度:', f"{report['trend_strength']}%"],
            ['投资建议:', report['investment_suggestion']]
        ]
        
        info_table = Table(info_data, colWidths=[150, 300])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(Spacer(1, 20))
        content.append(info_table)
        
        # 添加技术指标分析
        content.append(Spacer(1, 30))
        content.append(Paragraph('一、技术指标分析', heading_style))
        
        indicators_data = [
            ['指标名称', '当前值', '分析'],
            ['RSI (12日)', f"{report['technical_indicators']['rsi']}", 
             "超买" if report['technical_indicators']['rsi'] > 70 else "超卖" if report['technical_indicators']['rsi'] < 30 else "正常"],
            ['MACD', f"{report['technical_indicators']['macd']}", 
             "多头" if report['technical_indicators']['macd'] > 0 else "空头"],
            ['MACD柱状图', f"{report['technical_indicators']['macd_hist']}", 
             "上涨动能" if report['technical_indicators']['macd_hist'] > 0 else "下跌动能"],
            ['布林带位置', f"{report['technical_indicators']['bollinger_position']:.2f}", 
             "接近上轨" if report['technical_indicators']['bollinger_position'] > 0.8 else 
             "接近下轨" if report['technical_indicators']['bollinger_position'] < 0.2 else "中轨附近"]
        ]
        
        indicators_table = Table(indicators_data, colWidths=[150, 100, 200])
        indicators_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(indicators_table)
        
        # 添加支撑位和阻力位
        content.append(Spacer(1, 30))
        content.append(Paragraph('二、支撑位与阻力位', heading_style))
        
        levels_data = [
            ['支撑位:', ', '.join(map(str, report['support_levels'])) + ' 元'],
            ['阻力位:', ', '.join(map(str, report['resistance_levels'])) + ' 元']
        ]
        
        levels_table = Table(levels_data, colWidths=[150, 300])
        levels_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(levels_table)
        
        # 添加K线形态分析
        content.append(Spacer(1, 30))
        content.append(Paragraph('三、K线形态分析', heading_style))
        content.append(Paragraph(f"最新K线形态: {report['latest_candlestick_pattern']}", normal_style))
        
        # 添加图表
        content.append(Spacer(1, 30))
        content.append(Paragraph('四、图表分析', heading_style))
        
        for chart_path in report['chart_paths']:
            if os.path.exists(chart_path):
                try:
                    img = Image(chart_path, width=6*inch, height=4*inch)
                    content.append(img)
                    content.append(Paragraph(os.path.basename(chart_path), normal_style))
                    content.append(Spacer(1, 20))
                except Exception as e:
                    logger.error(f"添加图表 {chart_path} 失败: {str(e)}")
            else:
                logger.error(f"图表文件不存在: {chart_path}")
        
        # 生成PDF
        doc.build(content)
        
        logger.info(f"股票 {report['stock_code']} 的报告已导出为PDF格式: {output_path}")
        return output_path
    
    def export_to_html(self, report: dict, output_path: str = None) -> str:
        """
        导出报告为HTML格式
        
        Args:
            report: 完整的股票分析报告
            output_path: 输出路径，None表示自动生成
            
        Returns:
            str: 导出文件路径或空字符串
        """
        if not JINJA2_AVAILABLE:
            logger.error("jinja2库未安装，无法导出HTML报告")
            return ""
        
        logger.info(f"开始将股票 {report['stock_code']} 的报告导出为HTML格式")
        
        # 自动生成输出路径
        if output_path is None:
            output_path = os.path.join(
                self.report_output_dir,
                f"{report['stock_code']}_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 加载模板
        template = self.template_env.get_template("basic_report.html")
        
        # 渲染模板
        html_content = template.render(report=report)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"股票 {report['stock_code']} 的报告已导出为HTML格式: {output_path}")
        return output_path
    
    def export_report(self, report: dict, formats: list = None, output_dir: str = None) -> dict:
        """
        导出报告到多种格式
        
        Args:
            report: 完整的股票分析报告
            formats: 导出格式列表，默认使用配置中的格式
            output_dir: 输出目录，默认使用配置中的目录
            
        Returns:
            dict: 导出结果，键为格式名称，值为导出路径
        """
        logger.info(f"开始导出股票 {report['stock_code']} 的报告")
        
        if formats is None:
            formats = self.export_formats
        
        if output_dir is not None:
            self.report_output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(self.report_output_dir, exist_ok=True)
        
        # 导出结果
        export_results = {}
        
        # 导出到各种格式
        for fmt in formats:
            try:
                if fmt == "excel":
                    export_results[fmt] = self.export_to_excel(report)
                elif fmt == "pdf":
                    export_results[fmt] = self.export_to_pdf(report)
                elif fmt == "html":
                    export_results[fmt] = self.export_to_html(report)
                else:
                    logger.error(f"不支持的导出格式: {fmt}")
                    export_results[fmt] = ""
            except Exception as e:
                logger.error(f"导出报告为 {fmt} 格式失败: {str(e)}")
                export_results[fmt] = f"Error: {str(e)}"
        
        logger.info(f"股票 {report['stock_code']} 的报告导出完成")
        return export_results
    
    def generate_and_export_report(self, stock_data: pd.DataFrame, trend_report: dict, formats: list = None) -> dict:
        """
        生成并导出完整的股票分析报告
        
        Args:
            stock_data: 股票数据
            trend_report: 趋势分析报告
            formats: 导出格式列表
            
        Returns:
            dict: 导出结果
        """
        logger.info(f"开始生成并导出股票 {trend_report['stock_code']} 的分析报告")
        
        # 生成完整报告
        full_report = self.generate_report(stock_data, trend_report)
        
        # 导出报告
        export_results = self.export_report(full_report, formats)
        
        logger.info(f"股票 {trend_report['stock_code']} 的报告生成和导出完成")
        
        return {
            "report": full_report,
            "export_results": export_results
        }


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_data = {
        'stock_code': 'TEST.000001',
        'analysis_date': '2023-10-01 15:00:00',
        'latest_date': '2023-09-30',
        'latest_price': 100.5,
        'latest_trend': '上涨',
        'support_levels': [95.0, 92.5, 90.0],
        'resistance_levels': [105.0, 110.0, 115.0],
        'trend_strength': 5.2,
        'latest_candlestick_pattern': 'Bullish Engulfing',
        'technical_indicators': {
            'rsi': 65.5,
            'macd': 2.3,
            'macd_hist': 1.2,
            'bollinger_position': 0.75
        },
        'investment_suggestion': '建议买入: 股票处于上涨趋势，RSI指标正常',
        'chart_paths': []
    }
    
    # 创建股票数据
    stock_data = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=100),
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 101,
        'low': np.random.randn(100).cumsum() + 99,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, size=100)
    })
    
    # 创建报告生成器实例
    report_generator = ReportGenerator()
    
    # 生成并导出报告
    result = report_generator.generate_and_export_report(stock_data, test_data, formats=['excel'])
    
    print("报告生成和导出结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
