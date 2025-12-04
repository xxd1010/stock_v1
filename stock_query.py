import argparse
import json
from typing import Optional

import pandas as pd

from db_module import DatabaseManager
from log_utils import get_logger, setup_logger


def _load_config(config_path: str) -> dict:
    """
    简单加载配置文件中的 config 节点。

    与 `baostock_data_fetcher.py` 中的逻辑保持一致，但做了最小复制，
    避免循环依赖。
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            return config_data.get("config", {})
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def query_stock_data(
    db_path: str,
    code: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    从 SQLite 数据库中按条件查询股票数据，并返回 DataFrame。

    Args:
        db_path: 数据库文件路径
        code: 股票代码，例如 "sz.300662"
        start_date: 开始日期，格式 "YYYY-MM-DD"
        end_date: 结束日期，格式 "YYYY-MM-DD"

    Returns:
        pandas.DataFrame: 查询到的股票数据，按日期升序排序。
    """
    db_manager = DatabaseManager(db_path)

    sql = """
    SELECT
        date,
        code,
        open,
        high,
        low,
        close,
        preclose,
        volume,
        amount,
        adjustflag,
        turn,
        tradestatus,
        pctChg,
        isST
    FROM stock_data
    WHERE code = ?
      AND date BETWEEN ? AND ?
    ORDER BY date ASC
    """

    rows = db_manager.fetch_all(sql, (code, start_date, end_date))
    db_manager.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # 确保日期列为 datetime 类型，方便后续处理
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_indicators(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    使用 pandas 计算一些常见指标。

    - 日收益率（基于收盘价，百分比）
    - 累计收益率
    - 收益率的均值与波动率（标准差）
    - 5 日 / 20 日移动平均线
    """
    if df.empty:
        return None

    df = df.sort_values("date").reset_index(drop=True)

    # 使用收盘价计算日收益率（百分比）
    df["daily_return"] = df["close"].pct_change() * 100

    # 累计收益率（基于日收益率）
    df["cum_return"] = (1 + df["daily_return"] / 100).cumprod() - 1

    # 简单移动平均线
    df["ma5"] = df["close"].rolling(window=5).mean()
    df["ma20"] = df["close"].rolling(window=20).mean()

    return df


def summarize_indicators(df: pd.DataFrame, code: str) -> None:
    """
    打印一些概要指标信息到控制台。
    """
    logger = get_logger(__name__)

    if df.empty:
        logger.info(f"股票 {code} 在指定区间内没有查询到数据。")
        return

    # 丢掉第一个 NaN 的收益率再做统计
    returns = df["daily_return"].dropna()
    if returns.empty:
        logger.info(f"股票 {code} 在指定区间内数据太少，无法计算收益率统计。")
        return

    mean_ret = returns.mean()
    vol_ret = returns.std()
    cum_ret = df["cum_return"].iloc[-1] * 100  # 百分比

    start_date = df["date"].iloc[0].strftime("%Y-%m-%d")
    end_date = df["date"].iloc[-1].strftime("%Y-%m-%d")

    logger.info(f"股票: {code}")
    logger.info(f"区间: {start_date} ~ {end_date}")
    logger.info(f"总交易日数: {len(df)}")
    logger.info(f"平均日收益率: {mean_ret:.4f}%")
    logger.info(f"日收益率波动率(标准差): {vol_ret:.4f}%")
    logger.info(f"区间累计收益率: {cum_ret:.4f}%")

    # 简单展示末尾几行数据（含指标）
    logger.info("最近 5 条记录（含指标列）:")
    logger.info("\n" + df.tail(5).to_string(index=False))


def main():
    """
    命令行入口：

    示例：
        python stock_query.py --code sz.300662 --start 2025-11-01 --end 2025-11-30
        # 如需指定配置文件（从中读取数据库路径）：
        python stock_query.py --code sz.300662 --start 2025-11-01 --end 2025-11-30 --config config.json
    """
    setup_logger()
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="从 stock_data.db 查询股票数据并计算指标")
    parser.add_argument(
        "--code",
        required=True,
        help="股票代码，例如 sz.300662 / sh.600000",
    )
    parser.add_argument(
        "--start",
        required=True,
        help="开始日期，格式 YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="结束日期，格式 YYYY-MM-DD",
    )
    parser.add_argument(
        "--db",
        help="数据库文件路径。如果不指定，则从配置文件中读取 stock_data_db_path",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="配置文件路径（默认: config.json）",
    )

    args = parser.parse_args()

    if args.db:
        db_path = args.db
    else:
        config = _load_config(args.config)
        db_path = config.get("stock_data_db_path")

    if not db_path:
        logger.error("未能从参数或配置文件中获取数据库路径，请检查 --db 或 config.json。")
        return

    logger.info(
        f"开始查询股票 {args.code} 在 {args.start} ~ {args.end} 区间的数据，数据库: {db_path}"
    )

    df = query_stock_data(db_path, args.code, args.start, args.end)
    if df.empty:
        logger.info("查询结果为空。")
        return

    df_with_ind = compute_indicators(df)
    if df_with_ind is None:
        logger.info("数据不足以计算指标。")
        return

    summarize_indicators(df_with_ind, args.code)


if __name__ == "__main__":
    main()


