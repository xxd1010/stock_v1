#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
并行回测模块

支持多策略或多参数组合并行回测，提高回测效率
"""

import multiprocessing as mp
import pandas as pd
import numpy as np
from datetime import datetime
import uuid
from log_utils import get_logger
from backtest_engine import BacktestEngine


class ParallelBacktester:
    """
    并行回测器
    
    支持多策略或多参数组合并行回测
    """
    
    def __init__(self, max_workers=None):
        """
        初始化并行回测器
        
        Args:
            max_workers: 最大工作进程数，默认使用CPU核心数
        """
        self.logger = get_logger("parallel_backtester")
        self.logger.info("初始化并行回测器")
        
        # 回测参数
        self.params = {
            "max_workers": max_workers or mp.cpu_count(),
            "strategy_class": None,
            "data": None,
            "start_date": None,
            "end_date": None,
            "frequency": "d",
            "initial_cash": 1000000,
            "transaction_cost": 0.0003,
            "slippage": 0.0001
        }
        
        # 回测任务列表
        self.tasks = []
        
        # 回测结果
        self.results = []
        
        self.logger.info(f"并行回测器初始化完成，最大工作进程数: {self.params['max_workers']}")
    
    def set_params(self, params):
        """
        设置回测参数
        
        Args:
            params: 回测参数
        """
        self.logger.info(f"设置回测参数: {params}")
        self.params.update(params)
    
    def add_task(self, strategy_params=None, data=None, task_id=None):
        """
        添加回测任务
        
        Args:
            strategy_params: 策略参数
            data: 回测数据（可选，默认使用全局数据）
            task_id: 任务ID（可选，自动生成）
        """
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:8]}_{datetime.now().timestamp()}"
        
        task = {
            "task_id": task_id,
            "strategy_params": strategy_params or {},
            "data": data or self.params["data"],
            "status": "pending",
            "result": None,
            "start_time": None,
            "end_time": None,
            "duration": None
        }
        
        self.tasks.append(task)
        self.logger.info(f"添加回测任务: {task_id}")
    
    def add_param_grid(self, param_grid):
        """
        添加参数网格任务
        
        Args:
            param_grid: 参数网格，例如:
                {
                    "ma_short": [5, 10, 15],
                    "ma_long": [20, 30, 40],
                    "rsi_period": [6, 12, 24]
                }
        """
        self.logger.info(f"添加参数网格任务，参数组合数量: {self._calculate_param_combinations(param_grid)}")
        
        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_grid)
        
        # 添加任务
        for i, params in enumerate(param_combinations):
            task_id = f"param_task_{i}_{datetime.now().timestamp()}"
            self.add_task(strategy_params=params, task_id=task_id)
    
    def _calculate_param_combinations(self, param_grid):
        """
        计算参数组合数量
        
        Args:
            param_grid: 参数网格
            
        Returns:
            int: 参数组合数量
        """
        from itertools import product
        return len(list(product(*param_grid.values())))
    
    def _generate_param_combinations(self, param_grid):
        """
        生成参数组合
        
        Args:
            param_grid: 参数网格
            
        Returns:
            list: 参数组合列表
        """
        from itertools import product
        
        # 获取参数名称
        param_names = list(param_grid.keys())
        
        # 生成参数值组合
        param_values = list(product(*param_grid.values()))
        
        # 生成参数字典列表
        param_combinations = []
        for values in param_values:
            params = dict(zip(param_names, values))
            param_combinations.append(params)
        
        return param_combinations
    
    def run(self):
        """
        运行并行回测
        
        Returns:
            list: 回测结果列表
        """
        self.logger.info(f"开始并行回测，总任务数: {len(self.tasks)}, 最大工作进程数: {self.params['max_workers']}")
        
        if not self.tasks:
            self.logger.warning("没有待执行的回测任务")
            return []
        
        if not self.params["strategy_class"]:
            self.logger.error("未设置策略类")
            return []
        
        if not self.params["data"] and not all([task["data"] for task in self.tasks]):
            self.logger.error("未设置回测数据")
            return []
        
        # 重置结果
        self.results = []
        
        # 使用进程池执行回测任务
        with mp.Pool(processes=self.params["max_workers"]) as pool:
            # 准备任务参数
            task_args = []
            for task in self.tasks:
                task_args.append((
                    self.params["strategy_class"],
                    task["data"],
                    task["strategy_params"],
                    self.params.copy(),
                    task["task_id"]
                ))
            
            # 并行执行任务
            results = pool.starmap(self._run_backtest, task_args)
        
        # 处理回测结果
        for i, result in enumerate(results):
            self.tasks[i]["status"] = "completed"
            self.tasks[i]["result"] = result
            self.tasks[i]["end_time"] = datetime.now()
            if self.tasks[i]["start_time"]:
                self.tasks[i]["duration"] = (self.tasks[i]["end_time"] - self.tasks[i]["start_time"]).total_seconds()
            self.results.append(result)
        
        self.logger.info(f"并行回测完成，总任务数: {len(self.tasks)}, 成功完成: {len([r for r in self.results if r])}")
        return self.results
    
    @staticmethod
    def _run_backtest(strategy_class, data, strategy_params, backtest_params, task_id):
        """
        执行单个回测任务
        
        Args:
            strategy_class: 策略类
            data: 回测数据
            strategy_params: 策略参数
            backtest_params: 回测参数
            task_id: 任务ID
            
        Returns:
            dict: 回测结果
        """
        from log_utils import get_logger
        logger = get_logger(f"backtest_task_{task_id}")
        
        logger.info(f"开始执行回测任务: {task_id}")
        logger.info(f"策略参数: {strategy_params}")
        
        try:
            # 创建回测引擎
            backtester = BacktestEngine()
            
            # 设置回测参数
            backtester.set_params({
                "initial_cash": backtest_params["initial_cash"],
                "start_date": backtest_params["start_date"],
                "end_date": backtest_params["end_date"],
                "frequency": backtest_params["frequency"],
                "transaction_cost": backtest_params["transaction_cost"],
                "slippage": backtest_params["slippage"]
            })
            
            # 加载数据
            backtester.load_data(data)
            
            # 创建策略实例
            strategy = strategy_class()
            
            # 设置策略参数
            strategy.set_strategy_params(strategy_params)
            
            # 设置策略
            backtester.set_strategy(strategy)
            
            # 运行回测
            backtester.run()
            
            # 获取回测结果
            results = backtester.get_results()
            
            # 添加策略参数到结果中
            results["strategy_params"] = strategy_params
            results["task_id"] = task_id
            
            logger.info(f"回测任务完成: {task_id}")
            logger.info(f"回测结果: {results['performance_metrics']}")
            
            return results
        except Exception as e:
            logger.error(f"回测任务执行失败: {task_id}, 错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "task_id": task_id,
                "strategy_params": strategy_params,
                "error": str(e),
                "status": "failed"
            }
    
    def get_results(self, sort_by=None, ascending=True):
        """
        获取回测结果
        
        Args:
            sort_by: 排序字段
            ascending: 是否升序排列
            
        Returns:
            list: 回测结果列表
        """
        if not self.results:
            return []
        
        if sort_by:
            # 排序结果
            self.results.sort(key=lambda x: x["performance_metrics"].get(sort_by, 0), reverse=not ascending)
        
        return self.results
    
    def get_best_result(self, metric="sharpe_ratio", ascending=False):
        """
        获取最优回测结果
        
        Args:
            metric: 评估指标
            ascending: 是否升序排列
            
        Returns:
            dict: 最优回测结果
        """
        if not self.results:
            return None
        
        # 找到最优结果
        best_result = None
        best_value = None
        
        for result in self.results:
            if "error" in result:
                continue
            
            value = result["performance_metrics"].get(metric, 0)
            
            if best_result is None:
                best_result = result
                best_value = value
            else:
                if ascending:
                    if value < best_value:
                        best_result = result
                        best_value = value
                else:
                    if value > best_value:
                        best_result = result
                        best_value = value
        
        return best_result
    
    def save_results(self, file_path):
        """
        保存回测结果
        
        Args:
            file_path: 保存路径
        """
        self.logger.info(f"保存回测结果到: {file_path}")
        
        if not self.results:
            self.logger.warning("没有回测结果可保存")
            return
        
        # 保存结果到JSON文件
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            # 转换datetime对象为字符串
            def default_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.strftime('%Y-%m-%d %H:%M:%S')
                return obj
            
            json.dump(self.results, f, default=default_serializer, ensure_ascii=False, indent=2)
        
        self.logger.info(f"回测结果已保存到: {file_path}")
    
    def load_results(self, file_path):
        """
        加载回测结果
        
        Args:
            file_path: 加载路径
        """
        self.logger.info(f"加载回测结果从: {file_path}")
        
        # 从JSON文件加载结果
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            self.results = json.load(f)
        
        self.logger.info(f"回测结果加载完成，共 {len(self.results)} 个结果")
        return self.results
    
    def reset(self):
        """
        重置并行回测器
        """
        self.logger.info("重置并行回测器")
        self.tasks = []
        self.results = []
        self.logger.info("并行回测器重置完成")
    
    def generate_summary(self):
        """
        生成回测结果摘要
        
        Returns:
            dict: 回测结果摘要
        """
        if not self.results:
            return {"message": "没有回测结果"}
        
        # 统计结果
        total_tasks = len(self.results)
        successful_tasks = len([r for r in self.results if "error" not in r])
        failed_tasks = total_tasks - successful_tasks
        
        # 计算平均性能指标
        metrics = ["total_return", "annual_return", "sharpe_ratio", "max_drawdown", "win_rate"]
        avg_metrics = {}
        
        for metric in metrics:
            values = [r["performance_metrics"][metric] for r in self.results if "error" not in r and metric in r["performance_metrics"]]
            if values:
                avg_metrics[f"avg_{metric}"] = np.mean(values)
                avg_metrics[f"std_{metric}"] = np.std(values)
                avg_metrics[f"max_{metric}"] = np.max(values)
                avg_metrics[f"min_{metric}"] = np.min(values)
        
        summary = {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks * 100 if total_tasks > 0 else 0,
            "avg_metrics": avg_metrics,
            "best_result": self.get_best_result(),
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.logger.info(f"生成回测结果摘要: {summary}")
        return summary
