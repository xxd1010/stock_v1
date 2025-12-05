#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数优化模块

提供全面的参数优化功能，包括参数推荐、优化算法、性能评估等
"""

import pandas as pd
import numpy as np
import itertools
import random
import json
import os
from datetime import datetime
from log_utils import get_logger

# 获取日志记录器
logger = get_logger("parameter_optimizer")


class ParameterOptimizer:
    """
    参数优化器
    
    提供参数优化的核心功能，支持多种优化算法
    """
    
    def __init__(self, strategy_class, backtest_engine, data, context):
        """
        初始化参数优化器
        
        Args:
            strategy_class: 策略类
            backtest_engine: 回测引擎实例
            data: 回测数据
            context: 回测上下文
        """
        self.strategy_class = strategy_class
        self.backtest_engine = backtest_engine
        self.data = data
        self.context = context
        self.logger = get_logger("ParameterOptimizer")
        self.logger.info("初始化参数优化器")
        
        # 优化算法映射
        self.optimization_algorithms = {
            "grid_search": self._grid_search,
            "random_search": self._random_search,
            "genetic_algorithm": self._genetic_algorithm
        }
    
    def optimize(self, param_space, algorithm="grid_search", max_iterations=100, **kwargs):
        """
        执行参数优化
        
        Args:
            param_space: 参数空间配置
            algorithm: 优化算法名称
            max_iterations: 最大迭代次数
            **kwargs: 算法特定参数
            
        Returns:
            dict: 优化结果
        """
        self.logger.info(f"开始参数优化，使用算法: {algorithm}")
        
        # 检查算法是否支持
        if algorithm not in self.optimization_algorithms:
            self.logger.error(f"不支持的优化算法: {algorithm}")
            raise ValueError(f"不支持的优化算法: {algorithm}")
        
        # 执行优化
        optimization_func = self.optimization_algorithms[algorithm]
        results = optimization_func(param_space, max_iterations, **kwargs)
        
        # 排序并返回最优结果
        results.sort(key=lambda x: x["performance"]["sharpe_ratio"], reverse=True)
        
        best_result = results[0]
        self.logger.info(f"参数优化完成，最优结果: {best_result}")
        
        return {
            "best_params": best_result["params"],
            "best_performance": best_result["performance"],
            "all_results": results
        }
    
    def recommend_params(self, param_space, method="statistical"):
        """
        基于历史数据推荐参数
        
        Args:
            param_space: 参数空间配置
            method: 推荐方法
            
        Returns:
            dict: 推荐参数
        """
        self.logger.info(f"生成参数推荐，使用方法: {method}")
        
        # 简单的统计推荐逻辑，基于参数空间的统计特征
        recommended_params = {}
        
        for param_name, param_config in param_space.items():
            if param_config["type"] == "integer":
                # 对于整数参数，推荐中间值
                recommended_params[param_name] = (param_config["min"] + param_config["max"]) // 2
            elif param_config["type"] == "float":
                # 对于浮点数参数，推荐中间值
                recommended_params[param_name] = (param_config["min"] + param_config["max"]) / 2
            elif param_config["type"] == "choice":
                # 对于选择类型，推荐第一个选项
                recommended_params[param_name] = param_config["choices"][0]
            else:
                # 默认使用默认值
                recommended_params[param_name] = param_config.get("default", 0)
        
        self.logger.info(f"参数推荐完成: {recommended_params}")
        return recommended_params
    
    def evaluate_performance(self, params):
        """
        评估参数性能
        
        Args:
            params: 要评估的参数
            
        Returns:
            dict: 性能指标
        """
        self.logger.info(f"评估参数性能: {params}")
        
        # 创建策略实例
        strategy = self.strategy_class()
        strategy.set_strategy_params(params)
        
        # 设置策略并运行回测
        self.backtest_engine.set_strategy(strategy)
        self.backtest_engine.load_data(self.data)
        self.backtest_engine.initialize()
        self.backtest_engine.run()
        
        # 获取回测结果
        results = self.backtest_engine.get_results()
        performance_metrics = results.get("performance_metrics", {})
        
        self.logger.info(f"参数性能评估完成: {performance_metrics}")
        return performance_metrics
    
    def save_params_version(self, params, performance_metrics, version_name, description=""):
        """
        保存参数版本
        
        Args:
            params: 参数
            performance_metrics: 性能指标
            version_name: 版本名称
            description: 版本描述
            
        Returns:
            str: 版本ID
        """
        from param_version_manager import ParamVersionManager
        
        version_manager = ParamVersionManager()
        version_id = version_manager.save_version(
            params=params,
            performance=performance_metrics,
            name=version_name,
            description=description,
            strategy_name=self.strategy_class.__name__
        )
        return version_id
    
    def load_params_version(self, version_id):
        """
        加载参数版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            dict: 参数版本
        """
        from param_version_manager import ParamVersionManager
        
        version_manager = ParamVersionManager()
        return version_manager.load_version(version_id)
    
    def _grid_search(self, param_space, max_iterations=100, **kwargs):
        """
        网格搜索优化算法
        
        Args:
            param_space: 参数空间配置
            max_iterations: 最大迭代次数
            **kwargs: 算法特定参数
            
        Returns:
            list: 优化结果
        """
        self.logger.info("执行网格搜索优化")
        
        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_space)
        
        # 限制最大迭代次数
        if len(param_combinations) > max_iterations:
            param_combinations = param_combinations[:max_iterations]
        
        results = []
        
        # 评估每个参数组合
        for i, params in enumerate(param_combinations):
            self.logger.info(f"评估参数组合 {i+1}/{len(param_combinations)}: {params}")
            performance = self.evaluate_performance(params)
            results.append({
                "params": params,
                "performance": performance
            })
        
        return results
    
    def _random_search(self, param_space, max_iterations=100, **kwargs):
        """
        随机搜索优化算法
        
        Args:
            param_space: 参数空间配置
            max_iterations: 最大迭代次数
            **kwargs: 算法特定参数
            
        Returns:
            list: 优化结果
        """
        self.logger.info("执行随机搜索优化")
        
        results = []
        
        # 生成随机参数组合
        for i in range(max_iterations):
            # 生成随机参数
            random_params = {}
            for param_name, param_config in param_space.items():
                if param_config["type"] == "integer":
                    random_params[param_name] = random.randint(param_config["min"], param_config["max"])
                elif param_config["type"] == "float":
                    random_params[param_name] = random.uniform(param_config["min"], param_config["max"])
                elif param_config["type"] == "choice":
                    random_params[param_name] = random.choice(param_config["choices"])
            
            self.logger.info(f"评估随机参数组合 {i+1}/{max_iterations}: {random_params}")
            performance = self.evaluate_performance(random_params)
            results.append({
                "params": random_params,
                "performance": performance
            })
        
        return results
    
    def _genetic_algorithm(self, param_space, max_iterations=100, population_size=20, crossover_rate=0.8, mutation_rate=0.1, **kwargs):
        """
        遗传算法优化
        
        Args:
            param_space: 参数空间配置
            max_iterations: 最大迭代次数
            population_size: 种群大小
            crossover_rate: 交叉率
            mutation_rate: 变异率
            **kwargs: 算法特定参数
            
        Returns:
            list: 优化结果
        """
        self.logger.info("执行遗传算法优化")
        
        # 初始化种群
        population = []
        for _ in range(population_size):
            # 生成随机个体
            individual = {}
            for param_name, param_config in param_space.items():
                if param_config["type"] == "integer":
                    individual[param_name] = random.randint(param_config["min"], param_config["max"])
                elif param_config["type"] == "float":
                    individual[param_name] = random.uniform(param_config["min"], param_config["max"])
                elif param_config["type"] == "choice":
                    individual[param_name] = random.choice(param_config["choices"])
            population.append(individual)
        
        results = []
        
        # 进化过程
        for generation in range(max_iterations):
            self.logger.info(f"遗传算法第 {generation+1}/{max_iterations} 代")
            
            # 评估种群
            evaluated_population = []
            for individual in population:
                performance = self.evaluate_performance(individual)
                fitness = performance["sharpe_ratio"]  # 使用夏普比率作为适应度
                evaluated_population.append((fitness, individual))
            
            # 排序并记录最优个体
            evaluated_population.sort(reverse=True)
            best_individual = evaluated_population[0]
            results.append({
                "params": best_individual[1],
                "performance": self.evaluate_performance(best_individual[1])
            })
            
            # 选择（轮盘赌选择）
            total_fitness = sum(fitness for fitness, _ in evaluated_population)
            if total_fitness == 0:
                selected = [individual for _, individual in evaluated_population[:population_size//2]]
            else:
                selected = []
                for _ in range(population_size):
                    r = random.uniform(0, total_fitness)
                    current_sum = 0
                    for fitness, individual in evaluated_population:
                        current_sum += fitness
                        if current_sum >= r:
                            selected.append(individual)
                            break
            
            # 交叉
            new_population = []
            while len(new_population) < population_size:
                # 随机选择两个父代
                parent1, parent2 = random.sample(selected, 2)
                
                if random.random() < crossover_rate:
                    # 单点交叉
                    crossover_point = random.choice(list(param_space.keys()))
                    child1 = parent1.copy()
                    child2 = parent2.copy()
                    
                    # 交换交叉点后的参数
                    crossed = False
                    for param_name in param_space.keys():
                        if crossed:
                            child1[param_name] = parent2[param_name]
                            child2[param_name] = parent1[param_name]
                        if param_name == crossover_point:
                            crossed = True
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                new_population.extend([child1, child2])
            
            # 变异
            for i in range(population_size):
                if random.random() < mutation_rate:
                    # 随机选择一个参数进行变异
                    param_name = random.choice(list(param_space.keys()))
                    param_config = param_space[param_name]
                    
                    if param_config["type"] == "integer":
                        new_value = random.randint(param_config["min"], param_config["max"])
                    elif param_config["type"] == "float":
                        new_value = random.uniform(param_config["min"], param_config["max"])
                    elif param_config["type"] == "choice":
                        new_value = random.choice(param_config["choices"])
                    else:
                        new_value = param_config.get("default", 0)
                    
                    new_population[i][param_name] = new_value
            
            # 更新种群
            population = new_population[:population_size]
        
        return results
    
    def _generate_param_combinations(self, param_space):
        """
        生成参数组合
        
        Args:
            param_space: 参数空间配置
            
        Returns:
            list: 参数组合列表
        """
        # 生成每个参数的可能值
        param_values = []
        param_names = []
        
        for param_name, param_config in param_space.items():
            param_names.append(param_name)
            
            if param_config["type"] == "integer":
                # 整数参数，生成范围内的值
                values = list(range(param_config["min"], param_config["max"] + 1, param_config.get("step", 1)))
            elif param_config["type"] == "float":
                # 浮点数参数，生成采样值
                num_samples = param_config.get("num_samples", 5)
                values = np.linspace(param_config["min"], param_config["max"], num_samples).tolist()
            elif param_config["type"] == "choice":
                # 选择类型，使用提供的选项
                values = param_config["choices"]
            else:
                # 默认使用默认值
                values = [param_config.get("default", 0)]
            
            param_values.append(values)
        
        # 生成笛卡尔积，即所有参数组合
        combinations = []
        for values in itertools.product(*param_values):
            param_combination = {}
            for param_name, value in zip(param_names, values):
                param_combination[param_name] = value
            combinations.append(param_combination)
        
        return combinations
    
    def get_param_space(self, strategy_class=None):
        """
        获取策略的参数空间
        
        Args:
            strategy_class: 策略类（可选，默认使用初始化时的策略类）
            
        Returns:
            dict: 参数空间配置
        """
        if strategy_class is None:
            strategy_class = self.strategy_class
        
        # 简单的参数空间配置，实际应用中可以从策略的配置文件或注解中获取
        param_space = {
            "ma_short": {
                "type": "integer",
                "min": 5,
                "max": 50,
                "step": 5,
                "default": 10,
                "description": "短期均线周期"
            },
            "ma_long": {
                "type": "integer",
                "min": 10,
                "max": 100,
                "step": 10,
                "default": 20,
                "description": "长期均线周期"
            },
            "transaction_cost": {
                "type": "float",
                "min": 0,
                "max": 0.01,
                "num_samples": 3,
                "default": 0.0003,
                "description": "交易成本"
            },
            "slippage": {
                "type": "float",
                "min": 0,
                "max": 0.01,
                "num_samples": 3,
                "default": 0.0001,
                "description": "滑点"
            }
        }
        
        return param_space
