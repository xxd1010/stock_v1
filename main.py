from baostock_data_fetcher import BaoStockDataFetcher
from log_utils import get_logger,setup_logger
import time

"""
    使用方法：
    1. 创建实例
    2. 获取股票列表
    3. 获取指定股票数据
    4. 保存数据到数据库
"""
setup_logger()
logger = get_logger(__name__)

if __name__ == "__main__":
    # 创建实例并运行
    fetcher = BaoStockDataFetcher(config_path="config.json")
    stock_list = fetcher.get_stock_list()
    logger.info(f"前五只股票为：{stock_list[:5]}")  # 只记录前五只股票，不重复记录总数
    # 定义股票代码变量
    # stock_code = "sz.301662"
    # data = fetcher.get_stock_data(stock_code=stock_code,
    #                         start_date='2025-11-01',
    #                         end_date='2025-11-30')
    # # 不重复记录获取到的数据条数，get_stock_data方法内部已记录
    
    # # 保存股票数据到数据库
    # fetcher.save_stock_data_to_db(data, stock_code)
    
    for item in stock_list[1001:6785]:
        code = item[0]
        data = fetcher.get_stock_data(
            stock_code=code,
            start_date='2025-01-01',
            end_date='2025-11-30'
        )
        fetcher.save_stock_data_to_db(stock_data=data, stock_code=code)
        time.sleep(2)
    # 不要手动调用__del__方法，让Python解释器自动处理
    logger.info("已退出程序")