#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化模块

生成股票数据的可视化图表，如K线图、趋势图等
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from log_utils import get_logger
from config_manager import get_config
import os

# 获取日志记录器
logger = get_logger("visualization")


class Visualization:
    """
    可视化类
    
    生成股票数据的可视化图表
    """
    
    def __init__(self):
        """
        初始化可视化类
        """
        logger.info("初始化可视化模块")
        
        # 获取配置
        self.config = get_config()
        
        # 可视化配置
        self.default_chart_type = self.config.get("visualization.default_chart_type", "candlestick")
        self.show_grid = self.config.get("visualization.show_grid", True)
        self.theme = self.config.get("visualization.theme", "light")
        self.plotly_api_key = self.config.get("visualization.plotly_api_key", "")
        
        # 设置中文字体支持
        plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False
        
        logger.info("可视化模块初始化完成")
    
    def plot_candlestick_chart(self, df: pd.DataFrame, stock_code: str, save_path: str = None, show: bool = True) -> str:
        """
        绘制K线图
        
        Args:
            df: 股票数据DataFrame
            stock_code: 股票代码
            save_path: 图表保存路径，None表示不保存
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的K线图")
        
        # 创建图形
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        )])
        
        # 添加标题和标签
        fig.update_layout(
            title=f'{stock_code} K线图',
            xaxis_title='日期',
            yaxis_title='价格',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"K线图已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的K线图绘制完成")
        return save_path or ""
    
    def plot_candlestick_with_ma(self, df: pd.DataFrame, stock_code: str, ma_periods: list = None, save_path: str = None, show: bool = True) -> str:
        """
        绘制带均线的K线图
        
        Args:
            df: 包含均线数据的股票数据
            stock_code: 股票代码
            ma_periods: 显示的均线周期列表
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的带均线K线图")
        
        if ma_periods is None:
            ma_periods = [5, 10, 20]
        
        # 创建图形
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        )])
        
        # 添加均线
        for period in ma_periods:
            ma_column = f'MA{period}'
            if ma_column in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[ma_column],
                    name=ma_column,
                    line=dict(width=1)
                ))
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} K线图（带均线）',
            xaxis_title='日期',
            yaxis_title='价格',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"带均线K线图已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的带均线K线图绘制完成")
        return save_path or ""
    
    def plot_macd_chart(self, df: pd.DataFrame, stock_code: str, save_path: str = None, show: bool = True) -> str:
        """
        绘制MACD指标图
        
        Args:
            df: 包含MACD数据的股票数据
            stock_code: 股票代码
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的MACD指标图")
        
        # 检查MACD数据是否完整
        if 'MACD' not in df.columns or 'MACD_Signal' not in df.columns or 'MACD_Hist' not in df.columns:
            logger.error(f"股票 {stock_code} 的MACD数据不完整，无法绘制MACD图")
            return ""
        
        # 创建子图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ), row=1, col=1)
        
        # 添加MACD线和信号线
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MACD'],
            name='MACD',
            line=dict(color='blue', width=1)
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MACD_Signal'],
            name='信号线',
            line=dict(color='red', width=1)
        ), row=2, col=1)
        
        # 添加MACD柱状图
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['MACD_Hist'],
            name='MACD柱状图',
            marker_color=df['MACD_Hist'].apply(lambda x: 'green' if x > 0 else 'red')
        ), row=2, col=1)
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} K线图与MACD指标',
            yaxis_title='价格',
            yaxis2_title='MACD',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"MACD指标图已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的MACD指标图绘制完成")
        return save_path or ""
    
    def plot_rsi_chart(self, df: pd.DataFrame, stock_code: str, rsi_periods: list = None, save_path: str = None, show: bool = True) -> str:
        """
        绘制RSI指标图
        
        Args:
            df: 包含RSI数据的股票数据
            stock_code: 股票代码
            rsi_periods: 显示的RSI周期列表
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的RSI指标图")
        
        if rsi_periods is None:
            rsi_periods = [6, 12, 24]
        
        # 创建子图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ), row=1, col=1)
        
        # 添加RSI线
        for period in rsi_periods:
            rsi_column = f'RSI{period}'
            if rsi_column in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[rsi_column],
                    name=rsi_column,
                    line=dict(width=1)
                ), row=2, col=1)
        
        # 添加RSI阈值线
        fig.add_hline(y=70, line_dash="dash", line_color="red", name="超买线", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", name="超卖线", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", name="中线", row=2, col=1)
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} K线图与RSI指标',
            yaxis_title='价格',
            yaxis2_title='RSI',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"RSI指标图已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的RSI指标图绘制完成")
        return save_path or ""
    
    def plot_volatility_chart(self, df: pd.DataFrame, stock_code: str, save_path: str = None, show: bool = True) -> str:
        """
        绘制波动率图表
        
        Args:
            df: 包含波动率数据的股票数据
            stock_code: 股票代码
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的波动率图表")
        
        # 检查波动率数据是否存在
        if 'Volatility' not in df.columns:
            logger.error(f"股票 {stock_code} 的波动率数据不存在，无法绘制波动率图表")
            return ""
        
        # 创建图形
        fig = go.Figure()
        
        # 添加价格线
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['close'],
            name='收盘价',
            yaxis='y1'
        ))
        
        # 添加波动率线
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['Volatility'],
            name='波动率',
            yaxis='y2',
            line=dict(color='red', width=1)
        ))
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} 价格与波动率',
            xaxis_title='日期',
            yaxis_title='价格',
            yaxis2=dict(
                title='波动率 (%)',
                overlaying='y',
                side='right'
            ),
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"波动率图表已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的波动率图表绘制完成")
        return save_path or ""
    
    def plot_bollinger_bands(self, df: pd.DataFrame, stock_code: str, save_path: str = None, show: bool = True) -> str:
        """
        绘制布林带图表
        
        Args:
            df: 包含布林带数据的股票数据
            stock_code: 股票代码
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的布林带图表")
        
        # 检查布林带数据是否完整
        if 'BB_Upper' not in df.columns or 'BB_Mid' not in df.columns or 'BB_Lower' not in df.columns:
            logger.error(f"股票 {stock_code} 的布林带数据不完整，无法绘制布林带图表")
            return ""
        
        # 创建图形
        fig = go.Figure()
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ))
        
        # 添加布林带上轨
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['BB_Upper'],
            name='上轨',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        # 添加布林带中轨
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['BB_Mid'],
            name='中轨',
            line=dict(color='blue', width=1)
        ))
        
        # 添加布林带下轨
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['BB_Lower'],
            name='下轨',
            line=dict(color='green', width=1, dash='dash')
        ))
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} 布林带图表',
            xaxis_title='日期',
            yaxis_title='价格',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"布林带图表已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的布林带图表绘制完成")
        return save_path or ""
    
    def plot_volume_chart(self, df: pd.DataFrame, stock_code: str, save_path: str = None, show: bool = True) -> str:
        """
        绘制成交量图表
        
        Args:
            df: 包含成交量数据的股票数据
            stock_code: 股票代码
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的成交量图表")
        
        # 创建子图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ), row=1, col=1)
        
        # 添加成交量柱状图
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='成交量',
            marker_color=df['close'].diff().apply(lambda x: 'green' if x > 0 else 'red')
        ), row=2, col=1)
        
        # 添加成交量均线
        if 'MAVOL5' in df.columns and 'MAVOL10' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['MAVOL5'],
                name='成交量5日均线',
                line=dict(color='blue', width=1)
            ), row=2, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['MAVOL10'],
                name='成交量10日均线',
                line=dict(color='red', width=1)
            ), row=2, col=1)
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} K线图与成交量',
            xaxis_title='日期',
            yaxis_title='价格',
            yaxis2_title='成交量',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"成交量图表已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的成交量图表绘制完成")
        return save_path or ""
    
    def plot_trend_analysis(self, df: pd.DataFrame, stock_code: str, save_path: str = None, show: bool = True) -> str:
        """
        绘制趋势分析图表
        
        Args:
            df: 包含趋势信息的股票数据
            stock_code: 股票代码
            save_path: 图表保存路径
            show: 是否显示图表
            
        Returns:
            str: 图表保存路径或空字符串
        """
        logger.info(f"开始绘制股票 {stock_code} 的趋势分析图表")
        
        # 创建子图
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        
        # 添加K线图和趋势线
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ), row=1, col=1)
        
        # 添加MA5和MA20
        if 'MA5' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['MA5'],
                name='MA5',
                line=dict(color='blue', width=1)
            ), row=1, col=1)
        
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['MA20'],
                name='MA20',
                line=dict(color='red', width=1)
            ), row=1, col=1)
        
        # 添加RSI
        if 'RSI12' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['RSI12'],
                name='RSI12',
                line=dict(color='purple', width=1)
            ), row=2, col=1)
            
            # 添加RSI阈值
            fig.add_hline(y=70, line_dash="dash", line_color="red", name="超买线", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", name="超卖线", row=2, col=1)
        
        # 添加MACD
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns and 'MACD_Hist' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['MACD'],
                name='MACD',
                line=dict(color='blue', width=1)
            ), row=3, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['MACD_Signal'],
                name='信号线',
                line=dict(color='red', width=1)
            ), row=3, col=1)
            
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df['MACD_Hist'],
                name='MACD柱状图',
                marker_color=df['MACD_Hist'].apply(lambda x: 'green' if x > 0 else 'red')
            ), row=3, col=1)
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} 趋势分析图表',
            xaxis_title='日期',
            yaxis_title='价格',
            yaxis2_title='RSI',
            yaxis3_title='MACD',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template=self.theme
        )
        
        # 保存图表
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.write_image(save_path)
            logger.info(f"趋势分析图表已保存到: {save_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        logger.info(f"股票 {stock_code} 的趋势分析图表绘制完成")
        return save_path or ""
    
    def generate_all_charts(self, df: pd.DataFrame, stock_code: str, output_dir: str = "charts") -> list:
        """
        生成所有类型的图表
        
        Args:
            df: 股票数据DataFrame
            stock_code: 股票代码
            output_dir: 图表输出目录
            
        Returns:
            list: 图表文件路径列表
        """
        logger.info(f"开始为股票 {stock_code} 生成所有图表")
        
        # 确保输出目录存在
        output_dir = os.path.join(output_dir, stock_code)
        os.makedirs(output_dir, exist_ok=True)
        
        chart_paths = []
        
        # 生成K线图
        kline_path = os.path.join(output_dir, f"{stock_code}_kline.png")
        chart_paths.append(self.plot_candlestick_chart(df, stock_code, kline_path, show=False))
        
        # 生成带均线的K线图
        kline_ma_path = os.path.join(output_dir, f"{stock_code}_kline_ma.png")
        chart_paths.append(self.plot_candlestick_with_ma(df, stock_code, [5, 10, 20], kline_ma_path, show=False))
        
        # 生成MACD图表
        macd_path = os.path.join(output_dir, f"{stock_code}_macd.png")
        chart_paths.append(self.plot_macd_chart(df, stock_code, macd_path, show=False))
        
        # 生成RSI图表
        rsi_path = os.path.join(output_dir, f"{stock_code}_rsi.png")
        chart_paths.append(self.plot_rsi_chart(df, stock_code, [12], rsi_path, show=False))
        
        # 生成布林带图表
        boll_path = os.path.join(output_dir, f"{stock_code}_bollinger.png")
        chart_paths.append(self.plot_bollinger_bands(df, stock_code, boll_path, show=False))
        
        # 生成成交量图表
        volume_path = os.path.join(output_dir, f"{stock_code}_volume.png")
        chart_paths.append(self.plot_volume_chart(df, stock_code, volume_path, show=False))
        
        # 生成趋势分析图表
        trend_path = os.path.join(output_dir, f"{stock_code}_trend.png")
        chart_paths.append(self.plot_trend_analysis(df, stock_code, trend_path, show=False))
        
        # 过滤空路径
        chart_paths = [path for path in chart_paths if path]
        
        logger.info(f"股票 {stock_code} 的所有图表生成完成，共 {len(chart_paths)} 个图表")
        
        return chart_paths


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_data = {
        'date': pd.date_range(start='2023-01-01', periods=100),
        'close': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 101,
        'low': np.random.randn(100).cumsum() + 99,
        'open': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, size=100)
    }
    
    test_df = pd.DataFrame(test_data)
    
    # 添加一些简单的技术指标
    test_df['MA5'] = test_df['close'].rolling(window=5).mean()
    test_df['MA10'] = test_df['close'].rolling(window=10).mean()
    test_df['MA20'] = test_df['close'].rolling(window=20).mean()
    
    # 创建可视化实例
    viz = Visualization()
    
    # 绘制K线图
    viz.plot_candlestick_chart(test_df, "TEST.000001", save_path="test_kline.png", show=False)
    
    # 绘制带均线的K线图
    viz.plot_candlestick_with_ma(test_df, "TEST.000001", [5, 10, 20], save_path="test_kline_ma.png", show=False)
    
    print("测试图表绘制完成")
