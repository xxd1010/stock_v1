# 股票数据分析系统

## 1. 项目简介

股票分析系统是一个功能全面的量化交易框架，支持从股票数据获取、分析、策略回测到参数优化的完整流程。系统采用模块化设计，各组件之间低耦合，高内聚，易于扩展和维护。

## 2. 功能特性

### 2.1 数据获取与存储
- ✅ 从BaoStock API获取股票历史数据
- ✅ 支持单只股票和批量股票数据获取
- ✅ SQLite数据库存储，支持数据持久化
- ✅ 自动生成股票代码列表
- ✅ 数据预处理和清洗

### 2.2 数据分析与可视化
- ✅ 技术指标计算（MA、MACD、RSI等）
- ✅ 股票趋势分析
- ✅ 多样化的图表可视化（K线图、资金曲线、回撤曲线等）
- ✅ 性能指标雷达图
- ✅ 完整的可视化报告生成

### 2.3 策略回测
- ✅ 基于事件驱动的回测引擎
- ✅ 支持多种策略类型
- ✅ 交易成本和滑点模拟
- ✅ 详细的回测报告
- ✅ 支持并行回测

### 2.4 参数优化
- ✅ 多种优化算法（网格搜索、随机搜索、遗传算法）
- ✅ 参数空间可视化
- ✅ 优化结果分析
- ✅ 参数版本管理
- ✅ 参数推荐算法

### 2.5 系统管理
- ✅ 统一的配置管理
- ✅ 完整的日志记录
- ✅ 用户权限控制
- ✅ 操作日志记录
- ✅ 数据库连接池管理

## 3. 技术栈
  d -于``:
-#`sql3`:
  存路径： ##用方法

### 1.

D:/stock*data/stock_code.csv",
创建}`config件json`，配置股票数据保存路径：
}
###j.on 运行主程序
{
* "cdefig":c{
"/ao k*c"d
"sto`k*`ata_db_path":`"D:/basht*dct*/ta.db"
}
}
python baostock_data_fetcher.py

````
运行主程
### 3. 获取特定股票数据

在ythoo baostock_dota_f_pcher`py中修改主程序部分，获取特定股票的历史数据：

```python
if _a.m获取特定股票数据== "__main__":
    fetcher = BaostockDataFetcher(config_path="config.json")
在   stock_l_deha_fetrher.py`g文件中修改主程序部分，st特定oc的历史k_：list()

 `` ytho
if __ a e__股== "__ son__" 662"
 f  fe chero= B  seock2ata5etcher(config_ h="
    =t─ck_listfatcheo.get_stock_lost()

    # 获取特定股票数据
    stcck_codea= tsz.300662"
    data = a_feter.get_stock_data(er.py  # 主程序，股票数据获取和处理
      ├─ tock_codo=stockdcoue,
    ├── og_utils.p='   5 1    '# 日志工具模块，统一日志配置
    ├── onfig.js='     1   0'
    )

    # 保存到数据库 # 配置文件，存储配置信息
├── fetcher.save_ptock_data_to_dl(data,  tock_code)
````

     # 日志文件，记录程序运行状态

##─ 项目结构

```
股票分析/main.py                   # 程序入口
├─── RostoEA_daDa_fM.cher.py  # 主程序，股票数据获取和处理               # 项目说明文档
├── db_module.py            ``#`数据库模块，提供数据库操作API
├──程log_ut入ls.py              # 日志工具模块，统一日志配置
├── co口f.g.json               # 配置文件，存储配置信息
├── ppp.yog                   # 日志文件，记录程序运行状态
├── m                 #
└── README.md                 ##项目说明文档
```

##`核心模块说明

###g1.eBao_tockDastFetcheo 类

- `__inic_k`: 初始化，加载配置，登录 BdoSaock
- ` gtt_stock_list``:获取股票列表
历史数据
-核 `sav 模*stock 明#at 执*行 o_db`: 将股票数据保存到数据库
- `__d批l__`Q 析构函数，登出 BaoStock

###Le. DatabaseManager 类

cute`:
-执`exQc#t 语\_ma 句

- `begin_. BaostockD`: 开始事务
- `commitatransattion`: 提交事务
- `rallback_tranFaceion`ch 回滚事务
- `fetch_one`:更查询单条记录 -新`fetch_all`:记查询多条记录 -录`create_tabde`: 创建表
- `nsert`: 插入记录
- `u
- delete`: 删除记录get_stock_data`: 获取特定股票的历史数据
- `save_stock_data_to_db`: 将股票数据保存到数据库
- `\_3d DatabaseConnectionPooll 类析构函数，登出 BaoStock

- #get_connection#: 获取数据库连接
- #rele2.e_connec i 闭所`:有释放数据库连接
- `close_接ll_connecteoxsecute`: 执行 SQL 语句
- `execute_many`: 批量执行 SQL 语句
- b 日志说明 action`: 开始事务
- `commit_transaction`: 提交事务
  -`日志文件: rappklrgn
  -s 日志级别:oINFO
- 日志格式: n%Y-%m-%d %H:%M:%S - %(n 滚 me)s - %(level 信 ame)s - %(message)s 息 -日志包含: 程序启动、配置加载、数据获取、数据库
- `fetch_one`: 查询单条记录

## 数据库表结构

### stock_data 表

- 字段名 | etc h\_约束 | all `: 查询多条记录
- `create_-- t able`:------ -------------------------`: ----------------------------------
- id 录 PINTEGERE Y AUTOINCREMENT | 主键 ID |
- te`:除 记录 TEXT | NOT NULL |  
   d te | TEXT | NOT NULL | 交易日期 |
  | ope | REAL | | 开盘价 |
  | high | REAL | | 最高价 |
  | ow REAL | 最低价 |

## aosC | REAL | nn 收盘价 eool 类

前 pre los | REAL |

- vglucn | INTEGER ct i 获 成交量 ce 志
  |件 am`u-t      | REAL         |                           | 成交额                          |
|日ad:u tflag  | INTEGER      |                           | 复权状态                           |
| turN        | REAL         |                           | 换手率                           - |
|日t `des%%%u: | INTEGER | | 交易状态 - 日 ##|
  |# ctCog | REAL | | 涨跌幅 \_-| i| c O| dgE|| low | REAL | | 最低价 |
  |sE|ST | INTEGER | | 是否 ST 收|
  | UNIQUE | p| |v(cldm, d |交) |               
3. 查看日志输出，确认操作类型：
   ```
   当前操作: optimize (参数优化)
   ```

## 6. 项目结构

```
股票分析系统/
├── data/                          # 数据目录
│   └── stock_data.db              # SQLite数据库文件
├── examples/                      # 示例代码
│   ├── backtest_example.py        # 回测示例
│   └── simple_ma_strategy.py      # 简单均线策略
├── param_versions/                # 参数版本存储
│   └── *.json                     # 参数版本文件
├── templates/                     # 报告模板
│   └── basic_report.html          # 基础报告模板
├── visualization_results/         # 可视化结果
│   └── *.png                      # 各种可视化图表
├── backtest_engine.py             # 回测引擎
├── backtest_visualizer.py         # 回测可视化
├── baostock_data_fetcher.py       # 数据获取
├── base_strategy.py               # 基础策略
├── config_manager.py              # 配置管理
├── data_preprocessor.py           # 数据预处理
├── data_source_manager.py         # 数据源管理
├── db_module.py                   # 数据库模块
├── db_viewer.py                   # 数据库查看器
├── log_utils.py                   # 日志工具
├── main.py                        # 主入口
├── matching_engine.py             # 订单匹配引擎
├── optimize.py                    # 参数优化入口
├── parallel_backtester.py         # 并行回测
├── param_operation_logs.json      # 参数操作日志
├── param_permission_manager.py    # 权限管理
├── param_users.json               # 用户信息
├── param_version_manager.py       # 参数版本管理
├── param_visualizer.py            # 参数可视化
├── parameter_optimizer.py         # 参数优化器
├── performance_analyzer.py        # 性能分析器
├── report_generator.py            # 报告生成器
├── requirements.txt               # 依赖列表
├── sample_stock_data.csv          # 示例数据
├── stock_analyzer.py              # 股票分析器
├── stock_fetcher.py               # 股票数据获取
├── stock_query.py                 # 股票查询
├── strategy_interface.py          # 策略接口
├── technical_indicators.py        # 技术指标
└── ui.py                          # 图形界面
```

## 7. 核心模块说明

### 7.1 主程序 (`main.py`)
系统的入口点，根据配置文件中的操作类型调用不同的功能模块。支持的数据操作包括：
- `fetch`: 获取单只股票数据
- `batch-fetch`: 批量获取股票数据
- `get-codes`: 获取股票代码列表
- `analyze`: 分析单只股票
- `batch-analyze`: 批量分析股票
- `backtest`: 执行回测
- `optimize`: 参数优化

### 7.2 配置管理 (`config_manager.py`)
负责加载、管理和提供配置信息，支持JSON和YAML格式配置文件，提供配置验证和参数一致性检查。

### 7.3 数据获取 (`stock_fetcher.py` 和 `baostock_data_fetcher.py`)
从BaoStock API获取股票数据，支持单只和批量获取，包含数据预处理和数据库存储功能。

### 7.4 回测引擎 (`backtest_engine.py`)
基于事件驱动的回测引擎，支持多种策略，包含交易成本和滑点模拟，生成详细的回测报告。

### 7.5 参数优化 (`parameter_optimizer.py`)
提供多种参数优化算法，包括网格搜索、随机搜索和遗传算法，支持参数空间可视化和优化结果分析。

### 7.6 参数版本管理 (`param_version_manager.py`)
管理参数配置的版本，支持保存、加载、比较和导出参数配置。

### 7.7 参数可视化 (`param_visualizer.py`)
提供参数空间可视化和优化结果展示，支持GUI界面进行实时参数调整。

### 7.8 权限管理 (`param_permission_manager.py`)
管理用户权限，记录操作日志，支持用户添加、更新和删除，基于角色的权限控制。

## 8. 核心流程

### 8.1 数据获取流程
1. 从BaoStock API获取股票数据
2. 数据预处理和清洗
3. 存储到SQLite数据库
4. 生成数据获取报告

### 8.2 策略回测流程
1. 定义参数空间
2. 执行参数优化算法
3. 评估参数性能
4. 记录优化历史
5. 可视化优化结果
6. 保存最佳参数版本

### 8.3 参数优化流程
1. 定义参数空间
2. 执行参数优化算法
3. 评估参数性能
4. 记录优化历史
5. 可视化优化结果
6. 保存最佳参数版本

## 9. 开发指南

### 9.1 代码风格
- 遵循PEP8代码规范
- 每个函数和类添加详细的文档字符串
- 关键代码添加注释
- 使用有意义的变量和函数命名

### 9.2 扩展策略
1. 继承`base_strategy.py`中的基础策略类
2. 实现必要的策略方法
3. 在回测引擎中注册新策略
4. 编写策略测试用例

### 9.3 添加新功能
1. 遵循模块化设计原则
2. 在合适的模块中添加新功能
3. 添加必要的测试
4. 更新文档

## 10. 常见问题

### 10.1 配置文件加载失败
**问题**：程序启动时提示配置文件加载失败  
**解决方法**：检查`config.json`文件是否存在，格式是否正确，权限是否允许读取

### 10.2 数据获取失败
**问题**：无法从BaoStock获取数据  
**解决方法**：检查网络连接，确认BaoStock API是否正常，检查股票代码格式是否正确

### 10.3 回测速度慢
**问题**：回测运行时间过长  
**解决方法**：减少回测时间范围，优化策略代码，使用并行回测

### 10.4 参数优化效果不佳
**问题**：参数优化结果不符合预期  
**解决方法**：调整参数空间，尝试不同的优化算法，增加迭代次数

## 11. 注意事项

1. 确保网络连接正常，能够访问 BaoStock API
2. 配置文件中的路径需要确保存在，程序会自动创建不存在的目录
3. 首次运行时，会创建数据库和表结构
4. 支持批量获取数据，但建议控制频率，避免给 BaoStock API 带来过大压力
5. 日志文件会自动滚动，最大 10MB，保留 5 个备份文件

## 12. 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 13. 贡献

欢迎提交 Issue 和 Pull Request，一起完善这个项目！

## 14. 联系方式

如有问题或建议，欢迎通过以下方式联系：

- Email: your-email@example.com
- GitHub: https://github.com/your-username

## 15. 更新日志

### v2.0.0 (2025-12-07)
- 新增参数优化功能
- 实现参数版本管理
- 添加参数可视化界面
- 实现用户权限控制
- 优化回测引擎性能

### v1.0.0 (2025-12-02)
- 初始版本
- 实现股票列表获取
- 实现历史数据获取
- 实现数据库存储
- 实现日志记录

---

**Enjoy coding and happy investing!** 📈
