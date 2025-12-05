#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数权限管理模块

负责参数修改的权限控制和操作日志记录
"""

import json
import os
from datetime import datetime, timedelta
from log_utils import get_logger

# 获取日志记录器
logger = get_logger("param_permission_manager")


class ParamPermissionManager:
    """
    参数权限管理类
    
    提供参数修改的权限控制和操作日志记录功能
    """
    
    # 配置文件存储路径
    USERS_FILE = "param_users.json"
    LOGS_FILE = "param_operation_logs.json"
    
    def __init__(self):
        """
        初始化参数权限管理器
        """
        self.logger = get_logger("ParamPermissionManager")
        self.logger.info("初始化参数权限管理器")
        
        # 确保配置文件存在
        self._ensure_config_files_exist()
        
        # 加载用户权限数据
        self._load_users()
        
        # 加载操作日志
        self._load_logs()
    
    def _ensure_config_files_exist(self):
        """
        确保配置文件存在
        """
        # 确保用户文件存在
        if not os.path.exists(self.USERS_FILE):
            with open(self.USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({"users": []}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"创建用户权限文件: {self.USERS_FILE}")
        
        # 确保日志文件存在
        if not os.path.exists(self.LOGS_FILE):
            with open(self.LOGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"logs": []}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"创建操作日志文件: {self.LOGS_FILE}")
    
    def _load_users(self):
        """
        加载用户权限数据
        """
        try:
            with open(self.USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.users = data.get("users", [])
            self.logger.info(f"加载了 {len(self.users)} 个用户权限配置")
        except Exception as e:
            self.logger.error(f"加载用户权限数据失败: {e}")
            self.users = []
    
    def _save_users(self):
        """
        保存用户权限数据
        """
        try:
            with open(self.USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({"users": self.users}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存了 {len(self.users)} 个用户权限配置")
        except Exception as e:
            self.logger.error(f"保存用户权限数据失败: {e}")
    
    def _load_logs(self):
        """
        加载操作日志
        """
        try:
            with open(self.LOGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.logs = data.get("logs", [])
            self.logger.info(f"加载了 {len(self.logs)} 条操作日志")
        except Exception as e:
            self.logger.error(f"加载操作日志失败: {e}")
            self.logs = []
    
    def _save_logs(self):
        """
        保存操作日志
        """
        try:
            with open(self.LOGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"logs": self.logs}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存了 {len(self.logs)} 条操作日志")
        except Exception as e:
            self.logger.error(f"保存操作日志失败: {e}")
    
    def add_user(self, username, role="viewer", password="", description=""):
        """
        添加用户
        
        Args:
            username: 用户名
            role: 角色，可选值: viewer(查看者), editor(编辑者), admin(管理员)
            password: 密码（实际应用中应该加密存储）
            description: 用户描述
            
        Returns:
            bool: 添加成功返回True
        """
        self.logger.info(f"添加用户: {username}, 角色: {role}")
        
        # 检查用户是否已存在
        for user in self.users:
            if user["username"] == username:
                self.logger.warning(f"用户已存在: {username}")
                return False
        
        # 验证角色
        valid_roles = ["viewer", "editor", "admin"]
        if role not in valid_roles:
            self.logger.warning(f"无效的角色: {role}")
            return False
        
        # 添加用户
        new_user = {
            "username": username,
            "role": role,
            "password": password,  # 实际应用中应该使用加密存储
            "description": description,
            "created_time": datetime.now().isoformat()
        }
        
        self.users.append(new_user)
        self._save_users()
        
        # 记录日志
        self._log_operation("system", "add_user", {"username": username, "role": role})
        
        return True
    
    def update_user(self, username, role=None, password=None, description=None):
        """
        更新用户信息
        
        Args:
            username: 用户名
            role: 新角色
            password: 新密码
            description: 新描述
            
        Returns:
            bool: 更新成功返回True
        """
        self.logger.info(f"更新用户: {username}")
        
        # 查找用户
        for user in self.users:
            if user["username"] == username:
                # 更新用户信息
                if role is not None:
                    valid_roles = ["viewer", "editor", "admin"]
                    if role not in valid_roles:
                        self.logger.warning(f"无效的角色: {role}")
                        return False
                    user["role"] = role
                
                if password is not None:
                    user["password"] = password  # 实际应用中应该使用加密存储
                
                if description is not None:
                    user["description"] = description
                
                self._save_users()
                
                # 记录日志
                self._log_operation("system", "update_user", {"username": username})
                
                return True
        
        self.logger.warning(f"用户不存在: {username}")
        return False
    
    def delete_user(self, username):
        """
        删除用户
        
        Args:
            username: 用户名
            
        Returns:
            bool: 删除成功返回True
        """
        self.logger.info(f"删除用户: {username}")
        
        # 查找并删除用户
        for i, user in enumerate(self.users):
            if user["username"] == username:
                del self.users[i]
                self._save_users()
                
                # 记录日志
                self._log_operation("system", "delete_user", {"username": username})
                
                return True
        
        self.logger.warning(f"用户不存在: {username}")
        return False
    
    def check_permission(self, username, operation):
        """
        检查用户权限
        
        Args:
            username: 用户名
            operation: 操作类型，可选值: view(查看), edit(编辑), admin(管理)
            
        Returns:
            bool: 有权限返回True
        """
        self.logger.info(f"检查用户权限: {username}, 操作: {operation}")
        
        # 查找用户
        for user in self.users:
            if user["username"] == username:
                user_role = user["role"]
                
                # 权限映射
                permission_map = {
                    "viewer": {"view": True, "edit": False, "admin": False},
                    "editor": {"view": True, "edit": True, "admin": False},
                    "admin": {"view": True, "edit": True, "admin": True}
                }
                
                # 检查权限
                return permission_map.get(user_role, {}).get(operation, False)
        
        self.logger.warning(f"用户不存在: {username}")
        return False
    
    def authenticate_user(self, username, password):
        """
        认证用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            bool: 认证成功返回True
        """
        self.logger.info(f"认证用户: {username}")
        
        # 查找用户
        for user in self.users:
            if user["username"] == username:
                # 验证密码
                if user["password"] == password:
                    return True
                else:
                    self.logger.warning(f"用户密码错误: {username}")
                    return False
        
        self.logger.warning(f"用户不存在: {username}")
        return False
    
    def _log_operation(self, username, operation, details):
        """
        记录操作日志
        
        Args:
            username: 操作用户名
            operation: 操作类型
            details: 操作详情
        """
        log_entry = {
            "username": username,
            "operation": operation,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logs.append(log_entry)
        
        # 限制日志数量，只保留最近10000条
        if len(self.logs) > 10000:
            self.logs = self.logs[-10000:]
        
        # 保存日志
        self._save_logs()
    
    def log_param_operation(self, username, operation, params_before, params_after, strategy_name=""):
        """
        记录参数操作日志
        
        Args:
            username: 操作用户名
            operation: 操作类型，如: update, save, load, optimize
            params_before: 操作前的参数
            params_after: 操作后的参数
            strategy_name: 策略名称
        """
        self.logger.info(f"记录参数操作日志: {username}, 操作: {operation}, 策略: {strategy_name}")
        
        # 记录日志
        self._log_operation(username, operation, {
            "strategy_name": strategy_name,
            "params_before": params_before,
            "params_after": params_after
        })
    
    def get_operation_logs(self, username="", operation="", start_time="", end_time="", limit=100):
        """
        获取操作日志
        
        Args:
            username: 操作用户名，可选，用于过滤
            operation: 操作类型，可选，用于过滤
            start_time: 开始时间，可选，用于过滤
            end_time: 结束时间，可选，用于过滤
            limit: 返回日志数量限制
            
        Returns:
            list: 操作日志列表
        """
        self.logger.info(f"获取操作日志，用户: {username}, 操作: {operation}, 限制: {limit}")
        
        # 过滤日志
        filtered_logs = []
        
        for log in self.logs:
            # 用户名过滤
            if username and log["username"] != username:
                continue
            
            # 操作类型过滤
            if operation and log["operation"] != operation:
                continue
            
            # 时间过滤
            log_time = datetime.fromisoformat(log["timestamp"])
            if start_time:
                start = datetime.fromisoformat(start_time)
                if log_time < start:
                    continue
            
            if end_time:
                end = datetime.fromisoformat(end_time)
                if log_time > end:
                    continue
            
            filtered_logs.append(log)
        
        # 按时间降序排序
        filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 限制数量
        if limit > 0:
            filtered_logs = filtered_logs[:limit]
        
        return filtered_logs
    
    def get_user_list(self):
        """
        获取用户列表
        
        Returns:
            list: 用户列表
        """
        return self.users
    
    def export_logs(self, export_path, username="", operation="", start_time="", end_time=""):
        """
        导出操作日志
        
        Args:
            export_path: 导出路径
            username: 操作用户名，可选，用于过滤
            operation: 操作类型，可选，用于过滤
            start_time: 开始时间，可选，用于过滤
            end_time: 结束时间，可选，用于过滤
            
        Returns:
            bool: 导出成功返回True
        """
        self.logger.info(f"导出操作日志到: {export_path}")
        
        # 获取过滤后的日志
        logs_to_export = self.get_operation_logs(username, operation, start_time, end_time, -1)
        
        # 导出到文件
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump({"logs": logs_to_export}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"成功导出 {len(logs_to_export)} 条操作日志")
            return True
        except Exception as e:
            self.logger.error(f"导出操作日志失败: {e}")
            return False
    
    def get_permission_summary(self):
        """
        获取权限摘要
        
        Returns:
            dict: 权限摘要信息
        """
        # 统计用户角色分布
        role_stats = {"viewer": 0, "editor": 0, "admin": 0}
        for user in self.users:
            role_stats[user["role"]] += 1
        
        # 统计操作日志数量
        total_logs = len(self.logs)
        
        # 最近日志数量
        recent_logs = len([log for log in self.logs 
                          if datetime.fromisoformat(log["timestamp"]) > 
                          datetime.now() - timedelta(days=7)])
        
        return {
            "total_users": len(self.users),
            "role_distribution": role_stats,
            "total_logs": total_logs,
            "recent_logs": recent_logs
        }


# 示例用法
if __name__ == "__main__":
    # 创建权限管理器
    permission_manager = ParamPermissionManager()
    
    # 添加用户
    permission_manager.add_user("admin", "admin", "password123", "系统管理员")
    permission_manager.add_user("user1", "editor", "password456", "普通编辑用户")
    permission_manager.add_user("user2", "viewer", "password789", "只读用户")
    
    # 验证用户
    print("认证admin用户:", permission_manager.authenticate_user("admin", "password123"))
    print("认证user1用户:", permission_manager.authenticate_user("user1", "password456"))
    print("认证无效密码:", permission_manager.authenticate_user("admin", "wrong_password"))
    
    # 检查权限
    print("admin用户的编辑权限:", permission_manager.check_permission("admin", "edit"))
    print("user2用户的编辑权限:", permission_manager.check_permission("user2", "edit"))
    
    # 记录参数操作
    permission_manager.log_param_operation(
        "user1", 
        "update", 
        {"window_size": 20, "threshold": 0.5},
        {"window_size": 25, "threshold": 0.6},
        "strategy1"
    )
    
    # 获取操作日志
    logs = permission_manager.get_operation_logs(username="user1", limit=10)
    print(f"获取到 {len(logs)} 条操作日志")
    
    # 获取权限摘要
    summary = permission_manager.get_permission_summary()
    print("权限摘要:", summary)
