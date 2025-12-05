#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
撮合引擎

实现精准的撮合逻辑，模拟真实市场交易环境
"""

import pandas as pd
import numpy as np
from datetime import datetime
from log_utils import get_logger


class Order:
    """
    订单类
    
    定义订单的基本属性和状态
    """
    
    def __init__(self, order_id, symbol, action, price, volume, order_type="market", timestamp=None):
        """
        初始化订单
        
        Args:
            order_id: 订单ID
            symbol: 股票代码
            action: 交易方向，'buy' 或 'sell'
            price: 价格
            volume: 数量
            order_type: 订单类型，'market' 或 'limit'
            timestamp: 订单时间
        """
        self.order_id = order_id
        self.symbol = symbol
        self.action = action
        self.price = price
        self.volume = volume
        self.order_type = order_type
        self.timestamp = timestamp or datetime.now()
        self.status = "pending"  # pending, filled, partially_filled, cancelled
        self.filled_volume = 0
        self.filled_price = 0
        self.transaction_cost = 0
        self.slippage = 0
        self.fill_time = None
    
    def __repr__(self):
        return f"Order({self.order_id}, {self.symbol}, {self.action}, {self.price}, {self.volume}, {self.status})"


class MatchingEngine:
    """
    撮合引擎
    
    实现精准的撮合逻辑，模拟真实市场交易环境
    """
    
    def __init__(self):
        """
        初始化撮合引擎
        """
        self.logger = get_logger("matching_engine")
        self.logger.info("初始化撮合引擎")
        
        # 撮合参数
        self.params = {
            "transaction_cost": 0.0003,  # 交易成本（手续费）
            "slippage": 0.0001,  # 滑点
            "min_volume": 100,  # 最小成交数量
            "max_volume_per_trade": 1000000  # 每笔最大成交数量
        }
        
        # 订单簿
        self.order_book = {
            "buy": [],  # 买单列表
            "sell": []  # 卖单列表
        }
        
        # 成交记录
        self.trades = []
        
        self.logger.info("撮合引擎初始化完成")
    
    def set_params(self, params):
        """
        设置撮合参数
        
        Args:
            params: 撮合参数
        """
        self.logger.info(f"设置撮合参数: {params}")
        self.params.update(params)
    
    def add_order(self, order):
        """
        添加订单到订单簿
        
        Args:
            order: 订单对象
        """
        self.logger.info(f"添加订单: {order}")
        
        # 根据订单类型处理
        if order.order_type == "market":
            # 市价单直接撮合
            return self.match_market_order(order)
        elif order.order_type == "limit":
            # 限价单添加到订单簿
            self.order_book[order.action].append(order)
            # 排序订单簿
            self.sort_order_book()
            # 尝试撮合
            return self.match_limit_order(order)
        else:
            self.logger.error(f"不支持的订单类型: {order.order_type}")
            return None
    
    def match_market_order(self, order):
        """
        撮合市价单
        
        Args:
            order: 市价单对象
            
        Returns:
            dict: 成交结果
        """
        self.logger.info(f"撮合市价单: {order}")
        
        # 市价单总是以当前价格成交
        # 计算滑点
        slippage = order.price * self.params["slippage"]
        
        # 根据交易方向调整价格
        if order.action == "buy":
            fill_price = order.price + slippage  # 买单价格上浮
        else:
            fill_price = order.price - slippage  # 卖单价格下浮
        
        # 计算交易成本
        transaction_cost = fill_price * order.volume * self.params["transaction_cost"]
        
        # 更新订单状态
        order.status = "filled"
        order.filled_volume = order.volume
        order.filled_price = fill_price
        order.transaction_cost = transaction_cost
        order.slippage = slippage
        order.fill_time = datetime.now()
        
        # 生成成交记录
        trade = {
            "trade_id": f"trade_{datetime.now().timestamp()}",
            "order_id": order.order_id,
            "symbol": order.symbol,
            "action": order.action,
            "price": fill_price,
            "volume": order.volume,
            "transaction_cost": transaction_cost,
            "slippage": slippage,
            "timestamp": order.fill_time,
            "order_type": order.order_type
        }
        
        self.trades.append(trade)
        self.logger.info(f"市价单撮合完成: {trade}")
        
        return trade
    
    def match_limit_order(self, order):
        """
        撮合限价单
        
        Args:
            order: 限价单对象
            
        Returns:
            list: 成交结果列表
        """
        self.logger.info(f"撮合限价单: {order}")
        
        trades = []
        remaining_volume = order.volume
        
        # 买单和卖单匹配逻辑
        if order.action == "buy":
            # 买单匹配卖单
            for sell_order in self.order_book["sell"]:
                if sell_order.price <= order.price and remaining_volume > 0:
                    # 可以成交
                    fill_volume = min(remaining_volume, sell_order.volume - sell_order.filled_volume)
                    
                    # 计算成交价格（使用卖单价格）
                    fill_price = sell_order.price
                    
                    # 计算交易成本
                    transaction_cost = fill_price * fill_volume * self.params["transaction_cost"]
                    
                    # 更新订单状态
                    order.filled_volume += fill_volume
                    order.filled_price = fill_price
                    order.transaction_cost += transaction_cost
                    
                    sell_order.filled_volume += fill_volume
                    sell_order.filled_price = fill_price
                    sell_order.transaction_cost += transaction_cost
                    
                    # 生成成交记录
                    trade = {
                        "trade_id": f"trade_{datetime.now().timestamp()}_{len(trades)}",
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "action": order.action,
                        "price": fill_price,
                        "volume": fill_volume,
                        "transaction_cost": transaction_cost,
                        "timestamp": datetime.now(),
                        "order_type": order.order_type
                    }
                    
                    trades.append(trade)
                    self.trades.append(trade)
                    
                    remaining_volume -= fill_volume
                    
                    # 检查卖单是否完全成交
                    if sell_order.filled_volume >= sell_order.volume:
                        sell_order.status = "filled"
                        sell_order.fill_time = datetime.now()
                        self.order_book["sell"].remove(sell_order)
            
            # 更新买单状态
            if order.filled_volume > 0:
                if order.filled_volume >= order.volume:
                    order.status = "filled"
                    order.fill_time = datetime.now()
                    self.order_book["buy"].remove(order)
                else:
                    order.status = "partially_filled"
        else:
            # 卖单匹配买单
            for buy_order in self.order_book["buy"]:
                if buy_order.price >= order.price and remaining_volume > 0:
                    # 可以成交
                    fill_volume = min(remaining_volume, buy_order.volume - buy_order.filled_volume)
                    
                    # 计算成交价格（使用买单价格）
                    fill_price = buy_order.price
                    
                    # 计算交易成本
                    transaction_cost = fill_price * fill_volume * self.params["transaction_cost"]
                    
                    # 更新订单状态
                    order.filled_volume += fill_volume
                    order.filled_price = fill_price
                    order.transaction_cost += transaction_cost
                    
                    buy_order.filled_volume += fill_volume
                    buy_order.filled_price = fill_price
                    buy_order.transaction_cost += transaction_cost
                    
                    # 生成成交记录
                    trade = {
                        "trade_id": f"trade_{datetime.now().timestamp()}_{len(trades)}",
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "action": order.action,
                        "price": fill_price,
                        "volume": fill_volume,
                        "transaction_cost": transaction_cost,
                        "timestamp": datetime.now(),
                        "order_type": order.order_type
                    }
                    
                    trades.append(trade)
                    self.trades.append(trade)
                    
                    remaining_volume -= fill_volume
                    
                    # 检查买单是否完全成交
                    if buy_order.filled_volume >= buy_order.volume:
                        buy_order.status = "filled"
                        buy_order.fill_time = datetime.now()
                        self.order_book["buy"].remove(buy_order)
            
            # 更新卖单状态
            if order.filled_volume > 0:
                if order.filled_volume >= order.volume:
                    order.status = "filled"
                    order.fill_time = datetime.now()
                    self.order_book["sell"].remove(order)
                else:
                    order.status = "partially_filled"
        
        self.logger.info(f"限价单撮合完成，成交记录: {len(trades)}")
        return trades
    
    def sort_order_book(self):
        """
        排序订单簿
        
        买单按价格从高到低排序
        卖单按价格从低到高排序
        """
        # 排序买单（价格从高到低）
        self.order_book["buy"].sort(key=lambda x: x.price, reverse=True)
        
        # 排序卖单（价格从低到高）
        self.order_book["sell"].sort(key=lambda x: x.price)
    
    def cancel_order(self, order_id):
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            bool: 是否取消成功
        """
        self.logger.info(f"取消订单: {order_id}")
        
        # 在订单簿中查找订单
        for action in ["buy", "sell"]:
            for i, order in enumerate(self.order_book[action]):
                if order.order_id == order_id:
                    # 更新订单状态
                    order.status = "cancelled"
                    # 从订单簿中移除
                    self.order_book[action].pop(i)
                    self.logger.info(f"订单取消成功: {order_id}")
                    return True
        
        self.logger.error(f"订单不存在: {order_id}")
        return False
    
    def get_order_book(self):
        """
        获取订单簿
        
        Returns:
            dict: 订单簿数据
        """
        return self.order_book
    
    def get_trades(self):
        """
        获取成交记录
        
        Returns:
            list: 成交记录列表
        """
        return self.trades
    
    def reset(self):
        """
        重置撮合引擎
        """
        self.logger.info("重置撮合引擎")
        # 清空订单簿
        self.order_book = {
            "buy": [],
            "sell": []
        }
        # 清空成交记录
        self.trades = []
        self.logger.info("撮合引擎重置完成")
    
    def calculate_order_cost(self, order):
        """
        计算订单成本
        
        Args:
            order: 订单对象
            
        Returns:
            dict: 成本计算结果
        """
        # 计算滑点
        slippage = order.price * self.params["slippage"]
        
        # 计算成交价格
        if order.action == "buy":
            fill_price = order.price + slippage
        else:
            fill_price = order.price - slippage
        
        # 计算交易成本
        transaction_cost = fill_price * order.volume * self.params["transaction_cost"]
        
        # 计算总成本
        total_cost = fill_price * order.volume + transaction_cost
        
        return {
            "fill_price": fill_price,
            "slippage": slippage,
            "transaction_cost": transaction_cost,
            "total_cost": total_cost
        }
