import argparse
import json
from typing import Optional, List, Dict, Any

import pandas as pd

from db_module import DatabaseManager
from log_utils import get_logger, setup_logger


def _load_config(config_path: str) -> dict:
    """
    从配置文件中读取 config 节点，主要是 stock_data_db_path。
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            return config_data.get("config", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_db_path(args) -> Optional[str]:
    """
    根据命令行参数或配置文件获取数据库路径。
    """
    if args.db:
        return args.db

    config = _load_config(args.config)
    return config.get("stock_data_db_path")


def list_tables(db_path: str) -> List[str]:
    """
    列出数据库中的所有表。
    """
    db = DatabaseManager(db_path)
    sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    rows = db.fetch_all(sql)
    db.close()
    return [row["name"] for row in rows]


def show_schema(db_path: str, table: str) -> List[Dict[str, Any]]:
    """
    查看指定表的结构信息。
    """
    db = DatabaseManager(db_path)
    sql = f"PRAGMA table_info({table})"
    rows = db.fetch_all(sql)
    db.close()
    return rows


def show_table_head(db_path: str, table: str, limit: int) -> pd.DataFrame:
    """
    查看指定表的前几行数据。
    """
    db = DatabaseManager(db_path)
    sql = f"SELECT * FROM {table} LIMIT ?"
    rows = db.fetch_all(sql, (limit,))
    db.close()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def run_sql(db_path: str, sql: str, params: Optional[str] = None) -> pd.DataFrame:
    """
    执行任意只读 SQL（建议 SELECT），返回 DataFrame。

    params 可以是 JSON 字符串，例如: "[\"sz.300662\", \"2025-11-01\", \"2025-11-30\"]"
    """
    db = DatabaseManager(db_path)

    parsed_params: tuple = ()
    if params:
        try:
            parsed = json.loads(params)
            if isinstance(parsed, list):
                parsed_params = tuple(parsed)
        except json.JSONDecodeError:
            # 参数解析失败就当没参数
            parsed_params = ()

    rows = db.fetch_all(sql, parsed_params)
    db.close()

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def main():
    """
    一个简单的 SQLite 数据库查看工具。

    示例：
        # 1. 列出所有表
        python db_viewer.py --tables

        # 2. 查看表结构
        python db_viewer.py --schema stock_data

        # 3. 查看表前 10 行
        python db_viewer.py --table stock_data --limit 10

        # 4. 执行任意 SQL
        python db_viewer.py --sql "SELECT code, date, close FROM stock_data LIMIT 5"

        # 5. 指定数据库路径
        python db_viewer.py --tables --db D:\\stock_data\\stock_data.db
    """
    setup_logger()
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="简单的 SQLite 数据库查看工具")
    parser.add_argument(
        "--db",
        help="数据库文件路径。如果不指定，则从配置文件中读取 stock_data_db_path",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="配置文件路径（默认: config.json）",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tables", action="store_true", help="列出所有表")
    group.add_argument("--schema", metavar="TABLE", help="查看指定表的结构")
    group.add_argument("--table", metavar="TABLE", help="查看指定表的前几行数据")
    group.add_argument("--sql", metavar="SQL", help="执行任意只读 SQL（建议 SELECT）")

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="查看表数据时的行数限制（默认 10）",
    )
    parser.add_argument(
        "--params",
        help='SQL 参数，使用 JSON 数组字符串，例如: "[\\"sz.300662\\", \\"2025-11-01\\"]"',
    )

    args = parser.parse_args()

    db_path = get_db_path(args)
    if not db_path:
        logger.error("未能从参数或配置文件中获取数据库路径，请使用 --db 或检查 config.json。")
        return

    logger.info(f"使用数据库文件: {db_path}")

    # 1. 列出所有表
    if args.tables:
        tables = list_tables(db_path)
        if not tables:
            logger.info("数据库中没有表。")
            return
        logger.info("数据库中的表：")
        for name in tables:
            logger.info(f"- {name}")
        return

    # 2. 查看表结构
    if args.schema:
        rows = show_schema(db_path, args.schema)
        if not rows:
            logger.info(f"表 {args.schema} 不存在或没有结构信息。")
            return
        df = pd.DataFrame(rows)
        logger.info(f"表 {args.schema} 结构：")
        logger.info("\n" + df.to_string(index=False))
        return

    # 3. 查看表的前几行
    if args.table:
        df = show_table_head(db_path, args.table, args.limit)
        if df.empty:
            logger.info(f"表 {args.table} 中没有数据。")
            return
        logger.info(f"表 {args.table} 前 {args.limit} 行：")
        logger.info("\n" + df.to_string(index=False))
        return

    # 4. 执行任意 SQL
    if args.sql:
        df = run_sql(db_path, args.sql, args.params)
        if df.empty:
            logger.info("SQL 执行成功，但没有返回数据。")
            return
        logger.info("SQL 查询结果：")
        logger.info("\n" + df.to_string(index=False))
        return


if __name__ == "__main__":
    main()


