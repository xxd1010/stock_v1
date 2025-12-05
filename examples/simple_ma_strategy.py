#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例策略：双均线策略

实现一个简单的双均线策略，当短期均线上穿长期均线时买入，下穿时卖出
"""

import pandas as pd
import numpy as np
from base_strategy import BaseStrategy
from log_utils import get_logger


class SimpleMAStrategy(BaseStrategy):
    """
    简单双均线策略
    
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    
    def __init__(self):
        """
        初始化策略
        """
        super().__init__()
        self.logger = get_logger("simple_ma_strategy")
        self.logger.info("初始化双均线策略")
        
        # 策略参数
        self.params = {
            "name": "SimpleMAStrategy",
            "ma_short": 10,  # 短期均线周期
            "ma_long": 20,  # 长期均线周期
            "initial_cash": 1000000,
            "transaction_cost": 0.0003,
            "slippage": 0.0001,
            "max_position_percentage": 0.1
        }
        
        # 策略状态
        self.status = {
            "position": 0,  # 当前持仓数量
            "last_signal": None,  # 上一次交易信号
            "last_cross": None  # 上一次均线交叉方向
        }
        
        self.logger.info("双均线策略初始化完成")
    
    def calculate_custom_indicators(self, data):
        """
        计算自定义指标
        
        Args:
            data: 回测数据
            
        Returns:
            pd.DataFrame: 包含自定义指标的数据
        """
        self.logger.info("计算双均线策略自定义指标")
        
        # 计算短期均线
        data[f"MA{self.params['ma_short']}"] = data["close"].rolling(window=self.params["ma_short"]).mean()
        
        # 计算长期均线
        data[f"MA{self.params['ma_long']}"] = data["close"].rolling(window=self.params["ma_long"]).mean()
        
        # 计算均线交叉信号
        data["ma_diff"] = data[f"MA{self.params['ma_short']}"] - data[f"MA{self.params['ma_long']}"]
        data["ma_cross"] = 0
        
        # 金叉：短期均线上穿长期均线
        data.loc[(data["ma_diff"] > 0) & (data["ma_diff"].shift(1) < 0), "ma_cross"] = 1
        
        # 死叉：短期均线下穿长期均线
        data.loc[(data["ma_diff"] < 0) & (data["ma_diff"].shift(1) > 0), "ma_cross"] = -1
        
        self.logger.info("双均线策略自定义指标计算完成")
        return data
    
    def generate_signals(self, data, context):
        """
        生成交易信号
        
        Args:
            data: 当前数据
            context: 回测上下文
            
        Returns:
            list: 交易信号列表
        """
        signals = []
        
        # 获取当前日期和价格
        current_date = data.get("date", data.get("datetime", pd.Timestamp.now()))
        current_price = data["close"]
        
        # 检查是否有均线交叉
        if data["ma_cross"] == 1:  # 金叉，买入信号
            if self.status["position"] <= 0:
                # 计算买入数量
                volume = self.calculate_position_size(context, current_price)
                if volume > 0:
                    signal = {
                        "symbol": data.get("code", data.get("symbol", "UNKNOWN")),
                        "action": "buy",
                        "price": current_price,
                        "volume": volume,
                        "timestamp": current_date,
                        "signal_type": "golden_cross",
                        "strategy": self.params["name"]
                    }
                    signals.append(signal)
                    self.status["last_signal"] = "buy"
                    self.status["last_cross"] = "golden"
        
        elif data["ma_cross"] == -1:  # 死叉，卖出信号
            if self.status["position"] > 0:
                # 卖出全部持仓
                volume = self.status["position"]
                signal = {
                    "symbol": data.get("code", data.get("symbol", "UNKNOWN")),
                    "action": "sell",
                    "price": current_price,
                    "volume": volume,
                    "timestamp": current_date,
                    "signal_type": "death_cross",
                    "strategy": self.params["name"]
                }
                signals.append(signal)
                self.status["last_signal"] = "sell"
                self.status["last_cross"] = "death"
        
        return signals
    
    def execute_order(self, signal, context):
        """
        执行订单
        
        Args:
            signal: 交易信号
            context: 回测上下文
            
        Returns:
            dict: 订单执行结果
        """
        order_result = super().execute_order(signal, context)
        
        # 更新策略状态
        if order_result:
            if signal["action"] == "buy":
                self.status["position"] += order_result["volume"]
            elif signal["action"] == "sell":
                self.status["position"] -= order_result["volume"]
        
        return order_result
    
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
        super().set_strategy_params(params)
        self.logger.info(f"更新双均线策略参数: {params}")
    
    def reset_strategy(self):
        """
        重置策略状态
        """
        super().reset_strategy()
        # 添加自定义状态字段
        self.status.update({
            "position": 0,  # 当前持仓数量
            "last_signal": None,  # 上一次交易信号
            "last_cross": None  # 上一次均线交叉方向
        })
    
    def is_buy_signal(self, data):
        """
        判断买入信号
        
        Args:
            data: 当前数据
            
        Returns:
            bool: 是否为买入信号
        """
        return data["ma_cross"] == 1
    
    def is_sell_signal(self, data):
        """
        判断卖出信号
        
        Args:
            data: 当前数据
            
        Returns:
            bool: 是否为卖出信号
        """
        return data["ma_cross"] == -1
