from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QScrollArea, QFrame, QButtonGroup, QWidget,
                            QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QMetaObject, QThreadPool, pyqtSlot
from PyQt6.QtGui import QTextDocument, QResizeEvent, QCloseEvent
import mysql.connector
from mysql.connector import errorcode
from typing import List, Dict, Any, Optional, Callable
import logging
from ..config.constants import Constants
from ..database.db_manager import DatabaseManager
from ..services.deep_learning_manager import DeepLearningManager
from ..services.recommendation_system import RecommendationSystem
from ..services.knowledge_graph import KnowledgeGraph
from .components import FeedbackOverlay, QuestionWidget
from .statistics_dialog import StatisticsDialog
import time

logger = logging.getLogger(__name__)

class PracticeSystem(QMainWindow):
    """MySQL练习系统主窗口"""
    
    # 定义不同难度等级对应的等待时间（毫秒）
    DIFFICULTY_WAIT_TIMES = {
        '初级': 2000,    # 2秒
        '中级': 3000,    # 3秒
        '高级': 5000     # 5秒
    }
    
    def __init__(self) -> None:
        """初始化练习系统"""
        super().__init__()
        
        # 添加缓存机制
        self._cache = {}
        self._cache_timeout = 300  # 缓存超时时间（秒）
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager()
        if not self.db_manager.connect():
            QMessageBox.critical(self, "错误", "无法连接到数据库")
            return
            
        # 添加连接重试机制
        self._setup_connection_retry()
        
        # 当前题目和题目列表
        self.current_question_index = 0
        self.questions = []
        self.current_question_widget = None
        
        # 添加批量加载机制
        self.batch_size = 10
        self.total_loaded = 0
        
        # 添加防抖动定时器
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._handle_debounced_action)
        
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
        self.explanation_text: Optional[QTextEdit] = None
        
        # 导航按钮
        self.prev_button: Optional[QPushButton] = None
        self.next_button: Optional[QPushButton] = None
        self.stats_button: Optional[QPushButton] = None
        
        # 统计标签
        self.total_questions_label: Optional[QLabel] = None
        self.answered_questions_label: Optional[QLabel] = None
        self.correct_rate_label: Optional[QLabel] = None
        
        # 初始化遮罩层和定时器
        self.feedback_overlay = FeedbackOverlay(self)
        self.feedback_overlay.feedback_hidden.connect(self.handle_feedback_hidden)
        
        # 初始化自动跳转定时器
        self.auto_next_timer = QTimer(self)
        self.auto_next_timer.setSingleShot(True)  # 设置为单次触发
        self.auto_next_timer.timeout.connect(self.next_question)  # 直接连接到next_question方法
        
        # 初始化深度学习组件
        self.dl_manager = DeepLearningManager('say')
        self.recommendation_system = RecommendationSystem(self.db_manager)
        self.knowledge_graph = KnowledgeGraph(self.db_manager)
        
        # 初始化界面
        self.init_ui()
        
    def _setup_connection_retry(self) -> None:
        """设置连接重试机制"""
        self.max_retries = 3
        self.retry_delay = 1000  # 毫秒
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self._retry_connection)
        self.retry_count = 0
        
    def _retry_connection(self) -> None:
        """重试数据库连接"""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            if self.db_manager.connect():
                self.retry_timer.stop()
                self.load_questions()
            else:
                self.retry_timer.start(self.retry_delay * self.retry_count)
        else:
            self.retry_timer.stop()
            QMessageBox.critical(self, "错误", "无法连接到数据库，请检查网络连接")
            
    def _get_cached_data(self, key: str) -> Any:
        """获取缓存数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_timeout:
                return data
            del self._cache[key]
        return None
        
    def _set_cached_data(self, key: str, data: Any) -> None:
        """设置缓存数据"""
        self._cache[key] = (data, time.time())
        
    def init_ui(self) -> None:
        """初始化用户界面"""
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # 创建顶部工具栏
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout()
        toolbar.setLayout(toolbar_layout)
        
        # 左侧：筛选按钮
        filter_frame = QFrame()
        filter_layout = QHBoxLayout()
        filter_frame.setLayout(filter_layout)
        
        # 题型筛选
        type_frame = QFrame()
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
        difficulty_frame = QFrame()
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
        self.prev_button = QPushButton("上一题")
        self.prev_button.clicked.connect(self.prev_question)
        self.prev_button.setStyleSheet(Constants.STYLES['button'])
        
        self.next_button = QPushButton("下一题")
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setStyleSheet(Constants.STYLES['button'])
        
        # 添加测试按钮
        test_button = QPushButton("Alsay 测试")
        test_button.clicked.connect(self.test_with_alsay)
        test_button.setStyleSheet(Constants.STYLES['button'])
        
        # 添加生成内容按钮
        generate_button = QPushButton("生成题目")
        generate_button.clicked.connect(self.generate_database_content)
        generate_button.setStyleSheet(Constants.STYLES['button'])
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(test_button)
        nav_layout.addWidget(generate_button)
        toolbar_layout.addWidget(nav_frame)
        
        # 添加工具栏到主布局
        self.main_layout.addWidget(toolbar)
        
        # 创建题目区域
        self.question_area = QScrollArea()
        self.question_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.question_area)
        
        # 创建解析区域
        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setVisible(False)  # 初始时隐藏
        self.explanation_text.setMaximumHeight(150)  # 设置最大高度
        self.main_layout.addWidget(self.explanation_text)
        
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
        """从数据库加载题目（优化版）"""
        try:
            # 先检查题目总数
            count_query = "SELECT COUNT(*) as total FROM questions WHERE is_active = TRUE"
            count_result = self.db_manager.execute_query(count_query)
            total_questions = count_result[0]['total'] if count_result else 0
            logger.info(f"数据库中共有 {total_questions} 道题目")
            
            # 构建查询
            query = """
                SELECT 
                    q.question_id,
                    q.content,
                    q.type_id,
                    qt.type_name,
                    dl.level_name as difficulty_level,
                    GROUP_CONCAT(DISTINCT mco.option_content ORDER BY mco.option_id SEPARATOR '||') as options,
                    GROUP_CONCAT(DISTINCT CASE WHEN mco.is_correct = 1 THEN mco.option_id END) as correct_answers,
                    GROUP_CONCAT(DISTINCT CASE WHEN mco.is_correct = 1 THEN mco.option_content END) as correct_option,
                    a.answer_content,
                    COALESCE(a.explanation, '暂无解析') as explanation
                FROM 
                    questions q
                    JOIN question_types qt ON q.type_id = qt.type_id
                    JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
                    LEFT JOIN multiple_choice_options mco ON q.question_id = mco.question_id
                    LEFT JOIN answers a ON q.question_id = a.question_id
                WHERE 
                    q.is_active = TRUE
                GROUP BY 
                    q.question_id, q.content, q.type_id, qt.type_name, dl.level_name, 
                    a.answer_content, a.explanation
                ORDER BY RAND()
            """
            
            results = self.db_manager.execute_query(query)
            logger.info(f"查询到 {len(results) if results else 0} 道题目")
            
            if not results:
                QMessageBox.warning(self, "警告", "没有找到任何题目")
                return
                
            # 处理查询结果
            processed_questions = []
            for row in results:
                try:
                    # 创建基本题目信息
                    processed_question = {
                        'question_id': row['question_id'],
                        'content': row['content'],
                        'type_id': row['type_id'],
                        'type_name': row['type_name'],
                        'difficulty_level': row['difficulty_level'],
                        'answer_content': row['answer_content'],
                        'explanation': row['explanation']
                    }
                    
                    # 处理选项
                    if row['type_name'] == '选择题' and row['options']:
                        processed_question['options'] = row['options'].split('||')
                        processed_question['correct_answers'] = row['correct_answers']
                        processed_question['correct_option'] = row['correct_option']
                    else:
                        processed_question['options'] = []
                        processed_question['correct_answers'] = None
                        processed_question['correct_option'] = None
                        
                    processed_questions.append(processed_question)
                    logger.info(f"处理题目: ID={row['question_id']}, 类型={row['type_name']}")
                    
                except Exception as e:
                    logger.error(f"处理题目 {row.get('question_id', 'unknown')} 时出错: {str(e)}")
                    continue
            
            if not processed_questions:
                QMessageBox.warning(self, "警告", "没有找到有效的题目")
                return
                
            self.questions = processed_questions
            self.current_question_index = 0
            self.load_question()
            
        except Exception as e:
            logger.error(f"加载题目失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载题目失败: {str(e)}")
            
    def load_question(self) -> None:
        """加载当前题目"""
        if not self.questions:
            return
            
        logger.info(f"正在加载第 {self.current_question_index + 1} 题...")
        
        # 清除旧的题目视图
        if self.question_area.widget():
            self.question_area.widget().deleteLater()
            
        # 创建新的题目视图
        self.current_question_widget = QuestionWidget(
            self.questions[self.current_question_index],
            len(self.questions),
            self.current_question_index,
            self
        )
        self.current_question_widget.answer_submitted.connect(self.check_answer)
        
        # 设置为滚动区域的内容
        self.question_area.setWidget(self.current_question_widget)
        
        # 更新界面
        self.update_stats()
        self.update_navigation_buttons()
        
        logger.info(f"题目加载完成：{self.questions[self.current_question_index]['content']}")
        
    @pyqtSlot()
    def update_stats(self) -> None:
        """更新统计信息"""
        try:
            # 获取总题数
            query = "SELECT COUNT(*) as total FROM questions WHERE is_active = TRUE"
            result = self.db_manager.execute_query(query)
            total_questions = result[0]['total'] if result else 0
            self.total_questions_label.setText(f"总题数: {total_questions}")
            
            # 获取答题统计
            query = """
                SELECT 
                    COUNT(DISTINCT question_id) as answered,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts,
                    ROUND(AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy
                FROM user_answer_history
                WHERE user_id = 'test_user'
            """
            result = self.db_manager.execute_query(query)
            
            if result and result[0]:
                stats = result[0]
                self.answered_questions_label.setText(f"已答题数: {stats['answered'] or 0}")
                self.correct_rate_label.setText(f"正确率: {stats['accuracy'] or 0}%")
            else:
                self.answered_questions_label.setText("已答题数: 0")
                self.correct_rate_label.setText("正确率: 0%")
                
        except Exception as e:
            logger.error(f"更新统计信息失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"更新统计信息失败: {str(e)}")
            
    def update_navigation_buttons(self) -> None:
        """更新导航按钮状态"""
        if not self.questions:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
            
        # 启用导航按钮
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        # 根据当前位置设置按钮状态
        if self.current_question_index <= 0:
            self.prev_button.setEnabled(False)
        if self.current_question_index >= len(self.questions) - 1:
            self.next_button.setEnabled(False)
        
    def prev_question(self) -> None:
        """上一题"""
        try:
            if self.current_question_index > 0:
                self.current_question_index -= 1
                self.load_question()
                # 隐藏解析区域，准备下一题
                if hasattr(self, 'explanation_text'):
                    self.explanation_text.setVisible(False)
                    self.explanation_text.clear()
                logger.info(f"成功切换到第 {self.current_question_index + 1} 题")
            else:
                logger.info("已经是第一题")
                QMessageBox.information(self, "提示", "已经是第一题了")
        except Exception as e:
            logger.error(f"切换上一题时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"切换上一题时出错: {str(e)}")
            
    def next_question(self) -> None:
        """下一题"""
        try:
            # 停止定时器（如果正在运行）
            if hasattr(self, 'auto_next_timer'):
                self.auto_next_timer.stop()
            
            # 检查是否可以进入下一题
            if self.current_question_index < len(self.questions) - 1:
                self.current_question_index += 1
                self.load_question()
                # 隐藏解析区域，准备下一题
                if hasattr(self, 'explanation_text'):
                    self.explanation_text.setVisible(False)
                    self.explanation_text.clear()
                logger.info(f"成功切换到第 {self.current_question_index + 1} 题")
            else:
                logger.info("已经是最后一题")
                QMessageBox.information(self, "提示", "已经是最后一题了")
        except Exception as e:
            logger.error(f"切换下一题时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"切换下一题时出错: {str(e)}")
            
    def check_answer(self, answer: Optional[str] = None) -> None:
        """检查答案（优化版）"""
        if not self.current_question_widget:
            return
            
        if answer is None:
            answer = self.current_question_widget.get_answer()
            
        if not answer:
            QMessageBox.warning(self, "提示", "请先作答！")
            return
            
        # 使用防抖动机制
        self.debounce(self._process_answer, answer)
        
    def _process_answer(self, answer: str) -> None:
        """处理答案（新增）"""
        try:
            current_question = self.questions[self.current_question_index]
            
            # 检查答案是否正确
            is_correct = False
            if current_question['type_name'] == '选择题':
                # 获取正确答案的索引
                correct_answers = current_question.get('correct_answers', '').split(',') if current_question.get('correct_answers') else []
                if correct_answers:
                    try:
                        # 将用户答案转换为选项 ID（从 1 开始）
                        user_answer_id = ord(answer) - 65 + 1  # A->1, B->2, etc.
                        is_correct = str(user_answer_id) in correct_answers
                    except (ValueError, IndexError):
                        is_correct = False
            elif current_question['type_name'] == '判断题':
                # 判断题答案验证
                correct_answer = current_question.get('answer_content', '').strip()
                is_correct = answer.lower() == correct_answer.lower()
            elif current_question['type_name'] == '填空题':
                # 填空题答案验证
                correct_answer = current_question.get('answer_content', '').strip()
                is_correct = answer.lower() == correct_answer.lower()
            else:  # 简答题
                # 简答题答案验证
                correct_answer = current_question.get('answer_content', '').strip()
                if correct_answer:
                    # 预处理答案文本
                    user_answer = answer.lower().strip()
                    correct_answer = correct_answer.lower().strip()
                    
                    # 提取关键词（去除常见的标点符号和停用词）
                    def extract_keywords(text):
                        # 移除标点符号和特殊字符
                        import re
                        text = re.sub(r'[^\w\s]', ' ', text)
                        # 分词并去除停用词
                        words = [w.strip() for w in text.split() if len(w.strip()) > 1]
                        return set(words)
                    
                    user_keywords = extract_keywords(user_answer)
                    correct_keywords = extract_keywords(correct_answer)
                    
                    if len(correct_keywords) > 0:
                        # 计算关键词匹配度
                        matched_keywords = user_keywords.intersection(correct_keywords)
                        match_ratio = len(matched_keywords) / len(correct_keywords)
                        # 如果匹配度超过70%则认为答案正确
                        is_correct = match_ratio >= 0.7
                    else:
                        is_correct = False
                else:
                    is_correct = False
            
            # 异步更新答题记录
            self._async_update_answer_history(current_question['question_id'], answer, is_correct)
            
            # 显示反馈
            self.show_answer_feedback(is_correct, current_question)
            
        except Exception as e:
            logger.error(f"处理答案时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理答案时出错: {str(e)}")
            
    def _async_update_answer_history(self, question_id: int, answer: str, is_correct: bool) -> None:
        """异步更新答题历史"""
        try:
            # 创建异步任务
            def update_task():
                try:
                    query = """
                        INSERT INTO user_answer_history 
                        (user_id, question_id, user_answer, is_correct, answer_time)
                        VALUES (%s, %s, %s, %s, NOW())
                    """
                    # 暂时使用固定的用户ID
                    user_id = 'test_user'
                    self.db_manager.execute_transaction([(query, (user_id, question_id, answer, is_correct))])
                    
                    # 在主线程中更新统计信息
                    QMetaObject.invokeMethod(self, "update_stats", Qt.ConnectionType.QueuedConnection)
                except Exception as e:
                    logger.error(f"异步更新答题历史失败: {str(e)}")
                    
            # 在线程池中执行更新任务
            QThreadPool.globalInstance().start(update_task)
            
        except Exception as e:
            logger.error(f"创建异步任务失败: {str(e)}")
            
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
            
    def show_answer_feedback(self, is_correct: bool, question: Dict[str, Any]) -> None:
        """显示答案反馈"""
        try:
            # 显示遮罩层反馈
            self.feedback_overlay.show_feedback(is_correct)
            
            # 构建答案文本
            answer_text = ""
            if question['type_name'] == '选择题':
                # 对于选择题，显示正确选项的字母和内容
                correct_answers = question.get('correct_answers', '').split(',') if question.get('correct_answers') else []
                options = question.get('options', [])
                if correct_answers and options:
                    try:
                        # 选项的序号从 1 开始，但显示的字母从 A 开始
                        answer_letters = []
                        correct_options = []
                        for option_id in correct_answers:
                            # 将选项 ID 转换为 0-based 索引
                            index = int(option_id) - 1
                            if 0 <= index < len(options):
                                answer_letters.append(chr(65 + index))
                                correct_options.append(options[index])
                        
                        if answer_letters and correct_options:
                            answer_text = f"{', '.join(answer_letters)} ({', '.join(correct_options)})"
                        else:
                            answer_text = "答案格式错误"
                    except (ValueError, IndexError) as e:
                        logger.error(f"处理选择题答案时出错: {str(e)}")
                        answer_text = "答案格式错误"
                else:
                    answer_text = "未设置选项或答案"
            else:
                # 其他类型题目直接显示答案内容
                answer_text = question.get('answer_content', '未设置')
            
            # 获取或生成解析
            explanation = question.get('explanation', '').strip()
            if not explanation or explanation == '暂无解析':
                # 使用API生成解析
                prompt = f"""请为以下MySQL题目生成详细解析：

题目：{question['content']}

正确答案：{answer_text}

请提供：
1. 为什么这是正确答案
2. 相关的MySQL概念解释
3. 实际应用场景
4. 注意事项

输出格式：请直接输出解析文本，不需要任何标记或格式。"""

                try:
                    explanation = self.dl_manager.generate_content_sync(prompt)
                    if explanation:
                        # 更新数据库中的解析
                        def update_explanation():
                            query = """
                                UPDATE answers 
                                SET explanation = %s 
                                WHERE question_id = %s
                            """
                            self.db_manager.execute_transaction([(query, (explanation, question['question_id']))])
                            
                        # 在线程池中执行更新
                        QThreadPool.globalInstance().start(update_explanation)
                    else:
                        explanation = "暂无解析"
                except Exception as e:
                    logger.error(f"生成解析失败: {str(e)}")
                    explanation = "解析生成失败，请稍后重试"
            
            # 构建完整的解析文本
            explanation_text = f"【正确答案】\n{answer_text}\n\n"
            explanation_text += f"【解析】\n{explanation}"
            
            # 设置解析文本
            self.explanation_text.setText(explanation_text)
            self.explanation_text.setVisible(True)
            
            # 设置解析区域样式
            style = """
                QTextEdit {
                    border: 1px solid %s;
                    border-radius: 4px;
                    padding: 12px;
                    font-size: 14px;
                    background-color: %s;
                    line-height: 1.5;
                }
                QTextEdit p {
                    margin: 8px 0;
                }
            """ % (
                "#52c41a" if is_correct else "#ff4d4f",
                "#f6ffed" if is_correct else "#fff2f0"
            )
            self.explanation_text.setStyleSheet(style)
            
            # 确保解析区域在布局中可见
            self.explanation_text.show()
            self.explanation_text.raise_()
            
            # 更新布局
            self.main_layout.update()

            # 如果答案正确，设置自动跳转
            if is_correct and self.current_question_index < len(self.questions) - 1:
                # 获取当前题目难度
                difficulty = question.get('difficulty_level', '初级')
                # 获取对应的等待时间，如果没有设置则使用默认值（2秒）
                wait_time = self.DIFFICULTY_WAIT_TIMES.get(difficulty, 2000)
                
                # 显示倒计时信息
                self.feedback_overlay.show_countdown(wait_time)
                
                # 设置自动跳转定时器
                self.auto_next_timer.setInterval(wait_time)
                self.auto_next_timer.start()
            
        except Exception as e:
            logger.error(f"显示答案反馈时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"显示答案反馈时出错: {str(e)}")
            
    def handle_feedback_hidden(self, proceed: bool) -> None:
        """处理反馈隐藏事件"""
        try:
            if proceed:
                # 确保在跳转前停止定时器
                if hasattr(self, 'auto_next_timer'):
                    self.auto_next_timer.stop()
                
                if self.current_question_index < len(self.questions) - 1:
                    self.current_question_index += 1
                    self.load_question()
                    # 隐藏解析区域，准备下一题
                    self.explanation_text.setVisible(False)
                    self.explanation_text.clear()
        except Exception as e:
            logger.error(f"处理反馈隐藏事件时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理反馈隐藏事件时出错: {str(e)}")
            
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
                    qt.type_name,
                    dl.level_name as difficulty_level,
                    GROUP_CONCAT(DISTINCT mco.option_content ORDER BY mco.option_id SEPARATOR '||') as options,
                    GROUP_CONCAT(DISTINCT CASE WHEN mco.is_correct = 1 THEN mco.option_id END) as correct_answers,
                    GROUP_CONCAT(DISTINCT CASE WHEN mco.is_correct = 1 THEN mco.option_content END) as correct_option,
                    a.answer_content,
                    COALESCE(a.explanation, '暂无解析') as explanation
                FROM 
                    questions q
                    JOIN question_types qt ON q.type_id = qt.type_id
                    JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
                    LEFT JOIN multiple_choice_options mco ON q.question_id = mco.question_id
                    LEFT JOIN answers a ON q.question_id = a.question_id
                WHERE 
                    q.is_active = TRUE
            """
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
                
            query += """
                GROUP BY 
                    q.question_id, q.content, q.type_id, qt.type_name, dl.level_name, 
                    a.answer_content, a.explanation
                ORDER BY RAND()
            """
            
            # 执行查询
            results = self.db_manager.execute_query(query, tuple(params))
            
            # 处理查询结果
            if not self.process_query_results(results):
                QMessageBox.warning(self, "警告", "没有找到符合条件的题目")
                return
                
            # 重新加载第一题
            self.load_question()
            
        except Exception as e:
            logger.error(f"筛选题目时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"筛选题目失败: {str(e)}")
            
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
            
    def show_statistics(self) -> None:
        """显示统计对话框"""
        dialog = StatisticsDialog(self)
        dialog.exec()
        
    def closeEvent(self, event: QCloseEvent) -> None:
        """关闭事件处理（优化版）"""
        try:
            # 等待所有异步任务完成
            QThreadPool.globalInstance().waitForDone()
            
            # 清理缓存
            self._cache.clear()
            
            # 关闭数据库连接
            self.db_manager.close()
            
        except Exception as e:
            logger.error(f"关闭程序时出错: {e}")
        finally:
            event.accept()
        
    def test_with_alsay(self) -> None:
        """使用 Alsay API 测试代码问题"""
        try:
            # 获取当前题目的信息
            if not self.questions or not self.current_question_widget:
                return
                
            current_question = self.questions[self.current_question_index]
            
            # 使用 Alsay API 分析代码
            analysis = self.dl_manager.analyze_code_issues(f"""
当前题目：{current_question['content']}
答案：{current_question.get('answer', '未设置')}
解析：{current_question.get('explanation', '暂无解析')}

相关代码：
1. 答案验证逻辑：
{self.validate_answer.__code__.co_code}

2. 反馈显示逻辑：
{self.show_answer_feedback.__code__.co_code}

3. 自动跳转逻辑：
{self.next_question.__code__.co_code}
""")
            
            # 显示分析结果
            QMessageBox.information(self, "Alsay 分析结果", analysis)
            
        except Exception as e:
            logger.error(f"Alsay 测试失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"Alsay 测试失败: {str(e)}")
            
    def generate_database_content(self) -> None:
        """使用 Al API 生成数据库内容"""
        try:
            # 使用 Al API 生成题目
            prompt = """请生成一道MySQL选择题，包含以下内容：
1. 题目内容（要求涉及实际的MySQL操作场景）
2. 四个选项（要求选项具有干扰性和合理性）
3. 正确答案（用A、B、C、D表示）
4. 详细解析（要解释为什么正确答案正确，其他选项为什么错误）

格式要求：
{
    "content": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "A",
    "explanation": "解析内容"
}"""
            
            # 使用数据库专用的API密钥
            response = self.dl_manager.generate_content(prompt)
            
            try:
                # 解析生成的内容
                import json
                question_data = json.loads(response)
                
                # 插入题目
                query = """
                    INSERT INTO questions 
                    (type_id, difficulty_level, content, is_active)
                    VALUES (%s, %s, %s, %s)
                """
                params = (
                    Constants.QUESTION_TYPES['multiple_choice'],  # 选择题
                    Constants.DIFFICULTY_LEVELS['beginner'],      # 初级难度
                    question_data['content'],
                    True
                )
                
                # 执行插入并获取题目ID
                self.db_manager.execute_transaction([(query, params)])
                result = self.db_manager.execute_query("SELECT LAST_INSERT_ID() as id")
                question_id = result[0]['id']
                
                # 插入选项
                option_query = """
                    INSERT INTO multiple_choice_options
                    (question_id, option_content, is_correct)
                    VALUES (%s, %s, %s)
                """
                
                option_params = []
                for i, option in enumerate(question_data['options']):
                    is_correct = (chr(65 + i) == question_data['correct_answer'])
                    option_params.append((option_query, (question_id, option, is_correct)))
                
                # 插入答案和解析
                answer_query = """
                    INSERT INTO answers
                    (question_id, answer_content, explanation)
                    VALUES (%s, %s, %s)
                """
                correct_option = question_data['options'][ord(question_data['correct_answer']) - 65]
                answer_params = (question_id, correct_option, question_data['explanation'])
                option_params.append((answer_query, answer_params))
                
                # 执行所有插入
                if self.db_manager.execute_transaction(option_params):
                    QMessageBox.information(self, "成功", "已成功生成并添加新题目！")
                    # 重新加载题目
                    self.load_questions()
                else:
                    QMessageBox.warning(self, "警告", "题目生成成功但保存失败")
                    
            except json.JSONDecodeError:
                QMessageBox.warning(self, "格式错误", "API返回的内容格式不正确")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"处理生成的内容时出错: {str(e)}")
                
        except Exception as e:
            logger.error(f"生成数据库内容失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成数据库内容失败: {str(e)}")
            
    def _handle_debounced_action(self) -> None:
        """处理防抖动操作"""
        if hasattr(self, '_pending_action'):
            action, args = self._pending_action
            action(*args)
            
    def debounce(self, func: Callable, *args, delay: int = 300) -> None:
        """添加防抖动机制"""
        self._pending_action = (func, args)
        self.debounce_timer.start(delay)

    def process_query_results(self, results: List[Dict[str, Any]]) -> bool:
        """处理查询结果并返回是否成功"""
        try:
            if not results:
                return False
                
            processed_questions = []
            for row in results:
                try:
                    # 创建基本题目信息
                    processed_question = {
                        'question_id': row['question_id'],
                        'content': row['content'],
                        'type_id': row['type_id'],
                        'type_name': row['type_name'],
                        'difficulty_level': row['difficulty_level'],
                        'answer_content': row['answer_content'],
                        'explanation': row['explanation']
                    }
                    
                    # 处理选项
                    if row['type_name'] == '选择题' and row['options']:
                        processed_question['options'] = row['options'].split('||')
                        processed_question['correct_answers'] = row['correct_answers']
                        processed_question['correct_option'] = row['correct_option']
                    else:
                        processed_question['options'] = []
                        processed_question['correct_answers'] = None
                        processed_question['correct_option'] = None
                        
                    processed_questions.append(processed_question)
                    
                except Exception as e:
                    logger.error(f"处理题目 {row.get('question_id', 'unknown')} 时出错: {str(e)}")
                    continue
            
            if not processed_questions:
                return False
                
            self.questions = processed_questions
            self.current_question_index = 0
            return True
            
        except Exception as e:
            logger.error(f"处理查询结果时出错: {str(e)}")
            return False 