#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据预处理模块

负责股票数据的清洗、格式转换、缺失值处理等预处理操作
"""

import pandas as pd
import numpy as np
from log_utils import get_logger

# 获取日志记录器
logger = get_logger("data_preprocessor")


class DataPreprocessor:
    """
    数据预处理类
    
    提供股票数据的清洗、格式转换、缺失值处理等功能
    """
    
    def __init__(self):
        """
        初始化数据预处理类
        """
        pass
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗
        
        去除重复数据和异常值
        
        Args:
            df: 原始股票数据DataFrame
            
        Returns:
            pd.DataFrame: 清洗后的股票数据
        """
        logger.info(f"开始数据清洗，原始数据形状: {df.shape}")
        
        # 去除重复行
        df = df.drop_duplicates()
        logger.info(f"去除重复行后数据形状: {df.shape}")
        
        # 去除日期列重复的数据
        if 'date' in df.columns:
            df = df.drop_duplicates(subset=['date'])
            logger.info(f"去除日期重复数据后形状: {df.shape}")
        
        return df
    
    def convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据类型转换
        
        将字符串类型转换为数值类型和日期类型
        
        Args:
            df: 原始股票数据DataFrame
            
        Returns:
            pd.DataFrame: 转换后的数据
        """
        logger.info("开始数据类型转换")
        
        # 转换日期列
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            logger.info("日期列转换为datetime类型")
        
        # 数值列列表
        numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 
                          'volume', 'amount', 'adjustflag', 'turn', 
                          'tradestatus', 'pctChg', 'isST']
        
        # 转换数值列
        for col in numeric_columns:
            if col in df.columns:
                # 替换可能的空字符串或异常值
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.info(f"{col}列转换为数值类型")
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
        """
        缺失值处理
        
        Args:
            df: 包含缺失值的数据
            method: 缺失值处理方法，可选值: 'ffill'(前向填充), 'bfill'(后向填充), 'mean'(均值填充), 'drop'(删除)
            
        Returns:
            pd.DataFrame: 处理缺失值后的数据
        """
        logger.info(f"开始处理缺失值，缺失值数量: {df.isnull().sum().sum()}")
        
        if method == 'ffill':
            # 前向填充
            df = df.fillna(method='ffill')
        elif method == 'bfill':
            # 后向填充
            df = df.fillna(method='bfill')
        elif method == 'mean':
            # 均值填充（仅对数值列）
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif method == 'drop':
            # 删除包含缺失值的行
            df = df.dropna()
        else:
            logger.warning(f"未知的缺失值处理方法: {method}，使用默认的前向填充")
            df = df.fillna(method='ffill')
        
        logger.info(f"缺失值处理完成，剩余缺失值数量: {df.isnull().sum().sum()}")
        return df
    
    def normalize_data(self, df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
        """
        数据标准化
        
        Args:
            df: 原始数据
            columns: 需要标准化的列列表，默认为所有数值列
            
        Returns:
            pd.DataFrame: 标准化后的数据
        """
        logger.info("开始数据标准化")
        
        # 复制数据，避免修改原始数据
        df_normalized = df.copy()
        
        # 如果没有指定列，默认所有数值列
        if columns is None:
            columns = df_normalized.select_dtypes(include=[np.number]).columns
        
        for col in columns:
            if col in df_normalized.columns:
                # 使用Z-score标准化
                mean = df_normalized[col].mean()
                std = df_normalized[col].std()
                if std != 0:
                    df_normalized[f'{col}_normalized'] = (df_normalized[col] - mean) / std
                    logger.info(f"{col}列标准化完成")
        
        return df_normalized
    
    def add_technical_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加技术分析所需的基础列
        
        Args:
            df: 原始数据
            
        Returns:
            pd.DataFrame: 添加基础技术列后的数据
        """
        logger.info("开始添加技术分析基础列")
        
        # 确保数据按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # 添加涨跌幅列（如果不存在）
        if 'pctChg' not in df.columns and 'close' in df.columns:
            df['pctChg'] = df['close'].pct_change() * 100
            logger.info("添加涨跌幅列")
        
        # 添加成交量变化率列
        if 'volume' in df.columns:
            df['volume_change'] = df['volume'].pct_change() * 100
            logger.info("添加成交量变化率列")
        
        return df
    
    def preprocess(self, df: pd.DataFrame, missing_value_method: str = 'ffill') -> pd.DataFrame:
        """
        完整的数据预处理流程
        
        执行数据清洗、类型转换、缺失值处理、添加技术列等完整流程
        
        Args:
            df: 原始股票数据
            missing_value_method: 缺失值处理方法
            
        Returns:
            pd.DataFrame: 预处理完成的数据
        """
        logger.info("开始完整的数据预处理流程")
        
        # 1. 数据清洗
        df = self.clean_data(df)
        
        # 2. 数据类型转换
        df = self.convert_data_types(df)
        
        # 3. 缺失值处理
        df = self.handle_missing_values(df, missing_value_method)
        
        # 4. 添加技术分析基础列
        df = self.add_technical_columns(df)
        
        # 5. 确保数据按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        logger.info(f"数据预处理完成，最终数据形状: {df.shape}")
        return df
    
    def split_data(self, df: pd.DataFrame, train_ratio: float = 0.8) -> tuple:
        """
        数据拆分
        
        将数据拆分为训练集和测试集
        
        Args:
            df: 完整数据集
            train_ratio: 训练集比例
            
        Returns:
            tuple: (训练集, 测试集)
        """
        logger.info(f"开始数据拆分，训练集比例: {train_ratio}")
        
        # 确保数据按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # 计算拆分点
        split_point = int(len(df) * train_ratio)
        
        # 拆分数据
        train_df = df.iloc[:split_point]
        test_df = df.iloc[split_point:]
        
        logger.info(f"数据拆分完成，训练集形状: {train_df.shape}, 测试集形状: {test_df.shape}")
        
        return train_df, test_df
    
    def resample_data(self, df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
        """
        数据重采样
        
        将数据按照指定频率重采样
        
        Args:
            df: 原始数据
            freq: 重采样频率，可选值: 'D'(日), 'W'(周), 'M'(月), 'Q'(季), 'Y'(年)
            
        Returns:
            pd.DataFrame: 重采样后的数据
        """
        logger.info(f"开始数据重采样，目标频率: {freq}")
        
        # 确保日期列是索引
        if 'date' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index('date')
        
        # 重采样规则
        resample_rules = {
            'open': 'first',    # 开盘价取第一个值
            'high': 'max',       # 最高价取最大值
            'low': 'min',        # 最低价取最小值
            'close': 'last',     # 收盘价取最后一个值
            'volume': 'sum',     # 成交量求和
            'amount': 'sum',     # 成交额求和
            'turn': 'mean',      # 换手率取平均值
            'pctChg': 'last'     # 涨跌幅取最后一个值
        }
        
        # 执行重采样
        resampled_df = df.resample(freq).agg(resample_rules)
        
        # 重置索引
        resampled_df = resampled_df.reset_index()
        
        logger.info(f"数据重采样完成，原始形状: {df.shape}, 重采样后形状: {resampled_df.shape}")
        
        return resampled_df


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-03', '2023-01-04'],
        'open': ['10.0', '10.2', '10.1', '10.1', '10.3'],
        'high': ['10.5', '10.6', '10.4', '10.4', '10.7'],
        'low': ['9.8', '10.0', '9.9', '9.9', '10.1'],
        'close': ['10.3', '10.4', '10.2', '10.2', '10.5'],
        'volume': ['1000000', '1200000', '900000', '900000', '1100000']
    }
    
    test_df = pd.DataFrame(test_data)
    
    # 创建数据预处理实例
    preprocessor = DataPreprocessor()
    
    # 执行完整预处理流程
    processed_df = preprocessor.preprocess(test_df)
    
    # 打印结果
    print("预处理后的数据:")
    print(processed_df)
    print("\n数据信息:")
    print(processed_df.info())
    print("\n数据描述:")
    print(processed_df.describe())
