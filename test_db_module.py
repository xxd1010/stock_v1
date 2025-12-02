import unittest
import tempfile
import os
from db_module import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """
    测试数据库管理器类
    """
    
    def setUp(self):
        """
        测试前的准备工作
        创建临时数据库文件和数据库管理器实例
        """
        # 创建临时文件作为数据库
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()
        
        # 创建数据库管理器实例
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """
        测试后的清理工作
        关闭数据库管理器并删除临时文件
        """
        # 关闭数据库管理器
        self.db_manager.close()
        
        # 删除临时数据库文件
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_create_table(self):
        """
        测试创建表功能
        """
        # 定义表结构
        user_columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "age": "INTEGER",
            "email": "TEXT UNIQUE"
        }
        
        # 测试创建表
        result = self.db_manager.create_table("users", user_columns)
        self.assertTrue(result, "创建表失败")
    
    def test_insert_and_fetch_one(self):
        """
        测试插入记录和查询单条记录功能
        """
        # 先创建表
        self.test_create_table()
        
        # 插入记录
        user_data = {
            "name": "张三",
            "age": 30,
            "email": "zhangsan@example.com"
        }
        
        user_id = self.db_manager.insert("users", user_data)
        self.assertIsNotNone(user_id, "插入记录失败")
        
        # 查询记录
        user = self.db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        self.assertIsNotNone(user, "查询记录失败")
        self.assertEqual(user["name"], "张三", "记录姓名不匹配")
        self.assertEqual(user["age"], 30, "记录年龄不匹配")
        self.assertEqual(user["email"], "zhangsan@example.com", "记录邮箱不匹配")
    
    def test_fetch_all(self):
        """
        测试查询所有记录功能
        """
        # 先创建表和插入记录
        self.test_create_table()
        
        # 插入多条记录
        users_data = [
            {"name": "张三", "age": 30, "email": "zhangsan@example.com"},
            {"name": "李四", "age": 25, "email": "lisi@example.com"},
            {"name": "王五", "age": 35, "email": "wangwu@example.com"}
        ]
        
        for user_data in users_data:
            self.db_manager.insert("users", user_data)
        
        # 查询所有记录
        users = self.db_manager.fetch_all("SELECT * FROM users ORDER BY id")
        self.assertEqual(len(users), 3, "查询记录数量不匹配")
        self.assertEqual(users[0]["name"], "张三", "第一条记录姓名不匹配")
        self.assertEqual(users[1]["name"], "李四", "第二条记录姓名不匹配")
        self.assertEqual(users[2]["name"], "王五", "第三条记录姓名不匹配")
    
    def test_update(self):
        """
        测试更新记录功能
        """
        # 先创建表和插入记录
        self.test_create_table()
        
        # 插入记录
        user_data = {
            "name": "张三",
            "age": 30,
            "email": "zhangsan@example.com"
        }
        
        user_id = self.db_manager.insert("users", user_data)
        
        # 更新记录
        update_data = {"age": 31, "name": "张三三"}
        result = self.db_manager.update("users", update_data, "id = ?", (user_id,))
        self.assertTrue(result, "更新记录失败")
        
        # 查询更新后的记录
        user = self.db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        self.assertEqual(user["age"], 31, "记录年龄更新失败")
        self.assertEqual(user["name"], "张三三", "记录姓名更新失败")
    
    def test_delete(self):
        """
        测试删除记录功能
        """
        # 先创建表和插入记录
        self.test_create_table()
        
        # 插入记录
        user_data = {
            "name": "张三",
            "age": 30,
            "email": "zhangsan@example.com"
        }
        
        user_id = self.db_manager.insert("users", user_data)
        
        # 删除记录
        result = self.db_manager.delete("users", "id = ?", (user_id,))
        self.assertTrue(result, "删除记录失败")
        
        # 查询删除后的记录
        user = self.db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        self.assertIsNone(user, "记录删除失败")
    
    def test_transaction(self):
        """
        测试事务处理功能
        """
        # 先创建表
        self.test_create_table()
        
        # 开始事务
        conn = self.db_manager.begin_transaction()
        self.assertIsNotNone(conn, "开始事务失败")
        
        try:
            # 在事务中执行多个操作
            # 插入第一条记录
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, age, email) VALUES (?, ?, ?)", 
                          ("张三", 30, "zhangsan@example.com"))
            
            # 插入第二条记录（故意使用相同的邮箱，应该失败）
            cursor.execute("INSERT INTO users (name, age, email) VALUES (?, ?, ?)", 
                          ("李四", 25, "zhangsan@example.com"))
            
            # 提交事务（应该失败，因为违反了唯一约束）
            self.db_manager.commit_transaction(conn)
            self.fail("事务提交应该失败")
        except Exception as e:
            # 回滚事务
            self.db_manager.rollback_transaction(conn)
        
        # 检查是否没有记录被插入
        users = self.db_manager.fetch_all("SELECT * FROM users")
        self.assertEqual(len(users), 0, "事务回滚失败，应该没有记录")
    
    def test_execute_many(self):
        """
        测试批量执行功能
        """
        # 先创建表
        self.test_create_table()
        
        # 批量插入数据
        users_data = [
            ("张三", 30, "zhangsan@example.com"),
            ("李四", 25, "lisi@example.com"),
            ("王五", 35, "wangwu@example.com")
        ]
        
        sql = "INSERT INTO users (name, age, email) VALUES (?, ?, ?)"
        result = self.db_manager.execute_many(sql, users_data)
        self.assertTrue(result, "批量插入失败")
        
        # 检查插入的记录数量
        users = self.db_manager.fetch_all("SELECT * FROM users")
        self.assertEqual(len(users), 3, "批量插入记录数量不匹配")
    
    def test_error_handling(self):
        """
        测试错误处理功能
        """
        # 执行错误的SQL语句
        result = self.db_manager.execute("INSERT INTO non_existent_table (name) VALUES (?)", ("test",))
        self.assertIsNone(result, "错误的SQL语句应该返回None")
    

if __name__ == "__main__":
    unittest.main()
