"""
评分服务的单元测试
"""

import pytest
from datetime import datetime
from typing import Dict, List
from src.services.scoring_service import ScoringService
from src.database.db_manager import DatabaseManager
from src.config.constants import Constants

@pytest.fixture
def scoring_service():
    """创建评分服务实例"""
    db_manager = DatabaseManager()
    return ScoringService(db_manager)

@pytest.fixture
def mock_answers():
    """提供模拟答案数据"""
    return {
        'multiple_choice': {
            'question_id': 1,
            'type_id': Constants.QUESTION_TYPES['multiple_choice'],
            'user_answer': 'A',
            'correct_answer': 'A',
            'explanation': '这是正确答案，因为...'
        },
        'true_false': {
            'question_id': 2,
            'type_id': Constants.QUESTION_TYPES['true_false'],
            'user_answer': 'True',
            'correct_answer': 'True',
            'explanation': '这个说法是正确的，因为...'
        },
        'fill_blank': {
            'question_id': 3,
            'type_id': Constants.QUESTION_TYPES['fill_blank'],
            'user_answer': 'SELECT * FROM users;',
            'correct_answer': 'SELECT * FROM users;',
            'explanation': 'SQL查询语句正确...'
        },
        'short_answer': {
            'question_id': 4,
            'type_id': Constants.QUESTION_TYPES['short_answer'],
            'user_answer': '详细的答案内容...',
            'correct_answer': '标准答案内容...',
            'explanation': '答案评分标准...'
        }
    }

class TestScoringService:
    """评分服务测试类"""

    def test_evaluate_multiple_choice(self, scoring_service, mock_answers):
        """测试选择题评分"""
        result = scoring_service.evaluate_answer(
            question_id=mock_answers['multiple_choice']['question_id'],
            user_answer=mock_answers['multiple_choice']['user_answer'],
            question_type=Constants.QUESTION_TYPES['multiple_choice']
        )
        
        assert isinstance(result, dict)
        assert 'is_correct' in result
        assert 'score' in result
        assert 'feedback' in result
        assert result['is_correct'] is True
        assert result['score'] == 1.0

    def test_evaluate_true_false(self, scoring_service, mock_answers):
        """测试判断题评分"""
        result = scoring_service.evaluate_answer(
            question_id=mock_answers['true_false']['question_id'],
            user_answer=mock_answers['true_false']['user_answer'],
            question_type=Constants.QUESTION_TYPES['true_false']
        )
        
        assert result['is_correct'] is True
        assert result['score'] == 1.0
        assert isinstance(result['feedback'], str)

    def test_evaluate_fill_blank(self, scoring_service, mock_answers):
        """测试填空题评分"""
        result = scoring_service.evaluate_answer(
            question_id=mock_answers['fill_blank']['question_id'],
            user_answer=mock_answers['fill_blank']['user_answer'],
            question_type=Constants.QUESTION_TYPES['fill_blank']
        )
        
        assert result['is_correct'] is True
        assert result['score'] == 1.0
        assert 'sql_analysis' in result

    def test_evaluate_short_answer(self, scoring_service, mock_answers):
        """测试简答题评分"""
        result = scoring_service.evaluate_answer(
            question_id=mock_answers['short_answer']['question_id'],
            user_answer=mock_answers['short_answer']['user_answer'],
            question_type=Constants.QUESTION_TYPES['short_answer']
        )
        
        assert isinstance(result['score'], float)
        assert 0 <= result['score'] <= 1.0
        assert 'keyword_matches' in result
        assert 'content_quality' in result
        assert 'suggestions' in result

    @pytest.mark.parametrize('answer_type,user_answer,expected_score', [
        ('multiple_choice', 'B', 0.0),           # 错误选项
        ('multiple_choice', 'A', 1.0),           # 正确选项
        ('true_false', 'False', 0.0),            # 错误判断
        ('true_false', 'True', 1.0),             # 正确判断
        ('fill_blank', 'wrong query;', 0.0),     # 错误SQL
        ('fill_blank', 'SELECT * FROM users;', 1.0)  # 正确SQL
    ])
    def test_scoring_variations(self, scoring_service, mock_answers, answer_type, user_answer, expected_score):
        """测试不同类型答案的评分变化"""
        result = scoring_service.evaluate_answer(
            question_id=mock_answers[answer_type]['question_id'],
            user_answer=user_answer,
            question_type=mock_answers[answer_type]['type_id']
        )
        assert result['score'] == expected_score

    def test_partial_credit_scoring(self, scoring_service):
        """测试部分得分情况"""
        # 测试简答题部分得分
        result = scoring_service.evaluate_answer(
            question_id=4,
            user_answer="部分正确的答案...",
            question_type=Constants.QUESTION_TYPES['short_answer']
        )
        assert 0 < result['score'] < 1.0
        assert 'partial_matches' in result

    def test_sql_answer_evaluation(self, scoring_service):
        """测试SQL答案评估"""
        # 测试等价但不完全相同的SQL
        result = scoring_service.evaluate_sql_answer(
            user_sql="SELECT * FROM users WHERE age >= 18",
            correct_sql="SELECT * FROM users WHERE age > 17"
        )
        assert result['is_equivalent'] is True
        assert 'execution_plan' in result
        assert 'performance_analysis' in result

    def test_explanation_generation(self, scoring_service, mock_answers):
        """测试解析生成"""
        explanation = scoring_service.generate_explanation(
            question_id=mock_answers['multiple_choice']['question_id'],
            user_answer='A',
            is_correct=True
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert '正确答案' in explanation
        assert '解析' in explanation

    def test_batch_evaluation(self, scoring_service, mock_answers):
        """测试批量评分"""
        answers = [
            {
                'question_id': mock_answers['multiple_choice']['question_id'],
                'user_answer': 'A',
                'question_type': Constants.QUESTION_TYPES['multiple_choice']
            },
            {
                'question_id': mock_answers['true_false']['question_id'],
                'user_answer': 'True',
                'question_type': Constants.QUESTION_TYPES['true_false']
            }
        ]
        
        results = scoring_service.evaluate_batch(answers)
        assert isinstance(results, list)
        assert len(results) == len(answers)
        assert all('score' in result for result in results)

    def test_error_handling(self, scoring_service):
        """测试错误处理"""
        # 测试无效的问题ID
        with pytest.raises(ValueError):
            scoring_service.evaluate_answer(
                question_id=-1,
                user_answer='test',
                question_type=Constants.QUESTION_TYPES['multiple_choice']
            )
        
        # 测试无效的题目类型
        with pytest.raises(ValueError):
            scoring_service.evaluate_answer(
                question_id=1,
                user_answer='test',
                question_type=999
            )
        
        # 测试空答案
        with pytest.raises(ValueError):
            scoring_service.evaluate_answer(
                question_id=1,
                user_answer='',
                question_type=Constants.QUESTION_TYPES['multiple_choice']
            )

    @pytest.mark.asyncio
    async def test_async_evaluation(self, scoring_service, mock_answers):
        """测试异步评分"""
        result = await scoring_service.evaluate_answer_async(
            question_id=mock_answers['short_answer']['question_id'],
            user_answer=mock_answers['short_answer']['user_answer'],
            question_type=Constants.QUESTION_TYPES['short_answer']
        )
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'feedback' in result

    def test_scoring_cache(self, scoring_service, mock_answers):
        """测试评分缓存"""
        # 启用测试模式以添加人工延迟
        scoring_service.enable_testing_mode()
        
        try:
            # 第一次评分
            start_time = datetime.now()
            result1 = scoring_service.evaluate_answer(
                question_id=mock_answers['multiple_choice']['question_id'],
                user_answer='A',
                question_type=Constants.QUESTION_TYPES['multiple_choice']
            )
            first_time = datetime.now() - start_time
            
            # 第二次评分（应该使用缓存）
            start_time = datetime.now()
            result2 = scoring_service.evaluate_answer(
                question_id=mock_answers['multiple_choice']['question_id'],
                user_answer='A',
                question_type=Constants.QUESTION_TYPES['multiple_choice']
            )
            second_time = datetime.now() - start_time
            
            assert second_time < first_time
            assert result1 == result2
        finally:
            # 确保测试后禁用测试模式
            scoring_service.disable_testing_mode()

    def test_scoring_metrics(self, scoring_service):
        """测试评分指标"""
        metrics = scoring_service.get_scoring_metrics()
        assert isinstance(metrics, dict)
        assert 'average_score' in metrics
        assert 'total_evaluations' in metrics
        assert 'response_time_avg' in metrics
        assert 'cache_hit_rate' in metrics 