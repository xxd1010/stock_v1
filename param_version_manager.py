#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数版本管理模块

负责参数配置的保存、加载、比较和管理
"""

import json
import os
from datetime import datetime
from log_utils import get_logger

# 获取日志记录器
logger = get_logger("param_version_manager")


class ParamVersionManager:
    """
    参数版本管理类
    
    提供参数版本的保存、加载、比较和管理功能
    """
    
    # 版本文件存储目录
    VERSION_DIR = "param_versions"
    
    def __init__(self):
        """
        初始化参数版本管理器
        """
        self.logger = get_logger("ParamVersionManager")
        self.logger.info("初始化参数版本管理器")
        
        # 确保版本目录存在
        self._ensure_version_dir_exists()
    
    def _ensure_version_dir_exists(self):
        """
        确保版本目录存在
        """
        if not os.path.exists(self.VERSION_DIR):
            os.makedirs(self.VERSION_DIR)
            self.logger.info(f"创建版本目录: {self.VERSION_DIR}")
    
    def _generate_version_id(self, strategy_name, version_name=""):
        """
        生成版本ID
        
        Args:
            strategy_name: 策略名称
            version_name: 版本名称
            
        Returns:
            str: 版本ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if version_name:
            return f"{strategy_name}_{version_name}_{timestamp}"
        else:
            return f"{strategy_name}_{timestamp}"
    
    def _get_version_file_path(self, version_id):
        """
        获取版本文件路径
        
        Args:
            version_id: 版本ID
            
        Returns:
            str: 文件路径
        """
        return os.path.join(self.VERSION_DIR, f"{version_id}.json")
    
    def save_version(self, params, performance, name="", description="", strategy_name=""):
        """
        保存参数版本
        
        Args:
            params: 参数配置
            performance: 性能指标
            name: 版本名称
            description: 版本描述
            strategy_name: 策略名称
            
        Returns:
            str: 版本ID
        """
        self.logger.info(f"保存参数版本，策略: {strategy_name}")
        
        # 生成版本ID
        version_id = self._generate_version_id(strategy_name, name)
        
        # 创建版本数据
        version_data = {
            "version_id": version_id,
            "name": name,
            "description": description,
            "strategy_name": strategy_name,
            "params": params,
            "performance": performance,
            "created_time": datetime.now().isoformat(),
            "created_by": "system"  # 实际应用中应该是当前用户
        }
        
        # 保存到文件
        file_path = self._get_version_file_path(version_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"参数版本保存成功，版本ID: {version_id}")
        return version_id
    
    def load_version(self, version_id):
        """
        加载参数版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            dict: 版本数据
        """
        self.logger.info(f"加载参数版本，版本ID: {version_id}")
        
        # 获取文件路径
        file_path = self._get_version_file_path(version_id)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.error(f"版本文件不存在: {file_path}")
            raise FileNotFoundError(f"版本文件不存在: {version_id}")
        
        # 加载版本数据
        with open(file_path, "r", encoding="utf-8") as f:
            version_data = json.load(f)
        
        self.logger.info(f"参数版本加载成功，版本ID: {version_id}")
        return version_data
    
    def list_versions(self, strategy_name=""):
        """
        列出所有参数版本
        
        Args:
            strategy_name: 策略名称，可选，用于过滤
            
        Returns:
            list: 版本列表
        """
        self.logger.info(f"列出参数版本，策略: {strategy_name}")
        
        # 获取所有版本文件
        version_files = [f for f in os.listdir(self.VERSION_DIR) if f.endswith(".json")]
        
        versions = []
        
        for version_file in version_files:
            # 加载版本数据
            file_path = os.path.join(self.VERSION_DIR, version_file)
            with open(file_path, "r", encoding="utf-8") as f:
                version_data = json.load(f)
            
            # 过滤策略名称
            if strategy_name and version_data["strategy_name"] != strategy_name:
                continue
            
            # 添加到列表
            versions.append({
                "version_id": version_data["version_id"],
                "name": version_data["name"],
                "strategy_name": version_data["strategy_name"],
                "created_time": version_data["created_time"],
                "description": version_data["description"],
                "performance_summary": {
                    "sharpe_ratio": version_data["performance"].get("sharpe_ratio", 0),
                    "total_return": version_data["performance"].get("total_return", 0),
                    "max_drawdown": version_data["performance"].get("max_drawdown", 0)
                }
            })
        
        # 按创建时间排序，最新的在前面
        versions.sort(key=lambda x: x["created_time"], reverse=True)
        
        self.logger.info(f"共找到 {len(versions)} 个参数版本")
        return versions
    
    def delete_version(self, version_id):
        """
        删除参数版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            bool: 删除成功返回True
        """
        self.logger.info(f"删除参数版本，版本ID: {version_id}")
        
        # 获取文件路径
        file_path = self._get_version_file_path(version_id)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.error(f"版本文件不存在: {file_path}")
            return False
        
        # 删除文件
        try:
            os.remove(file_path)
            self.logger.info(f"参数版本删除成功，版本ID: {version_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除参数版本失败，版本ID: {version_id}, 错误: {e}")
            return False
    
    def compare_versions(self, version_id1, version_id2):
        """
        比较两个参数版本
        
        Args:
            version_id1: 第一个版本ID
            version_id2: 第二个版本ID
            
        Returns:
            dict: 比较结果
        """
        self.logger.info(f"比较参数版本: {version_id1} vs {version_id2}")
        
        # 加载两个版本
        version1 = self.load_version(version_id1)
        version2 = self.load_version(version_id2)
        
        # 比较参数差异
        params1 = version1["params"]
        params2 = version2["params"]
        
        # 找出共同参数
        common_params = set(params1.keys()) & set(params2.keys())
        
        # 找出差异参数
        diff_params = {
            "only_in_v1": set(params1.keys()) - set(params2.keys()),
            "only_in_v2": set(params2.keys()) - set(params1.keys()),
            "different_values": {}
        }
        
        # 比较共同参数的值
        for param in common_params:
            if params1[param] != params2[param]:
                diff_params["different_values"][param] = {
                    "v1": params1[param],
                    "v2": params2[param]
                }
        
        # 比较性能差异
        performance1 = version1["performance"]
        performance2 = version2["performance"]
        
        performance_diff = {}
        
        # 找出共同性能指标
        common_metrics = set(performance1.keys()) & set(performance2.keys())
        
        for metric in common_metrics:
            if isinstance(performance1[metric], (int, float)) and isinstance(performance2[metric], (int, float)):
                performance_diff[metric] = {
                    "v1": performance1[metric],
                    "v2": performance2[metric],
                    "diff": performance2[metric] - performance1[metric]
                }
        
        comparison_result = {
            "version1": {
                "version_id": version_id1,
                "name": version1["name"],
                "created_time": version1["created_time"]
            },
            "version2": {
                "version_id": version_id2,
                "name": version2["name"],
                "created_time": version2["created_time"]
            },
            "param_differences": diff_params,
            "performance_differences": performance_diff
        }
        
        self.logger.info(f"参数版本比较完成: {comparison_result}")
        return comparison_result
    
    def update_version_description(self, version_id, description):
        """
        更新版本描述
        
        Args:
            version_id: 版本ID
            description: 新描述
            
        Returns:
            bool: 更新成功返回True
        """
        self.logger.info(f"更新参数版本描述，版本ID: {version_id}")
        
        # 加载版本
        version_data = self.load_version(version_id)
        
        # 更新描述
        version_data["description"] = description
        
        # 保存回文件
        file_path = self._get_version_file_path(version_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"参数版本描述更新成功，版本ID: {version_id}")
        return True
    
    def get_best_version(self, strategy_name="", metric="sharpe_ratio", reverse=True):
        """
        获取最佳版本
        
        Args:
            strategy_name: 策略名称，可选，用于过滤
            metric: 评估指标
            reverse: 是否降序排序
            
        Returns:
            dict: 最佳版本
        """
        self.logger.info(f"获取最佳参数版本，策略: {strategy_name}, 指标: {metric}")
        
        # 获取所有版本
        versions = self.list_versions(strategy_name)
        
        if not versions:
            self.logger.warning("没有找到参数版本")
            return None
        
        # 加载完整版本数据
        full_versions = []
        for version_summary in versions:
            full_version = self.load_version(version_summary["version_id"])
            full_versions.append(full_version)
        
        # 按指定指标排序
        def get_metric_value(version):
            return version["performance"].get(metric, 0)
        
        full_versions.sort(key=get_metric_value, reverse=reverse)
        
        best_version = full_versions[0]
        self.logger.info(f"找到最佳参数版本，版本ID: {best_version['version_id']}")
        return best_version
    
    def export_version(self, version_id, export_path):
        """
        导出参数版本
        
        Args:
            version_id: 版本ID
            export_path: 导出路径
            
        Returns:
            bool: 导出成功返回True
        """
        self.logger.info(f"导出参数版本，版本ID: {version_id}, 导出路径: {export_path}")
        
        # 加载版本
        version_data = self.load_version(version_id)
        
        # 导出到指定路径
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"参数版本导出成功，版本ID: {version_id}")
        return True
    
    def import_version(self, import_path):
        """
        导入参数版本
        
        Args:
            import_path: 导入路径
            
        Returns:
            str: 导入的版本ID
        """
        self.logger.info(f"导入参数版本，导入路径: {import_path}")
        
        # 检查文件是否存在
        if not os.path.exists(import_path):
            self.logger.error(f"导入文件不存在: {import_path}")
            raise FileNotFoundError(f"导入文件不存在: {import_path}")
        
        # 加载导入的版本数据
        with open(import_path, "r", encoding="utf-8") as f:
            imported_version = json.load(f)
        
        # 生成新的版本ID（避免冲突）
        strategy_name = imported_version.get("strategy_name", "unknown")
        version_name = imported_version.get("name", "imported")
        new_version_id = self._generate_version_id(strategy_name, version_name)
        imported_version["version_id"] = new_version_id
        imported_version["created_time"] = datetime.now().isoformat()
        imported_version["imported_from"] = import_path
        
        # 保存到版本目录
        file_path = self._get_version_file_path(new_version_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(imported_version, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"参数版本导入成功，新版本ID: {new_version_id}")
        return new_version_id
