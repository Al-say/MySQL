from typing import List, Dict, Any
import logging
from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class KnowledgePoint:
    """知识点管理类"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def get_knowledge_points(self) -> List[Dict[str, Any]]:
        """获取所有知识点"""
        query = """
            SELECT 
                t.tag_id,
                t.tag_name,
                t.description,
                COUNT(qtr.question_id) as question_count,
                AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) as mastery_rate
            FROM question_tags t
            LEFT JOIN question_tag_relations qtr ON t.tag_id = qtr.tag_id
            LEFT JOIN user_answer_history ah ON qtr.question_id = ah.question_id
            WHERE t.is_active = TRUE
            GROUP BY t.tag_id, t.tag_name, t.description
            ORDER BY question_count DESC
        """
        try:
            return self.db_manager.execute_query(query) or []
        except Exception as e:
            logger.error(f"获取知识点列表失败: {str(e)}")
            return []
            
    def get_knowledge_point_details(self, tag_id: int) -> Dict[str, Any]:
        """获取知识点详细信息"""
        query = """
            SELECT 
                t.tag_id,
                t.tag_name,
                t.description,
                COUNT(DISTINCT qtr.question_id) as total_questions,
                COUNT(DISTINCT CASE WHEN ah.is_correct = 1 THEN ah.question_id END) as correct_questions,
                COUNT(DISTINCT CASE WHEN ah.is_correct = 0 THEN ah.question_id END) as wrong_questions,
                ROUND(AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as accuracy_rate
            FROM question_tags t
            LEFT JOIN question_tag_relations qtr ON t.tag_id = qtr.tag_id
            LEFT JOIN user_answer_history ah ON qtr.question_id = ah.question_id
            WHERE t.tag_id = %s AND t.is_active = TRUE
            GROUP BY t.tag_id, t.tag_name, t.description
        """
        try:
            results = self.db_manager.execute_query(query, (tag_id,))
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"获取知识点详情失败: {str(e)}")
            return {}
            
    def get_related_questions(self, tag_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取知识点相关的题目"""
        query = """
            SELECT 
                q.question_id,
                q.content,
                qt.type_name,
                dl.level_name as difficulty,
                COUNT(ah.question_id) as attempt_count,
                ROUND(AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as correct_rate
            FROM questions q
            JOIN question_tag_relations qtr ON q.question_id = qtr.question_id
            JOIN question_types qt ON q.type_id = qt.type_id
            JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
            LEFT JOIN user_answer_history ah ON q.question_id = ah.question_id
            WHERE qtr.tag_id = %s AND q.is_active = TRUE
            GROUP BY q.question_id, q.content, qt.type_name, dl.level_name
            ORDER BY attempt_count DESC, correct_rate ASC
            LIMIT %s
        """
        try:
            return self.db_manager.execute_query(query, (tag_id, limit)) or []
        except Exception as e:
            logger.error(f"获取知识点相关题目失败: {str(e)}")
            return []
            
    def add_knowledge_point(self, name: str, description: str) -> bool:
        """添加新知识点"""
        query = """
            INSERT INTO question_tags (tag_name, description, is_active)
            VALUES (%s, %s, TRUE)
        """
        try:
            return self.db_manager.execute_transaction([(query, (name, description))])
        except Exception as e:
            logger.error(f"添加知识点失败: {str(e)}")
            return False
            
    def update_knowledge_point(self, tag_id: int, name: str, description: str) -> bool:
        """更新知识点信息"""
        query = """
            UPDATE question_tags
            SET tag_name = %s, description = %s
            WHERE tag_id = %s AND is_active = TRUE
        """
        try:
            return self.db_manager.execute_transaction([(query, (name, description, tag_id))])
        except Exception as e:
            logger.error(f"更新知识点失败: {str(e)}")
            return False
            
    def delete_knowledge_point(self, tag_id: int) -> bool:
        """删除知识点（软删除）"""
        query = """
            UPDATE question_tags
            SET is_active = FALSE
            WHERE tag_id = %s
        """
        try:
            return self.db_manager.execute_transaction([(query, (tag_id,))])
        except Exception as e:
            logger.error(f"删除知识点失败: {str(e)}")
            return False
            
    def get_learning_path(self) -> List[Dict[str, Any]]:
        """获取学习路径建议"""
        query = """
            WITH tag_stats AS (
                SELECT 
                    t.tag_id,
                    t.tag_name,
                    t.description,
                    COUNT(DISTINCT qtr.question_id) as question_count,
                    AVG(CASE WHEN ah.is_correct = 1 THEN 1 ELSE 0 END) as mastery_rate,
                    dl.level_id
                FROM question_tags t
                JOIN question_tag_relations qtr ON t.tag_id = qtr.tag_id
                JOIN questions q ON qtr.question_id = q.question_id
                JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
                LEFT JOIN user_answer_history ah ON q.question_id = ah.question_id
                WHERE t.is_active = TRUE
                GROUP BY t.tag_id, t.tag_name, t.description, dl.level_id
            )
            SELECT 
                tag_id,
                tag_name,
                description,
                question_count,
                COALESCE(mastery_rate, 0) as mastery_rate,
                level_id as recommended_level
            FROM tag_stats
            ORDER BY 
                level_id,
                mastery_rate DESC,
                question_count DESC
        """
        try:
            return self.db_manager.execute_query(query) or []
        except Exception as e:
            logger.error(f"获取学习路径失败: {str(e)}")
            return [] 