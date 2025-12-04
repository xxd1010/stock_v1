import sqlite3
import threading
import queue
import logging
from typing import Optional, Any, List, Dict, Tuple

# 获取日志记录器，但不配置日志系统 - 由外部统一配置
logger = logging.getLogger('db_module')


class DatabaseConnectionPool:
    """
    SQLite数据库连接池类
    
    管理数据库连接，提供连接的获取和释放功能，优化数据库连接的使用
    """
    
    def __init__(self, db_path: str, max_connections: int = 5):
        """
        初始化数据库连接池
        
        Args:
            db_path: 数据库文件路径
            max_connections: 最大连接数，默认5
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        
        # 初始化连接池
        for _ in range(max_connections):
            conn = self._create_connection()
            if conn:
                self.connections.put(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """
        创建数据库连接
        
        Returns:
            sqlite3.Connection: 数据库连接对象，失败返回None
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # 允许跨线程使用连接
                isolation_level=None  # 禁用自动提交，支持事务
            )
            # 设置返回字典格式的结果
            conn.row_factory = sqlite3.Row
            logger.info(f"创建数据库连接成功: {self.db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"创建数据库连接失败: {str(e)}")
            return None
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """
        从连接池获取连接
        
        Returns:
            sqlite3.Connection: 数据库连接对象，失败返回None
        """
        try:
            # 尝试从队列获取连接，超时5秒
            return self.connections.get(timeout=5)
        except queue.Empty:
            logger.warning("连接池已用尽，尝试创建新连接")
            # 连接池用尽，创建新连接（超出最大连接数）
            return self._create_connection()
    
    def release_connection(self, conn: sqlite3.Connection) -> None:
        """
        释放连接回连接池
        
        Args:
            conn: 数据库连接对象
        """
        try:
            # 尝试将连接放回队列，超时1秒
            self.connections.put(conn, timeout=1)
        except queue.Full:
            logger.warning("连接池已满，关闭多余连接")
            # 连接池已满，关闭连接
            conn.close()
    
    def close_all_connections(self) -> None:
        """
        关闭连接池中的所有连接
        """
        closed_count = 0
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.close()
                closed_count += 1
            except (queue.Empty, sqlite3.Error) as e:
                logger.error(f"关闭连接失败: {str(e)}")
        
        if closed_count > 0:
            logger.info(f"成功关闭 {closed_count} 个数据库连接")


class DatabaseManager:
    """
    数据库管理类
    
    提供CRUD操作、事务处理等功能
    """
    
    def __init__(self, db_path: str, max_connections: int = 1):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
            max_connections: 最大连接数，默认5
        """
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path, max_connections)
    
    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Cursor]:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数元组，用于参数化查询
            
        Returns:
            sqlite3.Cursor: 游标对象，失败返回None
        """
        conn = None
        cursor = None
        
        try:
            # 获取连接
            conn = self.pool.get_connection()
            if not conn:
                logger.error("无法获取数据库连接")
                return None
            
            # 创建游标
            cursor = conn.cursor()
            
            # 执行SQL语句
            cursor.execute(sql, params)
            
            return cursor
        except sqlite3.Error as e:
            logger.error(f"执行SQL失败: {sql}, 参数: {params}, 错误: {str(e)}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor and conn:
                conn.commit()
                cursor.close()
            if conn:
                self.pool.release_connection(conn)
    
    def execute_many(self, sql: str, params_list: List[Tuple[Any, ...]]) -> bool:
        """
        批量执行SQL语句
        
        Args:
            sql: SQL语句
            params_list: 参数列表，每个元素是一个参数元组
            
        Returns:
            bool: 执行成功返回True，失败返回False
        """
        conn = None
        cursor = None
        
        try:
            # 获取连接
            conn = self.pool.get_connection()
            if not conn:
                logger.error("无法获取数据库连接")
                return False
            
            # 创建游标
            cursor = conn.cursor()
            
            # 批量执行SQL语句
            cursor.executemany(sql, params_list)
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"批量执行SQL失败: {sql}, 错误: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.release_connection(conn)
    
    def begin_transaction(self) -> Optional[sqlite3.Connection]:
        """
        开始事务
        
        Returns:
            sqlite3.Connection: 数据库连接对象，用于事务操作
        """
        conn = self.pool.get_connection()
        if not conn:
            logger.error("无法获取数据库连接开始事务")
            return None
        
        try:
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            return conn
        except sqlite3.Error as e:
            logger.error(f"开始事务失败: {str(e)}")
            self.pool.release_connection(conn)
            return None
    
    def commit_transaction(self, conn: sqlite3.Connection) -> bool:
        """
        提交事务
        
        Args:
            conn: 数据库连接对象
            
        Returns:
            bool: 提交成功返回True，失败返回False
        """
        try:
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"提交事务失败: {str(e)}")
            return False
        finally:
            self.pool.release_connection(conn)
    
    def rollback_transaction(self, conn: sqlite3.Connection) -> bool:
        """
        回滚事务
        
        Args:
            conn: 数据库连接对象
            
        Returns:
            bool: 回滚成功返回True，失败返回False
        """
        try:
            conn.rollback()
            return True
        except sqlite3.Error as e:
            logger.error(f"回滚事务失败: {str(e)}")
            return False
        finally:
            self.pool.release_connection(conn)
    
    def fetch_one(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """
        查询单条记录
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            Dict[str, Any]: 查询结果字典，失败返回None
        """
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None

        try:
            conn = self.pool.get_connection()
            if not conn:
                logger.error("无法获取数据库连接用于查询单条记录")
                return None

            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"查询单条记录失败: {sql}, 参数: {params}, 错误: {str(e)}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.commit()
                self.pool.release_connection(conn)
    
    def fetch_all(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """
        查询多条记录
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表，每个元素是字典
        """
        conn: Optional[sqlite3.Connection] = None
        cursor: Optional[sqlite3.Cursor] = None

        try:
            conn = self.pool.get_connection()
            if not conn:
                logger.error("无法获取数据库连接用于查询多条记录")
                return []

            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"查询多条记录失败: {sql}, 参数: {params}, 错误: {str(e)}")
            if conn:
                conn.rollback()
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.commit()
                self.pool.release_connection(conn)
    
    def create_table(self, table_name: str, columns: Dict[str, str]) -> bool:
        """
        创建表
        
        Args:
            table_name: 表名
            columns: 列定义字典，键为列名，值为列类型和约束
            
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        # 构建列定义字符串
        columns_def = [f"{col_name} {col_type}" for col_name, col_type in columns.items()]
        columns_str = ", ".join(columns_def)
        
        # 构建SQL语句
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
        
        # 执行SQL语句
        cursor = self.execute(sql)
        return cursor is not None
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """
        插入记录
        
        Args:
            table_name: 表名
            data: 插入数据字典
            
        Returns:
            Optional[int]: 插入记录的ID，失败返回None
        """
        # 构建字段列表和占位符
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = tuple(data.values())
        
        # 构建SQL语句
        sql = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
        
        # 执行SQL语句
        cursor = self.execute(sql, values)
        if cursor:
            return cursor.lastrowid
        return None
    
    def update(self, table_name: str, data: Dict[str, Any], condition: str, params: Tuple[Any, ...] = ()) -> bool:
        """
        更新记录
        
        Args:
            table_name: 表名
            data: 更新数据字典
            condition: WHERE条件
            params: 条件参数元组
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        # 构建更新字段列表
        update_fields = [f"{field} = ?" for field in data.keys()]
        update_str = ", ".join(update_fields)
        values = tuple(data.values()) + params
        
        # 构建SQL语句
        sql = f"UPDATE {table_name} SET {update_str} WHERE {condition}"
        
        # 执行SQL语句
        cursor = self.execute(sql, values)
        return cursor is not None
    
    def delete(self, table_name: str, condition: str, params: Tuple[Any, ...] = ()) -> bool:
        """
        删除记录
        
        Args:
            table_name: 表名
            condition: WHERE条件
            params: 条件参数元组
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        # 构建SQL语句
        sql = f"DELETE FROM {table_name} WHERE {condition}"
        
        # 执行SQL语句
        cursor = self.execute(sql, params)
        return cursor is not None
    
    def close(self) -> None:
        """
        关闭数据库管理器，释放所有连接
        """
        self.pool.close_all_connections()


# 使用示例
if __name__ == "__main__":
    # 创建数据库管理器实例
    db_manager = DatabaseManager(":memory:")  # 使用内存数据库
    
    # 创建表
    user_columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "name": "TEXT NOT NULL",
        "age": "INTEGER",
        "email": "TEXT UNIQUE"
    }
    
    if db_manager.create_table("users", user_columns):
        logger.info("创建表成功")
    
    # 插入记录
    user_data = {
        "name": "张三",
        "age": 30,
        "email": "zhangsan@example.com"
    }
    
    user_id = db_manager.insert("users", user_data)
    if user_id:
        logger.info(f"插入记录成功，ID: {user_id}")
    
    # 查询记录
    user = db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if user:
        logger.info(f"查询记录成功: {user}")
    
    # 更新记录
    update_data = {"age": 31}
    if db_manager.update("users", update_data, "id = ?", (user_id,)):
        logger.info("更新记录成功")
    
    # 查询更新后的记录
    user = db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if user:
        logger.info(f"查询更新后的记录: {user}")
    
    # 删除记录
    if db_manager.delete("users", "id = ?", (user_id,)):
        logger.info("删除记录成功")
    
    # 查询所有记录
    users = db_manager.fetch_all("SELECT * FROM users")
    logger.info(f"查询所有记录: {users}")
    
    # 关闭数据库管理器
    db_manager.close()