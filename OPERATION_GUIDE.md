# 操作类型切换指南

## 1. 概述

股票分析程序支持多种操作类型，通过配置文件中的 `operation` 字段可以切换不同的操作。程序启动时会从 `config.json` 文件中读取操作类型，如果不存在则默认使用 `fetch` 操作。

## 2. 支持的操作类型

| 操作类型 | 描述 | 分类 |
|---------|------|------|
| `fetch` | 获取单只股票数据 | 数据获取 |
| `batch-fetch` | 批量获取股票数据 | 数据获取 |
| `get-codes` | 获取股票代码列表 | 数据获取 |
| `analyze` | 分析单只股票 | 数据分析 |
| `batch-analyze` | 批量分析股票 | 数据分析 |
| `backtest` | 执行回测 | 回测 |
| `optimize` | 参数优化 | 回测 |

## 3. 切换操作类型的方法

### 3.1 方法一：修改 config.json 文件

1. 打开 `config.json` 文件
2. 在根目录下添加或修改 `operation` 字段
3. 保存文件并重新运行程序

**示例配置：**
```json
{
  "operation": "backtest",
  "sample_data": {
    "start_date": "2023-01-01",
    "end_date": "2025-12-31",
    "symbol": "sh.301662"
  },
  "backtest": {
    "initial_cash": 100000,
    "start_date": "2023-01-01",
    "end_date": "2025-12-31",
    "frequency": "d",
    "transaction_cost": 0.0003,
    "slippage": 0.0001
  }
}
```

### 3.2 方法二：直接修改代码（不推荐）

可以在 `main.py` 文件中修改默认操作类型，但不推荐这种方式，因为会影响代码的可维护性。

```python
# 在 main 函数中修改默认值
operation = config.get("operation", "optimize")  # 将默认值从 "fetch" 改为 "optimize"
```

## 4. 运行示例

### 4.1 执行回测操作

1. 修改 `config.json` 文件，添加：
   ```json
   "operation": "backtest"
   ```

2. 运行程序：
   ```bash
   python main.py
   ```

3. 查看日志输出，确认操作类型：
   ```
   当前操作: backtest (执行回测)
   ```

### 4.2 执行参数优化操作

1. 修改 `config.json` 文件，将 `operation` 改为：
   ```json
   "operation": "optimize"
   ```

2. 运行程序：
   ```bash
   python main.py
   ```

3. 查看日志输出，确认操作类型：
   ```
   当前操作: optimize (参数优化)
   ```

## 5. 操作类型与执行逻辑对应关系

| 操作类型 | 执行模块 | 主要功能 |
|---------|----------|----------|
| `fetch` | `stock_fetcher.py` | 从数据源获取单只股票历史数据 |
| `batch-fetch` | `stock_fetcher.py` | 批量获取多只股票历史数据 |
| `get-codes` | `stock_fetcher.py` | 获取股票代码列表 |
| `analyze` | `stock_analyzer.py` | 分析单只股票，生成报告和可视化 |
| `batch-analyze` | `stock_analyzer.py` | 批量分析多只股票 |
| `backtest` | `examples/backtest_example.py` | 执行策略回测 |
| `optimize` | `optimize.py` | 执行策略参数优化 |

## 6. 注意事项

1. **配置优先级**：程序会优先使用配置文件中的 `operation` 字段，如果不存在则使用默认值 `fetch`
2. **操作类型验证**：程序会验证操作类型是否支持，如果不支持会输出错误信息并退出
3. **日志查看**：可以通过查看日志输出确认当前执行的操作类型
4. **配置文件格式**：确保 `config.json` 文件格式正确，否则会导致配置加载失败
5. **操作依赖**：某些操作可能依赖特定的配置项，确保相关配置完整

## 7. 常见问题

### 7.1 配置文件加载失败

**问题**：程序启动时提示配置文件加载失败

**解决方法**：
- 检查 `config.json` 文件是否存在
- 检查 `config.json` 文件格式是否正确
- 检查文件权限是否允许读取

### 7.2 操作类型不支持

**问题**：程序提示 "不支持的操作类型"

**解决方法**：
- 检查 `operation` 字段的值是否正确
- 参考本文档中的支持操作类型列表
- 确保操作类型拼写正确（区分大小写）

### 7.3 执行结果不符合预期

**问题**：执行结果与预期不符

**解决方法**：
- 检查相关配置项是否正确
- 查看日志输出，了解程序执行过程
- 确认操作类型是否正确

## 8. 总结

通过修改 `config.json` 文件中的 `operation` 字段，可以方便地切换股票分析程序的操作类型。程序支持7种操作类型，涵盖了数据获取、数据分析和回测等主要功能。建议使用配置文件的方式切换操作类型，保持代码的可维护性。
