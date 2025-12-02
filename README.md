# 股票数据分析系统

## 项目简介

本项目是一个基于 Python 的股票数据分析系统，使用 BaoStock API 获取股票数据，并将数据保存到 SQLite 数据库中，方便后续分析和查询。

## 功能特性

- ✅ 股票列表获取与保存
- ✅ 历史数据获取与分析
- ✅ SQLite 数据库存储
- ✅ 完整的日志记录
- ✅ 数据库连接池管理
- ✅ 支持参数化查询，防止 SQL 注入
- ✅ 事务处理支持
- ✅ 错误处理机制

## 技术栈

- **语言**: Python 3.8+
- **股票数据**: BaoStock API
- **数据库**: SQLite
- **数据处理**: pandas
- **日志**: logging
- **代码风格**: 符合 PEP8 规范

## 安装说明

### 1. 克隆项目

```bash
git clone https://github.com/your-username/stock-analysis.git
cd stock-analysis
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 依赖说明

- `baostock`: 用于获取股票
数据
- `pandas`: 用于数据处理
- `sqlite3`: 内置数据库支持

## 使用方法

### 1. 配置文件

创建 `config.json` 文件，配置股票数据保存路径：

```json
{
  "config": {
    "stock_code_file_path": "D:/stock_data/stock_code.csv",
    "stock_data_db_path": "D:/stock_data/stock_data.db"
  }
}
```

### 2. 运行主程序

```bash
python baostock_data_fetcher.py
```

### 3. 获取特定股票数据

在 `baostock_data_fetcher.py` 文件中修改主程序部分，获取特定股票的历史数据：

```python
if __name__ == "__main__":
    fetcher = BaostockDataFetcher(config_path="config.json")
    stock_list = fetcher.get_stock_list()
    
    # 获取特定股票数据
    stock_code = "sz.300662"
    data = fetcher.get_stock_data(
        stock_code=stock_code,
        start_date='2025-11-01',
        end_date='2025-11-30'
    )
    
    # 保存到数据库
    fetcher.save_stock_data_to_db(data, stock_code)
```

## 项目结构

```
股票分析/
├── baostock_data_fetcher.py  # 主程序，股票数据获取和处理
├── db_module.py              # 数据库模块，提供数据库操作API
├── log_utils.py              # 日志工具模块，统一日志配置
├── config.json               # 配置文件，存储配置信息
├── app.log                   # 日志文件，记录程序运行状态
├── main.py                   # 程序入口
└── README.md                 # 项目说明文档
```

## 核心模块说明

### 1. BaostockDataFetcher 类

- `__init__`: 初始化，加载配置，登录 BaoStock
- `get_stock_list`: 获取股票列表
- `get_stock_data`: 获取特定股票的历史数据
- `save_stock_data_to_db`: 将股票数据保存到数据库
- `__del__`: 析构函数，登出 BaoStock

### 2. DatabaseManager 类

- `execute`: 执行 SQL 语句
- `execute_many`: 批量执行 SQL 语句
- `begin_transaction`: 开始事务
- `commit_transaction`: 提交事务
- `rollback_transaction`: 回滚事务
- `fetch_one`: 查询单条记录
- `fetch_all`: 查询多条记录
- `create_table`: 创建表
- `insert`: 插入记录
- `update`: 更新记录
- `delete`: 删除记录

### 3. DatabaseConnectionPool 类

- `get_connection`: 获取数据库连接
- `release_connection`: 释放数据库连接
- `close_all_connections`: 关闭所有连接

## 日志说明

- 日志文件: `app.log`
- 日志级别: INFO
- 日志格式: `%Y-%m-%d %H:%M:%S - %(name)s - %(levelname)s - %(message)s`
- 日志包含: 程序启动、配置加载、数据获取、数据库操作等信息

## 数据库表结构

### stock_data 表

| 字段名 | 类型 | 约束 | 描述 |
|-------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键ID |
| code | TEXT | NOT NULL | 股票代码 |
| date | TEXT | NOT NULL | 交易日期 |
| open | REAL | | 开盘价 |
| high | REAL | | 最高价 |
| low | REAL | | 最低价 |
| close | REAL | | 收盘价 |
| preclose | REAL | | 前收盘价 |
| volume | INTEGER | | 成交量 |
| amount | REAL | | 成交额 |
| adjustflag | INTEGER | | 复权状态 |
| turn | REAL | | 换手率 |
| tradestatus | INTEGER | | 交易状态 |
| pctChg | REAL | | 涨跌幅 |
| isST | INTEGER | | 是否ST |
| UNIQUE | (code, date) | | 确保每个股票每个交易日只有一条记录 |

## 注意事项

1. 确保网络连接正常，能够访问 BaoStock API
2. 配置文件中的路径需要确保存在，程序会自动创建不存在的目录
3. 首次运行时，会创建数据库和表结构
4. 支持批量获取数据，但建议控制频率，避免给 BaoStock API 带来过大压力
5. 日志文件会自动滚动，最大 10MB，保留 5 个备份文件

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request，一起完善这个项目！

## 联系方式

如有问题或建议，欢迎通过以下方式联系：

- Email: your-email@example.com
- GitHub: https://github.com/your-username

## 更新日志

### v1.0.0 (2025-12-02)

- 初始版本
- 实现股票列表获取
- 实现历史数据获取
- 实现数据库存储
- 实现日志记录

---

**Enjoy coding and happy investing!** 📈
