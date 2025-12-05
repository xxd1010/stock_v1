#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测引擎核心

实现完整的回测流程，包括数据加载、策略执行、账户管理、撮合引擎调用等
"""

import pandas as pd
import numpy as np
from datetime import datetime
import uuid
from log_utils import get_logger
from matching_engine import MatchingEngine, Order
from base_strategy import BaseStrategy
from data_source_manager import DataSourceManager


class BacktestEngine:
    """
    回测引擎
    
    实现完整的回测流程，包括数据加载、策略执行、账户管理、撮合引擎调用等
    """
    
    def __init__(self):
        """
        初始化回测引擎
        """
        self.logger = get_logger("backtest_engine")
        self.logger.info("初始化回测引擎")
        
        # 回测参数
        self.params = {
            "initial_cash": 1000000,
            "start_date": None,
            "end_date": None,
            "frequency": "d",  # 'd' for daily, 'h' for hourly, 'm' for minute, 't' for tick
            "transaction_cost": 0.0003,
            "slippage": 0.0001,
            "max_position_percentage": 0.1,
            "commission_rate": 0.0003,
            "stamp_tax": 0.001  # 印花税，仅卖出时收取
        }
        
        # 回测状态
        self.status = {
            "initialized": False,
            "running": False,
            "completed": False,
            "current_step": 0,
            "total_steps": 0
        }
        
        # 回测数据
        self.data = None
        self.data_with_indicators = None
        
        # 策略
        self.strategy = None
        
        # 撮合引擎
        self.matching_engine = MatchingEngine()
        
        # 数据源管理器
        self.data_source_manager = DataSourceManager()
        
        # 账户状态
        self.account = {
            "cash": self.params["initial_cash"],
            "total_equity": self.params["initial_cash"],
            "positions": {},  # {symbol: {volume, avg_price, market_value}}
            "frozen_cash": 0,
            "pnl": 0,
            "pnl_percentage": 0
        }
        
        # 回测结果
        self.results = {
            "orders": [],
            "trades": [],
            "signals": [],
            "account_history": [],
            "positions_history": [],
            "performance_metrics": {}
        }
        
        # 订单计数器
        self.order_counter = 0
        
        self.logger.info("回测引擎初始化完成")
    
    def set_params(self, params):
        """
        设置回测参数
        
        Args:
            params: 回测参数
        """
        self.logger.info(f"设置回测参数: {params}")
        self.params.update(params)
        
        # 更新撮合引擎参数
        self.matching_engine.set_params({
            "transaction_cost": params.get("transaction_cost", self.params["transaction_cost"]),
            "slippage": params.get("slippage", self.params["slippage"])
        })
        
        # 更新初始资金
        if "initial_cash" in params:
            self.account["cash"] = params["initial_cash"]
            self.account["total_equity"] = params["initial_cash"]
    
    def load_data(self, data):
        """
        加载回测数据
        
        Args:
            data: 回测数据，可以是DataFrame或数据文件路径
        """
        self.logger.info(f"加载回测数据")
        
        if isinstance(data, pd.DataFrame):
            self.data = data
        else:
            # 从文件加载数据
            if data.endswith('.csv'):
                self.data = pd.read_csv(data)
            elif data.endswith('.xlsx'):
                self.data = pd.read_excel(data)
            else:
                raise ValueError(f"不支持的数据格式: {data}")
        
        # 确保数据按日期排序
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
            self.data = self.data.sort_values('date')
        elif 'datetime' in self.data.columns:
            self.data['datetime'] = pd.to_datetime(self.data['datetime'])
            self.data = self.data.sort_values('datetime')
        
        # 设置日期索引
        if 'date' in self.data.columns:
            self.data.set_index('date', inplace=True)
        elif 'datetime' in self.data.columns:
            self.data.set_index('datetime', inplace=True)
        
        # 过滤日期范围
        if self.params["start_date"] and self.params["end_date"]:
            self.data = self.data.loc[self.params["start_date"]:self.params["end_date"]]
        
        # 重置索引
        self.data.reset_index(inplace=True)
        
        self.logger.info(f"回测数据加载完成，共 {len(self.data)} 条记录")
        self.status["total_steps"] = len(self.data)
    
    def fetch_data(self, stock_code: str, start_date: str = None, end_date: str = None, 
                  frequency: str = "d", source_name: str = None):
        """
        从数据源获取回测数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期，默认为回测参数中的开始日期
            end_date: 结束日期，默认为回测参数中的结束日期
            frequency: 数据频率
            source_name: 数据源名称
        """
        self.logger.info(f"从数据源获取回测数据: 股票代码={stock_code}, 开始日期={start_date}, 结束日期={end_date}, 频率={frequency}")
        
        # 使用回测参数中的日期如果未提供
        if start_date is None:
            start_date = self.params["start_date"]
        if end_date is None:
            end_date = self.params["end_date"]
        
        # 从数据源获取数据
        self.data = self.data_source_manager.fetch_stock_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            source_name=source_name,
            save_to_storage=True
        )
        
        if self.data.empty:
            self.logger.error(f"未获取到股票 {stock_code} 的数据")
            return False
        
        # 确保数据按日期排序
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
            self.data = self.data.sort_values('date')
        
        self.logger.info(f"回测数据获取完成，共 {len(self.data)} 条记录")
        self.status["total_steps"] = len(self.data)
        return True
    
    def set_strategy(self, strategy):
        """
        设置策略
        
        Args:
            strategy: 策略对象，必须继承自BaseStrategy
        """
        self.logger.info(f"设置策略: {strategy.__class__.__name__}")
        
        if not isinstance(strategy, BaseStrategy):
            raise ValueError("策略必须继承自BaseStrategy")
        
        self.strategy = strategy
        
        # 设置策略参数
        self.strategy.set_strategy_params({
            "initial_cash": self.params["initial_cash"],
            "transaction_cost": self.params["transaction_cost"],
            "slippage": self.params["slippage"],
            "max_position_percentage": self.params["max_position_percentage"]
        })
    
    def initialize(self):
        """
        初始化回测
        """
        self.logger.info("初始化回测")
        
        # 验证数据
        if self.data is None:
            raise ValueError("请先加载回测数据")
        
        # 验证策略
        if self.strategy is None:
            raise ValueError("请先设置策略")
        
        # 重置回测状态
        self.reset()
        
        # 初始化策略
        self.strategy.initialize(self.data, self.account)
        
        # 获取策略计算的指标数据
        if hasattr(self.strategy, 'data_with_indicators'):
            self.data_with_indicators = self.strategy.data_with_indicators
        else:
            self.data_with_indicators = self.data
        
        # 记录初始账户状态
        self.record_account_state()
        
        self.status["initialized"] = True
        self.logger.info("回测初始化完成")
    
    def run(self):
        """
        运行回测
        """
        self.logger.info("开始回测")
        
        # 检查初始化状态
        if not self.status["initialized"]:
            self.initialize()
        
        self.status["running"] = True
        
        try:
            # 回测主循环
            for step in range(self.status["total_steps"]):
                # 更新当前步骤
                self.status["current_step"] = step
                
                # 获取当前数据
                current_data = self.data.iloc[step]
                if self.data_with_indicators is not None:
                    current_data_with_indicators = self.data_with_indicators.iloc[step]
                else:
                    current_data_with_indicators = current_data
                
                # 记录当前账户状态
                self.record_account_state()
                
                # 执行策略
                self.execute_strategy(current_data_with_indicators)
                
                # 更新账户权益
                self.update_account_equity(current_data)
            
            # 回测完成
            self.status["running"] = False
            self.status["completed"] = True
            
            # 记录最终账户状态
            self.record_account_state()
            
            # 计算性能指标
            self.calculate_performance_metrics()
            
            self.logger.info("回测完成")
            
        except Exception as e:
            self.logger.error(f"回测过程中发生错误: {str(e)}")
            self.status["running"] = False
            raise
    
    def execute_strategy(self, current_data):
        """
        执行策略
        
        Args:
            current_data: 当前数据
        """
        # 生成交易信号
        signals = self.strategy.generate_signals(current_data, self.account)
        
        # 记录信号
        for signal in signals:
            signal["timestamp"] = current_data.get("date", current_data.get("datetime", datetime.now()))
            self.results["signals"].append(signal)
            self.strategy.add_signal(signal)
        
        # 执行订单
        for signal in signals:
            order = self.create_order(signal, current_data)
            if order:
                # 添加到订单列表
                self.results["orders"].append(order.__dict__)
                
                # 执行订单撮合
                trade_results = self.matching_engine.add_order(order)
                
                if trade_results:
                    # 处理成交结果
                    self.process_trade_results(trade_results, order, current_data)
    
    def create_order(self, signal, current_data):
        """
        创建订单
        
        Args:
            signal: 交易信号
            current_data: 当前数据
            
        Returns:
            Order: 订单对象
        """
        self.order_counter += 1
        
        # 计算订单价格
        if signal["price"] is None:
            # 使用当前收盘价
            price = current_data["close"]
        else:
            price = signal["price"]
        
        # 计算订单数量
        if signal["volume"] is None:
            # 使用策略的仓位计算方法
            volume = self.strategy.calculate_position_size(self.account, price)
        else:
            volume = signal["volume"]
        
        # 检查资金是否足够
        if signal["action"] == "buy":
            required_cash = price * volume * (1 + self.params["transaction_cost"] + self.params["slippage"])
            if required_cash > self.account["cash"]:
                self.logger.warning(f"资金不足，无法执行买入订单: 需要 {required_cash}, 可用 {self.account['cash']}")
                return None
        
        # 检查持仓是否足够
        if signal["action"] == "sell":
            symbol = signal["symbol"]
            if symbol not in self.account["positions"] or self.account["positions"][symbol]["volume"] < volume:
                self.logger.warning(f"持仓不足，无法执行卖出订单: 需要 {volume}, 可用 {self.account['positions'].get(symbol, {}).get('volume', 0)}")
                return None
        
        # 创建订单对象
        order = Order(
            order_id=f"order_{self.order_counter}_{uuid.uuid4().hex[:8]}",
            symbol=signal["symbol"],
            action=signal["action"],
            price=price,
            volume=volume,
            order_type=signal.get("order_type", "market"),
            timestamp=current_data.get("date", current_data.get("datetime", datetime.now()))
        )
        
        self.logger.info(f"创建订单: {order}")
        return order
    
    def process_trade_results(self, trade_results, order, current_data):
        """
        处理成交结果
        
        Args:
            trade_results: 成交结果
            order: 订单对象
            current_data: 当前数据
        """
        # 确保trade_results是列表
        if not isinstance(trade_results, list):
            trade_results = [trade_results]
        
        for trade in trade_results:
            # 更新账户
            self.update_account(trade, order.action)
            
            # 记录成交记录
            trade["timestamp"] = current_data.get("date", current_data.get("datetime", datetime.now()))
            self.results["trades"].append(trade)
            
            self.logger.info(f"成交记录: {trade}")
    
    def update_account(self, trade, action):
        """
        更新账户状态
        
        Args:
            trade: 成交记录
            action: 交易方向
        """
        symbol = trade["symbol"]
        price = trade["price"]
        volume = trade["volume"]
        transaction_cost = trade["transaction_cost"]
        
        if action == "buy":
            # 买入操作
            total_cost = price * volume + transaction_cost
            
            # 更新现金
            self.account["cash"] -= total_cost
            
            # 更新持仓
            if symbol in self.account["positions"]:
                # 已有持仓，加仓
                current_volume = self.account["positions"][symbol]["volume"]
                current_avg_price = self.account["positions"][symbol]["avg_price"]
                new_volume = current_volume + volume
                new_avg_price = (current_avg_price * current_volume + price * volume) / new_volume
                self.account["positions"][symbol] = {
                    "volume": new_volume,
                    "avg_price": new_avg_price,
                    "market_value": new_volume * price
                }
            else:
                # 新持仓
                self.account["positions"][symbol] = {
                    "volume": volume,
                    "avg_price": price,
                    "market_value": volume * price
                }
                
        elif action == "sell":
            # 卖出操作
            # 计算印花税
            stamp_tax = price * volume * self.params["stamp_tax"]
            total_cost = transaction_cost + stamp_tax
            
            # 计算卖出收入
            total_revenue = price * volume - total_cost
            
            # 更新现金
            self.account["cash"] += total_revenue
            
            # 更新持仓
            if symbol in self.account["positions"]:
                current_volume = self.account["positions"][symbol]["volume"]
                if current_volume <= volume:
                    # 全部卖出
                    del self.account["positions"][symbol]
                else:
                    # 部分卖出
                    new_volume = current_volume - volume
                    avg_price = self.account["positions"][symbol]["avg_price"]
                    self.account["positions"][symbol] = {
                        "volume": new_volume,
                        "avg_price": avg_price,
                        "market_value": new_volume * price
                    }
    
    def update_account_equity(self, current_data):
        """
        更新账户权益
        
        Args:
            current_data: 当前数据
        """
        # 计算持仓市值
        total_market_value = 0
        for symbol, position in self.account["positions"].items():
            # 获取当前价格
            if symbol == current_data.get("code", current_data.get("symbol")):
                current_price = current_data["close"]
            else:
                # 如果是多股票回测，需要从数据中获取对应股票的价格
                current_price = position["avg_price"]  # 简化处理，使用平均成本价
            
            # 更新持仓市值
            position["market_value"] = position["volume"] * current_price
            total_market_value += position["market_value"]
        
        # 更新总权益
        total_equity = self.account["cash"] + total_market_value
        
        # 更新账户
        self.account["total_equity"] = total_equity
        self.account["pnl"] = total_equity - self.params["initial_cash"]
        self.account["pnl_percentage"] = (self.account["pnl"] / self.params["initial_cash"]) * 100
    
    def record_account_state(self):
        """
        记录账户状态
        """
        # 记录账户历史
        account_state = {
            "timestamp": self.data.iloc[self.status["current_step"]].get("date", datetime.now()) if self.status["current_step"] < self.status["total_steps"] else datetime.now(),
            "cash": self.account["cash"],
            "total_equity": self.account["total_equity"],
            "pnl": self.account["pnl"],
            "pnl_percentage": self.account["pnl_percentage"]
        }
        self.results["account_history"].append(account_state)
        
        # 记录持仓历史
        positions_state = {
            "timestamp": account_state["timestamp"],
            "positions": self.account["positions"].copy()
        }
        self.results["positions_history"].append(positions_state)
    
    def calculate_performance_metrics(self):
        """
        计算性能指标
        """
        self.logger.info("计算性能指标")
        
        # 提取账户历史数据
        account_history = pd.DataFrame(self.results["account_history"])
        
        if len(account_history) == 0:
            self.logger.warning("账户历史数据为空，无法计算性能指标")
            return
        
        # 计算收益率
        returns = account_history["total_equity"].pct_change().dropna()
        
        if len(returns) == 0:
            self.logger.warning("收益率数据为空，无法计算性能指标")
            return
        
        # 计算性能指标
        total_return = (account_history["total_equity"].iloc[-1] / account_history["total_equity"].iloc[0] - 1) * 100
        
        # 计算年化收益率（假设一年252个交易日）
        days = (account_history["timestamp"].iloc[-1] - account_history["timestamp"].iloc[0]).days
        annual_return = (1 + total_return / 100) ** (365 / days) - 1 if days > 0 else 0
        annual_return *= 100
        
        # 计算波动率
        volatility = returns.std() * np.sqrt(252) * 100
        
        # 计算夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        sharpe_ratio = (annual_return / 100 - risk_free_rate) / (volatility / 100) if volatility > 0 else 0
        
        # 计算最大回撤
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # 计算索提诺比率
        negative_returns = returns[returns < 0]
        downside_risk = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = (annual_return / 100 - risk_free_rate) / downside_risk if downside_risk > 0 else 0
        
        # 计算胜率
        winning_trades = len([t for t in self.results["trades"] if (t["action"] == "buy" and t["price"] > t["price"]) or (t["action"] == "sell" and t["price"] < t["price"])])
        total_trades = len(self.results["trades"])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # 计算盈亏比
        total_profit = sum([t["volume"] * (t["price"] - t["price"]) for t in self.results["trades"] if (t["action"] == "buy" and t["price"] > t["price"]) or (t["action"] == "sell" and t["price"] < t["price"])])
        total_loss = sum([t["volume"] * (t["price"] - t["price"]) for t in self.results["trades"] if (t["action"] == "buy" and t["price"] < t["price"]) or (t["action"] == "sell" and t["price"] > t["price"])])
        profit_loss_ratio = abs(total_profit / total_loss) if total_loss != 0 else 0
        
        # 保存性能指标
        self.results["performance_metrics"] = {
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "win_rate": round(win_rate, 2),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            "total_trades": total_trades,
            "avg_trade_return": round(returns.mean() * 100, 4),
            "trading_days": len(account_history)
        }
        
        self.logger.info(f"性能指标计算完成: {self.results['performance_metrics']}")
    
    def reset(self):
        """
        重置回测引擎
        """
        self.logger.info("重置回测引擎")
        
        # 重置状态
        self.status = {
            "initialized": False,
            "running": False,
            "completed": False,
            "current_step": 0,
            "total_steps": len(self.data) if self.data is not None else 0
        }
        
        # 重置账户
        self.account = {
            "cash": self.params["initial_cash"],
            "total_equity": self.params["initial_cash"],
            "positions": {},
            "frozen_cash": 0,
            "pnl": 0,
            "pnl_percentage": 0
        }
        
        # 重置结果
        self.results = {
            "orders": [],
            "trades": [],
            "signals": [],
            "account_history": [],
            "positions_history": [],
            "performance_metrics": {}
        }
        
        # 重置订单计数器
        self.order_counter = 0
        
        # 重置撮合引擎
        self.matching_engine.reset()
        
        # 重置策略
        if self.strategy is not None:
            self.strategy.reset_strategy()
        
        self.logger.info("回测引擎重置完成")
    
    def get_results(self):
        """
        获取回测结果
        
        Returns:
            dict: 回测结果
        """
        return self.results
    
    def get_performance_metrics(self):
        """
        获取性能指标
        
        Returns:
            dict: 性能指标
        """
        return self.results["performance_metrics"]
    
    def get_account_history(self):
        """
        获取账户历史
        
        Returns:
            pd.DataFrame: 账户历史数据
        """
        return pd.DataFrame(self.results["account_history"])
    
    def save_results(self, file_path):
        """
        保存回测结果
        
        Args:
            file_path: 保存路径
        """
        self.logger.info(f"保存回测结果到: {file_path}")
        
        # 保存结果到JSON文件
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            # 将datetime对象转换为字符串
            def default_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.strftime('%Y-%m-%d %H:%M:%S')
                return obj
            
            json.dump(self.results, f, default=default_serializer, ensure_ascii=False, indent=2)
        
        self.logger.info("回测结果保存完成")
    
    def load_results(self, file_path):
        """
        加载回测结果
        
        Args:
            file_path: 加载路径
        """
        self.logger.info(f"加载回测结果从: {file_path}")
        
        # 从JSON文件加载结果
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            self.results = json.load(f)
        
        self.logger.info("回测结果加载完成")
