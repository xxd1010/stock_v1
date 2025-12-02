import baostock as bs
import json

import pandas as pd

# 导入日志工具模块，用于记录程序运行状态和错误信息
from log_utils import get_logger, setup_logger
from db_module import DatabaseManager

# 初始化日志配置
setup_logger()
logger = get_logger("baostock_data_fetcher")

def _load_config(config_path: str) -> dict:
    """
    加载配置文件函数

    从指定的JSON配置文件中读取配置信息，并返回配置字典

    Args:
        config_path: 配置文件的路径，通常是"config.json"

    Returns:
        dict: 包含配置信息的字典，如果加载失败则返回空字典
    """
    try:
        # 尝试以UTF-8编码打开配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            # 加载JSON数据并获取'config'节点
            config_data = json.load(f)
            return config_data.get('config', {})
    except FileNotFoundError:
        # 配置文件不存在时的处理
        logger.error(f"配置文件 {config_path} 未找到，使用默认配置")
        return {}
    except json.JSONDecodeError:
        # JSON格式错误时的处理
        logger.error(f"配置文件 {config_path} 格式错误，使用默认配置")
        return {}


def _load_all_stock_code(stock_code_file_path: str):
    """
    加载所有股票代码函数

    从指定的CSV文件中读取所有股票代码，并返回一个包含所有股票代码的列表

    Args:
        stock_code_file_path: 股票代码文件的路径，通常是"stock_code.csv"

    Returns:
        list: 包含所有股票代码的列表，如果加载失败则返回空列表
    """
    try:
        # 尝试以UTF-8编码打开股票代码文件
        with open(stock_code_file_path, 'r', encoding='utf-8') as f:
            # 读取所有行并提取股票代码
            stock_codes = [line.strip().split(',')[0] for line in f.readlines()]
            return stock_codes
    except FileNotFoundError:
        # 股票代码文件不存在时的处理
        logger.error(f"股票代码文件 {stock_code_file_path} 未找到，使用默认股票代码列表")


class BaoStockDataFetcher:
    """
    BaoStock数据获取器类

    用于从BaoStock API获取股票数据，包括股票列表、历史数据等
    """

    def __init__(self, config_path: str = "config.json"):
        """
        初始化BaoStock数据获取器

        Args:
            config_path: 配置文件路径，默认为"config.json"
            stock_code: 股票代码，默认为"SH.600300"（维维股份）
        """
        # 加载配置文件
        self.config = _load_config(config_path)

        # 从配置中获取股票代码文件路径，用于存储股票代码列表
        self.stock_code_file_path = self.config.get('stock_code_file_path')
        # 从配置中获取股票数据库路径，用于存储股票数据
        self.stock_data_db_path = self.config.get('stock_data_db_path')

        # 记录配置加载情况
        logger.info(
            f"配置加载完成: 股票代码文件路径={self.stock_code_file_path}, 数据库路径={self.stock_data_db_path}")

        # 登录BaoStock API
        self.lg = bs.login()
        # 检查登录是否成功
        if self.lg.error_code != '0':
            # 登录失败，记录错误信息
            logger.error(f"BaoStock登录失败: {self.lg.error_msg}")
        else:
            # 登录成功，记录信息
            logger.info("BaoStock登录成功")


    def get_stock_list(self):
        """
        获取股票列表

        从BaoStock API获取所有股票的基本信息，并保存到文件中

        Returns:
            list: 包含股票信息的列表，每个元素是一个包含股票基本信息的字典
        """
        # 记录开始获取股票列表
        logger.info("开始获取股票列表")

        # 查询股票基本信息
        rs = bs.query_stock_basic()

        # 如果配置了股票代码文件路径，则将股票列表写入文件
        if self.stock_code_file_path:
            try:
                # 确保目录存在
                import os
                os.makedirs(os.path.dirname(self.stock_code_file_path),
                            exist_ok=True)

                # 打开文件准备写入
                with open(self.stock_code_file_path, 'w',
                          encoding='utf-8') as f:
                    # 写入表头
                    f.write("code,code_name,ipoDate,outDate,type,status\n")

                    # 遍历查询结果并写入文件
                    while (rs.error_code == '0') & rs.next():
                        row_data = rs.get_row_data()
                        f.write(','.join(row_data) + '\n')

                logger.info(
                    f"股票列表已保存到 {self.stock_code_file_path}")

                # 重新查询，因为之前的查询结果已经遍历完毕
                rs = bs.query_stock_basic()
            except Exception as e:
                # 写入文件失败，记录错误
                logger.error(f"写入股票代码文件失败: {str(e)}")

        # 将股票数据存储到列表中
        stock_list = []
        while (rs.error_code == '0') & rs.next():
            stock_list.append(rs.get_row_data())

        # 记录获取结果（只在函数内部记录一次）
        logger.info(f"获取到 {len(stock_list)} 只股票信息")

        return stock_list

    # 在baostock_data_fecher.py的get_stock_data方法中
    # 确保只记录一次日志
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str,
                       frequency: str = "d"):
        """
        获取指定股票的历史数据
    
        Args:
            stock_code: 股票代码，如"SH.600000"
            start_date: 开始日期，格式如"2020-01-01"
            end_date: 结束日期，格式如"2020-12-31"
            frequency: 数据频率，默认为"d"（日线），可选"w"（周线）、"m"（月线）
    
        Returns:
            list: 包含股票历史数据的列表，每个元素是一个交易日的数据
        """
        # 记录开始获取股票数据
        logger.info(
            f"开始获取股票 {stock_code} 从 {start_date} 到 {end_date} 的历史数据")
    
        # 查询股票历史数据
        rs = bs.query_history_k_data_plus(
            code=stock_code,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            fields="date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
        )
    
        # 将股票数据存储到列表中
        stock_data = []
        while (rs.error_code == '0') & rs.next():
            stock_data.append(rs.get_row_data())
        
        # 只记录一次获取结果
        data_count = len(stock_data)
        logger.info(f"获取到股票 {stock_code} 的 {data_count} 条历史数据")
        
        data = pd.DataFrame(stock_data, columns=rs.fields)
        return data

    def save_stock_data_to_db(self, stock_data: pd.DataFrame, stock_code: str):
        """
        将股票数据保存到数据库

        Args:
            stock_data: 股票历史数据DataFrame
            stock_code: 股票代码
        """

        
        # 确保数据库路径存在
        import os
        db_dir = os.path.dirname(self.stock_data_db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        logger.info(f"准备将股票 {stock_code} 的数据保存到数据库: {self.stock_data_db_path}")
        
        try:
            # 创建数据库管理器实例
            db_manager = DatabaseManager(self.stock_data_db_path)
            
            # 创建股票数据表（如果不存在）
            stock_table_columns = {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "code": "TEXT NOT NULL",
                "date": "TEXT NOT NULL",
                "open": "REAL",
                "high": "REAL",
                "low": "REAL",
                "close": "REAL",
                "preclose": "REAL",
                "volume": "INTEGER",
                "amount": "REAL",
                "adjustflag": "INTEGER",
                "turn": "REAL",
                "tradestatus": "INTEGER",
                "pctChg": "REAL",
                "isST": "INTEGER"
            }
            
            # 使用原始SQL语句创建表，包含UNIQUE约束
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                preclose REAL,
                volume INTEGER,
                amount REAL,
                adjustflag INTEGER,
                turn REAL,
                tradestatus INTEGER,
                pctChg REAL,
                isST INTEGER,
                UNIQUE(code, date)
            )
            """
            
            cursor = db_manager.execute(create_table_sql)
            if cursor:
                logger.info("创建股票数据表成功")
            
            # 将DataFrame转换为字典列表，准备插入数据库
            stock_data_dict = stock_data.to_dict(orient='records')
            
            # 批量插入数据
            insert_count = 0
            for data in stock_data_dict:
                # 准备插入数据
                insert_data = {
                    "code": stock_code,
                    "date": data.get("date", ""),
                    "open": float(data.get("open", 0)),
                    "high": float(data.get("high", 0)),
                    "low": float(data.get("low", 0)),
                    "close": float(data.get("close", 0)),
                    "preclose": float(data.get("preclose", 0)),
                    "volume": int(data.get("volume", 0)),
                    "amount": float(data.get("amount", 0)),
                    "adjustflag": int(data.get("adjustflag", 0)),
                    "turn": float(data.get("turn", 0)),
                    "tradestatus": int(data.get("tradestatus", 0)),
                    "pctChg": float(data.get("pctChg", 0)),
                    "isST": int(data.get("isST", 0))
                }
                
                # 插入数据
                if db_manager.insert("stock_data", insert_data):
                    insert_count += 1
            
            logger.info(f"成功将股票 {stock_code} 的 {insert_count} 条数据保存到数据库")
            
            # 关闭数据库管理器
            db_manager.close()
        except Exception as e:
            logger.error(f"保存股票 {stock_code} 数据到数据库失败: {str(e)}")

    def __del__(self):
        """
        析构函数，在对象销毁时调用

        用于登出BaoStock API，释放资源
        """
        try:
            # 登出BaoStock API，添加错误处理以防止Python关闭时的ImportError
            bs.logout()
            logger.info("已登出BaoStock API")
        except Exception as e:
            # 忽略登出时的错误，特别是在Python解释器关闭时
            pass


