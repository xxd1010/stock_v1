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
        
        Raises:
            ValueError: 当股票代码或日期范围与配置不一致时抛出
        """
        self.logger.info(f"设置回测参数前的当前值: {self.params}")
        self.logger.info(f"设置的新参数: {params}")
        
        # 记录参数来源和最终值
        for key, value in params.items():
            self.logger.info(f"参数 {key}: 原值={self.params.get(key)}, 新值={value}, 来源=传入参数")
        
        # 更新参数
        self.params.update(params)
        
        # 从配置管理器获取配置，验证关键参数一致性
        from config_manager import get_config
        config = get_config()
        
        # 验证日期范围一致性（如果配置中有明确日期）
        config_start_date = config.get("backtest.start_date")
        config_end_date = config.get("backtest.end_date")
        
        if "start_date" in params and config_start_date:
            if params["start_date"] != config_start_date:
                error_msg = f"开始日期不一致 - 配置: {config_start_date}, 实际: {params['start_date']}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        if "end_date" in params and config_end_date:
            if params["end_date"] != config_end_date:
                error_msg = f"结束日期不一致 - 配置: {config_end_date}, 实际: {params['end_date']}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        # 更新撮合引擎参数
        self.matching_engine.set_params({
            "transaction_cost": params.get("transaction_cost", self.params["transaction_cost"]),
            "slippage": params.get("slippage", self.params["slippage"])
        })
        self.logger.info(f"更新撮合引擎参数 - 交易成本: {self.params['transaction_cost']}, 滑点: {self.params['slippage']}")
        
        # 更新初始资金
        if "initial_cash" in params:
            old_cash = self.account["cash"]
            self.account["cash"] = params["initial_cash"]
            self.account["total_equity"] = params["initial_cash"]
            self.logger.info(f"更新初始资金 - 原值: {old_cash}, 新值: {params['initial_cash']}")
        
        self.logger.info(f"参数设置完成，最终回测参数: {self.params}")
    
    def load_data(self, data):
        """
        加载回测数据
        
        Args:
            data: 回测数据，可以是DataFrame或数据文件路径
            
        Raises:
            ValueError: 当配置参数与实际数据不一致时抛出
        """
        self.logger.info(f"开始加载回测数据")
        
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
        date_col = 'date' if 'date' in self.data.columns else 'datetime' if 'datetime' in self.data.columns else None
        if date_col is None:
            raise ValueError("数据中缺少日期列(date或datetime)")
        
        self.data[date_col] = pd.to_datetime(self.data[date_col])
        self.data = self.data.sort_values(date_col)
        
        # 提取数据的股票代码（使用第一个股票代码）
        stock_code = self.data.get('code', self.data.get('symbol', None))
        if stock_code is not None:
            self.data_stock_code = stock_code.iloc[0] if isinstance(stock_code, pd.Series) else stock_code
            self.logger.info(f"数据中的股票代码: {self.data_stock_code}")
        
        # 提取数据的实际日期范围
        self.data_start_date = self.data[date_col].min().strftime('%Y-%m-%d')
        self.data_end_date = self.data[date_col].max().strftime('%Y-%m-%d')
        self.logger.info(f"数据的实际日期范围: {self.data_start_date} 至 {self.data_end_date}")
        
        # 设置日期索引
        self.data.set_index(date_col, inplace=True)
        
        # 过滤日期范围
        if self.params["start_date"] and self.params["end_date"]:
            self.logger.info(f"回测引擎配置的日期范围: {self.params['start_date']} 至 {self.params['end_date']}")
            
            # 验证回测日期范围是否在数据实际日期范围内
            if pd.to_datetime(self.params["start_date"]) < pd.to_datetime(self.data_start_date):
                self.logger.warning(f"回测开始日期 {self.params['start_date']} 早于数据实际开始日期 {self.data_start_date}")
            if pd.to_datetime(self.params["end_date"]) > pd.to_datetime(self.data_end_date):
                self.logger.warning(f"回测结束日期 {self.params['end_date']} 晚于数据实际结束日期 {self.data_end_date}")
            
            self.data = self.data.loc[self.params["start_date"]:self.params["end_date"]]
        
        # 重置索引
        self.data.reset_index(inplace=True)
        
        # 记录过滤后的实际回测日期范围
        if not self.data.empty:
            self.actual_start_date = self.data[date_col].min().strftime('%Y-%m-%d')
            self.actual_end_date = self.data[date_col].max().strftime('%Y-%m-%d')
            self.logger.info(f"过滤后的实际回测日期范围: {self.actual_start_date} 至 {self.actual_end_date}")
        
        self.logger.info(f"回测数据加载完成，共 {len(self.data)} 条记录")
        self.status["total_steps"] = len(self.data)
        
        # 验证数据完整性
        if self.data.empty:
            raise ValueError("加载的数据为空，请检查数据来源或日期范围")
    
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
        
        Raises:
            ValueError: 当股票代码与配置不一致时抛出
        """
        self.logger.info(f"从数据源获取回测数据: 股票代码={stock_code}, 开始日期={start_date}, 结束日期={end_date}, 频率={frequency}")
        
        # 使用回测参数中的日期如果未提供
        if start_date is None:
            start_date = self.params["start_date"]
        if end_date is None:
            end_date = self.params["end_date"]
        
        # 从配置管理器获取配置的股票代码，添加参数一致性验证
        from config_manager import get_config
        config = get_config()
        config_stock_code = config.get("sample_data.symbol")
        
        # 验证股票代码一致性
        if config_stock_code and stock_code and config_stock_code != stock_code:
            error_msg = f"股票代码不一致 - 配置: {config_stock_code}, 实际: {stock_code}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 记录参数来源和最终使用值
        self.logger.info(f"参数来源 - 股票代码: {'传入参数' if stock_code else '配置文件'}, 开始日期: {'传入参数' if start_date else '配置文件'}, 结束日期: {'传入参数' if end_date else '配置文件'}")
        self.logger.info(f"最终使用参数 - 股票代码={stock_code}, 开始日期={start_date}, 结束日期={end_date}")
        
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
        
        # 记录数据的实际股票代码和日期范围
        self.data_stock_code = stock_code
        self.data_start_date = self.data['date'].min().strftime('%Y-%m-%d')
        self.data_end_date = self.data['date'].max().strftime('%Y-%m-%d')
        self.logger.info(f"数据实际信息 - 股票代码: {self.data_stock_code}, 日期范围: {self.data_start_date} 至 {self.data_end_date}")
        
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
        
        Raises:
            ValueError: 当配置参数与实际数据不一致时抛出
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
        
        # 从配置管理器获取配置的股票代码和日期范围，进行参数一致性检查
        from config_manager import get_config
        config = get_config()
        config_stock_code = config.get("sample_data.symbol")
        config_start_date = config.get("backtest.start_date")
        config_end_date = config.get("backtest.end_date")
        
        # 确保data_stock_code属性存在
        if not hasattr(self, 'data_stock_code'):
            # 从数据中提取股票代码
            stock_code = self.data.get('code', self.data.get('symbol', None))
            if stock_code is not None:
                self.data_stock_code = stock_code.iloc[0] if isinstance(stock_code, pd.Series) else stock_code
            else:
                self.data_stock_code = None
        
        # 确保data_start_date和data_end_date属性存在
        if not hasattr(self, 'data_start_date') or not hasattr(self, 'data_end_date'):
            # 从数据中提取日期范围
            date_col = 'date' if 'date' in self.data.columns else 'datetime' if 'datetime' in self.data.columns else None
            if date_col is None:
                raise ValueError("数据中缺少日期列(date或datetime)")
            
            self.data_start_date = self.data[date_col].min().strftime('%Y-%m-%d')
            self.data_end_date = self.data[date_col].max().strftime('%Y-%m-%d')
        
        # 验证股票代码一致性
        if config_stock_code and self.data_stock_code and config_stock_code != self.data_stock_code:
            error_msg = f"股票代码不一致 - 配置: {config_stock_code}, 实际数据: {self.data_stock_code}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证日期范围一致性
        if config_start_date and self.params["start_date"] and config_start_date != self.params["start_date"]:
            error_msg = f"开始日期不一致 - 配置: {config_start_date}, 回测参数: {self.params['start_date']}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if config_end_date and self.params["end_date"] and config_end_date != self.params["end_date"]:
            error_msg = f"结束日期不一致 - 配置: {config_end_date}, 回测参数: {self.params['end_date']}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 调用配置管理器的参数一致性校验函数
        config.validate_param_consistency(
            actual_stock_code=self.data_stock_code,
            actual_start_date=self.data_start_date,
            actual_end_date=self.data_end_date
        )
        
        # 初始化策略
        self.strategy.initialize(self.data, self.account)
        
        # 获取策略计算的指标数据
        if hasattr(self.strategy, 'data_with_indicators'):
            self.data_with_indicators = self.strategy.data_with_indicators
        else:
            self.data_with_indicators = self.data
        
        # 记录初始账户状态
        self.record_account_state()
        
        # 打印回测参数摘要
        self.logger.info("=== 回测参数摘要 ===")
        self.logger.info(f"股票代码: {self.data_stock_code}")
        self.logger.info(f"配置回测日期范围: {config_start_date} 至 {config_end_date}")
        self.logger.info(f"回测引擎日期范围: {self.params['start_date']} 至 {self.params['end_date']}")
        self.logger.info(f"数据实际日期范围: {self.data_start_date} 至 {self.data_end_date}")
        self.logger.info(f"初始资金: {self.params['initial_cash']}")
        self.logger.info(f"交易成本: {self.params['transaction_cost']}")
        self.logger.info(f"滑点: {self.params['slippage']}")
        self.logger.info(f"数据条数: {len(self.data)}")
        self.logger.info(f"策略名称: {self.strategy.__class__.__name__}")
        self.logger.info("=== 回测参数摘要结束 ===")
        
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
