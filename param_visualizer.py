#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数可视化模块

负责参数配置的可视化展示、实时调整和优化结果展示
"""

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QGroupBox, QLabel, 
                             QSlider, QSpinBox, QDoubleSpinBox, QComboBox, 
                             QPushButton, QTextEdit, QTabWidget, QScrollArea,
                             QSplitter, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor
import numpy as np
import pandas as pd
from log_utils import get_logger
import sys

# 获取日志记录器
logger = get_logger("param_visualizer")


class ParamVisualizer:
    """
    参数可视化类
    
    提供参数配置的可视化展示、实时调整和优化结果展示
    """
    
    def __init__(self):
        """
        初始化参数可视化器
        """
        self.logger = get_logger("ParamVisualizer")
        self.logger.info("初始化参数可视化器")
        
    def visualize_parameter_space(self, param_space, sample_params=None, best_params=None):
        """
        可视化参数空间
        
        Args:
            param_space: 参数空间定义
            sample_params: 采样参数点（可选）
            best_params: 最佳参数点（可选）
        """
        self.logger.info("可视化参数空间")
        
        # 对于2D参数空间，使用散点图可视化
        param_names = list(param_space.keys())
        if len(param_names) == 2:
            self._visualize_2d_param_space(param_space, param_names, sample_params, best_params)
        elif len(param_names) > 2:
            self._visualize_high_dimensional_param_space(param_space, param_names, sample_params, best_params)
        else:
            self.logger.warning("参数空间维度不足，无法可视化")
    
    def _visualize_2d_param_space(self, param_space, param_names, sample_params, best_params):
        """
        可视化2D参数空间
        
        Args:
            param_space: 参数空间定义
            param_names: 参数名称列表
            sample_params: 采样参数点
            best_params: 最佳参数点
        """
        # 创建散点图
        fig = go.Figure()
        
        # 添加采样点
        if sample_params:
            x = [p[param_names[0]] for p in sample_params]
            y = [p[param_names[1]] for p in sample_params]
            
            # 如果有性能数据，使用颜色表示
            if isinstance(sample_params[0], dict) and "performance" in sample_params[0]:
                z = [p["performance"] for p in sample_params]
                fig.add_trace(go.Scatter(
                    x=x, y=y, mode='markers',
                    marker=dict(
                        size=10,
                        color=z,
                        colorscale='Viridis',
                        colorbar=dict(title='Performance')
                    ),
                    name='Sample Points'
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=x, y=y, mode='markers',
                    marker=dict(size=10),
                    name='Sample Points'
                ))
        
        # 添加最佳参数点
        if best_params:
            fig.add_trace(go.Scatter(
                x=[best_params[param_names[0]]], 
                y=[best_params[param_names[1]]], 
                mode='markers',
                marker=dict(
                    size=15,
                    color='red',
                    symbol='star'
                ),
                name='Best Params'
            ))
        
        # 设置图表标题和坐标轴
        fig.update_layout(
            title=f'Parameter Space: {param_names[0]} vs {param_names[1]}',
            xaxis_title=param_names[0],
            yaxis_title=param_names[1],
            hovermode='closest'
        )
        
        # 显示图表
        try:
            fig.show()
        except ValueError as e:
            self.logger.warning(f"无法显示图表: {e}")
            # 可以选择保存图表为HTML文件，而不是直接显示
            fig.write_html(f"{title.replace(' ', '_')}.html")
            self.logger.info(f"图表已保存为HTML文件: {title.replace(' ', '_')}.html")
    
    def _visualize_high_dimensional_param_space(self, param_space, param_names, sample_params, best_params):
        """
        可视化高维参数空间
        
        Args:
            param_space: 参数空间定义
            param_names: 参数名称列表
            sample_params: 采样参数点
            best_params: 最佳参数点
        """
        # 使用平行坐标图可视化高维数据
        if sample_params and isinstance(sample_params[0], dict):
            # 准备数据
            df = pd.DataFrame(sample_params)
            
            # 如果没有性能数据，添加默认值
            if "performance" not in df.columns:
                df["performance"] = np.random.rand(len(df))
            
            # 创建平行坐标图
            fig = px.parallel_coordinates(
                df, 
                color="performance", 
                color_continuous_scale=px.colors.diverging.Tealrose,
                title=f'High Dimensional Parameter Space ({len(param_names)} dimensions)'
            )
            
            # 显示图表
            try:
                fig.show()
            except ValueError as e:
                self.logger.warning(f"无法显示图表: {e}")
                # 可以选择保存图表为HTML文件，而不是直接显示
                title = f'High_Dimensional_Parameter_Space_{len(param_names)}_dimensions'
                fig.write_html(f"{title.replace(' ', '_')}.html")
                self.logger.info(f"图表已保存为HTML文件: {title.replace(' ', '_')}.html")
    
    def visualize_optimization_results(self, optimization_history):
        """
        可视化优化结果
        
        Args:
            optimization_history: 优化历史记录，包含迭代次数和性能指标
        """
        self.logger.info("可视化优化结果")
        
        # 提取数据
        iterations = [i for i in range(len(optimization_history))]
        performance = [h["performance"] for h in optimization_history]
        
        # 创建折线图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=iterations, y=performance, mode='lines+markers',
            name='Performance',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        # 添加最佳性能线
        best_performance = max(performance)
        best_iteration = performance.index(best_performance)
        
        fig.add_shape(
            type="line",
            x0=best_iteration, y0=0,
            x1=best_iteration, y1=best_performance,
            line=dict(color="red", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=best_iteration, y=best_performance,
            text=f'Best Performance: {best_performance:.4f}',
            showarrow=True,
            arrowhead=1
        )
        
        # 设置图表标题和坐标轴
        fig.update_layout(
            title='Optimization Process',
            xaxis_title='Iteration',
            yaxis_title='Performance',
            hovermode='x unified'
        )
        
        # 显示图表
        try:
            fig.show()
        except ValueError as e:
            self.logger.warning(f"无法显示图表: {e}")
            # 可以选择保存图表为HTML文件，而不是直接显示
            title = 'Optimization_Process'
            fig.write_html(f"{title.replace(' ', '_')}.html")
            self.logger.info(f"图表已保存为HTML文件: {title.replace(' ', '_')}.html")
    
    def visualize_parameter_importance(self, param_importance):
        """
        可视化参数重要性
        
        Args:
            param_importance: 参数重要性字典，格式为{param_name: importance_value}
        """
        self.logger.info("可视化参数重要性")
        
        # 创建水平条形图
        params = list(param_importance.keys())
        importance = list(param_importance.values())
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=importance,
            y=params,
            orientation='h',
            marker=dict(
                color='rgba(58, 71, 80, 0.6)',
                line=dict(color='rgba(58, 71, 80, 1.0)', width=1)
            )
        ))
        
        # 设置图表标题和坐标轴
        fig.update_layout(
            title='Parameter Importance',
            xaxis_title='Importance Score',
            yaxis_title='Parameters',
            yaxis=dict(autorange="reversed"),
            hovermode='closest'
        )
        
        # 显示图表
        try:
            fig.show()
        except ValueError as e:
            self.logger.warning(f"无法显示图表: {e}")
            # 可以选择保存图表为HTML文件，而不是直接显示
            title = 'Parameter_Importance'
            fig.write_html(f"{title.replace(' ', '_')}.html")
            self.logger.info(f"图表已保存为HTML文件: {title.replace(' ', '_')}.html")
    
    def create_param_adjustment_gui(self, param_space, callback=None):
        """
        创建参数调整GUI界面
        
        Args:
            param_space: 参数空间定义
            callback: 参数调整回调函数
        """
        self.logger.info("创建参数调整GUI界面")
        
        # 创建Qt应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = ParamAdjustmentWindow(param_space, callback)
        window.show()
        
        # 运行应用
        sys.exit(app.exec_())


class ParamAdjustmentWindow(QMainWindow):
    """
    参数调整窗口类
    
    用于创建参数调整GUI界面，支持实时参数调整和预览
    """
    
    def __init__(self, param_space, callback=None):
        """
        初始化参数调整窗口
        
        Args:
            param_space: 参数空间定义
            callback: 参数调整回调函数
        """
        super().__init__()
        
        self.param_space = param_space
        self.callback = callback
        self.current_params = {}
        
        # 设置窗口属性
        self.setWindowTitle("参数调整界面")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建参数调整选项卡
        self._create_param_adjustment_tab()
        
        # 创建参数说明选项卡
        self._create_param_description_tab()
        
        # 创建控制按钮
        self._create_control_buttons(main_layout)
        
        # 初始化当前参数
        self._init_current_params()
    
    def _create_param_adjustment_tab(self):
        """
        创建参数调整选项卡
        """
        param_tab = QWidget()
        param_layout = QVBoxLayout(param_tab)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        param_layout.addWidget(scroll_area)
        
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        
        # 创建参数控件
        self.param_widgets = {}
        row = 0
        
        for param_name, param_config in self.param_space.items():
            # 创建参数组
            group_box = QGroupBox(param_name)
            group_layout = QVBoxLayout(group_box)
            
            # 添加参数说明
            description = param_config.get("description", "无说明")
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            group_layout.addWidget(desc_label)
            
            # 根据参数类型创建不同的控件
            param_type = param_config.get("type", "float")
            min_val = param_config.get("min", 0)
            max_val = param_config.get("max", 100)
            default = param_config.get("default", (min_val + max_val) / 2)
            step = param_config.get("step", 0.1)
            
            control_layout = QHBoxLayout()
            
            if param_type in ["int", "float"]:
                # 数值型参数使用滑块和输入框
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(int(min_val / step))
                slider.setMaximum(int(max_val / step))
                slider.setValue(int(default / step))
                slider.setTickInterval(int((max_val - min_val) / step / 10))
                slider.setTickPosition(QSlider.TicksBelow)
                
                if param_type == "int":
                    spin_box = QSpinBox()
                    spin_box.setMinimum(int(min_val))
                    spin_box.setMaximum(int(max_val))
                    spin_box.setValue(int(default))
                    spin_box.setSingleStep(int(step))
                else:
                    spin_box = QDoubleSpinBox()
                    spin_box.setMinimum(min_val)
                    spin_box.setMaximum(max_val)
                    spin_box.setValue(default)
                    spin_box.setSingleStep(step)
                    spin_box.setDecimals(4)
                
                # 连接信号
                slider.valueChanged.connect(lambda value, sb=spin_box, s=step: sb.setValue(value * s))
                spin_box.valueChanged.connect(lambda value, sl=slider, s=step: sl.setValue(int(value / s)))
                spin_box.valueChanged.connect(lambda value, pn=param_name: self._on_param_changed(pn, value))
                
                control_layout.addWidget(slider, 3)
                control_layout.addWidget(spin_box, 1)
                
                self.param_widgets[param_name] = spin_box
            
            elif param_type == "select":
                # 选择型参数使用下拉框
                options = param_config.get("options", [])
                combo_box = QComboBox()
                combo_box.addItems(options)
                if default in options:
                    combo_box.setCurrentText(default)
                
                combo_box.currentTextChanged.connect(lambda value, pn=param_name: self._on_param_changed(pn, value))
                
                control_layout.addWidget(combo_box)
                self.param_widgets[param_name] = combo_box
            
            group_layout.addLayout(control_layout)
            scroll_layout.addWidget(group_box, row, 0, 1, 2)
            row += 1
        
        # 添加预览区域
        preview_group = QGroupBox("实时预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(150)
        preview_layout.addWidget(self.preview_text)
        
        scroll_layout.addWidget(preview_group, row, 0, 1, 2)
        
        self.tab_widget.addTab(param_tab, "参数调整")
    
    def _create_param_description_tab(self):
        """
        创建参数说明选项卡
        """
        desc_tab = QWidget()
        desc_layout = QVBoxLayout(desc_tab)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        desc_layout.addWidget(scroll_area)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        
        # 添加参数详细说明
        for param_name, param_config in self.param_space.items():
            # 创建参数说明区域
            param_frame = QFrame()
            param_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
            param_frame.setLineWidth(1)
            param_layout = QVBoxLayout(param_frame)
            
            # 参数名称
            name_label = QLabel(param_name)
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            name_label.setFont(font)
            param_layout.addWidget(name_label)
            
            # 参数类型
            type_label = QLabel(f"类型: {param_config.get('type', 'float')}")
            param_layout.addWidget(type_label)
            
            # 参数范围
            if "min" in param_config and "max" in param_config:
                range_label = QLabel(f"范围: {param_config['min']} - {param_config['max']}")
                param_layout.addWidget(range_label)
            
            # 默认值
            default_label = QLabel(f"默认值: {param_config.get('default', '无')}")
            param_layout.addWidget(default_label)
            
            # 详细说明
            desc_label = QLabel(f"说明: {param_config.get('description', '无说明')}")
            desc_label.setWordWrap(True)
            param_layout.addWidget(desc_label)
            
            # 添加到布局
            scroll_layout.addWidget(param_frame)
            scroll_layout.addSpacing(10)
        
        self.tab_widget.addTab(desc_tab, "参数说明")
    
    def _create_control_buttons(self, main_layout):
        """
        创建控制按钮
        """
        button_layout = QHBoxLayout()
        
        # 重置按钮
        reset_button = QPushButton("重置参数")
        reset_button.clicked.connect(self._reset_params)
        button_layout.addWidget(reset_button)
        
        # 应用按钮
        apply_button = QPushButton("应用参数")
        apply_button.clicked.connect(self._apply_params)
        button_layout.addWidget(apply_button)
        
        # 保存按钮
        save_button = QPushButton("保存参数")
        save_button.clicked.connect(self._save_params)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)
    
    def _init_current_params(self):
        """
        初始化当前参数
        """
        for param_name, param_config in self.param_space.items():
            default = param_config.get("default", 0)
            self.current_params[param_name] = default
        
        self._update_preview()
    
    def _on_param_changed(self, param_name, value):
        """
        参数值变化处理
        
        Args:
            param_name: 参数名称
            value: 新的参数值
        """
        self.current_params[param_name] = value
        self._update_preview()
        
        # 调用回调函数
        if self.callback:
            self.callback(self.current_params)
    
    def _update_preview(self):
        """
        更新预览信息
        """
        preview_text = "当前参数配置:\n\n"
        for param_name, value in self.current_params.items():
            preview_text += f"{param_name}: {value}\n"
        
        self.preview_text.setText(preview_text)
    
    def _reset_params(self):
        """
        重置参数到默认值
        """
        for param_name, param_config in self.param_space.items():
            default = param_config.get("default", 0)
            widget = self.param_widgets.get(param_name)
            
            if widget:
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(default)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(default)
    
    def _apply_params(self):
        """
        应用当前参数
        """
        self.logger.info(f"应用参数: {self.current_params}")
        if self.callback:
            self.callback(self.current_params)
    
    def _save_params(self):
        """
        保存当前参数
        """
        # 这里可以调用版本管理模块保存参数
        self.logger.info(f"保存参数: {self.current_params}")
    
    def get_current_params(self):
        """
        获取当前参数
        
        Returns:
            dict: 当前参数配置
        """
        return self.current_params


# 示例用法
if __name__ == "__main__":
    # 创建参数可视化器
    visualizer = ParamVisualizer()
    
    # 示例参数空间
    param_space = {
        "window_size": {
            "type": "int",
            "min": 5,
            "max": 50,
            "default": 20,
            "step": 1,
            "description": "移动窗口大小，用于计算指标"
        },
        "threshold": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "step": 0.01,
            "description": "触发信号的阈值"
        },
        "risk_level": {
            "type": "select",
            "options": ["low", "medium", "high"],
            "default": "medium",
            "description": "风险等级设置"
        }
    }
    
    # 示例优化历史
    optimization_history = [{"performance": 0.1}, {"performance": 0.3}, {"performance": 0.25}, 
                           {"performance": 0.4}, {"performance": 0.35}, {"performance": 0.5}]
    
    # 示例参数重要性
    param_importance = {"window_size": 0.6, "threshold": 0.3, "risk_level": 0.1}
    
    # 可视化优化结果
    visualizer.visualize_optimization_results(optimization_history)
    
    # 可视化参数重要性
    visualizer.visualize_parameter_importance(param_importance)
    
    # 启动参数调整GUI
    def on_param_change(params):
        print(f"参数已调整: {params}")
    
    visualizer.create_param_adjustment_gui(param_space, on_param_change)
