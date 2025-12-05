#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技术指标计算模块

实现常用技术指标的计算，如MACD、RSI、均线等
"""

import pandas as pd
import numpy as np
from log_utils import get_logger
from config_manager import get_config

# 获取日志记录器
logger = get_logger("technical_indicators")


class TechnicalIndicators:
    """
    技术指标计算类
    
    实现常用技术指标的计算
    """
    
    def __init__(self):
        """
        初始化技术指标计算类
        """
        logger.info("初始化技术指标计算模块")
        self.config = get_config()
        
        # 从配置中获取参数
        self.ma_periods = self.config.get("technical_indicators.ma_periods", [5, 10, 20, 30, 60, 120, 250])
        self.macd_fast = self.config.get("technical_indicators.macd.fast_period", 12)
        self.macd_slow = self.config.get("technical_indicators.macd.slow_period", 26)
        self.macd_signal = self.config.get("technical_indicators.macd.signal_period", 9)
        self.rsi_periods = self.config.get("technical_indicators.rsi.periods", [6, 12, 24])
        self.kdj_k = self.config.get("technical_indicators.kdj.k_period", 9)
        self.kdj_d = self.config.get("technical_indicators.kdj.d_period", 3)
        self.kdj_j = self.config.get("technical_indicators.kdj.j_period", 3)
        self.bollinger_period = self.config.get("technical_indicators.bollinger.period", 20)
        self.bollinger_std = self.config.get("technical_indicators.bollinger.std_dev", 2)
        
        logger.info("技术指标计算模块初始化完成")
    
    def calculate_moving_averages(self, df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 股票数据DataFrame
            periods: 均线周期列表，默认使用配置中的周期
            
        Returns:
            pd.DataFrame: 包含均线数据的DataFrame
        """
        logger.info("开始计算移动平均线")
        
        if periods is None:
            periods = self.ma_periods
        
        result_df = df.copy()
        
        for period in periods:
            # 计算均线
            result_df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            logger.info(f"计算 {period} 日均线完成")
        
        return result_df
    
    def calculate_macd(self, df: pd.DataFrame, fast_period: int = None, slow_period: int = None, signal_period: int = None) -> pd.DataFrame:
        """
        计算MACD指标
        
        MACD = 12日EMA - 26日EMA
        Signal = MACD的9日EMA
        Histogram = MACD - Signal
        
        Args:
            df: 股票数据DataFrame
            fast_period: 快速EMA周期
            slow_period: 慢速EMA周期
            signal_period: 信号线周期
            
        Returns:
            pd.DataFrame: 包含MACD数据的DataFrame
        """
        logger.info("开始计算MACD指标")
        
        if fast_period is None:
            fast_period = self.macd_fast
        if slow_period is None:
            slow_period = self.macd_slow
        if signal_period is None:
            signal_period = self.macd_signal
        
        result_df = df.copy()
        
        # 计算EMA
        ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # 计算MACD线
        result_df['MACD'] = ema_fast - ema_slow
        
        # 计算信号线
        result_df['MACD_Signal'] = result_df['MACD'].ewm(span=signal_period, adjust=False).mean()
        
        # 计算柱状图
        result_df['MACD_Hist'] = result_df['MACD'] - result_df['MACD_Signal']
        
        logger.info(f"计算MACD指标完成，参数: fast={fast_period}, slow={slow_period}, signal={signal_period}")
        
        return result_df
    
    def calculate_rsi(self, df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """
        计算RSI指标
        
        RSI = 100 - (100 / (1 + (平均上涨幅度 / 平均下跌幅度)))
        
        Args:
            df: 股票数据DataFrame
            periods: RSI周期列表
            
        Returns:
            pd.DataFrame: 包含RSI数据的DataFrame
        """
        logger.info("开始计算RSI指标")
        
        if periods is None:
            periods = self.rsi_periods
        
        result_df = df.copy()
        
        # 计算价格变化
        delta = df['close'].diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        for period in periods:
            # 计算平均上涨和下跌
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # 计算相对强度
            rs = avg_gain / avg_loss
            
            # 计算RSI
            result_df[f'RSI{period}'] = 100 - (100 / (1 + rs))
            logger.info(f"计算 RSI{period} 完成")
        
        return result_df
    
    def calculate_kdj(self, df: pd.DataFrame, k_period: int = None, d_period: int = None, j_period: int = None) -> pd.DataFrame:
        """
        计算KDJ指标
        
        RSV = (收盘价 - 最低价) / (最高价 - 最低价) * 100
        K = RSV的3日移动平均
        D = K的3日移动平均
        J = 3*K - 2*D
        
        Args:
            df: 股票数据DataFrame
            k_period: K线周期
            d_period: D线周期
            j_period: J线周期
            
        Returns:
            pd.DataFrame: 包含KDJ数据的DataFrame
        """
        logger.info("开始计算KDJ指标")
        
        if k_period is None:
            k_period = self.kdj_k
        if d_period is None:
            d_period = self.kdj_d
        if j_period is None:
            j_period = self.kdj_j
        
        result_df = df.copy()
        
        # 计算最高价和最低价的滚动窗口值
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        # 计算RSV
        result_df['RSV'] = (df['close'] - low_min) / (high_max - low_min) * 100
        
        # 计算K值（使用SMA）
        result_df['KDJ_K'] = result_df['RSV'].rolling(window=d_period).mean()
        
        # 计算D值
        result_df['KDJ_D'] = result_df['KDJ_K'].rolling(window=d_period).mean()
        
        # 计算J值
        result_df['KDJ_J'] = 3 * result_df['KDJ_K'] - 2 * result_df['KDJ_D']
        
        logger.info(f"计算KDJ指标完成，参数: K={k_period}, D={d_period}, J={j_period}")
        
        return result_df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = None, std_dev: float = None) -> pd.DataFrame:
        """
        计算布林带指标
        
        中轨 = N日移动平均线
        上轨 = 中轨 + K倍标准差
        下轨 = 中轨 - K倍标准差
        
        Args:
            df: 股票数据DataFrame
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            pd.DataFrame: 包含布林带数据的DataFrame
        """
        logger.info("开始计算布林带指标")
        
        if period is None:
            period = self.bollinger_period
        if std_dev is None:
            std_dev = self.bollinger_std
        
        result_df = df.copy()
        
        # 计算中轨（20日均线）
        result_df['BB_Mid'] = df['close'].rolling(window=period).mean()
        
        # 计算标准差
        std = df['close'].rolling(window=period).std()
        
        # 计算上轨和下轨
        result_df['BB_Upper'] = result_df['BB_Mid'] + (std_dev * std)
        result_df['BB_Lower'] = result_df['BB_Mid'] - (std_dev * std)
        
        logger.info(f"计算布林带指标完成，参数: 周期={period}, 标准差倍数={std_dev}")
        
        return result_df
    
    def calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        计算波动率
        
        Args:
            df: 股票数据DataFrame
            period: 周期
            
        Returns:
            pd.DataFrame: 包含波动率数据的DataFrame
        """
        logger.info("开始计算波动率")
        
        result_df = df.copy()
        
        # 计算日收益率
        returns = df['close'].pct_change()
        
        # 计算波动率（标准差）
        result_df['Volatility'] = returns.rolling(window=period).std() * np.sqrt(252)  # 年化波动率
        
        logger.info(f"计算 {period} 日波动率完成")
        
        return result_df
    
    def calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算成交量相关指标
        
        包括成交量5日、10日均线
        
        Args:
            df: 股票数据DataFrame
            
        Returns:
            pd.DataFrame: 包含成交量指标的DataFrame
        """
        logger.info("开始计算成交量指标")
        
        result_df = df.copy()
        
        # 成交量5日均线
        result_df['MAVOL5'] = df['volume'].rolling(window=5).mean()
        
        # 成交量10日均线
        result_df['MAVOL10'] = df['volume'].rolling(window=10).mean()
        
        logger.info("计算成交量指标完成")
        
        return result_df
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df: 股票数据DataFrame
            
        Returns:
            pd.DataFrame: 包含所有技术指标的DataFrame
        """
        logger.info("开始计算所有技术指标")
        
        # 确保数据按日期排序
        df = df.sort_values('date')
        
        # 计算所有指标
        result_df = self.calculate_moving_averages(df)
        result_df = self.calculate_macd(result_df)
        result_df = self.calculate_rsi(result_df)
        result_df = self.calculate_kdj(result_df)
        result_df = self.calculate_bollinger_bands(result_df)
        result_df = self.calculate_volatility(result_df)
        result_df = self.calculate_volume_indicators(result_df)
        
        logger.info("所有技术指标计算完成")
        
        return result_df
    
    def calculate_single_indicator(self, df: pd.DataFrame, indicator_name: str, **kwargs) -> pd.DataFrame:
        """
        计算单个技术指标
        
        Args:
            df: 股票数据DataFrame
            indicator_name: 指标名称，支持: 'ma', 'macd', 'rsi', 'kdj', 'bollinger', 'volatility', 'volume'
            **kwargs: 指标参数
            
        Returns:
            pd.DataFrame: 包含指定指标的DataFrame
        """
        logger.info(f"开始计算单个指标: {indicator_name}")
        
        indicator_map = {
            'ma': self.calculate_moving_averages,
            'macd': self.calculate_macd,
            'rsi': self.calculate_rsi,
            'kdj': self.calculate_kdj,
            'bollinger': self.calculate_bollinger_bands,
            'volatility': self.calculate_volatility,
            'volume': self.calculate_volume_indicators
        }
        
        if indicator_name not in indicator_map:
            logger.error(f"不支持的指标名称: {indicator_name}")
            return df.copy()
        
        # 计算指标
        result_df = indicator_map[indicator_name](df, **kwargs)
        
        logger.info(f"计算单个指标 {indicator_name} 完成")
        
        return result_df


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
    
    # 创建技术指标计算实例
    ti = TechnicalIndicators()
    
    # 计算所有指标
    result_df = ti.calculate_all_indicators(test_df)
    
    # 打印结果
    print("计算结果示例:")
    print(result_df[['date', 'close', 'MA5', 'MA10', 'MACD', 'RSI6', 'KDJ_K', 'KDJ_D', 'KDJ_J', 'BB_Mid', 'BB_Upper', 'BB_Lower']].tail(10))
    
    # 打印数据信息
    print("\n数据信息:")
    print(result_df.info())
