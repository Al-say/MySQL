from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QTextEdit, QTabWidget, QWidget, QMessageBox,
                            QFileDialog)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
import mysql.connector
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
            
    def refresh_statistics(self) -> None:
        """刷新统计数据"""
        self.load_statistics() 