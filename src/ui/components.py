from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QFrame, QRadioButton, QButtonGroup, QTextEdit,
                            QLineEdit, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

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
        self.countdown_label: Optional[QLabel] = None
        self.next_button: Optional[QPushButton] = None
        self.retry_button: Optional[QPushButton] = None
        
        # 初始化倒计时定时器
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.remaining_time = 0
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI界面"""
        # 设置遮罩层样式
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
            }
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                padding: 20px;
                border-radius: 10px;
                background-color: rgba(0, 0, 0, 0.5);
            }
            QLabel#countdown {
                font-size: 24px;
                color: rgba(255, 255, 255, 0.85);
                background-color: transparent;
                padding: 10px;
            }
            QPushButton {
                color: white;
                border: none;
                padding: 15px 32px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#next {
                background-color: rgba(76, 175, 80, 0.8);
            }
            QPushButton#next:hover {
                background-color: rgba(76, 175, 80, 0.9);
            }
            QPushButton#next:pressed {
                background-color: rgba(76, 175, 80, 0.7);
            }
            QPushButton#retry {
                background-color: rgba(244, 67, 54, 0.8);
            }
            QPushButton#retry:hover {
                background-color: rgba(244, 67, 54, 0.9);
            }
            QPushButton#retry:pressed {
                background-color: rgba(244, 67, 54, 0.7);
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # 创建反馈标签
        self.feedback_label = QLabel()
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.feedback_label)
        
        # 创建倒计时标签
        self.countdown_label = QLabel()
        self.countdown_label.setObjectName("countdown")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.hide()  # 初始时隐藏
        layout.addWidget(self.countdown_label)
        
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
        self.next_button.setObjectName("next")
        self.next_button.clicked.connect(lambda: self.hide_feedback(True))
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
        
    def show_feedback(self, is_correct: bool) -> None:
        """显示反馈"""
        self.is_correct = is_correct
        
        # 停止倒计时
        self.countdown_timer.stop()
        self.countdown_label.hide()
        
        # 设置反馈文本和样式
        if is_correct:
            self.feedback_label.setText("✓ 回答正确！")
            self.feedback_label.setStyleSheet("""
                QLabel {
                    color: #52c41a;
                    background-color: rgba(82, 196, 26, 0.1);
                    border: 2px solid #52c41a;
                }
            """)
        else:
            self.feedback_label.setText("✗ 回答错误！")
            self.feedback_label.setStyleSheet("""
                QLabel {
                    color: #f5222d;
                    background-color: rgba(245, 34, 45, 0.1);
                    border: 2px solid #f5222d;
                }
            """)
            
        # 只有答对时才显示下一题按钮
        self.next_button.setVisible(is_correct)
        self.retry_button.setVisible(not is_correct)
        
        # 显示遮罩层
        self.show()
        self.raise_()
        self.feedback_shown.emit()
        
    def show_countdown(self, wait_time: int) -> None:
        """显示倒计时"""
        self.remaining_time = wait_time
        self._update_countdown()
        self.countdown_label.show()
        # 每100毫秒更新一次倒计时显示
        self.countdown_timer.start(100)
        
    def _update_countdown(self) -> None:
        """更新倒计时显示"""
        self.remaining_time = max(0, self.remaining_time - 100)
        seconds = self.remaining_time / 1000
        self.countdown_label.setText(f"{seconds:.1f} 秒后自动进入下一题...")
        
        if self.remaining_time <= 0:
            self.countdown_timer.stop()
            self.countdown_label.hide()
        
    def hide_feedback(self, proceed: bool) -> None:
        """隐藏反馈"""
        self.countdown_timer.stop()
        self.hide()
        self.feedback_hidden.emit(proceed)

class ProgressIndicator(QProgressBar):
    """答题进度指示器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e8e8e8;
                border-radius: 4px;
                background-color: #f5f5f5;
                text-align: center;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 3px;
            }
        """)
        self.setTextVisible(False)

class QuestionWidget(QWidget):
    """题目部件"""
    
    answer_submitted = pyqtSignal(str)  # 定义信号
    
    def __init__(self, question_data: Dict[str, Any], total_questions: int, current_index: int, parent=None):
        super().__init__(parent)
        self.question_data = question_data
        self.has_submitted = False
        self.total_questions = total_questions
        self.current_index = current_index
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建进度指示器
        self.progress_bar = ProgressIndicator(self)
        self.progress_bar.setMaximum(total_questions)
        self.progress_bar.setValue(current_index + 1)
        main_layout.addWidget(self.progress_bar)
        
        # 创建标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel(f"第 {question_data.get('question_id', '')} 题")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        type_label = QLabel(f"[{question_data.get('type_name', '')}]")
        type_label.setStyleSheet("color: #1890ff; font-size: 14px; margin-left: 10px;")
        
        difficulty_label = QLabel(f"难度: {question_data.get('difficulty_level', '普通')}")
        difficulty_label.setStyleSheet("""
            background-color: #f5f5f5;
            padding: 4px 8px;
            border-radius: 4px;
            color: #666;
            font-size: 12px;
        """)
        
        progress_label = QLabel(f"{current_index + 1}/{total_questions}")
        progress_label.setStyleSheet("""
            color: #666;
            font-size: 14px;
            margin-left: 10px;
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(type_label)
        title_layout.addStretch()
        title_layout.addWidget(progress_label)
        title_layout.addWidget(difficulty_label)
        
        # 创建内容区域
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e8e8e8;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        
        content_label = QLabel(question_data.get('content', ''))
        content_label.setWordWrap(True)
        content_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        content_layout.addWidget(content_label)
        
        # 创建答题区域
        answer_widget = self._create_answer_widget()
        
        # 创建提交按钮
        self.submit_button = QPushButton("提交答案 (Enter)")
        self.submit_button.setMinimumWidth(120)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
            }
        """)
        self.submit_button.clicked.connect(self.submit_answer)
        
        # 添加键盘快捷键
        self._setup_shortcuts()
        
        # 添加所有组件到主布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(content_frame)
        main_layout.addWidget(answer_widget)
        main_layout.addWidget(self.submit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def _setup_shortcuts(self) -> None:
        """设置键盘快捷键"""
        # 提交答案快捷键
        submit_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        submit_shortcut.activated.connect(self.submit_answer)
        
        # 选择题选项快捷键
        if self.question_data.get('type_name') == '选择题':
            for i in range(min(len(self.question_data.get('options', [])), 4)):
                key = Qt.Key.Key_A + i
                shortcut = QShortcut(QKeySequence(key), self)
                shortcut.activated.connect(lambda idx=i: self._select_option(idx))
                
        # 判断题快捷键
        elif self.question_data.get('type_name') == '判断题':
            true_shortcut = QShortcut(QKeySequence(Qt.Key.Key_T), self)
            true_shortcut.activated.connect(lambda: self._select_option(0))
            false_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F), self)
            false_shortcut.activated.connect(lambda: self._select_option(1))
            
    def _select_option(self, index: int) -> None:
        """选择选项"""
        if not self.has_submitted and self.option_group.button(index):
            self.option_group.button(index).setChecked(True)
            
    def _validate_answer(self, answer: str) -> bool:
        """验证答案格式是否正确"""
        question_type = self.question_data.get('type_name', '')
        
        if question_type == '选择题':
            return len(answer) == 1 and answer in 'ABCD'
        elif question_type == '判断题':
            return answer in ['True', 'False']
        elif question_type == '填空题':
            return bool(answer.strip())
        elif question_type == '简答题':
            return len(answer.strip()) >= 10  # 简答题至少需要10个字符
            
        return False
        
    def submit_answer(self) -> None:
        """提交答案"""
        if self.has_submitted:
            return
            
        answer = self.get_answer()
        if not answer:
            QMessageBox.warning(self, "提示", "请输入答案！")
            return
            
        if not self._validate_answer(answer):
            QMessageBox.warning(self, "提示", "答案格式不正确！")
            return
            
        self.has_submitted = True
        self.answer_submitted.emit(answer)
        self._disable_input_controls()
        self._update_submit_button_state()
        
    def _update_submit_button_state(self) -> None:
        """更新提交按钮状态"""
        self.submit_button.setEnabled(False)
        self.submit_button.setText("已提交")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #d9d9d9;
                color: #666;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
        """)
        
    def _create_answer_widget(self) -> QWidget:
        answer_widget = QWidget()
        answer_layout = QVBoxLayout(answer_widget)
        answer_layout.setContentsMargins(0, 10, 0, 10)
        
        # 添加答题区域标题
        answer_title = QLabel("请选择或输入你的答案：")
        answer_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                margin-bottom: 10px;
                padding: 5px 0;
            }
        """)
        answer_layout.addWidget(answer_title)
        
        question_type = self.question_data.get('type_name', '')
        
        if question_type == '选择题':
            options_frame = QFrame()
            options_layout = QVBoxLayout(options_frame)
            options_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e8e8e8;
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            
            self.option_group = QButtonGroup(answer_widget)
            self.option_group.setExclusive(True)
            
            options = self.question_data.get('options', [])
            for i, option in enumerate(options):
                option_button = QRadioButton(f"{chr(65 + i)}. {option}")
                option_button.setStyleSheet("""
                    QRadioButton {
                        font-size: 14px;
                        padding: 10px;
                        border: 1px solid transparent;
                        border-radius: 4px;
                        background-color: transparent;
                    }
                    QRadioButton:hover {
                        background-color: rgba(24, 144, 255, 0.1);
                    }
                    QRadioButton:checked {
                        background-color: rgba(24, 144, 255, 0.2);
                        border-color: #1890ff;
                    }
                """)
                self.option_group.addButton(option_button, i)
                options_layout.addWidget(option_button)
            
            answer_layout.addWidget(options_frame)
            
        elif question_type == '判断题':
            options_frame = QFrame()
            options_layout = QHBoxLayout(options_frame)
            options_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e8e8e8;
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            
            self.option_group = QButtonGroup(answer_widget)
            self.option_group.setExclusive(True)
            
            true_button = QRadioButton("✓ 正确")
            false_button = QRadioButton("✗ 错误")
            
            button_style = """
                QRadioButton {
                    font-size: 14px;
                    padding: 15px 30px;
                    border: 1px solid #d9d9d9;
                    border-radius: 4px;
                    margin: 5px;
                    min-width: 120px;
                    text-align: center;
                    background-color: transparent;
                }
                QRadioButton:hover {
                    background-color: rgba(24, 144, 255, 0.1);
                    border-color: #40a9ff;
                }
                QRadioButton:checked {
                    background-color: rgba(24, 144, 255, 0.2);
                    border-color: #1890ff;
                }
            """
            true_button.setStyleSheet(button_style)
            false_button.setStyleSheet(button_style)
            
            self.option_group.addButton(true_button, 0)
            self.option_group.addButton(false_button, 1)
            
            options_layout.addStretch()
            options_layout.addWidget(true_button)
            options_layout.addWidget(false_button)
            options_layout.addStretch()
            
            answer_layout.addWidget(options_frame)
            
        elif question_type == '填空题':
            self.answer_input = QLineEdit()
            self.answer_input.setPlaceholderText("请在此输入答案")
            self.answer_input.setStyleSheet("""
                QLineEdit {
                    font-size: 14px;
                    padding: 12px;
                    border: 1px solid #d9d9d9;
                    border-radius: 4px;
                    margin: 10px 0;
                    background-color: white;
                }
                QLineEdit:focus {
                    border-color: #1890ff;
                    outline: none;
                    background-color: rgba(24, 144, 255, 0.05);
                }
            """)
            answer_layout.addWidget(self.answer_input)
            
        elif question_type == '简答题':
            self.answer_text = QTextEdit()
            self.answer_text.setPlaceholderText("请在此输入答案")
            self.answer_text.setMinimumHeight(150)
            self.answer_text.setStyleSheet("""
                QTextEdit {
                    font-size: 14px;
                    padding: 12px;
                    border: 1px solid #d9d9d9;
                    border-radius: 4px;
                    margin: 10px 0;
                    background-color: white;
                }
                QTextEdit:focus {
                    border-color: #1890ff;
                    outline: none;
                    background-color: rgba(24, 144, 255, 0.05);
                }
            """)
            answer_layout.addWidget(self.answer_text)
        
        return answer_widget
        
    def _disable_input_controls(self) -> None:
        """禁用所有输入控件"""
        question_type = self.question_data.get('type_name', '')
        
        if question_type in ['选择题', '判断题']:
            for button in self.option_group.buttons():
                button.setEnabled(False)
        elif question_type == '填空题':
            self.answer_input.setEnabled(False)
        elif question_type == '简答题':
            self.answer_text.setEnabled(False)
            
    def reset(self) -> None:
        """重置答题状态"""
        self.has_submitted = False  # 重置提交状态
        question_type = self.question_data.get('type_name', '')
        
        if question_type in ['选择题', '判断题']:
            self.option_group.setExclusive(False)
            for button in self.option_group.buttons():
                button.setChecked(False)
                button.setEnabled(True)  # 重新启用按钮
            self.option_group.setExclusive(True)
        elif question_type == '填空题':
            self.answer_input.clear()
            self.answer_input.setEnabled(True)  # 重新启用输入框
        elif question_type == '简答题':
            self.answer_text.clear()
            self.answer_text.setEnabled(True)  # 重新启用文本框
            
        # 重置提交按钮状态
        self.submit_button.setEnabled(True)
        self.submit_button.setText("提交答案")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
            }
        """)
        
    def get_answer(self) -> Optional[str]:
        """获取答案"""
        question_type = self.question_data.get('type_name', '')
        
        if question_type in ['选择题', '判断题']:
            selected_button = self.option_group.checkedButton()
            if not selected_button:
                return None
                
            if question_type == '选择题':
                answer_index = self.option_group.checkedId()
                return chr(65 + answer_index)
            else:  # 判断题
                return "True" if self.option_group.checkedId() == 0 else "False"
                
        elif question_type == '填空题':
            return self.answer_input.text().strip()
            
        elif question_type == '简答题':
            return self.answer_text.toPlainText().strip()
            
        return None 