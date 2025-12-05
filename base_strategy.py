#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略基类

实现策略接口的基本功能，提供常用辅助方法，方便用户继承和扩展
"""

import pandas as pd
import numpy as np
from strategy_interface import StrategyInterface
from technical_indicators import TechnicalIndicators
from log_utils import get_logger


class BaseStrategy(StrategyInterface):
    """
    策略基类
    
    实现策略接口的基本功能，提供常用辅助方法
    """
    
    def __init__(self):
        """
        初始化策略基类
        """
        self.logger = get_logger("base_strategy")
        self.logger.info("初始化策略基类")
        
        # 初始化技术指标计算模块
        self.technical_indicators = TechnicalIndicators()
        
        # 策略参数
        self.params = {
            "name": "BaseStrategy",
            "initial_cash": 1000000,
            "transaction_cost": 0.0003,
            "slippage": 0.0001,
            "max_position_percentage": 0.1
        }
        
        # 策略状态
        self.status = {
            "initialized": False,
            "running": False,
            "signals": [],
            "orders": [],
            "trades": []
        }
        
        self.logger.info("策略基类初始化完成")
    
    def initialize(self, data, context):
        """
        策略初始化方法
        
        Args:
            data: 回测数据
            context: 回测上下文，包含初始资金、持仓等信息
        """
        self.logger.info("初始化策略")
        self.status["initialized"] = True
        self.status["running"] = False
        
        # 计算技术指标
        if isinstance(data, pd.DataFrame):
            self.data_with_indicators = self.technical_indicators.calculate_all_indicators(data)
        else:
            self.data_with_indicators = data
        
        # 计算自定义指标
        self.data_with_indicators = self.calculate_custom_indicators(self.data_with_indicators)
        
        self.logger.info("策略初始化完成")
    
    def on_bar(self, data, context):
        """
        K线级别的策略执行方法
        
        Args:
            data: 当前K线数据
            context: 当前回测上下文，包含持仓、资金等信息
        """
        # 生成交易信号
        signals = self.generate_signals(data, context)
        
        # 执行订单
        for signal in signals:
            result = self.execute_order(signal, context)
            if result:
                self.status["trades"].append(result)
    
    def on_tick(self, data, context):
        """
        Tick级别的策略执行方法
        
        Args:
            data: 当前Tick数据
            context: 当前回测上下文，包含持仓、资金等信息
        """
        # 默认不实现Tick级别策略
        pass
    
    def generate_signals(self, data, context):
        """
        生成交易信号
        
        Args:
            data: 回测数据
            context: 回测上下文
            
        Returns:
            list: 交易信号列表
        """
        # 默认返回空信号列表，子类需要重写
        return []
    
    def execute_order(self, signal, context):
        """
        执行订单
        
        Args:
            signal: 交易信号
            context: 回测上下文
            
        Returns:
            dict: 订单执行结果
        """
        self.logger.info(f"执行订单: {signal}")
        
        # 简单的订单执行逻辑，回测引擎会进行实际撮合
        order_result = {
            "symbol": signal["symbol"],
            "action": signal["action"],
            "price": signal["price"],
            "volume": signal["volume"],
            "timestamp": pd.Timestamp.now(),
            "status": "pending"
        }
        
        return order_result
    
    def calculate_custom_indicators(self, data):
        """
        计算自定义指标
        
        Args:
            data: 回测数据
            
        Returns:
            pd.DataFrame: 包含自定义指标的数据
        """
        # 默认返回原始数据，子类可以重写以添加自定义指标
        return data
    
    def get_strategy_params(self):
        """
        获取策略参数
        
        Returns:
            dict: 策略参数
        """
        return self.params
    
    def set_strategy_params(self, params):
        """
        设置策略参数
        
        Args:
            params: 策略参数
        """
        self.logger.info(f"设置策略参数: {params}")
        self.params.update(params)
    
    def add_signal(self, signal):
        """
        添加交易信号
        
        Args:
            signal: 交易信号
        """
        self.status["signals"].append(signal)
    
    def get_signals(self):
        """
        获取所有交易信号
        
        Returns:
            list: 交易信号列表
        """
        return self.status["signals"]
    
    def get_trades(self):
        """
        获取所有交易记录
        
        Returns:
            list: 交易记录列表
        """
        return self.status["trades"]
    
    def reset_strategy(self):
        """
        重置策略状态
        """
        self.logger.info("重置策略状态")
        self.status = {
            "initialized": False,
            "running": False,
            "signals": [],
            "orders": [],
            "trades": []
        }
    
    def calculate_position_size(self, context, price, risk_per_trade=0.01):
        """
        计算仓位大小
        
        Args:
            context: 回测上下文
            price: 价格
            risk_per_trade: 每笔交易风险比例
            
        Returns:
            int: 持仓数量
        """
        # 计算可用于交易的资金
        available_cash = context["cash"] * self.params["max_position_percentage"]
        
        # 计算持仓数量（向下取整）
        position_size = int(available_cash / (price * (1 + self.params["transaction_cost"] + self.params["slippage"])))
        
        return max(position_size, 0)
    
    def is_buy_signal(self, data):
        """
        判断买入信号
        
        Args:
            data: 当前数据
            
        Returns:
            bool: 是否为买入信号
        """
        # 默认返回False，子类需要重写
        return False
    
    def is_sell_signal(self, data):
        """
        判断卖出信号
        
        Args:
            data: 当前数据
            
        Returns:
            bool: 是否为卖出信号
        """
        # 默认返回False，子类需要重写
        return False
