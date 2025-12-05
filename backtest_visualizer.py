#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测可视化模块

为回测结果提供直观的数据可视化展示，包括资金曲线、回撤曲线、交易信号等
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import matplotlib.dates as mdates
from log_utils import get_logger


class BacktestVisualizer:
    """
    回测可视化器
    
    为回测结果提供直观的数据可视化展示
    """
    
    def __init__(self):
        """
        初始化回测可视化器
        """
        self.logger = get_logger("backtest_visualizer")
        self.logger.info("初始化回测可视化器")
        
        # 可视化参数
        self.params = {
            "style": "seaborn-v0_8-darkgrid",  # matplotlib样式
            "figsize": (12, 8),  # 默认图表大小
            "dpi": 300,  # 图片分辨率
            "font_size": 10,
            "title_font_size": 14,
            "legend_font_size": 10,
            "colors": {
                "equity": "#2196F3",  # 资金曲线颜色
                "drawdown": "#F44336",  # 回撤曲线颜色
                "benchmark": "#9C27B0",  # 基准曲线颜色
                "buy_signal": "#4CAF50",  # 买入信号颜色
                "sell_signal": "#FF5722"  # 卖出信号颜色
            }
        }
        
        # 设置matplotlib样式
        plt.style.use(self.params["style"])
        
        # 设置中文支持（必须在样式设置之后，确保覆盖样式中的字体设置）
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']  # 用于显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        self.logger.info("回测可视化器初始化完成")
    
    def _generate_filename(self, chart_type, stock_info=None):
        """
        生成统一格式的文件名
        
        Args:
            chart_type: 图表类型（如 equity_curve, drawdown 等）
            stock_info: 股票信息字典
            
        Returns:
            str: 生成的文件名
        """
        # 获取当前日期，格式为 YYYYMMDD
        current_date = datetime.now().strftime('%Y%m%d')
        
        # 构建文件名基本格式
        if stock_info:
            # 提取股票信息
            symbol = stock_info.get('symbol', 'unknown')
            name = stock_info.get('name', 'unknown')
            # 移除名称中的特殊字符，避免文件名错误
            name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            # 生成完整文件名
            filename = f"{symbol}_{name}_{chart_type}_{current_date}.png"
        else:
            # 没有股票信息时的默认文件名
            filename = f"{chart_type}_{current_date}.png"
        
        return filename
    
    def set_params(self, params):
        """
        设置可视化参数
        
        Args:
            params: 可视化参数
        """
        self.logger.info(f"设置可视化参数: {params}")
        self.params.update(params)
        
        # 更新matplotlib样式
        if "style" in params:
            plt.style.use(params["style"])
    
    def plot_equity_curve(self, account_history, benchmark_history=None, title="资金曲线", save_path=None, stock_info=None):
        """
        绘制资金曲线
        
        Args:
            account_history: 账户历史数据
            benchmark_history: 基准数据（可选）
            title: 图表标题
            save_path: 保存路径（可选）
            stock_info: 股票信息字典，包含symbol、name、start_date、end_date、frequency等信息
        """
        self.logger.info("绘制资金曲线")
        
        # 转换数据格式
        if isinstance(account_history, list):
            account_df = pd.DataFrame(account_history)
        else:
            account_df = account_history.copy()
        
        # 转换时间格式
        account_df["timestamp"] = pd.to_datetime(account_df["timestamp"])
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.params["figsize"])
        
        # 绘制策略资金曲线
        ax.plot(account_df["timestamp"], account_df["total_equity"], 
               label="策略资金", color=self.params["colors"]["equity"], linewidth=2)
        
        # 绘制基准曲线（如果提供）
        if benchmark_history is not None:
            if isinstance(benchmark_history, list):
                benchmark_df = pd.DataFrame(benchmark_history)
            else:
                benchmark_df = benchmark_history.copy()
            
            benchmark_df["timestamp"] = pd.to_datetime(benchmark_df["timestamp"])
            ax.plot(benchmark_df["timestamp"], benchmark_df["total_equity"], 
                   label="基准资金", color=self.params["colors"]["benchmark"], linewidth=2, linestyle="--")
        
        # 设置图表属性
        ax.set_title(title, fontsize=self.params["title_font_size"])
        
        # 添加股票信息（如果提供）
        if stock_info:
            # 提取股票信息
            symbol = stock_info.get('symbol', 'N/A')
            name = stock_info.get('name', 'N/A')
            start_date = stock_info.get('start_date', 'N/A')
            end_date = stock_info.get('end_date', 'N/A')
            frequency = stock_info.get('frequency', 'N/A')
            
            # 计算当前价格、价格变化和百分比变化（如果有价格数据）
            current_price = "N/A"
            price_change = "N/A"
            pct_change = "N/A"
            if 'current_price' in stock_info:
                current_price = f"{stock_info['current_price']:.2f}"
                if 'previous_price' in stock_info:
                    price_change = f"{stock_info['current_price'] - stock_info['previous_price']:.2f}"
                    pct_change = f"{(price_change / stock_info['previous_price'] * 100):.2f}%"
            
            # 构建完整的股票信息文本
            stock_info_text = f"股票代码: {symbol} | 股票名称: {name} | 当前价格: {current_price} | 价格变化: {price_change} ({pct_change})"
            stock_info_text += f" | 回测时间: {start_date} 至 {end_date} | 频率: {frequency}"
            
            ax.text(0.5, 0.95, stock_info_text, transform=ax.transAxes, 
                   horizontalalignment='center', fontsize=self.params["font_size"] - 1,
                   bbox=dict(facecolor='white', alpha=0.8, pad=5))
        
        ax.set_xlabel("时间", fontsize=self.params["font_size"])
        ax.set_ylabel("资金（元）", fontsize=self.params["font_size"])
        ax.legend(fontsize=self.params["legend_font_size"])
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        # 保存图表
        if save_path:
            # 如果save_path是目录，则生成完整文件名
            import os
            if os.path.isdir(save_path):
                filename = self._generate_filename("equity_curve", stock_info)
                save_path = os.path.join(save_path, filename)
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"资金曲线已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def plot_drawdown(self, account_history, title="回撤曲线", save_path=None, stock_info=None):
        """
        绘制回撤曲线
        
        Args:
            account_history: 账户历史数据
            title: 图表标题
            save_path: 保存路径（可选）
            stock_info: 股票信息字典，包含symbol、name、start_date、end_date、frequency等信息
        """
        self.logger.info("绘制回撤曲线")
        
        # 转换数据格式
        if isinstance(account_history, list):
            account_df = pd.DataFrame(account_history)
        else:
            account_df = account_history.copy()
        
        # 转换时间格式
        account_df["timestamp"] = pd.to_datetime(account_df["timestamp"])
        
        # 计算回撤
        equity = account_df["total_equity"]
        cumulative_returns = (equity / equity.iloc[0]) - 1
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.params["figsize"])
        
        # 绘制回撤曲线
        ax.fill_between(account_df["timestamp"], drawdown, 0, 
                      color=self.params["colors"]["drawdown"], alpha=0.7, 
                      label="回撤（%）")
        
        # 设置图表属性
        ax.set_title(title, fontsize=self.params["title_font_size"])
        
        # 添加股票信息（如果提供）
        if stock_info:
            # 提取股票信息
            symbol = stock_info.get('symbol', 'N/A')
            name = stock_info.get('name', 'N/A')
            start_date = stock_info.get('start_date', 'N/A')
            end_date = stock_info.get('end_date', 'N/A')
            frequency = stock_info.get('frequency', 'N/A')
            
            # 计算当前价格、价格变化和百分比变化（如果有价格数据）
            current_price = "N/A"
            price_change = "N/A"
            pct_change = "N/A"
            if 'current_price' in stock_info:
                current_price = f"{stock_info['current_price']:.2f}"
                if 'previous_price' in stock_info:
                    price_change = f"{stock_info['current_price'] - stock_info['previous_price']:.2f}"
                    pct_change = f"{(price_change / stock_info['previous_price'] * 100):.2f}%"
            
            # 构建完整的股票信息文本
            stock_info_text = f"股票代码: {symbol} | 股票名称: {name} | 当前价格: {current_price} | 价格变化: {price_change} ({pct_change})"
            stock_info_text += f" | 回测时间: {start_date} 至 {end_date} | 频率: {frequency}"
            
            ax.text(0.5, 0.95, stock_info_text, transform=ax.transAxes, 
                   horizontalalignment='center', fontsize=self.params["font_size"] - 1,
                   bbox=dict(facecolor='white', alpha=0.8, pad=5))
        
        ax.set_xlabel("时间", fontsize=self.params["font_size"])
        ax.set_ylabel("回撤（%）", fontsize=self.params["font_size"])
        ax.legend(fontsize=self.params["legend_font_size"])
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        # 设置y轴范围
        ax.set_ylim(drawdown.min() - 5, 0)
        
        # 标记最大回撤
        max_drawdown = drawdown.min()
        max_drawdown_date = account_df.loc[drawdown.idxmin(), "timestamp"]
        ax.annotate(f"最大回撤: {max_drawdown:.2f}%", 
                   xy=(max_drawdown_date, max_drawdown),
                   xytext=(max_drawdown_date, max_drawdown - 5),
                   arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                   fontsize=self.params["font_size"])
        
        # 保存图表
        if save_path:
            # 如果save_path是目录，则生成完整文件名
            import os
            if os.path.isdir(save_path):
                filename = self._generate_filename("drawdown", stock_info)
                save_path = os.path.join(save_path, filename)
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"回撤曲线已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def plot_returns_distribution(self, account_history, bins=50, title="收益率分布", save_path=None, stock_info=None):
        """
        绘制收益率分布直方图
        
        Args:
            account_history: 账户历史数据
            bins: 直方图 bins 数量
            title: 图表标题
            save_path: 保存路径（可选）
            stock_info: 股票信息字典，包含symbol、name、start_date、end_date、frequency等信息
        """
        self.logger.info("绘制收益率分布直方图")
        
        # 转换数据格式
        if isinstance(account_history, list):
            account_df = pd.DataFrame(account_history)
        else:
            account_df = account_history.copy()
        
        # 计算日收益率
        daily_returns = account_df["total_equity"].pct_change().dropna() * 100
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.params["figsize"])
        
        # 绘制直方图
        sns.histplot(daily_returns, bins=bins, kde=True, ax=ax, 
                    color=self.params["colors"]["equity"], alpha=0.7)
        
        # 设置图表属性
        ax.set_title(title, fontsize=self.params["title_font_size"])
        
        # 添加股票信息（如果提供）
        if stock_info:
            # 提取股票信息
            symbol = stock_info.get('symbol', 'N/A')
            name = stock_info.get('name', 'N/A')
            start_date = stock_info.get('start_date', 'N/A')
            end_date = stock_info.get('end_date', 'N/A')
            frequency = stock_info.get('frequency', 'N/A')
            
            # 计算当前价格、价格变化和百分比变化（如果有价格数据）
            current_price = "N/A"
            price_change = "N/A"
            pct_change = "N/A"
            if 'current_price' in stock_info:
                current_price = f"{stock_info['current_price']:.2f}"
                if 'previous_price' in stock_info:
                    price_change = f"{stock_info['current_price'] - stock_info['previous_price']:.2f}"
                    pct_change = f"{(price_change / stock_info['previous_price'] * 100):.2f}%"
            
            # 构建完整的股票信息文本
            stock_info_text = f"股票代码: {symbol} | 股票名称: {name} | 当前价格: {current_price} | 价格变化: {price_change} ({pct_change})"
            stock_info_text += f" | 回测时间: {start_date} 至 {end_date} | 频率: {frequency}"
            
            ax.text(0.5, 0.95, stock_info_text, transform=ax.transAxes, 
                   horizontalalignment='center', fontsize=self.params["font_size"] - 1,
                   bbox=dict(facecolor='white', alpha=0.8, pad=5))
        
        ax.set_xlabel("日收益率（%）", fontsize=self.params["font_size"])
        ax.set_ylabel("频率", fontsize=self.params["font_size"])
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        stats_text = f"均值: {daily_returns.mean():.4f}%\n"
        stats_text += f"中位数: {daily_returns.median():.4f}%\n"
        stats_text += f"标准差: {daily_returns.std():.4f}%\n"
        stats_text += f"偏度: {daily_returns.skew():.4f}\n"
        stats_text += f"峰度: {daily_returns.kurtosis():.4f}"
        
        ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
               verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
               fontsize=self.params["font_size"])
        
        # 保存图表
        if save_path:
            # 如果save_path是目录，则生成完整文件名
            import os
            if os.path.isdir(save_path):
                filename = self._generate_filename("returns_distribution", stock_info)
                save_path = os.path.join(save_path, filename)
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"收益率分布直方图已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def plot_trading_signals(self, data, signals, title="交易信号图", save_path=None, stock_info=None):
        """
        绘制交易信号图
        
        Args:
            data: 原始数据，包含价格信息
            signals: 交易信号
            title: 图表标题
            save_path: 保存路径（可选）
            stock_info: 股票信息字典，包含symbol、name、start_date、end_date、frequency等信息
        """
        self.logger.info("绘制交易信号图")
        
        # 转换数据格式
        if isinstance(data, list):
            data_df = pd.DataFrame(data)
        else:
            data_df = data.copy()
        
        if isinstance(signals, list):
            signals_df = pd.DataFrame(signals)
        else:
            signals_df = signals.copy()
        
        # 转换时间格式
        data_df["timestamp"] = pd.to_datetime(data_df["timestamp"])
        signals_df["timestamp"] = pd.to_datetime(signals_df["timestamp"])
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.params["figsize"])
        
        # 绘制价格曲线
        ax.plot(data_df["timestamp"], data_df["close"], 
               label="收盘价", color=self.params["colors"]["equity"], linewidth=2)
        
        # 绘制买入信号
        buy_signals = signals_df[signals_df["action"] == "buy"]
        if not buy_signals.empty:
            ax.scatter(buy_signals["timestamp"], buy_signals["price"], 
                      marker="^", color=self.params["colors"]["buy_signal"], 
                      s=100, label="买入信号", edgecolors='black', linewidths=0.5)
        
        # 绘制卖出信号
        sell_signals = signals_df[signals_df["action"] == "sell"]
        if not sell_signals.empty:
            ax.scatter(sell_signals["timestamp"], sell_signals["price"], 
                      marker="v", color=self.params["colors"]["sell_signal"], 
                      s=100, label="卖出信号", edgecolors='black', linewidths=0.5)
        
        # 设置图表属性
        ax.set_title(title, fontsize=self.params["title_font_size"])
        
        # 添加股票信息（如果提供）
        if stock_info:
            # 提取股票信息
            symbol = stock_info.get('symbol', 'N/A')
            name = stock_info.get('name', 'N/A')
            start_date = stock_info.get('start_date', 'N/A')
            end_date = stock_info.get('end_date', 'N/A')
            frequency = stock_info.get('frequency', 'N/A')
            
            # 计算当前价格、价格变化和百分比变化（如果有价格数据）
            current_price = "N/A"
            price_change = "N/A"
            pct_change = "N/A"
            if 'current_price' in stock_info:
                current_price = f"{stock_info['current_price']:.2f}"
                if 'previous_price' in stock_info:
                    price_change = f"{stock_info['current_price'] - stock_info['previous_price']:.2f}"
                    pct_change = f"{(price_change / stock_info['previous_price'] * 100):.2f}%"
            
            # 构建完整的股票信息文本
            stock_info_text = f"股票代码: {symbol} | 股票名称: {name} | 当前价格: {current_price} | 价格变化: {price_change} ({pct_change})"
            stock_info_text += f" | 回测时间: {start_date} 至 {end_date} | 频率: {frequency}"
            
            ax.text(0.5, 0.95, stock_info_text, transform=ax.transAxes, 
                   horizontalalignment='center', fontsize=self.params["font_size"] - 1,
                   bbox=dict(facecolor='white', alpha=0.8, pad=5))
        
        ax.set_xlabel("时间", fontsize=self.params["font_size"])
        ax.set_ylabel("价格（元）", fontsize=self.params["font_size"])
        ax.legend(fontsize=self.params["legend_font_size"])
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        # 保存图表
        if save_path:
            # 如果save_path是目录，则生成完整文件名
            import os
            if os.path.isdir(save_path):
                filename = self._generate_filename("trading_signals", stock_info)
                save_path = os.path.join(save_path, filename)
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"交易信号图已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def plot_performance_metrics(self, metrics, title="性能指标雷达图", save_path=None, stock_info=None):
        """
        绘制性能指标雷达图
        
        Args:
            metrics: 性能指标字典
            title: 图表标题
            save_path: 保存路径（可选）
            stock_info: 股票信息字典，包含symbol、name、start_date、end_date、frequency等信息
        """
        self.logger.info("绘制性能指标雷达图")
        
        # 提取关键指标
        radar_metrics = {
            "年化收益率": metrics.get("annual_return", 0),
            "夏普比率": metrics.get("sharpe_ratio", 0),
            "最大回撤": -metrics.get("max_drawdown", 0),  # 取绝对值
            "胜率": metrics.get("win_rate", 0),
            "盈亏比": metrics.get("profit_loss_ratio", 0),
            "波动率": metrics.get("volatility", 0)
        }
        
        # 转换为DataFrame
        metrics_df = pd.DataFrame(list(radar_metrics.items()), columns=['指标', '值'])
        
        # 计算角度
        categories = list(metrics_df['指标'])
        values = metrics_df['值'].tolist()
        num_vars = len(categories)
        angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
        angles += angles[:1]  # 闭合雷达图
        values += values[:1]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.params["figsize"], subplot_kw=dict(polar=True))
        
        # 绘制雷达图
        ax.plot(angles, values, linewidth=2, linestyle='solid', 
               color=self.params["colors"]["equity"], label="策略指标")
        ax.fill(angles, values, color=self.params["colors"]["equity"], alpha=0.25)
        
        # 设置图表属性
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=self.params["font_size"])
        ax.set_yticklabels([])
        ax.set_title(title, fontsize=self.params["title_font_size"], pad=20)
        
        # 添加股票信息（如果提供）
        if stock_info:
            # 提取股票信息
            symbol = stock_info.get('symbol', 'N/A')
            name = stock_info.get('name', 'N/A')
            start_date = stock_info.get('start_date', 'N/A')
            end_date = stock_info.get('end_date', 'N/A')
            frequency = stock_info.get('frequency', 'N/A')
            
            # 计算当前价格、价格变化和百分比变化（如果有价格数据）
            current_price = "N/A"
            price_change = "N/A"
            pct_change = "N/A"
            if 'current_price' in stock_info:
                current_price = f"{stock_info['current_price']:.2f}"
                if 'previous_price' in stock_info:
                    price_change = f"{stock_info['current_price'] - stock_info['previous_price']:.2f}"
                    pct_change = f"{(price_change / stock_info['previous_price'] * 100):.2f}%"
            
            # 构建完整的股票信息文本
            stock_info_text = f"股票代码: {symbol} | 股票名称: {name} | 当前价格: {current_price} | 价格变化: {price_change} ({pct_change})"
            stock_info_text += f" | 回测时间: {start_date} 至 {end_date} | 频率: {frequency}"
            # 在雷达图下方添加股票信息
            ax.text(0.5, -0.15, stock_info_text, transform=ax.transAxes, 
                   horizontalalignment='center', fontsize=self.params["font_size"] - 1,
                   bbox=dict(facecolor='white', alpha=0.8, pad=5))
        
        # 添加数值标签
        for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
            ax.text(angle, value * 1.1, f"{value:.2f}", 
                   horizontalalignment='center', 
                   verticalalignment='center',
                   fontsize=self.params["font_size"])
        
        # 保存图表
        if save_path:
            # 如果save_path是目录，则生成完整文件名
            import os
            if os.path.isdir(save_path):
                filename = self._generate_filename("performance_metrics", stock_info)
                save_path = os.path.join(save_path, filename)
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"性能指标雷达图已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def plot_parameter_optimization(self, optimization_results, title="参数优化结果", save_path=None):
        """
        绘制参数优化结果
        
        Args:
            optimization_results: 参数优化结果
            title: 图表标题
            save_path: 保存路径（可选）
        """
        self.logger.info("绘制参数优化结果")
        
        # 提取优化历史
        history = optimization_results.get("optimization_history", [])
        
        if not history:
            self.logger.warning("没有优化历史数据，无法绘制参数优化结果图")
            return
        
        # 转换为DataFrame
        history_df = pd.DataFrame(history)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.params["figsize"])
        
        # 绘制最优适应度曲线
        ax.plot(history_df["generation"], history_df["best_fitness"], 
               label="最优适应度", color=self.params["colors"]["equity"], linewidth=2)
        
        # 绘制平均适应度曲线
        ax.plot(history_df["generation"], history_df["avg_fitness"], 
               label="平均适应度", color=self.params["colors"]["benchmark"], 
               linewidth=2, linestyle="--")
        
        # 设置图表属性
        ax.set_title(title, fontsize=self.params["title_font_size"])
        ax.set_xlabel("迭代次数", fontsize=self.params["font_size"])
        ax.set_ylabel("适应度值", fontsize=self.params["font_size"])
        ax.legend(fontsize=self.params["legend_font_size"])
        ax.grid(True, alpha=0.3)
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"参数优化结果图已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def plot_performance_comparison(self, metrics_list, strategy_names=None, 
                                  title="策略性能对比", save_path=None):
        """
        绘制策略性能对比图
        
        Args:
            metrics_list: 多个策略的性能指标列表
            strategy_names: 策略名称列表
            title: 图表标题
            save_path: 保存路径（可选）
        """
        self.logger.info("绘制策略性能对比图")
        
        # 设置策略名称
        if strategy_names is None:
            strategy_names = [f"策略{i+1}" for i in range(len(metrics_list))]
        
        # 提取关键指标
        metrics_to_compare = ["total_return", "annual_return", "sharpe_ratio", 
                            "max_drawdown", "win_rate", "profit_loss_ratio"]
        
        # 转换为DataFrame
        comparison_data = {}
        for metric in metrics_to_compare:
            comparison_data[metric] = [m["performance_metrics"][metric] for m in metrics_list]
        
        comparison_df = pd.DataFrame(comparison_data, index=strategy_names)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 绘制柱状图
        comparison_df.plot(kind='bar', ax=ax, alpha=0.7)
        
        # 设置图表属性
        ax.set_title(title, fontsize=self.params["title_font_size"])
        ax.set_xlabel("策略", fontsize=self.params["font_size"])
        ax.set_ylabel("指标值", fontsize=self.params["font_size"])
        ax.legend(fontsize=self.params["legend_font_size"])
        ax.grid(True, alpha=0.3, axis='y')
        
        # 旋转x轴标签
        plt.xticks(rotation=45, ha='right', fontsize=self.params["font_size"])
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=self.params["dpi"], bbox_inches="tight")
            self.logger.info(f"策略性能对比图已保存到: {save_path}")
        
        # 显示图表
        plt.tight_layout()
        plt.show()
        plt.close()
    
    def generate_report(self, results, save_dir=None, stock_info=None):
        """
        生成完整的回测结果可视化报告
        
        Args:
            results: 回测结果
            save_dir: 报告保存目录
            stock_info: 股票信息字典，包含symbol、name、start_date、end_date、frequency等信息
            
        Returns:
            list: 生成的图表路径列表
        """
        self.logger.info("生成回测结果可视化报告")
        
        generated_files = []
        
        # 提取数据
        account_history = results.get("account_history", [])
        signals = results.get("signals", [])
        metrics = results.get("performance_metrics", {})
        
        # 检查数据
        if not account_history:
            self.logger.warning("账户历史数据为空，无法生成可视化报告")
            return generated_files
        
        # 创建保存目录
        if save_dir:
            import os
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
        
        # 绘制资金曲线
        self.plot_equity_curve(account_history, title="策略资金曲线", save_path=save_dir, stock_info=stock_info)
        if save_dir:
            equity_curve_path = os.path.join(save_dir, self._generate_filename("equity_curve", stock_info))
            generated_files.append(equity_curve_path)
        
        # 绘制回撤曲线
        self.plot_drawdown(account_history, title="策略回撤曲线", save_path=save_dir, stock_info=stock_info)
        if save_dir:
            drawdown_path = os.path.join(save_dir, self._generate_filename("drawdown", stock_info))
            generated_files.append(drawdown_path)
        
        # 绘制收益率分布
        self.plot_returns_distribution(account_history, title="策略日收益率分布", save_path=save_dir, stock_info=stock_info)
        if save_dir:
            returns_dist_path = os.path.join(save_dir, self._generate_filename("returns_distribution", stock_info))
            generated_files.append(returns_dist_path)
        
        # 绘制交易信号（如果有）
        if signals:
            # 这里需要原始价格数据，暂时跳过
            pass
        
        # 绘制性能指标雷达图
        self.plot_performance_metrics(metrics, title="策略性能指标雷达图", save_path=save_dir, stock_info=stock_info)
        if save_dir:
            radar_chart_path = os.path.join(save_dir, self._generate_filename("performance_metrics", stock_info))
            generated_files.append(radar_chart_path)
        
        self.logger.info(f"回测结果可视化报告生成完成，共生成 {len(generated_files)} 个图表")
        return generated_files
    
    def reset(self):
        """
        重置可视化器
        """
        self.logger.info("重置可视化器")
        # 重置matplotlib
        plt.close('all')
        plt.style.use(self.params["style"])
        self.logger.info("可视化器重置完成")
