from pathlib import Path

class Constants:
    """Constants configuration class"""
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '178309',
        'database': 'mysql_exercise_db',
        'buffered': True,
        'autocommit': True
    }
    
    WINDOW_TITLE = 'MySQL Practice System'
    WINDOW_GEOMETRY = (100, 100, 800, 600)
    
    # Question type ID mapping (updated to match database)
    QUESTION_TYPES = {
        'all': 0,
        'multiple_choice': 1,  # 选择题
        'true_false': 2,      # 判断题
        'fill_blank': 3,      # 填空题
        'short_answer': 4,    # 简答题
        'mysql_design': 5     # MySQL Design
    }
    
    # Difficulty level ID mapping
    DIFFICULTY_LEVELS = {
        'all': 0,
        'beginner': 1,
        'intermediate': 2,
        'advanced': 3
    }
    
    # Cache configuration
    CACHE_DIR = Path('cache')
    CACHE_DURATION = 3600  # Cache duration in seconds
    
    # Style configuration
    STYLES = {
        'button': """
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #0056b3;
            }
        """,
        'group_box': """
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """
    } 