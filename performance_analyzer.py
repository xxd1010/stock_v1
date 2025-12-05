#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能分析模块

计算和分析回测结果的各项性能指标，包括收益率、最大回撤、夏普比率等关键指标
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from log_utils import get_logger


class PerformanceAnalyzer:
    """
    性能分析器
    
    计算和分析回测结果的各项性能指标
    """
    
    def __init__(self):
        """
        初始化性能分析器
        """
        self.logger = get_logger("performance_analyzer")
        self.logger.info("初始化性能分析器")
        
        # 分析参数
        self.params = {
            "risk_free_rate": 0.03,  # 无风险利率
            "benchmark": None,  # 基准收益率，用于比较分析
            "annualization_factor": 252,  # 年化因子，默认252个交易日
            "min_period": 10  # 计算指标所需的最小数据点数
        }
        
        # 性能指标
        self.metrics = {
            "return_metrics": {},
            "risk_metrics": {},
            "risk_adjusted_metrics": {},
            "trade_metrics": {},
            "other_metrics": {}
        }
        
        self.logger.info("性能分析器初始化完成")
    
    def set_params(self, params):
        """
        设置分析参数
        
        Args:
            params: 分析参数
        """
        self.logger.info(f"设置分析参数: {params}")
        self.params.update(params)
    
    def analyze(self, account_history, trades, benchmark_returns=None):
        """
        执行性能分析
        
        Args:
            account_history: 账户历史数据
            trades: 交易记录
            benchmark_returns: 基准收益率数据
            
        Returns:
            dict: 性能分析结果
        """
        self.logger.info("开始执行性能分析")
        
        # 转换数据格式
        if isinstance(account_history, list):
            account_df = pd.DataFrame(account_history)
        else:
            account_df = account_history.copy()
        
        if isinstance(trades, list):
            trades_df = pd.DataFrame(trades)
        else:
            trades_df = trades.copy()
        
        # 验证数据
        if account_df.empty:
            self.logger.error("账户历史数据为空，无法进行性能分析")
            return {}
        
        # 计算各项指标
        self.calculate_return_metrics(account_df)
        self.calculate_risk_metrics(account_df)
        self.calculate_risk_adjusted_metrics(account_df)
        self.calculate_trade_metrics(trades_df)
        
        # 如果提供了基准收益率，计算相对指标
        if benchmark_returns is not None:
            self.calculate_relative_metrics(account_df, benchmark_returns)
        
        self.logger.info("性能分析完成")
        return self.metrics
    
    def calculate_return_metrics(self, account_df):
        """
        计算收益率指标
        
        Args:
            account_df: 账户历史数据DataFrame
        """
        self.logger.info("计算收益率指标")
        
        # 提取权益数据
        equity = account_df["total_equity"]
        
        # 计算总收益率
        total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
        
        # 计算日收益率
        daily_returns = equity.pct_change().dropna()
        
        # 计算年化收益率
        annual_return = (1 + total_return / 100) ** (self.params["annualization_factor"] / len(daily_returns)) - 1
        annual_return *= 100
        
        # 计算累计收益率
        cumulative_returns = (1 + daily_returns).cumprod() - 1
        
        # 计算平均日收益率
        avg_daily_return = daily_returns.mean() * 100
        
        # 计算中位数日收益率
        median_daily_return = daily_returns.median() * 100
        
        # 计算正收益率天数比例
        positive_days_ratio = (daily_returns > 0).sum() / len(daily_returns) * 100
        
        # 保存收益率指标
        self.metrics["return_metrics"] = {
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "avg_daily_return": round(avg_daily_return, 4),
            "median_daily_return": round(median_daily_return, 4),
            "positive_days_ratio": round(positive_days_ratio, 2),
            "cumulative_returns": cumulative_returns.tolist()
        }
        
        self.logger.info(f"收益率指标计算完成: {self.metrics['return_metrics']}")
    
    def calculate_risk_metrics(self, account_df):
        """
        计算风险指标
        
        Args:
            account_df: 账户历史数据DataFrame
        """
        self.logger.info("计算风险指标")
        
        # 提取权益数据
        equity = account_df["total_equity"]
        
        # 计算日收益率
        daily_returns = equity.pct_change().dropna()
        
        # 计算波动率
        volatility = daily_returns.std() * np.sqrt(self.params["annualization_factor"]) * 100
        
        # 计算最大回撤
        cumulative_returns = (1 + daily_returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # 计算最大回撤持续时间
        max_drawdown_duration = self._calculate_max_drawdown_duration(drawdown)
        
        # 计算下行风险
        negative_returns = daily_returns[daily_returns < 0]
        downside_risk = negative_returns.std() * np.sqrt(self.params["annualization_factor"]) * 100
        
        # 计算VaR (Value at Risk) - 95%置信区间
        var_95 = np.percentile(daily_returns, 5) * 100
        
        # 计算CVaR (Conditional Value at Risk) - 95%置信区间
        cvar_95 = daily_returns[daily_returns <= var_95 / 100].mean() * 100
        
        # 计算最大单日亏损
        max_daily_loss = daily_returns.min() * 100
        
        # 计算最大单日盈利
        max_daily_gain = daily_returns.max() * 100
        
        # 保存风险指标
        self.metrics["risk_metrics"] = {
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_duration": max_drawdown_duration,
            "downside_risk": round(downside_risk, 2),
            "var_95": round(var_95, 4),
            "cvar_95": round(cvar_95, 4),
            "max_daily_loss": round(max_daily_loss, 4),
            "max_daily_gain": round(max_daily_gain, 4)
        }
        
        self.logger.info(f"风险指标计算完成: {self.metrics['risk_metrics']}")
    
    def calculate_risk_adjusted_metrics(self, account_df):
        """
        计算风险调整后收益指标
        
        Args:
            account_df: 账户历史数据DataFrame
        """
        self.logger.info("计算风险调整后收益指标")
        
        # 提取权益数据
        equity = account_df["total_equity"]
        
        # 计算日收益率
        daily_returns = equity.pct_change().dropna()
        
        # 计算年化收益率
        annual_return = self.metrics["return_metrics"]["annual_return"] / 100
        
        # 计算年化波动率
        annual_volatility = self.metrics["risk_metrics"]["volatility"] / 100
        
        # 计算夏普比率
        sharpe_ratio = (annual_return - self.params["risk_free_rate"]) / annual_volatility if annual_volatility > 0 else 0
        
        # 计算索提诺比率
        negative_returns = daily_returns[daily_returns < 0]
        annual_downside_risk = negative_returns.std() * np.sqrt(self.params["annualization_factor"])
        sortino_ratio = (annual_return - self.params["risk_free_rate"]) / annual_downside_risk if annual_downside_risk > 0 else 0
        
        # 计算卡玛比率 (Calmar Ratio)
        max_drawdown = abs(self.metrics["risk_metrics"]["max_drawdown"] / 100)
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        # 计算信息比率 (假设基准收益率为无风险利率)
        excess_returns = daily_returns - (self.params["risk_free_rate"] / self.params["annualization_factor"])
        information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(self.params["annualization_factor"]) if excess_returns.std() > 0 else 0
        
        # 计算特雷诺比率 (Treynor Ratio)
        # 假设贝塔系数为1（简化计算）
        beta = 1.0
        treynor_ratio = (annual_return - self.params["risk_free_rate"]) / beta if beta != 0 else 0
        
        # 保存风险调整后收益指标
        self.metrics["risk_adjusted_metrics"] = {
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "calmar_ratio": round(calmar_ratio, 2),
            "information_ratio": round(information_ratio, 2),
            "treynor_ratio": round(treynor_ratio, 2)
        }
        
        self.logger.info(f"风险调整后收益指标计算完成: {self.metrics['risk_adjusted_metrics']}")
    
    def calculate_trade_metrics(self, trades_df):
        """
        计算交易相关指标
        
        Args:
            trades_df: 交易记录DataFrame
        """
        self.logger.info("计算交易相关指标")
        
        if trades_df.empty:
            self.logger.warning("交易记录为空，无法计算交易相关指标")
            self.metrics["trade_metrics"] = {
                "total_trades": 0,
                "win_rate": 0,
                "profit_loss_ratio": 0,
                "avg_trade_return": 0,
                "max_win_trade": 0,
                "max_loss_trade": 0,
                "avg_win_trade": 0,
                "avg_loss_trade": 0,
                "consecutive_wins": 0,
                "consecutive_losses": 0
            }
            return
        
        # 计算总交易次数
        total_trades = len(trades_df)
        
        # 计算胜率
        winning_trades = len(trades_df[(trades_df["action"] == "sell") & (trades_df["price"] > trades_df["price"])])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # 计算盈亏比
        # 简化计算：假设每次交易的盈亏金额为 (卖出价格 - 买入价格) * 数量
        # 这里需要根据实际交易记录结构调整
        try:
            # 假设交易记录中包含profit字段
            if "profit" in trades_df.columns:
                profits = trades_df["profit"]
                total_profit = profits[profits > 0].sum()
                total_loss = abs(profits[profits < 0].sum())
            else:
                # 简化计算，假设每次交易的盈亏为价格差
                total_profit = trades_df[trades_df["action"] == "sell"]["price"].sum()
                total_loss = trades_df[trades_df["action"] == "buy"]["price"].sum()
        except Exception as e:
            self.logger.error(f"计算盈亏比时出错: {str(e)}")
            total_profit = 0
            total_loss = 1
        
        profit_loss_ratio = abs(total_profit / total_loss) if total_loss != 0 else 0
        
        # 计算平均每笔交易收益率
        # 简化计算：使用账户总收益率除以交易次数
        avg_trade_return = self.metrics["return_metrics"]["total_return"] / total_trades if total_trades > 0 else 0
        
        # 计算最大盈利交易和最大亏损交易
        max_win_trade = 0
        max_loss_trade = 0
        avg_win_trade = 0
        avg_loss_trade = 0
        
        # 计算连续盈利和连续亏损次数
        consecutive_wins = 0
        consecutive_losses = 0
        current_streak = 0
        current_streak_type = None
        
        # 保存交易相关指标
        self.metrics["trade_metrics"] = {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            "avg_trade_return": round(avg_trade_return, 4),
            "max_win_trade": round(max_win_trade, 2),
            "max_loss_trade": round(max_loss_trade, 2),
            "avg_win_trade": round(avg_win_trade, 2),
            "avg_loss_trade": round(avg_loss_trade, 2),
            "consecutive_wins": consecutive_wins,
            "consecutive_losses": consecutive_losses
        }
        
        self.logger.info(f"交易相关指标计算完成: {self.metrics['trade_metrics']}")
    
    def calculate_relative_metrics(self, account_df, benchmark_returns):
        """
        计算相对基准的指标
        
        Args:
            account_df: 账户历史数据DataFrame
            benchmark_returns: 基准收益率数据
        """
        self.logger.info("计算相对基准的指标")
        
        # 转换基准数据格式
        if isinstance(benchmark_returns, list):
            benchmark_df = pd.DataFrame(benchmark_returns)
        else:
            benchmark_df = benchmark_returns.copy()
        
        # 提取收益率数据
        equity = account_df["total_equity"]
        strategy_returns = equity.pct_change().dropna()
        
        # 确保基准数据长度匹配
        if len(strategy_returns) != len(benchmark_df):
            self.logger.warning(f"策略数据和基准数据长度不匹配: {len(strategy_returns)} vs {len(benchmark_df)}")
            # 截取较短的数据
            min_length = min(len(strategy_returns), len(benchmark_df))
            strategy_returns = strategy_returns.iloc[-min_length:]
            benchmark_returns = benchmark_df.iloc[-min_length:]
        
        # 计算超额收益
        excess_returns = strategy_returns - benchmark_returns
        
        # 计算年化超额收益
        annual_excess_return = excess_returns.mean() * self.params["annualization_factor"] * 100
        
        # 计算信息比率
        information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(self.params["annualization_factor"]) if excess_returns.std() > 0 else 0
        
        # 计算跟踪误差
        tracking_error = excess_returns.std() * np.sqrt(self.params["annualization_factor"]) * 100
        
        # 计算Beta系数
        # 简化计算：假设基准收益率为独立变量
        covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # 保存相对指标
        self.metrics["other_metrics"] = {
            "annual_excess_return": round(annual_excess_return, 2),
            "information_ratio": round(information_ratio, 2),
            "tracking_error": round(tracking_error, 2),
            "beta": round(beta, 2)
        }
        
        self.logger.info(f"相对基准指标计算完成: {self.metrics['other_metrics']}")
    
    def _calculate_max_drawdown_duration(self, drawdown):
        """
        计算最大回撤持续时间
        
        Args:
            drawdown: 回撤序列
            
        Returns:
            int: 最大回撤持续时间（单位：天）
        """
        # 计算回撤持续时间
        drawdown_duration = 0
        max_drawdown_duration = 0
        
        for val in drawdown:
            if val < 0:
                drawdown_duration += 1
                max_drawdown_duration = max(max_drawdown_duration, drawdown_duration)
            else:
                drawdown_duration = 0
        
        return max_drawdown_duration
    
    def generate_report(self, output_format="json", file_path=None):
        """
        生成性能分析报告
        
        Args:
            output_format: 报告格式，支持json、html、pdf
            file_path: 报告保存路径
            
        Returns:
            dict or str: 性能分析报告
        """
        self.logger.info(f"生成性能分析报告，格式: {output_format}")
        
        if output_format == "json":
            report = self.metrics.copy()
            if file_path:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                self.logger.info(f"性能分析报告已保存到: {file_path}")
            return report
        elif output_format == "html":
            # 生成HTML报告
            html_report = self._generate_html_report()
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_report)
                self.logger.info(f"HTML报告已保存到: {file_path}")
            return html_report
        else:
            self.logger.error(f"不支持的报告格式: {output_format}")
            return {}
    
    def _generate_html_report(self):
        """
        生成HTML格式的性能分析报告
        
        Returns:
            str: HTML报告内容
        """
        # 简化实现，生成基本的HTML报告
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>量化交易回测性能分析报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .metric-section {{ margin: 20px 0; }}
                .metric-item {{ margin: 10px 0; }}
                .metric-label {{ font-weight: bold; display: inline-block; width: 200px; }}
                .metric-value {{ color: #0066cc; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .summary-box {{ background-color: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>量化交易回测性能分析报告</h1>
                <div class="summary-box">
                    <h2>报告摘要</h2>
                    <div class="metric-item">
                        <span class="metric-label">总收益率:</span>
                        <span class="metric-value">{self.metrics['return_metrics'].get('total_return', 0)}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">年化收益率:</span>
                        <span class="metric-value">{self.metrics['return_metrics'].get('annual_return', 0)}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">夏普比率:</span>
                        <span class="metric-value">{self.metrics['risk_adjusted_metrics'].get('sharpe_ratio', 0)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">最大回撤:</span>
                        <span class="metric-value">{self.metrics['risk_metrics'].get('max_drawdown', 0)}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">胜率:</span>
                        <span class="metric-value">{self.metrics['trade_metrics'].get('win_rate', 0)}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">总交易次数:</span>
                        <span class="metric-value">{self.metrics['trade_metrics'].get('total_trades', 0)}</span>
                    </div>
                </div>
                
                <div class="metric-section">
                    <h2>收益率指标</h2>
                    {self._generate_metric_html(self.metrics['return_metrics'])}
                </div>
                
                <div class="metric-section">
                    <h2>风险指标</h2>
                    {self._generate_metric_html(self.metrics['risk_metrics'])}
                </div>
                
                <div class="metric-section">
                    <h2>风险调整后收益指标</h2>
                    {self._generate_metric_html(self.metrics['risk_adjusted_metrics'])}
                </div>
                
                <div class="metric-section">
                    <h2>交易相关指标</h2>
                    {self._generate_metric_html(self.metrics['trade_metrics'])}
                </div>
                
                {self._generate_metric_html(self.metrics['other_metrics'], "其他指标") if self.metrics['other_metrics'] else ""}
                
                <div style="margin-top: 50px; text-align: center; color: #999;">
                    <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_metric_html(self, metrics, title=None):
        """
        生成指标的HTML片段
        
        Args:
            metrics: 指标字典
            title: 标题
            
        Returns:
            str: HTML片段
        """
        html = ""
        if title:
            html += f"<h3>{title}</h3>"
        html += "<table class='table'>"
        html += "<tr><th>指标名称</th><th>指标值</th></tr>"
        
        for key, value in metrics.items():
            # 跳过不需要显示的指标
            if key in ["cumulative_returns"]:
                continue
            # 格式化指标名称
            metric_name = key.replace('_', ' ').title()
            # 格式化指标值
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            html += f"<tr><td>{metric_name}</td><td>{formatted_value}</td></tr>"
        
        html += "</table>"
        return html
    
    def get_metrics(self):
        """
        获取性能指标
        
        Returns:
            dict: 性能指标
        """
        return self.metrics
    
    def reset(self):
        """
        重置性能分析器
        """
        self.logger.info("重置性能分析器")
        # 重置指标
        self.metrics = {
            "return_metrics": {},
            "risk_metrics": {},
            "risk_adjusted_metrics": {},
            "trade_metrics": {},
            "other_metrics": {}
        }
        self.logger.info("性能分析器重置完成")
