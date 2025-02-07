"""
问题服务的单元测试
"""

import pytest
from typing import Dict, List
from datetime import datetime, timedelta
from src.services.question_service import QuestionService
from src.database.db_manager import DatabaseManager
from src.config.constants import Constants

@pytest.fixture
def question_service(test_config):
    """创建问题服务实例"""
    db_manager = DatabaseManager(
        host=test_config['DB_HOST'],
        port=test_config['DB_PORT'],
        user=test_config['DB_USER'],
        password=test_config['DB_PASSWORD'],
        database=test_config['DB_NAME']
    )
    return QuestionService(db_manager)

@pytest.fixture
def mock_questions():
    """提供模拟题目数据"""
    return [
        {
            'question_id': 1,
            'content': 'SHOW DATABASES命令的作用是什么？',
            'type_id': Constants.QUESTION_TYPES['multiple_choice'],
            'difficulty_level': Constants.DIFFICULTY_LEVELS['beginner'],
            'options': ['显示所有数据库', '创建数据库', '删除数据库', '修改数据库'],
            'correct_answer': 'A'
        },
        {
            'question_id': 2,
            'content': 'MySQL中的主键是否可以包含NULL值？',
            'type_id': Constants.QUESTION_TYPES['true_false'],
            'difficulty_level': Constants.DIFFICULTY_LEVELS['intermediate'],
            'correct_answer': 'False'
        }
    ]

class TestQuestionService:
    """问题服务测试类"""
    
    def test_get_questions_basic(self, question_service, sample_question):
        """测试基本的题目获取功能"""
        questions = question_service.get_questions()
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        # 验证题目格式
        question = questions[0]
        required_fields = {'question_id', 'content', 'type_id', 'difficulty_level'}
        assert all(field in question for field in required_fields)
        
        # 验证字段类型
        assert isinstance(question['question_id'], int)
        assert isinstance(question['content'], str)
        assert isinstance(question['type_id'], int)
        assert isinstance(question['difficulty_level'], int)

    def test_get_questions_empty_result(self, question_service):
        """测试无结果的情况"""
        # 使用不存在的类型ID
        questions = question_service.get_questions(type_id=999)
        assert isinstance(questions, list)
        assert len(questions) == 0

    @pytest.mark.parametrize('type_id,difficulty_level,expected_count', [
        (1, None, 5),    # 只筛选类型
        (None, 1, 3),    # 只筛选难度
        (1, 1, 2),       # 同时筛选类型和难度
    ])
    def test_get_questions_with_filters_count(self, question_service, type_id, difficulty_level, expected_count):
        """测试不同筛选条件下的题目数量"""
        questions = question_service.get_questions(
            type_id=type_id,
            difficulty_level=difficulty_level
        )
        assert len(questions) == expected_count

    def test_verify_answer_detailed(self, question_service, mock_questions):
        """测试详细的答案验证功能"""
        # 测试选择题
        result = question_service.verify_answer(
            question_id=mock_questions[0]['question_id'],
            user_answer='A',
            user_id='test_user'
        )
        assert result['is_correct'] is True
        assert result['score'] == 1
        assert 'explanation' in result
        assert 'response_time' in result
        
        # 测试判断题
        result = question_service.verify_answer(
            question_id=mock_questions[1]['question_id'],
            user_answer='False',
            user_id='test_user'
        )
        assert result['is_correct'] is True
        assert result['score'] == 1
        
        # 验证答题历史记录
        history = question_service.get_user_answer_history('test_user')
        assert len(history) >= 2

    @pytest.mark.parametrize('question_type,answer,expected_validation', [
        # 选择题测试用例
        (Constants.QUESTION_TYPES['multiple_choice'], 'A', True),
        (Constants.QUESTION_TYPES['multiple_choice'], 'E', False),
        (Constants.QUESTION_TYPES['multiple_choice'], '1', False),
        # 判断题测试用例
        (Constants.QUESTION_TYPES['true_false'], 'True', True),
        (Constants.QUESTION_TYPES['true_false'], 'False', True),
        (Constants.QUESTION_TYPES['true_false'], 'Yes', False),
        # 填空题测试用例
        (Constants.QUESTION_TYPES['fill_blank'], 'SELECT * FROM users;', True),
        (Constants.QUESTION_TYPES['fill_blank'], '', False),
        (Constants.QUESTION_TYPES['fill_blank'], ' ', False),
        # 简答题测试用例
        (Constants.QUESTION_TYPES['short_answer'], '详细的答案内容...', True),
        (Constants.QUESTION_TYPES['short_answer'], '太短', False),
    ])
    def test_answer_validation_comprehensive(self, question_service, question_type, answer, expected_validation):
        """全面的答案验证测试"""
        result = question_service.validate_answer(question_type, answer)
        assert result == expected_validation

    def test_get_questions_pagination_comprehensive(self, question_service):
        """全面的分页功能测试"""
        # 测试不同页码和每页数量的组合
        test_cases = [
            {'page': 1, 'per_page': 5},
            {'page': 2, 'per_page': 5},
            {'page': 1, 'per_page': 10},
            {'page': 3, 'per_page': 3},
        ]
        
        previous_questions = set()
        for case in test_cases:
            questions = question_service.get_questions(
                page=case['page'],
                per_page=case['per_page']
            )
            
            # 验证数量
            assert len(questions) <= case['per_page']
            
            # 验证唯一性
            current_ids = {q['question_id'] for q in questions}
            assert not current_ids.intersection(previous_questions)
            previous_questions.update(current_ids)
            
            # 验证排序
            if len(questions) > 1:
                assert all(
                    questions[i]['question_id'] < questions[i+1]['question_id']
                    for i in range(len(questions)-1)
                )

    def test_question_cache(self, question_service):
        """测试题目缓存功能"""
        # 第一次调用，应该从数据库获取
        start_time = datetime.now()
        questions1 = question_service.get_questions()
        first_call_time = datetime.now() - start_time
        
        # 第二次调用，应该从缓存获取
        start_time = datetime.now()
        questions2 = question_service.get_questions()
        second_call_time = datetime.now() - start_time
        
        # 验证缓存生效
        assert second_call_time < first_call_time
        assert questions1 == questions2

    def test_error_handling(self, question_service):
        """测试错误处理"""
        # 测试无效的页码
        with pytest.raises(ValueError):
            question_service.get_questions(page=0)
        
        with pytest.raises(ValueError):
            question_service.get_questions(page=-1)
        
        # 测试无效的每页数量
        with pytest.raises(ValueError):
            question_service.get_questions(per_page=0)
        
        with pytest.raises(ValueError):
            question_service.get_questions(per_page=1001)  # 超过最大限制
        
        # 测试无效的题目类型
        with pytest.raises(ValueError):
            question_service.get_questions(type_id=-1)
        
        # 测试无效的难度等级
        with pytest.raises(ValueError):
            question_service.get_questions(difficulty_level=999)

    @pytest.mark.asyncio
    async def test_async_operations(self, question_service):
        """测试异步操作"""
        # 测试异步获取题目
        questions = await question_service.get_questions_async()
        assert isinstance(questions, list)
        assert len(questions) > 0
        
        # 测试异步验证答案
        result = await question_service.verify_answer_async(
            question_id=1,
            user_answer='A',
            user_id='test_user'
        )
        assert isinstance(result, dict)
        assert 'is_correct' in result 