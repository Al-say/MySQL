import sys
import mysql.connector
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                         QHBoxLayout, QPushButton, QLabel, QScrollArea,
                         QFrame, QRadioButton, QButtonGroup, QTextEdit, QDialog,
                         QMessageBox, QSizePolicy, QTabWidget, QFileDialog,
                         QAbstractButton, QGroupBox, QCheckBox, QLineEdit, QInputDialog)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import (Qt, QTimer, pyqtSignal, QSize, QObject, QEvent)
from PyQt6.QtGui import (QKeyEvent, QTextCursor, QPainter, QColor, QBrush,
                      QFont, QPen, QTextCharFormat)
import json
from pathlib import Path
import logging
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import tensorflow as tf
import requests
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('practice_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Constants:
    """常量配置类"""
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '178309',
        'database': 'mysql_exercise_db',
        'buffered': True,
        'autocommit': True
    }
    
    WINDOW_TITLE = 'MySQL练习系统'
    WINDOW_GEOMETRY = (100, 100, 800, 600)
    
    # 题型ID映射
    QUESTION_TYPES = {
        'all': 0,
        'multiple_choice': 1,
        'true_false': 2,
        'fill_blank': 3,
        'short_answer': 4
    }
    
    # 难度级别ID映射
    DIFFICULTY_LEVELS = {
        'all': 0,
        'beginner': 1,
        'intermediate': 2,
        'advanced': 3
    }
    
    # 缓存配置
    CACHE_DIR = Path('cache')
    CACHE_DURATION = 3600  # 缓存有效期（秒）
    
    # 样式配置
    STYLES = {
        'button': """
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #0056b3;
            }
        """,
        'group_box': """
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """
    }

class Cache:
    """缓存管理类"""
    def __init__(self, cache_dir: Path = Constants.CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
            
        try:
            data = json.loads(cache_file.read_text(encoding='utf-8'))
            # 检查缓存是否过期
            if datetime.now().timestamp() - data['timestamp'] > Constants.CACHE_DURATION:
                cache_file.unlink()
                return None
            return data['value']
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return None
            
    def set(self, key: str, value: Any) -> None:
        """设置缓存数据"""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            data = {
                'timestamp': datetime.now().timestamp(),
                'value': value
            }
            cache_file.write_text(json.dumps(data), encoding='utf-8')
        except Exception as e:
            logger.error(f"写入缓存失败: {e}")
            
    def clear(self) -> None:
        """清除所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")

class DatabaseManager:
    """数据库管理类"""
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.cache = Cache()
        
    def connect(self) -> bool:
        """连接数据库"""
        try:
            if self.conn:
                self.close()
                
            self.conn = mysql.connector.connect(**Constants.DB_CONFIG)
            self.cursor = self.conn.cursor()
            logger.info("数据库连接成功")
            return True
            
        except mysql.connector.Error as e:
            error_msg = self.get_error_message(e)
            logger.error(f"数据库连接失败: {error_msg}")
            return False
            
    def close(self) -> None:
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接时出错: {e}")
            
    @staticmethod
    def get_error_message(error: mysql.connector.Error) -> str:
        """获取数据库错误信息"""
        error_messages = {
            errorcode.ER_ACCESS_DENIED_ERROR: "数据库用户名或密码错误",
            errorcode.ER_BAD_DB_ERROR: "数据库不存在",
            1370: "存储过程访问被拒绝",  # ER_PROC_ACCESS_DENIED
            1305: "存储过程不存在"  # ER_SP_DOES_NOT_EXIST
        }
        return error_messages.get(error.errno, str(error))
        
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[tuple]]:
        """执行查询"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            logger.error(f"执行查询失败: {self.get_error_message(e)}")
            return None
            
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """执行事务"""
        try:
            self.conn.start_transaction()
            for query, params in queries:
                self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except mysql.connector.Error as e:
            self.conn.rollback()
            logger.error(f"执行事务失败: {self.get_error_message(e)}")
            return False

class FeedbackOverlay(QWidget):
    """反馈遮罩层"""
    feedback_shown = pyqtSignal()  # 反馈显示信号
    feedback_hidden = pyqtSignal(bool)  # 反馈隐藏信号，参数表示是否答对
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        if not parent:
            raise ValueError("FeedbackOverlay must have a valid parent window")
            
        self.parent: QWidget = parent
        self.hide()  # 初始时隐藏
        self.is_correct: bool = False  # 记录当前答题是否正确
        
        # 初始化UI组件
        self.feedback_label: Optional[QLabel] = None
        self.next_button: Optional[QPushButton] = None
        self.retry_button: Optional[QPushButton] = None
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI界面"""
        # 设置遮罩层样式
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
            }
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 32px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#retry {
                background-color: #f44336;
            }
            QPushButton#retry:hover {
                background-color: #da190b;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建反馈标签
        self.feedback_label = QLabel()
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.feedback_label)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # 创建重试按钮
        self.retry_button = QPushButton("重新作答")
        self.retry_button.setObjectName("retry")
        self.retry_button.clicked.connect(lambda: self.hide_feedback(False))
        button_layout.addWidget(self.retry_button)
        
        # 创建下一题按钮
        self.next_button = QPushButton("下一题")
        self.next_button.clicked.connect(lambda: self.hide_feedback(True))
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
        
    def show_feedback(self, is_correct: bool) -> None:
        """显示反馈"""
        self.is_correct = is_correct
        self.feedback_label.setText("✓ 正确!" if is_correct else "✗ 错误!")
        self.feedback_label.setStyleSheet(
            "color: #4CAF50;" if is_correct else "color: #F44336;"
        )
        # 只有答对时才显示下一题按钮
        self.next_button.setVisible(is_correct)
        self.retry_button.setVisible(not is_correct)
        self.show()
        self.feedback_shown.emit()
        
    def hide_feedback(self, proceed: bool) -> None:
        """隐藏反馈"""
        self.hide()
        self.feedback_hidden.emit(proceed)

class QuestionWidget(QFrame):
    """问题显示组件"""
    answer_submitted = pyqtSignal(str)  # 答案提交信号
    
    def __init__(self, question: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.question = question
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI界面"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(main_layout)
        
        # 题目类型和难度
        info_layout = QHBoxLayout()
        type_label = QLabel(f"题目类型：{self.question['type_name']}")
        difficulty_label = QLabel(f"难度：{self.question['difficulty']}")
        info_layout.addWidget(type_label)
        info_layout.addWidget(difficulty_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)
        
        # 题目内容
        content_label = QLabel(self.question['content'])
        content_label.setWordWrap(True)
        content_label.setStyleSheet("font-size: 14px; margin: 10px 0;")
        main_layout.addWidget(content_label)
        
        # 答题区域
        answer_frame = QFrame()
        answer_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        answer_layout = QVBoxLayout()
        answer_layout.setSpacing(8)
        answer_frame.setLayout(answer_layout)
        
        if self.question['type_name'] == '选择题':
            self.setup_choice_question(answer_layout)
        elif self.question['type_name'] == '判断题':
            self.setup_judgement_question(answer_layout)
        elif self.question['type_name'] == '填空题':
            self.setup_fill_blank_question(answer_layout)
        else:  # 简答题或设计题
            self.setup_text_question(answer_layout)
            
        main_layout.addWidget(answer_frame)
        
        # 提交按钮
        submit_button = QPushButton("提交答案")
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        submit_button.clicked.connect(self.submit_answer)
        main_layout.addWidget(submit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 设置整体样式
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QLabel {
                color: #212529;
                font-size: 14px;
            }
            QRadioButton, QCheckBox {
                color: #495057;
                font-size: 14px;
                padding: 5px;
                spacing: 5px;
            }
            QRadioButton:hover, QCheckBox:hover {
                background-color: #e9ecef;
                border-radius: 4px;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #80bdff;
                outline: 0;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
        """)
        
    def setup_choice_question(self, layout: QVBoxLayout) -> None:
        """设置选择题界面"""
        self.options_group = QButtonGroup(self)
        self.options_group.setExclusive(False)
        
        for i, option in enumerate(self.question['options']):
            radio = QRadioButton(f"{chr(65+i)}. {option}")
            layout.addWidget(radio)
            self.options_group.addButton(radio, i+1)
            
    def setup_judgement_question(self, layout: QVBoxLayout) -> None:
        """设置判断题界面"""
        self.judgement_group = QButtonGroup(self)
        
        true_radio = QRadioButton("正确")
        false_radio = QRadioButton("错误")
        
        layout.addWidget(true_radio)
        layout.addWidget(false_radio)
        
        self.judgement_group.addButton(true_radio, 1)
        self.judgement_group.addButton(false_radio, 0)
        
    def setup_fill_blank_question(self, layout: QVBoxLayout) -> None:
        """设置填空题界面"""
        self.fill_blank_edit = QLineEdit()
        self.fill_blank_edit.setPlaceholderText("请输入答案")
        layout.addWidget(self.fill_blank_edit)
        
    def setup_text_question(self, layout: QVBoxLayout) -> None:
        """设置简答题界面"""
        self.text_answer_edit = QTextEdit()
        self.text_answer_edit.setPlaceholderText("请输入答案")
        self.text_answer_edit.setMinimumHeight(150)
        layout.addWidget(self.text_answer_edit)
        
    def get_answer(self) -> Optional[str]:
        """获取答案"""
        if self.question['type_name'] == '选择题':
            selected = []
            for button in self.options_group.buttons():
                if button.isChecked():
                    selected.append(str(self.options_group.id(button)))
            return ','.join(selected) if selected else None
            
        elif self.question['type_name'] == '判断题':
            selected = self.judgement_group.checkedButton()
            if selected:
                return "1" if self.judgement_group.id(selected) == 1 else "0"
            return None
            
        elif self.question['type_name'] == '填空题':
            return self.fill_blank_edit.text().strip() if self.fill_blank_edit else None
            
        else:  # 简答题
            return self.text_answer_edit.toPlainText().strip() if self.text_answer_edit else None
            
    def submit_answer(self) -> None:
        """提交答案"""
        try:
            answer = self.get_answer()
            if answer:
                self.answer_submitted.emit(answer)
            else:
                QMessageBox.warning(self, "提示", "请先作答！")
        except KeyboardInterrupt:
            print("\n继续答题...")
        except Exception as e:
            print(f"提交答案时发生错误: {str(e)}")
            QMessageBox.warning(self, "错误", f"提交答案时发生错误: {str(e)}")

class StatisticsDialog(QDialog):
    """学习统计对话框"""
    stats_updated = pyqtSignal()  # 统计数据更新信号
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        if not parent:
            raise ValueError("StatisticsDialog must have a valid parent window")
            
        self.parent: QWidget = parent
        self.setWindowTitle("学习统计")
        self.setMinimumSize(800, 600)
        
        # 获取父窗口的数据库连接和游标
        if not hasattr(self.parent, 'conn') or not self.parent.conn:
            raise ValueError("Parent window must have a valid database connection")
            
        self.conn: mysql.connector.MySQLConnection = self.parent.conn
        self.cursor: mysql.connector.cursor.MySQLCursor = self.parent.cursor
        
        # 初始化UI组件
        self.stats_text: Optional[QTextEdit] = None
        self.mastery_text: Optional[QTextEdit] = None
        self.mistakes_text: Optional[QTextEdit] = None
        
        self.setup_ui()
        self.load_statistics()
        
        # 连接信号
        self.stats_updated.connect(self.parent.update_stats)
        
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background: white;
            }
            QTabBar::tab {
                background: #F5F5F5;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
            }
        """)
        
        # 总体统计选项卡
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: white;
                font-family: 'Microsoft YaHei UI';
                font-size: 14px;
            }
        """)
        overview_layout.addWidget(self.stats_text)
        
        # 知识点掌握度选项卡
        mastery_tab = QWidget()
        mastery_layout = QVBoxLayout(mastery_tab)
        
        self.mastery_text = QTextEdit()
        self.mastery_text.setReadOnly(True)
        self.mastery_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: white;
                font-family: 'Microsoft YaHei UI';
                font-size: 14px;
            }
        """)
        mastery_layout.addWidget(self.mastery_text)
        
        # 错题分析选项卡
        mistakes_tab = QWidget()
        mistakes_layout = QVBoxLayout(mistakes_tab)
        
        self.mistakes_text = QTextEdit()
        self.mistakes_text.setReadOnly(True)
        self.mistakes_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: white;
                font-family: 'Microsoft YaHei UI';
                font-size: 14px;
            }
        """)
        mistakes_layout.addWidget(self.mistakes_text)
        
        # 添加选项卡
        tab_widget.addTab(overview_tab, "总体统计")
        tab_widget.addTab(mastery_tab, "知识点掌握度")
        tab_widget.addTab(mistakes_tab, "错题分析")
        
        layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("导出报告")
        export_button.setFont(QFont("Microsoft YaHei UI", 11))
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        export_button.clicked.connect(self.export_report)
        
        close_button = QPushButton("关闭")
        close_button.setFont(QFont("Microsoft YaHei UI", 11))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(export_button)
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def load_statistics(self):
        """加载统计数据"""
        try:
            # 获取总题数和已答题数
            self.cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM questions) as total,
                    COUNT(DISTINCT question_id) as answered
                FROM answer_history
            """)
            total_stats = self.cursor.fetchone()
            
            # 获取正确率统计
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts,
                    ROUND(AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy
                FROM answer_history
            """)
            accuracy_stats = self.cursor.fetchone()
            
            # 更新统计文本
            stats_text = "总体统计：\n\n"
            if total_stats:
                stats_text += f"总题数：{total_stats[0]}\n"
                stats_text += f"已答题数：{total_stats[1] or 0}\n"
            else:
                stats_text += "总题数：0\n已答题数：0\n"
                
            if accuracy_stats and accuracy_stats[0] > 0:
                stats_text += f"总答题次数：{accuracy_stats[0]}\n"
                stats_text += f"正确次数：{accuracy_stats[1]}\n"
                stats_text += f"正确率：{accuracy_stats[2]}%"
            else:
                stats_text += "总答题次数：0\n正确次数：0\n正确率：0%"
                
            self.stats_text.setText(stats_text)
            
            # 获取掌握度统计
            self.cursor.execute("""
                SELECT 
                    dl.level_name,
                    COUNT(*) as count
                FROM questions q
                JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
                GROUP BY dl.level_id, dl.level_name
                ORDER BY dl.level_id
            """)
            mastery_stats = self.cursor.fetchall()
            
            if mastery_stats:
                mastery_text = "难度分布：\n\n"
                for level_name, count in mastery_stats:
                    mastery_text += f"{level_name}：{count}题\n"
                self.mastery_text.setText(mastery_text)
            
            # 获取错题统计
            self.cursor.execute("""
                SELECT 
                    q.content,
                    COUNT(*) as error_count,
                    MAX(a.answer_content) as correct_answer
                FROM answer_history ah
                JOIN questions q ON ah.question_id = q.question_id
                LEFT JOIN answers a ON q.question_id = a.question_id
                WHERE ah.is_correct = 0
                GROUP BY q.question_id, q.content
                ORDER BY error_count DESC
                LIMIT 10
            """)
            mistake_stats = self.cursor.fetchall()
            
            if mistake_stats:
                mistakes_text = "最常错误的题目（Top 10）：\n\n"
                for content, error_count, correct_answer in mistake_stats:
                    mistakes_text += f"题目：{content}\n"
                    mistakes_text += f"错误次数：{error_count}\n"
                    mistakes_text += f"正确答案：{correct_answer}\n\n"
                self.mistakes_text.setText(mistakes_text)
                
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "数据库错误", f"加载统计数据时出错: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载统计数据时出现未知错误: {str(e)}")
            
    def export_report(self) -> None:
        """导出统计报告"""
        try:
            # 获取保存文件路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存统计报告",
                "",
                "HTML文件 (*.html);;文本文件 (*.txt)"
            )
            
            if not file_path:
                return
                
            # 准备报告内容
            report_content = ""
            if self.stats_text:
                report_content += "===== 学习统计 =====\n\n"
                report_content += self.stats_text.toPlainText()
                report_content += "\n\n"
                
            if self.mastery_text:
                report_content += "===== 掌握度统计 =====\n\n"
                report_content += self.mastery_text.toPlainText()
                report_content += "\n\n"
                
            if self.mistakes_text:
                report_content += "===== 错题统计 =====\n\n"
                report_content += self.mistakes_text.toPlainText()
                
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            QMessageBox.information(self, "成功", "统计报告已成功导出！")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出报告时出错: {str(e)}")
            
    def print_report(self) -> None:
        """打印统计报告"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.Accepted:
                document = QTextDocument()
                
                # 准备HTML格式的报告内容
                html_content = "<html><body>"
                
                if self.stats_text:
                    html_content += "<h2>学习统计</h2>"
                    html_content += f"<pre>{self.stats_text.toPlainText()}</pre>"
                    html_content += "<br><br>"
                    
                if self.mastery_text:
                    html_content += "<h2>掌握度统计</h2>"
                    html_content += f"<pre>{self.mastery_text.toPlainText()}</pre>"
                    html_content += "<br><br>"
                    
                if self.mistakes_text:
                    html_content += "<h2>错题统计</h2>"
                    html_content += f"<pre>{self.mistakes_text.toPlainText()}</pre>"
                    
                html_content += "</body></html>"
                
                document.setHtml(html_content)
                document.print_(printer)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打印报告时出错: {str(e)}")
            
    def refresh_statistics(self) -> None:
        """刷新统计数据"""
        self.load_statistics()

class DeepLearningManager:
    """深度学习管理类 - 使用 DeepSeek API"""
    def __init__(self):
        self.api_key = "sk-efef2a4b47ea473caf51824685914da2"
        self.api_base = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        
    def get_text_embedding(self, text: str) -> np.ndarray:
        """获取文本的嵌入向量"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "input": text
            }
            
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                embedding = response.json()["data"][0]["embedding"]
                return np.array(embedding)
            else:
                logger.error(f"API调用失败: {response.text}")
                raise Exception(f"API调用失败: {response.text}")
                
        except Exception as e:
            logger.error(f"获取文本嵌入失败: {str(e)}")
            raise
            
    def evaluate_answer(self, student_answer: str, correct_answer: str) -> Tuple[float, str]:
        """评估答案并提供反馈"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一个专业的MySQL教育评估助手。你可以联网搜索最新的MySQL文档和相关资料来辅助评估。评分标准：1.0分（完全正确），0.8分（大致正确），0.6分（部分正确），0.4分（基本错误），0.0分（完全错误）。请参考最新的MySQL文档验证答案的准确性，考虑版本差异，并提供改进建议。"""
                    },
                    {
                        "role": "user",
                        "content": f"参考答案：{correct_answer}\n学生答案：{student_answer}\n请评分并解释。"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 800,
                "tools": [{"type": "web_search"}]
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                feedback = result["choices"][0]["message"]["content"]
                
                try:
                    score_match = re.search(r'(?:分数：)?([01]\.?\d*)', feedback)
                    score = float(score_match.group(1)) if score_match else self.calculate_similarity(student_answer, correct_answer)
                except:
                    score = self.calculate_similarity(student_answer, correct_answer)
                
                return score, feedback
            else:
                logger.error(f"API调用失败: {response.text}")
                raise Exception(f"API调用失败: {response.text}")
                
        except Exception as e:
            logger.error(f"评估答案失败: {str(e)}")
            raise
            
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        try:
            embedding1 = self.get_text_embedding(text1)
            embedding2 = self.get_text_embedding(text2)
            similarity = cosine_similarity([embedding1], [embedding2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"计算相似度失败: {str(e)}")
            raise

class RecommendationSystem:
    """智能推荐系统"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.dl_manager = DeepLearningManager()
        
    def get_user_profile(self, user_id: str) -> np.ndarray:
        """获取用户学习画像"""
        # 获取用户的答题历史
        query = """
            SELECT q.content, ah.is_correct, q.difficulty_level
            FROM answer_history ah
            JOIN questions q ON ah.question_id = q.question_id
            WHERE ah.user_id = %s
            ORDER BY ah.answer_time DESC
            LIMIT 50
        """
        results = self.db_manager.execute_query(query, (user_id,))
        
        if not results:
            return np.zeros(768)  # BERT embedding 维度
            
        # 计算用户答题的平均向量表示
        embeddings = []
        for content, is_correct, difficulty in results:
            embedding = self.dl_manager.get_text_embedding(content)
            weight = float(is_correct) * (difficulty / 5.0)  # 根据正确性和难度加权
            embeddings.append(embedding * weight)
            
        return np.mean(embeddings, axis=0)
        
    def recommend_questions(self, user_id: str, n_questions: int = 10) -> List[Dict]:
        """推荐适合用户水平的题目"""
        user_profile = self.get_user_profile(user_id)
        
        # 获取所有可用题目
        query = """
            SELECT q.question_id, q.content, q.difficulty_level, q.type_id
            FROM questions q
            WHERE q.is_active = TRUE
            AND q.question_id NOT IN (
                SELECT question_id 
                FROM answer_history 
                WHERE user_id = %s
            )
        """
        questions = self.db_manager.execute_query(query, (user_id,))
        
        if not questions:
            return []
            
        # 计算每个题目与用户画像的相似度
        recommendations = []
        for q_id, content, difficulty, type_id in questions:
            q_embedding = self.dl_manager.get_text_embedding(content)
            similarity = cosine_similarity([user_profile], [q_embedding])[0][0]
            recommendations.append({
                'question_id': q_id,
                'content': content,
                'difficulty': difficulty,
                'type_id': type_id,
                'similarity': similarity
            })
            
        # 根据相似度排序并返回推荐结果
        recommendations.sort(key=lambda x: x['similarity'], reverse=True)
        return recommendations[:n_questions]

class KnowledgeGraph:
    """知识图谱管理类"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.dl_manager = DeepLearningManager()
        
    def build_knowledge_graph(self) -> Dict:
        """构建知识图谱"""
        # 获取所有题目和标签
        query = """
            SELECT q.question_id, q.content, 
                   GROUP_CONCAT(t.tag_name) as tags
            FROM questions q
            LEFT JOIN question_tag_relations qtr ON q.question_id = qtr.question_id
            LEFT JOIN question_tags t ON qtr.tag_id = t.tag_id
            GROUP BY q.question_id, q.content
        """
        results = self.db_manager.execute_query(query)
        
        # 构建知识点关联网络
        graph = {}
        for q_id, content, tags in results:
            embedding = self.dl_manager.get_text_embedding(content)
            tag_list = tags.split(',') if tags else []
            
            graph[q_id] = {
                'content': content,
                'embedding': embedding,
                'tags': tag_list,
                'related_questions': []
            }
            
        # 计算题目间的关联关系
        question_ids = list(graph.keys())
        for i, q1_id in enumerate(question_ids):
            for q2_id in question_ids[i+1:]:
                similarity = cosine_similarity(
                    [graph[q1_id]['embedding']], 
                    [graph[q2_id]['embedding']]
                )[0][0]
                
                if similarity > 0.7:  # 设置相似度阈值
                    graph[q1_id]['related_questions'].append(q2_id)
                    graph[q2_id]['related_questions'].append(q1_id)
                    
        return graph

class PracticeSystem(QMainWindow):
    """MySQL练习系统主窗口"""
    
    def __init__(self, conn: mysql.connector.MySQLConnection) -> None:
        """初始化练习系统"""
        super().__init__()
        
        # 数据库连接
        self.conn = conn
        self.cursor = conn.cursor(dictionary=True)
        
        # 当前题目和题目列表
        self.current_question_index = 0
        self.questions = []
        self.current_question_widget = None
        
        # 创建按钮组
        self.type_button_group = QButtonGroup(self)
        self.type_button_group.setExclusive(True)
        self.type_button_group.buttonClicked.connect(self.filter_questions)
        
        self.difficulty_button_group = QButtonGroup(self)
        self.difficulty_button_group.setExclusive(True)
        self.difficulty_button_group.buttonClicked.connect(self.filter_questions)
        
        # 初始化UI组件
        self.central_widget: Optional[QWidget] = None
        self.main_layout: Optional[QVBoxLayout] = None
        self.question_area: Optional[QFrame] = None
        self.stats_area: Optional[QFrame] = None
        self.navigation_area: Optional[QFrame] = None
        
        # 导航按钮
        self.prev_button: Optional[QPushButton] = None
        self.next_button: Optional[QPushButton] = None
        self.stats_button: Optional[QPushButton] = None
        
        # 统计标签
        self.total_questions_label: Optional[QLabel] = None
        self.answered_questions_label: Optional[QLabel] = None
        self.correct_rate_label: Optional[QLabel] = None
        
        # 初始化遮罩层
        self.feedback_overlay = FeedbackOverlay(self)
        self.feedback_overlay.feedback_hidden.connect(self.handle_feedback_hidden)
        
        # 初始化自动跳转定时器
        self.auto_next_timer = QTimer(self)
        self.auto_next_timer.setSingleShot(True)  # 设置为单次触发
        self.auto_next_timer.timeout.connect(lambda: self.feedback_overlay.hide_feedback(True))
        
        # 初始化深度学习组件
        self.dl_manager = DeepLearningManager()
        self.recommendation_system = RecommendationSystem(self)
        self.knowledge_graph = KnowledgeGraph(self)
        
        # 初始化界面
        self.init_ui()
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 创建顶部工具栏
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout()
        toolbar.setLayout(toolbar_layout)
        
        # 左侧：筛选按钮
        filter_frame = QFrame()
        filter_layout = QHBoxLayout()
        filter_frame.setLayout(filter_layout)
        
        # 题型筛选
        type_frame = QGroupBox("题型")
        type_frame.setStyleSheet(Constants.STYLES['group_box'])
        type_layout = QHBoxLayout()
        
        type_buttons = [
            ("全部", 0),
            ("选择题", Constants.QUESTION_TYPES['multiple_choice']),
            ("判断题", Constants.QUESTION_TYPES['true_false']),
            ("填空题", Constants.QUESTION_TYPES['fill_blank']),
            ("简答题", Constants.QUESTION_TYPES['short_answer'])
        ]
        
        for text, type_id in type_buttons:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(Constants.STYLES['button'])
            self.type_button_group.addButton(btn, type_id)
            type_layout.addWidget(btn)
            
        type_frame.setLayout(type_layout)
        
        # 难度筛选
        difficulty_frame = QGroupBox("难度")
        difficulty_frame.setStyleSheet(Constants.STYLES['group_box'])
        difficulty_layout = QHBoxLayout()
        
        difficulty_buttons = [
            ("全部", 0),
            ("初级", Constants.DIFFICULTY_LEVELS['beginner']),
            ("中级", Constants.DIFFICULTY_LEVELS['intermediate']),
            ("高级", Constants.DIFFICULTY_LEVELS['advanced'])
        ]
        
        for text, level_id in difficulty_buttons:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(Constants.STYLES['button'])
            self.difficulty_button_group.addButton(btn, level_id)
            difficulty_layout.addWidget(btn)
            
        difficulty_frame.setLayout(difficulty_layout)
        
        # 添加筛选框到布局
        filter_layout.addWidget(type_frame)
        filter_layout.addWidget(difficulty_frame)
        toolbar_layout.addWidget(filter_frame)
        
        # 右侧：导航按钮
        nav_frame = QFrame()
        nav_layout = QHBoxLayout()
        nav_frame.setLayout(nav_layout)
        
        # 添加导航按钮
        self.prev_btn = QPushButton("上一题")
        self.prev_btn.clicked.connect(self.prev_question)
        self.prev_btn.setStyleSheet(Constants.STYLES['button'])
        
        self.next_btn = QPushButton("下一题")
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setStyleSheet(Constants.STYLES['button'])
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        toolbar_layout.addWidget(nav_frame)
        
        # 添加工具栏到主布局
        self.main_layout.addWidget(toolbar)
        
        # 创建题目区域
        self.question_area = QScrollArea()
        self.question_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.question_area)
        
        # 创建底部状态栏
        footer = QFrame()
        footer_layout = QHBoxLayout()
        footer.setLayout(footer_layout)
        
        # 添加统计标签
        self.total_questions_label = QLabel("总题数: 0")
        self.answered_questions_label = QLabel("已答题数: 0")
        self.correct_rate_label = QLabel("正确率: 0%")
        
        footer_layout.addWidget(self.total_questions_label)
        footer_layout.addWidget(self.answered_questions_label)
        footer_layout.addWidget(self.correct_rate_label)
        
        # 添加底部状态栏到主布局
        self.main_layout.addWidget(footer)
        
        # 设置窗口属性
        self.setWindowTitle(Constants.WINDOW_TITLE)
        self.setGeometry(*Constants.WINDOW_GEOMETRY)
        
        # 选中默认按钮
        self.type_button_group.button(0).setChecked(True)
        self.difficulty_button_group.button(0).setChecked(True)
        
        # 加载题目
        self.load_questions()
        
    def load_questions(self) -> None:
        """从数据库加载题目"""
        try:
            if not self.cursor:
                raise ValueError("Database cursor is not initialized")
                
            print("开始加载题目...")  # 添加调试信息
            # 加载题目
            query = """
                SELECT 
                    q.question_id,
                    q.content,
                    q.type_id,
                    TRIM('MySQL' FROM qt.type_name) as type_name,
                    dl.level_name as difficulty_level,
                    GROUP_CONCAT(mco.option_content ORDER BY mco.option_id SEPARATOR '||') as options,
                    GROUP_CONCAT(CASE WHEN mco.is_correct = 1 THEN mco.option_id END) as correct_answers,
                    a.answer_content,
                    a.explanation
                FROM 
                    questions q
                    JOIN question_types qt ON q.type_id = qt.type_id
                    JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
                    LEFT JOIN multiple_choice_options mco ON q.question_id = mco.question_id
                    LEFT JOIN answers a ON q.question_id = a.question_id
                WHERE 
                    q.is_active = TRUE
                    AND qt.is_active = TRUE
                    AND dl.is_active = TRUE
                GROUP BY 
                    q.question_id, q.content, q.type_id, qt.type_name, dl.level_name, a.answer_content, a.explanation
                ORDER BY RAND()
                LIMIT 10
            """
            
            print("执行查询...")  # 添加调试信息
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            print(f"查询到 {len(rows)} 条记录")  # 添加调试信息
            
            if not self.process_query_results(rows):
                QMessageBox.warning(self, "警告", "没有找到任何题目")
                return
                
            print("开始加载第一题...")  # 添加调试信息
            self.load_question()
            print("题目加载完成")  # 添加调试信息
            
        except mysql.connector.Error as e:
            error_msg = self.get_mysql_error_message(e)
            print(f"从数据库加载题目时发生错误: {error_msg}")
            QMessageBox.critical(self, "错误", f"从数据库加载题目失败: {error_msg}")
        except Exception as e:
            print(f"加载题目时发生未知错误: {e}")
            QMessageBox.critical(self, "错误", "加载题目时发生未知错误")
            
    def process_query_results(self, rows: List[Dict[str, Any]]) -> bool:
        """处理查询结果"""
        if not rows:
            return False
            
        self.questions = []
        for row in rows:
            question = {
                'id': row['question_id'],
                'content': row['content'],
                'type_id': row['type_id'],
                'type_name': row['type_name'],
                'difficulty_level': row['difficulty_level'],
                'explanation': row['explanation']
            }
            
            # 处理选项
            if row['options']:
                options = row['options'].split('||')
                question['options'] = options
                
                if row['correct_answers']:
                    correct_answers = [int(x) for x in row['correct_answers'].split(',')]
                    question['correct_answers'] = correct_answers
                    
            # 处理答案
            if row['answer_content']:
                question['answer'] = row['answer_content']
                
            self.questions.append(question)
            
        return True
        
    def load_question(self) -> None:
        """加载当前题目"""
        if not self.questions:
            return
            
        logger.info(f"正在加载第 {self.current_question_index + 1} 题...")
        
        # 清除旧的题目视图
        if self.question_area.layout():
            # 递归删除所有子部件
            def clear_layout(layout):
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                    elif item.layout():
                        clear_layout(item.layout())
            
            clear_layout(self.question_area.layout())
            
        # 如果没有布局，创建新的布局
        if not self.question_area.layout():
            question_layout = QVBoxLayout(self.question_area)
            question_layout.setContentsMargins(20, 20, 20, 20)
            
        # 创建新的题目视图
        self.current_question_widget = QuestionWidget(self.questions[self.current_question_index], self)
        self.current_question_widget.answer_submitted.connect(self.check_answer)
        
        # 添加到现有布局
        self.question_area.layout().addWidget(self.current_question_widget)
        
        # 更新界面
        self.update_stats()
        self.update_navigation_buttons()
        
        # 更新进度显示
        if hasattr(self, 'progress_label'):
            self.progress_label.setText(f"第 {self.current_question_index + 1} 题 / 共 {len(self.questions)} 题")
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setMaximum(len(self.questions))
            self.progress_bar.setValue(self.current_question_index + 1)
        
        logger.info(f"题目加载完成：{self.questions[self.current_question_index]['content']}")
        
    def update_stats(self) -> None:
        """更新统计信息"""
        try:
            # 获取总题数
            self.cursor.execute("SELECT COUNT(*) FROM questions")
            total_questions = self.cursor.fetchone()[0]
            self.total_questions_label.setText(f"总题数: {total_questions}")
            
            try:
                # 尝试从 answer_history 获取统计数据
                self.cursor.execute("""
                    SELECT COUNT(DISTINCT question_id) as answered,
                           COUNT(*) as total_attempts,
                           SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts,
                           ROUND(AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy
                    FROM answer_history
                """)
                stats = self.cursor.fetchone()
                
                if stats:
                    self.answered_questions_label.setText(f"已答题数: {stats[0] or 0}")
                    self.correct_rate_label.setText(f"正确率: {stats[3] or 0}%")
                else:
                    self.answered_questions_label.setText("已答题数: 0")
                    self.correct_rate_label.setText("正确率: 0%")
                    
            except mysql.connector.Error as e:
                if e.errno == 1146:  # 表不存在的错误码
                    # 创建答题历史表
                    self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS answer_history (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            question_id INT NOT NULL,
                            answer_content TEXT NOT NULL,
                            is_correct BOOLEAN NOT NULL,
                            answer_time DATETIME NOT NULL,
                            FOREIGN KEY (question_id) REFERENCES questions(question_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """)
                    self.conn.commit()
                    
                    # 设置初始统计数据
                    self.answered_questions_label.setText("已答题数: 0")
                    self.correct_rate_label.setText("正确率: 0%")
                else:
                    raise e
                    
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "错误", f"更新统计信息失败: {self.get_mysql_error_message(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新统计信息时发生未知错误: {str(e)}")
            
    def update_navigation_buttons(self) -> None:
        """更新导航按钮状态"""
        if not self.questions:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
            
        self.prev_btn.setEnabled(self.current_question_index > 0)
        self.next_btn.setEnabled(self.current_question_index < len(self.questions) - 1)
        
    def prev_question(self) -> None:
        """上一题"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.load_question()
            
    def next_question(self) -> None:
        """下一题"""
        # 只有在未答题或已答对的情况下才能进入下一题
        if not self.current_question_widget or getattr(self.feedback_overlay, 'is_correct', True):
            if self.current_question_index < len(self.questions) - 1:
                self.current_question_index += 1
                self.load_question()
            
    def check_answer(self, answer: Optional[str] = None) -> None:
        """检查答案（使用深度学习评分）"""
        if not self.current_question_widget:
            return
            
        if answer is None:
            answer = self.current_question_widget.get_answer()
            
        if not answer:
            QMessageBox.warning(self, "提示", "请先作答！")
            return
            
        current_question = self.questions[self.current_question_index]
        
        # 根据题目类型选择评分方式
        if current_question['type_name'] in ['简答题', '设计题']:
            # 使用深度学习评分
            score, feedback = self.dl_manager.evaluate_answer(
                answer, 
                current_question['answer']
            )
            is_correct = score >= 0.7  # 设置及格分数线
        else:
            # 其他题型使用原有的评分方式
            is_correct = self.validate_answer(current_question, answer)
            
        # 更新答题记录
        self.update_answer_history(current_question['id'], answer, is_correct)
        
        # 显示反馈
        self.show_answer_feedback(is_correct, current_question)
        
    def validate_answer(self, question: Dict[str, Any], answer: str) -> bool:
        """验证答案"""
        if question['type_name'] == '选择题':
            try:
                user_answers = [int(x) for x in answer.split(',')]
                return sorted(user_answers) == sorted(question['correct_answers'])
            except ValueError:
                return False
        elif question['type_name'] == '判断题':
            return answer.lower() == question['answer'].lower()
        elif question['type_name'] == '填空题':
            return answer.strip().lower() == question['answer'].strip().lower()
        else:  # 简答题和设计题
            # 预处理答案文本
            user_answer = answer.lower().strip()
            correct_answer = question['answer'].lower().strip()
            
            # 提取关键词（去除常见的标点符号和停用词）
            def extract_keywords(text):
                # 移除标点符号
                text = ''.join(c for c in text if c.isalnum() or c.isspace())
                # 分词并去除停用词
                words = [w for w in text.split() if len(w) > 1]
                return set(words)
            
            user_keywords = extract_keywords(user_answer)
            correct_keywords = extract_keywords(correct_answer)
            
            if len(correct_keywords) == 0:
                return False
                
            # 计算关键词匹配度
            matched_keywords = user_keywords.intersection(correct_keywords)
            match_ratio = len(matched_keywords) / len(correct_keywords)
            
            # 如果匹配度超过70%则认为答案正确
            return match_ratio >= 0.7
            
    def update_answer_history(self, question_id: int, answer: str, is_correct: bool) -> None:
        """更新答题历史"""
        try:
            self.cursor.execute("""
                INSERT INTO answer_history 
                (question_id, answer_content, is_correct, answer_time)
                VALUES (%s, %s, %s, NOW())
            """, (question_id, answer, is_correct))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"更新答题历史失败: {e}")
            QMessageBox.critical(self, "错误", f"更新答题历史失败: {str(e)}")
            
    def show_answer_feedback(self, is_correct: bool, question: Dict[str, Any]) -> None:
        """显示答案反馈"""
        # 显示遮罩层反馈
        self.feedback_overlay.show_feedback(is_correct)
        
        # 更新解析区域
        explanation_text = f"正确答案：{question['answer']}\n\n"
        explanation_text += f"解析：\n{question['explanation']}"
        self.explanation_text.setText(explanation_text)
        
        # 根据答题结果设置解析区域样式
        if not is_correct:
            self.explanation_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ff4d4f;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 14px;
                    background-color: #fff2f0;
                }
            """)
        else:
            self.explanation_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #52c41a;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 14px;
                    background-color: #f6ffed;
                }
            """)
            # 答对题目3秒后自动跳转
            self.auto_next_timer.start(3000)  # 3000毫秒 = 3秒
        
    def resizeEvent(self, event: QResizeEvent) -> None:
        """调整大小事件处理"""
        super().resizeEvent(event)
        # 在这里可以添加调整大小时的特殊处理逻辑
        
    def closeEvent(self, event: QCloseEvent) -> None:
        """关闭事件处理"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"关闭数据库连接时出错: {e}")
        event.accept()

    def show_statistics(self) -> None:
        """显示统计对话框"""
        dialog = StatisticsDialog(self)
        dialog.exec()

    def show_home(self) -> None:
        """显示首页"""
        # TODO: 实现首页功能
        pass
        
    def show_mistakes(self) -> None:
        """显示错题本"""
        # TODO: 实现错题本功能
        pass
        
    def show_notes(self) -> None:
        """显示笔记"""
        # TODO: 实现笔记功能
        pass
        
    def show_settings(self) -> None:
        """显示设置"""
        # TODO: 实现设置功能
        pass
            
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """处理键盘事件"""
        if not self.current_question_widget:
            return
            
        # 选项快捷键 (1-4)
        if self.current_question_widget.question['type_name'] == '选择题':
            if event.key() in [Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4]:
                option_index = event.key() - Qt.Key.Key_1
                if option_index < len(self.current_question_widget.options_group.buttons()):
                    button = self.current_question_widget.options_group.buttons()[option_index]
                    button.setChecked(not button.isChecked())  # 切换选中状态
                    
        # 判断题快捷键 (T/F)
        elif self.current_question_widget.question['type_name'] == '判断题':
            if event.key() == Qt.Key.Key_T:
                self.current_question_widget.judgement_group.buttons()[0].setChecked(True)
            elif event.key() == Qt.Key.Key_F:
                self.current_question_widget.judgement_group.buttons()[1].setChecked(True)
                
        # 导航快捷键
        if event.key() == Qt.Key.Key_Left:
            self.prev_question()
        elif event.key() == Qt.Key.Key_Right:
            self.next_question()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.current_question_widget.submit_answer()
                
        super().keyPressEvent(event)

    def handle_feedback_hidden(self, proceed: bool) -> None:
        """处理反馈隐藏事件"""
        if proceed and self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.load_question()
            
    def filter_questions(self) -> None:
        """根据选中的题型和难度筛选题目"""
        try:
            # 获取选中的题型和难度
            type_id = self.type_button_group.checkedId()
            difficulty_id = self.difficulty_button_group.checkedId()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if type_id > 0:
                conditions.append("q.type_id = %s")
                params.append(type_id)
                
            if difficulty_id > 0:
                conditions.append("q.difficulty_level = %s")
                params.append(difficulty_id)
                
            # 构建完整的查询语句
            query = """
                SELECT 
                    q.question_id,
                    q.content,
                    q.type_id,
                    TRIM('MySQL' FROM qt.type_name) as type_name,
                    dl.level_name as difficulty_level,
                    GROUP_CONCAT(mco.option_content ORDER BY mco.option_id SEPARATOR '||') as options,
                    GROUP_CONCAT(CASE WHEN mco.is_correct = 1 THEN mco.option_id END) as correct_answers,
                    a.answer_content,
                    a.explanation
                FROM 
                    questions q
                    JOIN question_types qt ON q.type_id = qt.type_id
                    JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
                    LEFT JOIN multiple_choice_options mco ON q.question_id = mco.question_id
                    LEFT JOIN answers a ON q.question_id = a.question_id
                WHERE 
                    q.is_active = TRUE
                    AND qt.is_active = TRUE
                    AND dl.is_active = TRUE
            """
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
                
            query += """
                GROUP BY 
                    q.question_id, q.content, q.type_id, qt.type_name, dl.level_name, a.answer_content, a.explanation
                ORDER BY RAND()
                LIMIT 10
            """
            
            # 执行查询
            self.cursor.execute(query, tuple(params))
            rows = self.cursor.fetchall()
            
            # 处理查询结果
            if not self.process_query_results(rows):
                QMessageBox.warning(self, "警告", "没有找到符合条件的题目")
                return
                
            # 重新加载第一题
            self.load_question()
            
        except mysql.connector.Error as e:
            error_msg = self.get_mysql_error_message(e)
            print(f"筛选题目时发生错误: {error_msg}")
            QMessageBox.critical(self, "错误", f"筛选题目失败: {error_msg}")
        except Exception as e:
            print(f"筛选题目时发生未知错误: {e}")
            QMessageBox.critical(self, "错误", "筛选题目时发生未知错误")

    def get_recommended_questions(self) -> None:
        """获取推荐题目"""
        # 假设当前用户ID为'test_user'
        recommended_questions = self.recommendation_system.recommend_questions('test_user')
        if recommended_questions:
            self.questions = recommended_questions
            self.current_question_index = 0
            self.load_question()
        else:
            QMessageBox.information(self, "提示", "暂无推荐题目")
            
    def show_knowledge_map(self) -> None:
        """显示知识图谱"""
        # TODO: 实现知识图谱可视化
        pass

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        conn = mysql.connector.connect(**Constants.DB_CONFIG)
        window = PracticeSystem(conn)
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n程序继续运行中...")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1) 