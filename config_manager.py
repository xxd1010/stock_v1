#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块

负责加载、管理和提供程序配置
"""

import json
import yaml
import os
from log_utils import get_logger

# 获取日志记录器
logger = get_logger("config_manager")


class ConfigManager:
    """
    配置管理类
    
    提供配置的加载、管理和访问功能
    """
    
    # 默认配置
    DEFAULT_CONFIG = {
        # 数据获取配置
        "data_fetcher": {
            "stock_code_file_path": "data/stock_codes.csv",
            "stock_data_db_path": "data/stock_data.db",
            "baostock": {
                "retry_times": 3,
                "timeout": 30
            }
        },
        
        # 数据源管理配置
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
        },
        
        # 数据预处理配置
        "data_preprocessor": {
            "missing_value_method": "ffill",
            "train_test_ratio": 0.8
        },
        
        # 技术指标计算配置
        "technical_indicators": {
            "ma_periods": [5, 10, 20, 30, 60, 120, 250],
            "macd": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            "rsi": {
                "periods": [6, 12, 24]
            },
            "kdj": {
                "k_period": 9,
                "d_period": 3,
                "j_period": 3
            },
            "bollinger": {
                "period": 20,
                "std_dev": 2
            }
        },
        
        # 可视化配置
        "visualization": {
            "plotly_api_key": "",
            "default_chart_type": "candlestick",
            "show_grid": True,
            "theme": "light"
        },
        
        # 报告生成配置
        "report_generator": {
            "default_template": "basic",
            "export_formats": ["excel", "pdf", "html"],
            "report_output_dir": "reports"
        },
        
        # 日志配置
        "logging": {
            "log_file": "logs/app.log",
            "log_level": "INFO",
            "max_bytes": 10485760,  # 10MB
            "backup_count": 5
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理类
        
        Args:
            config_path: 配置文件路径，可选。如果不提供，将使用默认配置
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # 如果提供了配置文件路径，加载配置文件
        if config_path:
            self.load_config(config_path)
        
        logger.info("配置管理器初始化完成")
    
    def load_config(self, config_path: str) -> bool:
        """
        从配置文件加载配置
        
        支持JSON和YAML格式的配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        logger.info(f"开始加载配置文件: {config_path}")
        
        # 检查文件是否存在
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            return False
        
        # 获取文件扩展名
        _, ext = os.path.splitext(config_path)
        
        try:
            # 根据文件扩展名选择加载方式
            if ext.lower() in ['.json']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
            elif ext.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
            else:
                logger.error(f"不支持的配置文件格式: {ext}")
                return False
            
            # 如果配置文件包含'config'节点，使用该节点内容，否则使用整个配置
            if 'config' in file_config:
                file_config = file_config['config']
            
            # 合并配置（文件配置覆盖默认配置）
            self._merge_config(self.config, file_config)
            logger.info(f"配置文件加载成功: {config_path}")
            return True
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON配置文件解析错误: {str(e)}")
            return False
        except yaml.YAMLError as e:
            logger.error(f"YAML配置文件解析错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return False
    
    def _merge_config(self, base_config: dict, new_config: dict) -> None:
        """
        递归合并配置字典
        
        新配置中的值会覆盖基础配置中的对应值
        
        Args:
            base_config: 基础配置字典
            new_config: 新配置字典
        """
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                self._merge_config(base_config[key], value)
            else:
                # 直接覆盖值
                base_config[key] = value
    
    def get(self, key: str, default: any = None, delimiter: str = ".") -> any:
        """
        获取配置值
        
        支持使用点分隔符访问嵌套配置
        
        Args:
            key: 配置键，支持点分隔符，如 "data_fetcher.stock_code_file_path"
            default: 默认值，如果配置不存在则返回默认值
            delimiter: 分隔符，默认为点号
            
        Returns:
            any: 配置值或默认值
        """
        keys = key.split(delimiter)
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"配置键不存在: {key}，返回默认值: {default}")
            return default
    
    def set(self, key: str, value: any, delimiter: str = ".") -> bool:
        """
        设置配置值
        
        支持使用点分隔符设置嵌套配置
        
        Args:
            key: 配置键，支持点分隔符
            value: 配置值
            delimiter: 分隔符，默认为点号
            
        Returns:
            bool: 设置成功返回True，失败返回False
        """
        keys = key.split(delimiter)
        config = self.config
        
        try:
            # 遍历到倒数第二个键
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            logger.info(f"配置键 {key} 设置成功: {value}")
            return True
        except (TypeError, AttributeError):
            logger.error(f"配置键 {key} 设置失败")
            return False
    
    def save_config(self, config_path: str) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        logger.info(f"开始保存配置到文件: {config_path}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(config_path)
        
        # 确保目录存在
        dir_path = os.path.dirname(config_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        try:
            # 根据文件扩展名选择保存格式
            if ext.lower() in ['.json']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
            elif ext.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            else:
                logger.error(f"不支持的配置文件格式: {ext}")
                return False
            
            logger.info(f"配置保存成功: {config_path}")
            return True
        
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def get_full_config(self) -> dict:
        """
        获取完整配置
        
        Returns:
            dict: 完整的配置字典
        """
        return self.config
    
    def validate_config(self) -> bool:
        """
        验证配置的完整性和正确性
        
        Returns:
            bool: 配置有效返回True，无效返回False
        """
        logger.info("开始验证配置")
        
        # 检查必要的配置项
        required_configs = [
            "data_fetcher.stock_code_file_path",
            "data_fetcher.stock_data_db_path",
            "technical_indicators.ma_periods"
        ]
        
        for config_key in required_configs:
            if self.get(config_key) is None:
                logger.error(f"缺少必要配置项: {config_key}")
                return False
        
        logger.info("配置验证通过")
        return True


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Returns:
        ConfigManager: 全局配置管理器实例
    """
    return config_manager


def load_config(config_path: str) -> bool:
    """
    加载配置文件（全局便捷函数）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 加载成功返回True，失败返回False
    """
    return config_manager.load_config(config_path)


def get(key: str, default: any = None) -> any:
    """
    获取配置值（全局便捷函数）
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        any: 配置值或默认值
    """
    return config_manager.get(key, default)


def set(key: str, value: any) -> bool:
    """
    设置配置值（全局便捷函数）
    
    Args:
        key: 配置键
        value: 配置值
        
    Returns:
        bool: 设置成功返回True，失败返回False
    """
    return config_manager.set(key, value)


# 测试代码
if __name__ == "__main__":
    # 创建配置管理器实例
    config = ConfigManager()
    
    # 获取配置值
    stock_code_path = config.get("data_fetcher.stock_code_file_path")
    print(f"股票代码文件路径: {stock_code_path}")
    
    # 获取不存在的配置，使用默认值
    non_existent = config.get("non_existent_key", "默认值")
    print(f"不存在的配置键: {non_existent}")
    
    # 设置配置值
    config.set("new_key", "新值")
    print(f"新设置的配置: {config.get('new_key')}")
    
    # 设置嵌套配置
    config.set("data_fetcher.new_setting", "嵌套新值")
    print(f"嵌套配置: {config.get('data_fetcher.new_setting')}")
    
    # 保存配置到文件
    config.save_config("test_config.json")
    config.save_config("test_config.yaml")
    
    # 加载配置文件
    config2 = ConfigManager()
    config2.load_config("test_config.json")
    print(f"从文件加载的配置: {config2.get('new_key')}")
    
    # 验证配置
    print(f"配置验证结果: {config.validate_config()}")
    
    # 清理测试文件
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
    if os.path.exists("test_config.yaml"):
        os.remove("test_config.yaml")
