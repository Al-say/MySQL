import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
import logging
from ..database.db_manager import DatabaseManager
from .deep_learning_manager import DeepLearningManager

logger = logging.getLogger(__name__)

class RecommendationSystem:
    """智能推荐系统"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.dl_manager = DeepLearningManager('al')  # 使用数据库专用API实例
        
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
            return np.zeros(1024)  # DeepSeek embedding 维度
            
        # 计算用户答题的平均向量表示
        embeddings = []
        for content, is_correct, difficulty in results:
            # 使用新的API调用方式获取嵌入向量
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