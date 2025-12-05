#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
趋势分析模块

基于技术指标进行趋势预测和分析
"""

import pandas as pd
import numpy as np
from log_utils import get_logger

# 获取日志记录器
logger = get_logger("trend_analysis")


class TrendAnalysis:
    """
    趋势分析类
    
    基于技术指标进行趋势识别、支撑阻力位计算和K线形态分析
    """
    
    def __init__(self):
        """
        初始化趋势分析类
        """
        logger.info("初始化趋势分析模块")
        
        # 趋势判断参数
        self.trend_threshold = 0.02  # 趋势阈值，用于判断上涨/下跌/横盘
        self.support_resistance_window = 20  # 支撑阻力位计算窗口
        
        logger.info("趋势分析模块初始化完成")
    
    def identify_trend(self, df: pd.DataFrame, method: str = "ma") -> pd.DataFrame:
        """
        趋势识别
        
        根据不同方法识别股票趋势（上涨、下跌、横盘）
        
        Args:
            df: 包含技术指标的股票数据
            method: 趋势识别方法，可选值: "ma"（均线）, "macd"（MACD）, "combined"（综合）
            
        Returns:
            pd.DataFrame: 包含趋势信息的DataFrame
        """
        logger.info(f"开始趋势识别，方法: {method}")
        
        result_df = df.copy()
        
        if method == "ma":
            # 基于均线的趋势识别
            result_df = self._identify_trend_by_ma(result_df)
        elif method == "macd":
            # 基于MACD的趋势识别
            result_df = self._identify_trend_by_macd(result_df)
        elif method == "combined":
            # 综合多种方法的趋势识别
            result_df = self._identify_trend_combined(result_df)
        else:
            logger.error(f"不支持的趋势识别方法: {method}")
            return result_df
        
        logger.info("趋势识别完成")
        return result_df
    
    def _identify_trend_by_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于均线的趋势识别
        
        根据短期均线和长期均线的关系判断趋势
        
        Args:
            df: 包含均线数据的股票数据
            
        Returns:
            pd.DataFrame: 包含趋势信息的DataFrame
        """
        # 确保数据包含MA5和MA20
        if 'MA5' not in df.columns or 'MA20' not in df.columns:
            logger.error("均线数据不完整，无法进行趋势识别")
            return df
        
        # 计算均线斜率（使用最近5天的数据）
        df['MA5_Slope'] = df['MA5'].diff(periods=5) / 5
        df['MA20_Slope'] = df['MA20'].diff(periods=5) / 5
        
        # 计算收盘价相对MA20的偏离程度
        df['Price_MA20_Ratio'] = (df['close'] - df['MA20']) / df['MA20']
        
        # 趋势判断
        def get_trend(row):
            if row['Price_MA20_Ratio'] > self.trend_threshold and row['MA5_Slope'] > 0 and row['MA20_Slope'] > 0:
                return '上涨'
            elif row['Price_MA20_Ratio'] < -self.trend_threshold and row['MA5_Slope'] < 0 and row['MA20_Slope'] < 0:
                return '下跌'
            else:
                return '横盘'
        
        df['Trend'] = df.apply(get_trend, axis=1)
        
        return df
    
    def _identify_trend_by_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于MACD的趋势识别
        
        根据MACD线和信号线的关系判断趋势
        
        Args:
            df: 包含MACD数据的股票数据
            
        Returns:
            pd.DataFrame: 包含趋势信息的DataFrame
        """
        # 确保数据包含MACD相关列
        if 'MACD' not in df.columns or 'MACD_Signal' not in df.columns or 'MACD_Hist' not in df.columns:
            logger.error("MACD数据不完整，无法进行趋势识别")
            return df
        
        # 趋势判断
        def get_trend(row):
            if row['MACD'] > row['MACD_Signal'] and row['MACD_Hist'] > 0:
                return '上涨'
            elif row['MACD'] < row['MACD_Signal'] and row['MACD_Hist'] < 0:
                return '下跌'
            else:
                return '横盘'
        
        df['Trend'] = df.apply(get_trend, axis=1)
        
        return df
    
    def _identify_trend_combined(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        综合多种方法的趋势识别
        
        结合均线、MACD等多种指标判断趋势
        
        Args:
            df: 包含技术指标的股票数据
            
        Returns:
            pd.DataFrame: 包含趋势信息的DataFrame
        """
        # 先使用均线和MACD分别识别趋势
        df = self._identify_trend_by_ma(df)
        df = self._identify_trend_by_macd(df)
        
        # 保存MA趋势结果
        df['Trend_MA'] = df['Trend']
        
        # 再次使用MACD识别趋势
        df = self._identify_trend_by_macd(df)
        df['Trend_MACD'] = df['Trend']
        
        # 综合判断趋势
        def get_combined_trend(row):
            # 如果两种方法判断一致，则使用该趋势
            if row['Trend_MA'] == row['Trend_MACD']:
                return row['Trend_MA']
            # 否则，基于MACD和均线斜率综合判断
            elif row['MACD_Hist'] > 0 and row['MA5_Slope'] > 0:
                return '上涨'
            elif row['MACD_Hist'] < 0 and row['MA5_Slope'] < 0:
                return '下跌'
            else:
                return '横盘'
        
        df['Trend'] = df.apply(get_combined_trend, axis=1)
        
        return df
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = None) -> tuple:
        """
        计算支撑位和阻力位
        
        基于价格波动计算支撑位和阻力位
        
        Args:
            df: 股票数据
            window: 计算窗口，默认使用类初始化的窗口
            
        Returns:
            tuple: (支撑位列表, 阻力位列表)
        """
        logger.info("开始计算支撑位和阻力位")
        
        if window is None:
            window = self.support_resistance_window
        
        # 获取最近window天的数据
        recent_data = df.tail(window)
        
        # 计算支撑位（最低价的峰值）
        support_levels = self._find_support_levels(recent_data)
        
        # 计算阻力位（最高价的峰值）
        resistance_levels = self._find_resistance_levels(recent_data)
        
        logger.info(f"支撑位计算完成: {support_levels}")
        logger.info(f"阻力位计算完成: {resistance_levels}")
        
        return support_levels, resistance_levels
    
    def _find_support_levels(self, df: pd.DataFrame) -> list:
        """
        查找支撑位
        
        Args:
            df: 股票数据
            
        Returns:
            list: 支撑位列表
        """
        # 使用价格的最低价计算支撑位
        # 找到最低价中的局部最小值
        lows = df['low'].values
        support_levels = []
        
        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                support_levels.append(round(lows[i], 2))
        
        # 去重并排序
        support_levels = sorted(list(set(support_levels)))
        
        # 只保留最近的几个支撑位
        return support_levels[-3:]
    
    def _find_resistance_levels(self, df: pd.DataFrame) -> list:
        """
        查找阻力位
        
        Args:
            df: 股票数据
            
        Returns:
            list: 阻力位列表
        """
        # 使用价格的最高价计算阻力位
        # 找到最高价中的局部最大值
        highs = df['high'].values
        resistance_levels = []
        
        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                resistance_levels.append(round(highs[i], 2))
        
        # 去重并排序
        resistance_levels = sorted(list(set(resistance_levels)))
        
        # 只保留最近的几个阻力位
        return resistance_levels[-3:]
    
    def identify_candlestick_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        K线形态识别
        
        识别常见的K线形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含K线形态信息的DataFrame
        """
        logger.info("开始K线形态识别")
        
        result_df = df.copy()
        
        # 初始化形态列
        result_df['Candlestick_Pattern'] = 'Unknown'
        
        # 识别各种K线形态
        result_df = self._identify_bullish_engulfing(result_df)
        result_df = self._identify_bearish_engulfing(result_df)
        result_df = self._identify_hammer(result_df)
        result_df = self._identify_hanging_man(result_df)
        result_df = self._identify_morning_star(result_df)
        result_df = self._identify_evening_star(result_df)
        
        logger.info("K线形态识别完成")
        return result_df
    
    def _identify_bullish_engulfing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别看涨吞没形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含形态信息的DataFrame
        """
        for i in range(1, len(df)):
            # 前一天是阴线
            if df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                # 当天是阳线
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    # 当天开盘价低于前一天收盘价
                    if df['open'].iloc[i] < df['close'].iloc[i-1]:
                        # 当天收盘价高于前一天开盘价
                        if df['close'].iloc[i] > df['open'].iloc[i-1]:
                            df.loc[df.index[i], 'Candlestick_Pattern'] = 'Bullish Engulfing'
        
        return df
    
    def _identify_bearish_engulfing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别看跌吞没形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含形态信息的DataFrame
        """
        for i in range(1, len(df)):
            # 前一天是阳线
            if df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                # 当天是阴线
                if df['close'].iloc[i] < df['open'].iloc[i]:
                    # 当天开盘价高于前一天收盘价
                    if df['open'].iloc[i] > df['close'].iloc[i-1]:
                        # 当天收盘价低于前一天开盘价
                        if df['close'].iloc[i] < df['open'].iloc[i-1]:
                            df.loc[df.index[i], 'Candlestick_Pattern'] = 'Bearish Engulfing'
        
        return df
    
    def _identify_hammer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别锤子线形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含形态信息的DataFrame
        """
        for i in range(len(df)):
            # 计算实体长度
            body_length = abs(df['close'].iloc[i] - df['open'].iloc[i])
            # 计算下影线长度
            if df['close'].iloc[i] > df['open'].iloc[i]:
                lower_shadow = df['open'].iloc[i] - df['low'].iloc[i]
            else:
                lower_shadow = df['close'].iloc[i] - df['low'].iloc[i]
            # 计算上影线长度
            if df['close'].iloc[i] > df['open'].iloc[i]:
                upper_shadow = df['high'].iloc[i] - df['close'].iloc[i]
            else:
                upper_shadow = df['high'].iloc[i] - df['open'].iloc[i]
            
            # 锤子线条件：实体小，下影线长，上影线短
            if body_length < lower_shadow * 0.5 and upper_shadow < body_length * 0.5:
                df.loc[df.index[i], 'Candlestick_Pattern'] = 'Hammer'
        
        return df
    
    def _identify_hanging_man(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别上吊线形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含形态信息的DataFrame
        """
        # 上吊线形态与锤子线类似，但出现在上涨趋势末尾
        for i in range(len(df)):
            # 计算实体长度
            body_length = abs(df['close'].iloc[i] - df['open'].iloc[i])
            # 计算下影线长度
            if df['close'].iloc[i] > df['open'].iloc[i]:
                lower_shadow = df['open'].iloc[i] - df['low'].iloc[i]
            else:
                lower_shadow = df['close'].iloc[i] - df['low'].iloc[i]
            # 计算上影线长度
            if df['close'].iloc[i] > df['open'].iloc[i]:
                upper_shadow = df['high'].iloc[i] - df['close'].iloc[i]
            else:
                upper_shadow = df['high'].iloc[i] - df['open'].iloc[i]
            
            # 上吊线条件：实体小，下影线长，上影线短
            if body_length < lower_shadow * 0.5 and upper_shadow < body_length * 0.5:
                df.loc[df.index[i], 'Candlestick_Pattern'] = 'Hanging Man'
        
        return df
    
    def _identify_morning_star(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别早晨之星形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含形态信息的DataFrame
        """
        for i in range(2, len(df)):
            # 第一天是阴线
            if df['close'].iloc[i-2] < df['open'].iloc[i-2]:
                # 第二天是十字星或小实体
                body_length = abs(df['close'].iloc[i-1] - df['open'].iloc[i-1])
                if body_length < (df['high'].iloc[i-1] - df['low'].iloc[i-1]) * 0.3:
                    # 第三天是阳线
                    if df['close'].iloc[i] > df['open'].iloc[i]:
                        # 第三天收盘价高于第一天开盘价
                        if df['close'].iloc[i] > df['open'].iloc[i-2]:
                            df.loc[df.index[i], 'Candlestick_Pattern'] = 'Morning Star'
        
        return df
    
    def _identify_evening_star(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别黄昏之星形态
        
        Args:
            df: 股票数据
            
        Returns:
            pd.DataFrame: 包含形态信息的DataFrame
        """
        for i in range(2, len(df)):
            # 第一天是阳线
            if df['close'].iloc[i-2] > df['open'].iloc[i-2]:
                # 第二天是十字星或小实体
                body_length = abs(df['close'].iloc[i-1] - df['open'].iloc[i-1])
                if body_length < (df['high'].iloc[i-1] - df['low'].iloc[i-1]) * 0.3:
                    # 第三天是阴线
                    if df['close'].iloc[i] < df['open'].iloc[i]:
                        # 第三天收盘价低于第一天开盘价
                        if df['close'].iloc[i] < df['open'].iloc[i-2]:
                            df.loc[df.index[i], 'Candlestick_Pattern'] = 'Evening Star'
        
        return df
    
    def calculate_trend_strength(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算趋势强度
        
        Args:
            df: 包含趋势信息的股票数据
            
        Returns:
            pd.DataFrame: 包含趋势强度的DataFrame
        """
        logger.info("开始计算趋势强度")
        
        result_df = df.copy()
        
        # 基于价格变化率计算趋势强度
        result_df['Trend_Strength'] = df['close'].pct_change(periods=10) * 100
        
        # 基于RSI计算趋势强度
        if 'RSI12' in df.columns:
            result_df['RSI_Strength'] = (df['RSI12'] - 50) / 50  # 归一化到-1到1
        
        logger.info("趋势强度计算完成")
        return result_df
    
    def analyze_trend(self, df: pd.DataFrame, trend_method: str = "combined") -> tuple:
        """
        综合趋势分析
        
        执行完整的趋势分析流程
        
        Args:
            df: 包含技术指标的股票数据
            trend_method: 趋势识别方法
            
        Returns:
            tuple: (包含趋势信息的DataFrame, 支撑位列表, 阻力位列表, 最新趋势)
        """
        logger.info("开始综合趋势分析")
        
        # 1. 趋势识别
        df = self.identify_trend(df, trend_method)
        
        # 2. K线形态识别
        df = self.identify_candlestick_patterns(df)
        
        # 3. 计算趋势强度
        df = self.calculate_trend_strength(df)
        
        # 4. 计算支撑位和阻力位
        support_levels, resistance_levels = self.calculate_support_resistance(df)
        
        # 5. 获取最新趋势
        latest_trend = df['Trend'].iloc[-1] if len(df) > 0 else "Unknown"
        
        logger.info("综合趋势分析完成")
        
        return df, support_levels, resistance_levels, latest_trend
    
    def generate_trend_report(self, df: pd.DataFrame, stock_code: str) -> dict:
        """
        生成趋势分析报告
        
        Args:
            df: 包含趋势信息的股票数据
            stock_code: 股票代码
            
        Returns:
            dict: 趋势分析报告
        """
        logger.info(f"开始生成股票 {stock_code} 的趋势分析报告")
        
        # 执行综合趋势分析
        df, support_levels, resistance_levels, latest_trend = self.analyze_trend(df)
        
        # 生成报告
        report = {
            'stock_code': stock_code,
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'latest_date': df['date'].iloc[-1].strftime('%Y-%m-%d') if len(df) > 0 else "N/A",
            'latest_price': float(df['close'].iloc[-1]) if len(df) > 0 else 0,
            'latest_trend': latest_trend,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'trend_strength': float(df['Trend_Strength'].iloc[-1]) if 'Trend_Strength' in df.columns and len(df) > 0 else 0,
            'latest_candlestick_pattern': df['Candlestick_Pattern'].iloc[-1] if 'Candlestick_Pattern' in df.columns and len(df) > 0 else "Unknown",
            'technical_indicators': {
                'rsi': float(df['RSI12'].iloc[-1]) if 'RSI12' in df.columns and len(df) > 0 else 0,
                'macd': float(df['MACD'].iloc[-1]) if 'MACD' in df.columns and len(df) > 0 else 0,
                'macd_hist': float(df['MACD_Hist'].iloc[-1]) if 'MACD_Hist' in df.columns and len(df) > 0 else 0,
                'bollinger_position': float((df['close'].iloc[-1] - df['BB_Lower'].iloc[-1]) / (df['BB_Upper'].iloc[-1] - df['BB_Lower'].iloc[-1])) if all(col in df.columns for col in ['close', 'BB_Upper', 'BB_Lower']) and len(df) > 0 else 0
            }
        }
        
        # 生成投资建议
        report['investment_suggestion'] = self._generate_investment_suggestion(report)
        
        logger.info(f"股票 {stock_code} 的趋势分析报告生成完成")
        
        return report
    
    def _generate_investment_suggestion(self, report: dict) -> str:
        """
        生成投资建议
        
        Args:
            report: 趋势分析报告
            
        Returns:
            str: 投资建议
        """
        # 基于趋势和技术指标生成投资建议
        if report['latest_trend'] == '上涨':
            if report['technical_indicators']['rsi'] < 70:
                return "建议买入: 股票处于上涨趋势，RSI指标正常"
            else:
                return "谨慎买入: 股票处于上涨趋势，但RSI指标偏高，可能面临回调"
        elif report['latest_trend'] == '下跌':
            if report['technical_indicators']['rsi'] > 30:
                return "建议观望: 股票处于下跌趋势，RSI指标有反弹迹象"
            else:
                return "建议卖出: 股票处于下跌趋势，RSI指标偏低"
        else:
            return "建议观望: 股票处于横盘趋势，等待明确方向"


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
    
    # 添加一些简单的技术指标用于测试
    test_df['MA5'] = test_df['close'].rolling(window=5).mean()
    test_df['MA20'] = test_df['close'].rolling(window=20).mean()
    
    # 创建趋势分析实例
    trend_analyzer = TrendAnalysis()
    
    # 执行趋势分析
    result_df = trend_analyzer.identify_trend(test_df, method="ma")
    result_df = trend_analyzer.calculate_trend_strength(result_df)
    result_df = trend_analyzer.identify_candlestick_patterns(result_df)
    
    # 计算支撑位和阻力位
    support, resistance = trend_analyzer.calculate_support_resistance(result_df)
    
    # 生成趋势报告
    report = trend_analyzer.generate_trend_report(result_df, "TEST.000001")
    
    # 打印结果
    print("趋势分析结果:")
    print(result_df[['date', 'close', 'MA5', 'MA20', 'Trend', 'Trend_Strength', 'Candlestick_Pattern']].tail(10))
    print(f"\n支撑位: {support}")
    print(f"阻力位: {resistance}")
    print(f"\n最新趋势: {result_df['Trend'].iloc[-1]}")
    print(f"\n趋势分析报告:")
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))
