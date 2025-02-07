import mysql.connector
import sys
import os
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Generator

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_questions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@contextmanager
def db_connection() -> Generator[DatabaseManager, None, None]:
    """创建数据库连接的上下文管理器"""
    db_manager = DatabaseManager()
    if not db_manager.connect():
        raise Exception("无法连接到数据库")
    try:
        yield db_manager
    finally:
        db_manager.close()

def insert_question(db_manager: DatabaseManager, question: Dict[str, Any]) -> bool:
    """插入单个题目及其相关数据"""
    try:
        # 准备所有需要执行的查询
        queries = []
        
        # 插入题目
        question_query = """
            INSERT INTO questions 
            (type_id, difficulty_level, content, is_active)
            VALUES (%s, %s, %s, %s)
        """
        question_params = (
            question['type_id'],
            question['difficulty_level'],
            question['content'],
            True
        )
        
        # 执行插入题目的查询
        if not db_manager.execute_transaction([(question_query, question_params)]):
            logger.error("插入题目失败")
            return False
            
        # 获取最后插入的ID
        last_id_query = "SELECT LAST_INSERT_ID() as id"
        result = db_manager.execute_query(last_id_query)
        if not result:
            logger.error("无法获取插入的题目ID")
            return False
        question_id = result[0]['id']
        
        # 准备选项和答案的查询
        queries = []
        
        # 如果是选择题，添加选项
        if question['type_id'] == 1:  # 选择题
            options_query = """
                INSERT INTO multiple_choice_options
                (question_id, option_content, is_correct)
                VALUES (%s, %s, %s)
            """
            
            for option, is_correct in question['options']:
                queries.append((options_query, (question_id, option, is_correct)))
        
        # 添加答案和解析
        answer_query = """
            INSERT INTO answers
            (question_id, answer_content, explanation)
            VALUES (%s, %s, %s)
        """
        queries.append((answer_query, (question_id, question['answer'], question['explanation'])))
        
        # 执行所有查询作为一个事务
        if db_manager.execute_transaction(queries):
            return True
        else:
            logger.error("执行事务失败")
            return False
            
    except Exception as e:
        logger.error(f"插入题目时发生错误: {str(e)}", exc_info=True)
        return False

def insert_questions_batch(db_manager: DatabaseManager, questions: List[Dict[str, Any]]) -> bool:
    """批量插入题目"""
    try:
        success_count = 0
        for i, question in enumerate(questions, 1):
            if insert_question(db_manager, question):
                logger.info(f"成功插入测试题目{i}")
                success_count += 1
            else:
                logger.error(f"插入测试题目{i}失败")
        
        logger.info(f"批量插入完成: 成功 {success_count}/{len(questions)}")
        return success_count == len(questions)
    except Exception as e:
        logger.error(f"批量插入题目时发生错误: {str(e)}", exc_info=True)
        return False

def get_test_questions() -> List[Dict[str, Any]]:
    """获取测试题目数据"""
    return [
        # 选择题1
        {
            'content': '以下哪个命令用于显示MySQL中的所有数据库？',
            'type_id': 1,  # 选择题
            'difficulty_level': 1,
            'options': [
                ('SHOW DATABASES;', True),
                ('LIST DATABASES;', False),
                ('SELECT DATABASES;', False),
                ('DISPLAY DATABASES;', False)
            ],
            'answer': 'A',
            'explanation': '在MySQL中，SHOW DATABASES;是显示所有数据库的标准命令。其他选项都不是有效的MySQL命令。'
        },
        
        # 选择题2
        {
            'content': '在MySQL中，以下哪个语句可以创建名为"students"的数据库？',
            'type_id': 1,  # 选择题
            'difficulty_level': 1,
            'options': [
                ('CREATE DATABASE students;', True),
                ('MAKE DATABASE students;', False),
                ('NEW DATABASE students;', False),
                ('GENERATE DATABASE students;', False)
            ],
            'answer': 'A',
            'explanation': 'CREATE DATABASE是MySQL中创建新数据库的标准命令。其他选项都不是有效的MySQL命令。'
        },

        # 判断题1
        {
            'content': 'MySQL中的主键（PRIMARY KEY）可以包含NULL值。',
            'type_id': 2,  # 判断题
            'difficulty_level': 2,
            'answer': 'False',
            'explanation': '主键是用来唯一标识表中每一行的字段，它必须包含唯一的非NULL值。主键列会自动添加NOT NULL约束。'
        },

        # 判断题2
        {
            'content': 'MySQL的SELECT语句中，WHERE子句在GROUP BY子句之前执行。',
            'type_id': 2,  # 判断题
            'difficulty_level': 2,
            'answer': 'True',
            'explanation': 'SQL语句的执行顺序是：FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY。WHERE在GROUP BY之前执行，用于过滤原始数据。'
        },

        # 填空题1
        {
            'content': '在MySQL中，要删除名为"students"的数据库，正确的SQL语句是：_____ students;',
            'type_id': 3,  # 填空题
            'difficulty_level': 1,
            'answer': 'DROP DATABASE',
            'explanation': 'DROP DATABASE是MySQL中删除数据库的标准命令。完整语句应为：DROP DATABASE students;'
        },

        # 填空题2
        {
            'content': '在MySQL中，要将查询结果按照age字段降序排列，在SQL语句末尾应添加：ORDER BY age _____;',
            'type_id': 3,  # 填空题
            'difficulty_level': 1,
            'answer': 'DESC',
            'explanation': 'DESC关键字用于指定降序排序。相对应的，ASC用于指定升序排序（默认值）。'
        },

        # 简答题1
        {
            'content': '请解释MySQL中INNER JOIN和LEFT JOIN的区别，并给出示例。',
            'type_id': 4,  # 简答题
            'difficulty_level': 3,
            'answer': '''INNER JOIN和LEFT JOIN的主要区别：
1. INNER JOIN只返回两个表中匹配的行
2. LEFT JOIN返回左表的所有行，即使右表中没有匹配的行

示例：
假设有两个表：students和scores
- INNER JOIN：
SELECT s.name, sc.score 
FROM students s 
INNER JOIN scores sc 
ON s.id = sc.student_id;
只返回有成绩的学生

- LEFT JOIN：
SELECT s.name, sc.score 
FROM students s 
LEFT JOIN scores sc 
ON s.id = sc.student_id;
返回所有学生，没有成绩的显示为NULL''',
            'explanation': '理解不同JOIN类型的区别对于数据查询和分析非常重要。INNER JOIN用于获取两个表中的交集，而LEFT JOIN可以保留左表的所有数据，适用于不同的业务场景。'
        },

        # 简答题2
        {
            'content': '请说明在MySQL中如何优化一个慢查询，列出主要的优化步骤和方法。',
            'type_id': 4,  # 简答题
            'difficulty_level': 3,
            'answer': '''MySQL查询优化的主要步骤和方法：
1. 使用EXPLAIN分析查询执行计划
2. 检查并优化索引使用情况
   - 为常用查询条件创建适当的索引
   - 避免索引失效的情况
3. 优化查询语句
   - 只查询需要的字段，避免SELECT *
   - 减少子查询，使用JOIN替代
   - 使用LIMIT限制结果集大小
4. 优化表结构
   - 选择合适的数据类型
   - 适当分表分库
5. 优化配置
   - 调整缓冲池大小
   - 优化并发参数
6. 定期维护
   - 更新统计信息
   - 定期清理碎片''',
            'explanation': '查询优化是数据库性能调优的关键部分，需要从多个层面进行综合考虑，包括索引优化、查询重写、表结构优化等。'
        }
    ]

def insert_test_questions() -> None:
    """插入测试题目的主函数"""
    try:
        with db_connection() as db_manager:
            questions = get_test_questions()
            if insert_questions_batch(db_manager, questions):
                logger.info("所有测试题目插入成功")
            else:
                logger.error("部分或全部测试题目插入失败")
    except Exception as e:
        logger.error(f"执行测试题目插入时发生错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    insert_test_questions() 