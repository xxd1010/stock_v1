#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户界面模块

提供股票分析程序的图形用户界面
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox, QTabWidget,
    QTextBrowser, QFileDialog, QMessageBox, QProgressBar, QGroupBox,
    QFormLayout, QTableWidget, QTableWidgetItem, QSplitter, QListWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

# 确保项目根目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from main import StockAnalyzer
from log_utils import get_logger, setup_logger

# 初始化日志
setup_logger()
logger = get_logger("ui")


class AnalysisThread(QThread):
    """
    分析线程类
    
    在后台线程中执行股票分析，避免阻塞UI
    """
    
    # 信号定义
    update_progress = pyqtSignal(str, int)
    analysis_finished = pyqtSignal(str, dict)
    analysis_error = pyqtSignal(str, str)
    
    def __init__(self, analyzer: StockAnalyzer, stock_code: str, start_date: str, end_date: str):
        """
        初始化分析线程
        
        Args:
            analyzer: 股票分析器实例
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        super().__init__()
        self.analyzer = analyzer
        self.stock_code = stock_code
        self.start_date = start_date
        self.end_date = end_date
    
    def run(self):
        """
        线程执行方法
        """
        try:
            self.update_progress.emit(self.stock_code, 10)
            
            # 执行分析
            result = self.analyzer.analyze_stock(self.stock_code, self.start_date, self.end_date)
            
            self.update_progress.emit(self.stock_code, 100)
            self.analysis_finished.emit(self.stock_code, result)
        except Exception as e:
            self.analysis_error.emit(self.stock_code, str(e))


class BatchAnalysisThread(QThread):
    """
    批量分析线程类
    
    在后台线程中执行批量股票分析
    """
    
    # 信号定义
    update_progress = pyqtSignal(int, int)
    batch_finished = pyqtSignal(dict)
    batch_error = pyqtSignal(str)
    
    def __init__(self, analyzer: StockAnalyzer, stock_codes: list, start_date: str, end_date: str):
        """
        初始化批量分析线程
        
        Args:
            analyzer: 股票分析器实例
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        super().__init__()
        self.analyzer = analyzer
        self.stock_codes = stock_codes
        self.start_date = start_date
        self.end_date = end_date
    
    def run(self):
        """
        线程执行方法
        """
        try:
            total = len(self.stock_codes)
            results = {}
            
            for i, stock_code in enumerate(self.stock_codes):
                progress = int((i + 1) / total * 100)
                self.update_progress.emit(i + 1, total)
                
                # 执行分析
                result = self.analyzer.analyze_stock(stock_code, self.start_date, self.end_date)
                results[stock_code] = result
            
            self.batch_finished.emit(results)
        except Exception as e:
            self.batch_error.emit(str(e))


class StockAnalysisUI(QMainWindow):
    """
    股票分析程序主界面
    """
    
    def __init__(self):
        """
        初始化主界面
        """
        super().__init__()
        self.setWindowTitle("股票分析程序")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化股票分析器
        self.analyzer = None
        
        # 初始化分析线程
        self.analysis_thread = None
        self.batch_thread = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化定时器，用于定期更新日志
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.update_log)
        self.log_timer.start(1000)  # 每秒更新一次
    
    def init_ui(self):
        """
        初始化UI组件
        """
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建单只股票分析标签页
        self.create_single_analysis_tab()
        
        # 创建批量分析标签页
        self.create_batch_analysis_tab()
        
        # 创建日志标签页
        self.create_log_tab()
        
        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
    
    def create_menu_bar(self):
        """
        创建菜单栏
        """
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 分析菜单
        analysis_menu = menu_bar.addMenu("分析")
        single_analysis_action = analysis_menu.addAction("单只股票分析")
        single_analysis_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        
        batch_analysis_action = analysis_menu.addAction("批量分析")
        batch_analysis_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
    
    def create_tool_bar(self):
        """
        创建工具栏
        """
        tool_bar = self.addToolBar("工具栏")
        
        # 单只股票分析按钮
        single_btn = QPushButton("单只分析")
        single_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        tool_bar.addWidget(single_btn)
        
        # 批量分析按钮
        batch_btn = QPushButton("批量分析")
        batch_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        tool_bar.addWidget(batch_btn)
        
        # 退出按钮
        exit_btn = QPushButton("退出")
        exit_btn.clicked.connect(self.close)
        tool_bar.addWidget(exit_btn)
    
    def create_single_analysis_tab(self):
        """
        创建单只股票分析标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # 创建参数输入区域
        param_group = QGroupBox("分析参数")
        param_layout = QFormLayout(param_group)
        
        # 股票代码输入
        self.stock_code_edit = QLineEdit()
        self.stock_code_edit.setPlaceholderText("例如: SH.600000")
        param_layout.addRow("股票代码:", self.stock_code_edit)
        
        # 日期范围选择
        date_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(datetime.now().replace(year=datetime.now().year - 1))
        self.start_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel(" 至 "))
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(datetime.now())
        self.end_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.end_date_edit)
        
        param_layout.addRow("日期范围:", date_layout)
        
        # 分析按钮
        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.clicked.connect(self.start_single_analysis)
        btn_layout.addWidget(self.analyze_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_single_analysis)
        btn_layout.addWidget(self.clear_btn)
        
        param_layout.addRow(btn_layout)
        
        splitter.addWidget(param_group)
        
        # 结果显示区域
        result_group = QGroupBox("分析结果")
        result_layout = QVBoxLayout(result_group)
        
        # 结果表格
        self.result_table = QTableWidget(0, 7)
        self.result_table.setHorizontalHeaderLabels([
            "股票代码", "最新价格", "当前趋势", "趋势强度", "支撑位", "阻力位", "投资建议"
        ])
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        result_layout.addWidget(self.result_table)
        
        splitter.addWidget(result_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.tab_widget.addTab(tab, "单只股票分析")
    
    def create_batch_analysis_tab(self):
        """
        创建批量分析标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # 批量分析参数
        batch_group = QGroupBox("批量分析参数")
        batch_layout = QFormLayout(batch_group)
        
        # 股票代码列表
        self.stock_list = QListWidget()
        self.stock_list.setSelectionMode(QListWidget.MultiSelection)
        batch_layout.addRow("股票代码列表:", self.stock_list)
        
        # 加载股票代码按钮
        load_btn = QPushButton("加载股票代码文件")
        load_btn.clicked.connect(self.load_stock_codes)
        batch_layout.addRow(load_btn)
        
        # 日期范围
        date_layout = QHBoxLayout()
        self.batch_start_date = QDateEdit()
        self.batch_start_date.setDate(datetime.now().replace(year=datetime.now().year - 1))
        self.batch_start_date.setCalendarPopup(True)
        date_layout.addWidget(self.batch_start_date)
        
        date_layout.addWidget(QLabel(" 至 "))
        
        self.batch_end_date = QDateEdit()
        self.batch_end_date.setDate(datetime.now())
        self.batch_end_date.setCalendarPopup(True)
        date_layout.addWidget(self.batch_end_date)
        
        batch_layout.addRow("日期范围:", date_layout)
        
        # 批量分析按钮
        btn_layout = QHBoxLayout()
        self.batch_analyze_btn = QPushButton("开始批量分析")
        self.batch_analyze_btn.clicked.connect(self.start_batch_analysis)
        btn_layout.addWidget(self.batch_analyze_btn)
        
        self.batch_clear_btn = QPushButton("清空")
        self.batch_clear_btn.clicked.connect(self.clear_batch_analysis)
        btn_layout.addWidget(self.batch_clear_btn)
        
        batch_layout.addRow(btn_layout)
        
        splitter.addWidget(batch_group)
        
        # 批量分析结果
        batch_result_group = QGroupBox("批量分析结果")
        batch_result_layout = QVBoxLayout(batch_result_group)
        
        self.batch_result_table = QTableWidget(0, 5)
        self.batch_result_table.setHorizontalHeaderLabels([
            "股票代码", "分析状态", "当前趋势", "投资建议", "报告路径"
        ])
        self.batch_result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        batch_result_layout.addWidget(self.batch_result_table)
        
        splitter.addWidget(batch_result_group)
        
        # 进度条
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setVisible(False)
        layout.addWidget(self.batch_progress_bar)
        
        self.tab_widget.addTab(tab, "批量分析")
    
    def create_log_tab(self):
        """
        创建日志标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 日志显示
        self.log_browser = QTextBrowser()
        self.log_browser.setReadOnly(True)
        layout.addWidget(self.log_browser)
        
        self.tab_widget.addTab(tab, "日志")
    
    def start_single_analysis(self):
        """
        开始单只股票分析
        """
        # 获取参数
        stock_code = self.stock_code_edit.text().strip()
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # 验证参数
        if not stock_code:
            QMessageBox.warning(self, "警告", "请输入股票代码")
            return
        
        # 检查日期
        if start_date > end_date:
            QMessageBox.warning(self, "警告", "开始日期不能晚于结束日期")
            return
        
        # 初始化分析器
        if not self.analyzer:
            try:
                self.analyzer = StockAnalyzer()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"初始化分析器失败: {str(e)}")
                return
        
        # 禁用按钮
        self.analyze_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        
        # 创建并启动分析线程
        self.analysis_thread = AnalysisThread(self.analyzer, stock_code, start_date, end_date)
        self.analysis_thread.update_progress.connect(self.update_single_progress)
        self.analysis_thread.analysis_finished.connect(self.on_single_analysis_finished)
        self.analysis_thread.analysis_error.connect(self.on_single_analysis_error)
        self.analysis_thread.start()
    
    def update_single_progress(self, stock_code, progress):
        """
        更新单只分析进度
        """
        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(f"正在分析 {stock_code}... {progress}%")
    
    def on_single_analysis_finished(self, stock_code, result):
        """
        单只分析完成处理
        """
        # 恢复按钮状态
        self.analyze_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 更新状态栏
        self.status_bar.showMessage("分析完成")
        
        # 获取趋势报告
        trend_report = result['trend_report']
        
        # 添加到结果表格
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        
        # 股票代码
        self.result_table.setItem(row, 0, QTableWidgetItem(trend_report['stock_code']))
        # 最新价格
        self.result_table.setItem(row, 1, QTableWidgetItem(f"{trend_report['latest_price']} 元"))
        # 当前趋势
        self.result_table.setItem(row, 2, QTableWidgetItem(trend_report['latest_trend']))
        # 趋势强度
        self.result_table.setItem(row, 3, QTableWidgetItem(f"{trend_report['trend_strength']}%"))
        # 支撑位
        self.result_table.setItem(row, 4, QTableWidgetItem(', '.join(map(str, trend_report['support_levels']))))
        # 阻力位
        self.result_table.setItem(row, 5, QTableWidgetItem(', '.join(map(str, trend_report['resistance_levels']))))
        # 投资建议
        self.result_table.setItem(row, 6, QTableWidgetItem(trend_report['investment_suggestion']))
    
    def on_single_analysis_error(self, stock_code, error):
        """
        单只分析错误处理
        """
        # 恢复按钮状态
        self.analyze_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 显示错误信息
        QMessageBox.critical(self, "错误", f"分析股票 {stock_code} 失败: {error}")
        self.status_bar.showMessage("分析失败")
    
    def clear_single_analysis(self):
        """
        清空单只分析
        """
        self.stock_code_edit.clear()
        self.start_date_edit.setDate(datetime.now().replace(year=datetime.now().year - 1))
        self.end_date_edit.setDate(datetime.now())
        self.result_table.setRowCount(0)
    
    def load_stock_codes(self):
        """
        加载股票代码文件
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择股票代码文件", ".", "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 假设文件格式为: 股票代码,股票名称
                            parts = line.split(',')
                            if parts:
                                self.stock_list.addItem(parts[0])
                
                QMessageBox.information(self, "提示", f"成功加载 {self.stock_list.count()} 个股票代码")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载股票代码失败: {str(e)}")
    
    def start_batch_analysis(self):
        """
        开始批量分析
        """
        # 获取选中的股票代码
        selected_items = self.stock_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要分析的股票")
            return
        
        stock_codes = [item.text() for item in selected_items]
        start_date = self.batch_start_date.date().toString("yyyy-MM-dd")
        end_date = self.batch_end_date.date().toString("yyyy-MM-dd")
        
        # 检查日期
        if start_date > end_date:
            QMessageBox.warning(self, "警告", "开始日期不能晚于结束日期")
            return
        
        # 初始化分析器
        if not self.analyzer:
            try:
                self.analyzer = StockAnalyzer()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"初始化分析器失败: {str(e)}")
                return
        
        # 禁用按钮
        self.batch_analyze_btn.setEnabled(False)
        self.batch_clear_btn.setEnabled(False)
        
        # 显示进度条
        self.batch_progress_bar.setVisible(True)
        self.batch_progress_bar.setValue(0)
        self.batch_progress_bar.setRange(0, len(stock_codes))
        
        # 创建并启动批量分析线程
        self.batch_thread = BatchAnalysisThread(self.analyzer, stock_codes, start_date, end_date)
        self.batch_thread.update_progress.connect(self.update_batch_progress)
        self.batch_thread.batch_finished.connect(self.on_batch_analysis_finished)
        self.batch_thread.batch_error.connect(self.on_batch_analysis_error)
        self.batch_thread.start()
    
    def update_batch_progress(self, current, total):
        """
        更新批量分析进度
        """
        self.batch_progress_bar.setValue(current)
        self.status_bar.showMessage(f"正在分析第 {current} / {total} 只股票...")
    
    def on_batch_analysis_finished(self, results):
        """
        批量分析完成处理
        """
        # 恢复按钮状态
        self.batch_analyze_btn.setEnabled(True)
        self.batch_clear_btn.setEnabled(True)
        
        # 隐藏进度条
        self.batch_progress_bar.setVisible(False)
        
        # 更新状态栏
        self.status_bar.showMessage(f"批量分析完成，共分析 {len(results)} 只股票")
        
        # 清空结果表格
        self.batch_result_table.setRowCount(0)
        
        # 添加结果到表格
        for stock_code, result in results.items():
            if isinstance(result, dict) and 'trend_report' in result:
                trend_report = result['trend_report']
                row = self.batch_result_table.rowCount()
                self.batch_result_table.insertRow(row)
                
                self.batch_result_table.setItem(row, 0, QTableWidgetItem(stock_code))
                self.batch_result_table.setItem(row, 1, QTableWidgetItem("成功"))
                self.batch_result_table.setItem(row, 2, QTableWidgetItem(trend_report['latest_trend']))
                self.batch_result_table.setItem(row, 3, QTableWidgetItem(trend_report['investment_suggestion']))
                
                # 获取报告路径
                report_path = ""
                if 'export_results' in result:
                    for fmt, path in result['export_results'].items():
                        if path and isinstance(path, str) and not path.startswith("Error"):
                            report_path = path
                            break
                
                self.batch_result_table.setItem(row, 4, QTableWidgetItem(report_path))
    
    def on_batch_analysis_error(self, error):
        """
        批量分析错误处理
        """
        # 恢复按钮状态
        self.batch_analyze_btn.setEnabled(True)
        self.batch_clear_btn.setEnabled(True)
        
        # 隐藏进度条
        self.batch_progress_bar.setVisible(False)
        
        # 显示错误信息
        QMessageBox.critical(self, "错误", f"批量分析失败: {error}")
        self.status_bar.showMessage("批量分析失败")
    
    def clear_batch_analysis(self):
        """
        清空批量分析
        """
        self.stock_list.clearSelection()
        self.batch_result_table.setRowCount(0)
    
    def update_log(self):
        """
        更新日志显示
        """
        # 这里可以添加日志更新逻辑
        # 例如，读取日志文件并显示
        pass
    
    def show_about(self):
        """
        显示关于信息
        """
        about_text = """
        股票分析程序
        版本: 1.0
        功能: 股票数据获取、技术指标计算、趋势分析、可视化展示、报告生成与导出
        """
        QMessageBox.about(self, "关于", about_text)
    
    def closeEvent(self, event):
        """
        关闭事件处理
        """
        reply = QMessageBox.question(
            self, "退出确认", "确定要退出程序吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockAnalysisUI()
    window.show()
    sys.exit(app.exec_())
