#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略接口定义

提供策略编写的标准接口，定义策略必须实现的方法
"""

from abc import ABC, abstractmethod


class StrategyInterface(ABC):
    """
    策略接口类
    
    定义策略必须实现的核心方法
    """
    
    @abstractmethod
    def initialize(self, data, context):
        """
        策略初始化方法
        
        Args:
            data: 回测数据
            context: 回测上下文，包含初始资金、持仓等信息
        """
        pass
    
    @abstractmethod
    def on_bar(self, data, context):
        """
        K线级别的策略执行方法
        
        Args:
            data: 当前K线数据
            context: 当前回测上下文，包含持仓、资金等信息
        """
        pass
    
    @abstractmethod
    def on_tick(self, data, context):
        """
        Tick级别的策略执行方法
        
        Args:
            data: 当前Tick数据
            context: 当前回测上下文，包含持仓、资金等信息
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data, context):
        """
        生成交易信号
        
        Args:
            data: 回测数据
            context: 回测上下文
            
        Returns:
            list: 交易信号列表，每个信号包含：
                - action: 'buy' 或 'sell'
                - symbol: 股票代码
                - price: 价格
                - volume: 数量
        """
        pass
    
    @abstractmethod
    def execute_order(self, signal, context):
        """
        执行订单
        
        Args:
            signal: 交易信号
            context: 回测上下文
            
        Returns:
            dict: 订单执行结果
        """
        pass
    
    @abstractmethod
    def calculate_custom_indicators(self, data):
        """
        计算自定义指标
        
        Args:
            data: 回测数据
            
        Returns:
            pd.DataFrame: 包含自定义指标的数据
        """
        pass
    
    @abstractmethod
    def get_strategy_params(self):
        """
        获取策略参数
        
        Returns:
            dict: 策略参数
        """
        pass
    
    @abstractmethod
    def set_strategy_params(self, params):
        """
        设置策略参数
        
        Args:
            params: 策略参数
        """
        pass
