#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据源管理模块

统一管理不同数据源，提供统一的数据获取接口，支持多种数据源接入
"""

import abc
import pandas as pd
from typing import Dict, List, Optional, Any
from log_utils import get_logger, setup_logger
from config_manager import get_config, load_config
from data_preprocessor import DataPreprocessor

# 初始化日志
setup_logger()
logger = get_logger("data_source_manager")


class DataSource(abc.ABC):
    """
    数据源抽象基类，定义数据源的基本接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据源
        
        Args:
            config: 数据源配置
        """
        self.config = config
        self.data_preprocessor = DataPreprocessor()
    
    @abc.abstractmethod
    def get_stock_list(self) -> List[List[str]]:
        """
        获取股票列表
        
        Returns:
            股票列表，每个元素包含股票代码、名称等信息
        """
        pass
    
    @abc.abstractmethod
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str, 
                      frequency: str = "d") -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
        
        Returns:
            股票历史数据DataFrame
        """
        pass
    
    @abc.abstractmethod
    def save_stock_data(self, stock_data: pd.DataFrame, stock_code: str) -> bool:
        """
        保存股票数据
        
        Args:
            stock_data: 股票数据
            stock_code: 股票代码
        
        Returns:
            是否保存成功
        """
        pass
    
    @abc.abstractmethod
    def get_stock_data_from_storage(self, stock_code: str, start_date: str, 
                                   end_date: str) -> pd.DataFrame:
        """
        从存储中获取股票数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            股票历史数据DataFrame
        """
        pass
    
    def preprocess_data(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        预处理股票数据
        
        Args:
            stock_data: 原始股票数据
        
        Returns:
            预处理后的股票数据
        """
        return self.data_preprocessor.preprocess(stock_data)


class BaoStockDataSource(DataSource):
    """
    BaoStock数据源实现
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化BaoStock数据源
        
        Args:
            config: 数据源配置
        """
        super().__init__(config)
        
        # 延迟导入，避免不必要的依赖
        import baostock as bs
        self.bs = bs
        
        # 登录BaoStock API
        self.lg = self.bs.login()
        if self.lg.error_code != '0':
            logger.error(f"BaoStock登录失败: {self.lg.error_msg}")
        else:
            logger.info("BaoStock登录成功")
    
    def get_stock_list(self) -> List[List[str]]:
        """
        获取股票列表
        """
        logger.info("开始获取股票列表")
        
        rs = self.bs.query_stock_basic()
        stock_list = []
        
        while (rs.error_code == '0') & rs.next():
            stock_list.append(rs.get_row_data())
        
        logger.info(f"获取到 {len(stock_list)} 只股票信息")
        return stock_list
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str, 
                      frequency: str = "d") -> pd.DataFrame:
        """
        获取股票历史数据
        """
        logger.info(f"开始获取股票 {stock_code} 从 {start_date} 到 {end_date} 的历史数据")
        
        rs = self.bs.query_history_k_data_plus(
            code=stock_code,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            fields="date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
        )
        
        stock_data = []
        while (rs.error_code == '0') & rs.next():
            stock_data.append(rs.get_row_data())
        
        data_count = len(stock_data)
        logger.info(f"获取到股票 {stock_code} 的 {data_count} 条历史数据")
        
        data = pd.DataFrame(stock_data, columns=rs.fields)
        return self.preprocess_data(data)
    
    def save_stock_data(self, stock_data: pd.DataFrame, stock_code: str) -> bool:
        """
        保存股票数据到数据库
        """
        from baostock_data_fetcher import BaoStockDataFetcher
        
        try:
            # 使用现有的BaoStockDataFetcher来保存数据
            fetcher = BaoStockDataFetcher()
            fetcher.save_stock_data_to_db(stock_data, stock_code)
            return True
        except Exception as e:
            logger.error(f"保存股票 {stock_code} 数据失败: {str(e)}")
            return False
    
    def get_stock_data_from_storage(self, stock_code: str, start_date: str, 
                                   end_date: str) -> pd.DataFrame:
        """
        从数据库获取股票数据
        """
        from baostock_data_fetcher import BaoStockDataFetcher
        
        try:
            fetcher = BaoStockDataFetcher()
            return fetcher.get_stock_data_from_db(stock_code, start_date, end_date)
        except Exception as e:
            logger.error(f"从数据库获取股票 {stock_code} 数据失败: {str(e)}")
            return pd.DataFrame()
    
    def __del__(self):
        """
        析构函数，登出BaoStock API
        """
        try:
            self.bs.logout()
            logger.info("已登出BaoStock API")
        except Exception as e:
            pass


class CSVDataSource(DataSource):
    """
    CSV文件数据源实现
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化CSV数据源
        
        Args:
            config: 数据源配置
        """
        super().__init__(config)
        self.data_dir = config.get("data_dir", ".")
    
    def get_stock_list(self) -> List[List[str]]:
        """
        获取股票列表
        """
        # 从CSV文件中获取股票列表
        logger.info("从CSV文件获取股票列表")
        import os
        
        stock_list = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".csv"):
                stock_code = filename[:-4]  # 去掉.csv后缀
                stock_list.append([stock_code, stock_code, "", "", "", ""])
        
        logger.info(f"获取到 {len(stock_list)} 只股票信息")
        return stock_list
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str, 
                      frequency: str = "d") -> pd.DataFrame:
        """
        获取股票历史数据
        """
        logger.info(f"从CSV文件获取股票 {stock_code} 的历史数据")
        
        import os
        file_path = os.path.join(self.data_dir, f"{stock_code}.csv")
        
        if not os.path.exists(file_path):
            logger.error(f"CSV文件不存在: {file_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path)
            df = self.preprocess_data(df)
            
            # 过滤日期范围
            df['date'] = pd.to_datetime(df['date'])
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            df = df.loc[mask]
            
            logger.info(f"获取到股票 {stock_code} 的 {len(df)} 条历史数据")
            return df
        except Exception as e:
            logger.error(f"读取CSV文件失败: {str(e)}")
            return pd.DataFrame()
    
    def save_stock_data(self, stock_data: pd.DataFrame, stock_code: str) -> bool:
        """
        保存股票数据到CSV文件
        """
        import os
        
        try:
            file_path = os.path.join(self.data_dir, f"{stock_code}.csv")
            stock_data.to_csv(file_path, index=False)
            logger.info(f"股票数据已保存到CSV文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存股票数据到CSV文件失败: {str(e)}")
            return False
    
    def get_stock_data_from_storage(self, stock_code: str, start_date: str, 
                                   end_date: str) -> pd.DataFrame:
        """
        从CSV文件获取股票数据
        """
        return self.get_stock_data(stock_code, start_date, end_date)


class DataSourceManager:
    """
    数据源管理器，用于管理不同的数据源
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化数据源管理器
        
        Args:
            config_path: 配置文件路径
        """
        logger.info("初始化数据源管理器")
        
        # 加载配置
        if config_path:
            load_config(config_path)
        
        self.config = get_config()
        self.data_sources = {}
        self.default_source = None
        
        # 初始化数据源
        self._init_data_sources()
    
    def _init_data_sources(self):
        """
        初始化数据源
        """
        # 获取数据源配置
        data_sources_config = self.config.get("data_sources", {})
        
        for source_name, source_config in data_sources_config.items():
            source_type = source_config.get("type")
            
            try:
                if source_type == "baostock":
                    self.data_sources[source_name] = BaoStockDataSource(source_config)
                elif source_type == "csv":
                    self.data_sources[source_name] = CSVDataSource(source_config)
                else:
                    logger.warning(f"不支持的数据源类型: {source_type}")
                    continue
                
                logger.info(f"初始化数据源成功: {source_name}")
                
                # 设置默认数据源
                if self.default_source is None or source_config.get("default", False):
                    self.default_source = source_name
                    logger.info(f"设置默认数据源: {source_name}")
            except Exception as e:
                logger.error(f"初始化数据源 {source_name} 失败: {str(e)}")
    
    def get_data_source(self, source_name: str = None) -> Optional[DataSource]:
        """
        获取数据源
        
        Args:
            source_name: 数据源名称，默认为默认数据源
        
        Returns:
            数据源实例
        """
        if source_name is None:
            source_name = self.default_source
        
        if source_name not in self.data_sources:
            logger.error(f"数据源 {source_name} 不存在")
            return None
        
        return self.data_sources[source_name]
    
    def fetch_stock_data(self, stock_code: str, start_date: str, end_date: str, 
                        frequency: str = "d", source_name: str = None, 
                        save_to_storage: bool = True) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            source_name: 数据源名称
            save_to_storage: 是否保存到存储
        
        Returns:
            股票历史数据DataFrame
        """
        source = self.get_data_source(source_name)
        if source is None:
            return pd.DataFrame()
        
        # 尝试从存储中获取数据
        stock_data = source.get_stock_data_from_storage(stock_code, start_date, end_date)
        
        if stock_data.empty:
            # 存储中没有数据，从数据源获取
            stock_data = source.get_stock_data(stock_code, start_date, end_date, frequency)
            
            if not stock_data.empty and save_to_storage:
                source.save_stock_data(stock_data, stock_code)
        
        return stock_data
    
    def batch_fetch(self, stock_codes: list, start_date: str, end_date: str, 
                   frequency: str = "d", source_name: str = None, 
                   save_to_storage: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量获取股票数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            source_name: 数据源名称
            save_to_storage: 是否保存到存储
        
        Returns:
            股票数据字典，键为股票代码，值为对应的DataFrame
        """
        logger.info(f"开始批量获取 {len(stock_codes)} 只股票数据")
        
        results = {}
        success_count = 0
        
        for stock_code in stock_codes:
            try:
                stock_data = self.fetch_stock_data(stock_code, start_date, end_date, 
                                                  frequency, source_name, save_to_storage)
                
                if not stock_data.empty:
                    results[stock_code] = stock_data
                    success_count += 1
                    logger.info(f"股票 {stock_code} 数据获取完成")
                else:
                    results[stock_code] = pd.DataFrame()
            except Exception as e:
                logger.error(f"获取股票 {stock_code} 数据失败: {str(e)}")
                results[stock_code] = pd.DataFrame()
        
        logger.info(f"批量获取完成，成功获取 {success_count} 只股票数据，失败 {len(stock_codes) - success_count} 只股票数据")
        return results
    
    def get_all_stock_codes(self, source_name: str = None) -> List[str]:
        """
        获取所有股票代码
        
        Args:
            source_name: 数据源名称
        
        Returns:
            股票代码列表
        """
        source = self.get_data_source(source_name)
        if source is None:
            return []
        
        stock_list = source.get_stock_list()
        return [stock[0] for stock in stock_list]


# 测试数据源管理器
if __name__ == "__main__":
    # 示例配置
    test_config = {
        "data_sources": {
            "baostock": {
                "type": "baostock",
                "default": True
            },
            "csv": {
                "type": "csv",
                "data_dir": "./data",
                "default": False
            }
        }
    }
    
    # 保存测试配置
    import json
    with open("test_config.json", "w") as f:
        json.dump({"config": test_config}, f)
    
    # 初始化数据源管理器
    data_source_manager = DataSourceManager("test_config.json")
    
    # 获取股票数据
    stock_data = data_source_manager.fetch_stock_data("sh.600000", "2023-01-01", "2023-12-31")
    print(stock_data.head())
    
    # 清理测试文件
    import os
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
