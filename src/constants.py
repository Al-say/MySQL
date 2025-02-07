"""常量定义模块"""

class Constants:
    """常量类"""
    
    # 题目类型
    QUESTION_TYPES = {
        'multiple_choice': 1,
        'true_false': 2,
        'fill_blank': 3,
        'short_answer': 4
    }
    
    # 数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'password',
        'database': 'quiz_db'
    }
    
    # 评分相关常量
    SCORING = {
        'default_weight': 1.0,
        'partial_credit_threshold': 0.5,
        'min_score': 0.0,
        'max_score': 1.0
    }
    
    # 缓存配置
    CACHE = {
        'max_size': 1000,
        'ttl_seconds': 3600  # 1小时
    }
    
    # API响应状态码
    STATUS_CODES = {
        'success': 200,
        'bad_request': 400,
        'not_found': 404,
        'server_error': 500
    } 