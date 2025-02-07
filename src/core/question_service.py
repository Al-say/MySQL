from typing import List, Optional
from src.database.base import db_manager
from src.models.question import Question
from sqlalchemy.orm import Session
from src.utils.exceptions import QuestionNotFoundError
import logging

logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(self):
        self.db = db_manager
    
    def get_questions(
        self, 
        page: int = 1, 
        per_page: int = 20,
        type_id: Optional[int] = None,
        difficulty: Optional[int] = None
    ) -> List[Question]:
        try:
            with self.db.get_session() as session:
                query = session.query(Question)
                
                if type_id:
                    query = query.filter(Question.type_id == type_id)
                if difficulty:
                    query = query.filter(Question.difficulty_level == difficulty)
                
                questions = query.offset((page - 1) * per_page)\
                                .limit(per_page)\
                                .all()
                return questions
        except Exception as e:
            logger.error(f"Error fetching questions: {e}")
            raise
    
    def verify_answer(self, question_id: int, user_answer: str) -> bool:
        try:
            with self.db.get_session() as session:
                question = session.query(Question).get(question_id)
                if not question:
                    raise QuestionNotFoundError(f"Question {question_id} not found")
                
                # 根据题目类型进行不同的验证逻辑
                if question.type_id in [1, 2]:  # 选择题和判断题
                    return user_answer.strip().upper() == question.correct_answer.strip().upper()
                elif question.type_id == 3:  # SQL填空题
                    return self._verify_sql_answer(user_answer, question.correct_answer)
                else:  # 其他类型题目使用AI评分
                    return self._ai_score_answer(user_answer, question)
        except Exception as e:
            logger.error(f"Error verifying answer: {e}")
            raise
    
    def _verify_sql_answer(self, user_sql: str, correct_sql: str) -> bool:
        # SQL答案验证逻辑
        pass
    
    def _ai_score_answer(self, user_answer: str, question: Question) -> bool:
        # AI评分逻辑
        pass

question_service = QuestionService()
