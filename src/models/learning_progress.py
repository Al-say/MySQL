from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta
from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class LearningProgress:
    """学习进度跟踪类"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def get_daily_progress(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日学习进度"""
        query = """
            SELECT 
                DATE(answer_time) as study_date,
                COUNT(DISTINCT question_id) as questions_attempted,
                COUNT(DISTINCT CASE WHEN is_correct = 1 THEN question_id END) as questions_correct,
                ROUND(AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy_rate
            FROM user_answer_history
            WHERE user_id = %s
            AND answer_time >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY DATE(answer_time)
            ORDER BY study_date DESC
        """
        try:
            return self.db_manager.execute_query(query, (user_id, days)) or []
        except Exception as e:
            logger.error(f"获取每日进度失败: {str(e)}")
            return []
            
    def get_topic_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """获取各主题的学习进度"""
        query = """
            SELECT 
                t.tag_name,
                COUNT(DISTINCT q.question_id) as total_questions,
                COUNT(DISTINCT ah.question_id) as attempted_questions,
                COUNT(DISTINCT CASE WHEN ah.is_correct = 1 THEN ah.question_id END) as correct_questions,
                ROUND(AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as mastery_rate
            FROM question_tags t
            JOIN question_tag_relations qtr ON t.tag_id = qtr.tag_id
            JOIN questions q ON qtr.question_id = q.question_id
            LEFT JOIN user_answer_history ah ON q.question_id = ah.question_id AND ah.user_id = %s
            WHERE t.is_active = TRUE
            GROUP BY t.tag_id, t.tag_name
            ORDER BY mastery_rate DESC
        """
        try:
            return self.db_manager.execute_query(query, (user_id,)) or []
        except Exception as e:
            logger.error(f"获取主题进度失败: {str(e)}")
            return []
            
    def get_difficulty_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """获取各难度级别的学习进度"""
        query = """
            SELECT 
                dl.level_name,
                COUNT(DISTINCT q.question_id) as total_questions,
                COUNT(DISTINCT ah.question_id) as attempted_questions,
                COUNT(DISTINCT CASE WHEN ah.is_correct = 1 THEN ah.question_id END) as correct_questions,
                ROUND(AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy_rate
            FROM difficulty_levels dl
            JOIN questions q ON dl.level_id = q.difficulty_level
            LEFT JOIN user_answer_history ah ON q.question_id = ah.question_id AND ah.user_id = %s
            WHERE q.is_active = TRUE
            GROUP BY dl.level_id, dl.level_name
            ORDER BY dl.level_id
        """
        try:
            return self.db_manager.execute_query(query, (user_id,)) or []
        except Exception as e:
            logger.error(f"获取难度进度失败: {str(e)}")
            return []
            
    def get_weak_points(self, user_id: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """获取用户的薄弱知识点"""
        query = """
            WITH topic_stats AS (
                SELECT 
                    t.tag_id,
                    t.tag_name,
                    t.description,
                    COUNT(DISTINCT ah.question_id) as attempt_count,
                    AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) as accuracy_rate
                FROM question_tags t
                JOIN question_tag_relations qtr ON t.tag_id = qtr.tag_id
                JOIN questions q ON qtr.question_id = q.question_id
                LEFT JOIN user_answer_history ah ON q.question_id = ah.question_id AND ah.user_id = %s
                WHERE t.is_active = TRUE
                GROUP BY t.tag_id, t.tag_name, t.description
                HAVING attempt_count > 0 AND accuracy_rate < %s
            )
            SELECT 
                ts.*,
                q.question_id as recommended_question_id,
                q.content as recommended_question
            FROM topic_stats ts
            JOIN question_tag_relations qtr ON ts.tag_id = qtr.tag_id
            JOIN questions q ON qtr.question_id = q.question_id
            LEFT JOIN user_answer_history ah ON q.question_id = ah.question_id AND ah.user_id = %s
            WHERE q.is_active = TRUE AND ah.question_id IS NULL
            GROUP BY ts.tag_id, ts.tag_name, ts.description, ts.attempt_count, ts.accuracy_rate
            ORDER BY ts.accuracy_rate ASC
        """
        try:
            return self.db_manager.execute_query(query, (user_id, threshold, user_id)) or []
        except Exception as e:
            logger.error(f"获取薄弱知识点失败: {str(e)}")
            return []
            
    def get_learning_streak(self, user_id: str) -> Dict[str, Any]:
        """获取学习连续天数"""
        query = """
            WITH daily_activity AS (
                SELECT DISTINCT DATE(answer_time) as study_date
                FROM user_answer_history
                WHERE user_id = %s
                ORDER BY study_date DESC
            ),
            streak_calc AS (
                SELECT 
                    study_date,
                    ROW_NUMBER() OVER (ORDER BY study_date DESC) as row_num,
                    DATE_SUB(study_date, INTERVAL ROW_NUMBER() OVER (ORDER BY study_date DESC) DAY) as group_date
                FROM daily_activity
            )
            SELECT 
                COUNT(*) as current_streak,
                MIN(study_date) as streak_start,
                MAX(study_date) as streak_end
            FROM streak_calc
            WHERE group_date = (
                SELECT group_date
                FROM streak_calc
                WHERE study_date = (
                    SELECT MAX(study_date)
                    FROM streak_calc
                )
            )
        """
        try:
            results = self.db_manager.execute_query(query, (user_id,))
            if results and results[0]['current_streak']:
                streak_end = results[0]['streak_end']
                if isinstance(streak_end, str):
                    streak_end = datetime.strptime(streak_end, '%Y-%m-%d').date()
                
                # 检查是否中断（超过一天没有学习）
                if (datetime.now().date() - streak_end) > timedelta(days=1):
                    return {'current_streak': 0, 'streak_start': None, 'streak_end': None}
                    
            return results[0] if results else {'current_streak': 0, 'streak_start': None, 'streak_end': None}
        except Exception as e:
            logger.error(f"获取学习连续天数失败: {str(e)}")
            return {'current_streak': 0, 'streak_start': None, 'streak_end': None}
            
    def get_study_time_distribution(self, user_id: str) -> List[Dict[str, Any]]:
        """获取学习时间分布"""
        query = """
            SELECT 
                HOUR(answer_time) as study_hour,
                COUNT(*) as activity_count,
                ROUND(AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy_rate
            FROM user_answer_history
            WHERE user_id = %s
            GROUP BY HOUR(answer_time)
            ORDER BY activity_count DESC
        """
        try:
            return self.db_manager.execute_query(query, (user_id,)) or []
        except Exception as e:
            logger.error(f"获取学习时间分布失败: {str(e)}")
            return [] 