import os
import sys
import time
import logging
import schedule
from datetime import datetime
from pathlib import Path
import json
import subprocess
from typing import Dict, Any, List, Optional
from mysql.connector import errorcode
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.database.db_manager import DatabaseManager
from src.services.deep_learning_manager import DeepLearningManager
from src.services.knowledge_graph import KnowledgeGraph
from src.services.recommendation_system import RecommendationSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomationManager:
    """自动化管理器"""
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.dl_manager = DeepLearningManager('alsay')  # 使用项目管理专用API实例
        self.knowledge_graph = KnowledgeGraph(self.db_manager)
        self.recommendation_system = RecommendationSystem(self.db_manager)
        
        # 创建必要的目录
        self.setup_directories()
        
    def setup_directories(self):
        """创建必要的目录结构"""
        directories = [
            'logs',
            'data',
            'reports',
            'backups',
            'temp'
        ]
        
        for dir_name in directories:
            path = Path(project_root) / dir_name
            path.mkdir(exist_ok=True)
            logger.info(f"创建目录: {path}")
            
    def run_database_maintenance(self):
        """数据库维护任务"""
        logger.info("开始数据库维护...")
        try:
            # 备份数据库
            self.backup_database()
            
            # 清理过期数据
            self.clean_expired_data()
            
            # 优化数据库
            self.optimize_database()
            
            logger.info("数据库维护完成")
        except Exception as e:
            logger.error(f"数据库维护失败: {str(e)}")
            
    def backup_database(self):
        """备份数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(project_root) / 'backups' / f'db_backup_{timestamp}.sql'
        
        try:
            # 使用mysqldump进行备份
            cmd = [
                'mysqldump',
                '-u', 'root',
                '-p178309',
                'mysql_exercise_db',
                f'--result-file={backup_file}'
            ]
            
            subprocess.run(cmd, check=True)
            logger.info(f"数据库备份成功: {backup_file}")
        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
            
    def clean_expired_data(self):
        """清理过期数据"""
        try:
            # 清理30天前的答题历史
            query = """
                DELETE FROM answer_history
                WHERE answer_time < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            self.db_manager.execute_transaction([(query, None)])
            
            # 清理无效的题目标签关联
            query = """
                DELETE FROM question_tag_relations
                WHERE question_id NOT IN (
                    SELECT question_id FROM questions WHERE is_active = TRUE
                )
            """
            self.db_manager.execute_transaction([(query, None)])
            
            logger.info("过期数据清理完成")
        except Exception as e:
            logger.error(f"清理过期数据失败: {str(e)}")
            
    def optimize_database(self):
        """优化数据库"""
        try:
            # 优化表
            tables = [
                'questions',
                'answers',
                'answer_history',
                'question_tags',
                'question_tag_relations'
            ]
            
            for table in tables:
                query = f"OPTIMIZE TABLE {table}"
                self.db_manager.execute_query(query)
                
            logger.info("数据库优化完成")
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
            
    def update_knowledge_graph(self):
        """更新知识图谱"""
        logger.info("开始更新知识图谱...")
        try:
            # 构建新的知识图谱
            graph = self.knowledge_graph.build_knowledge_graph()
            
            # 保存知识图谱数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            graph_file = Path(project_root) / 'data' / f'knowledge_graph_{timestamp}.json'
            
            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(graph, f, ensure_ascii=False, indent=2)
                
            # 生成可视化图表
            vis_file = Path(project_root) / 'reports' / f'knowledge_graph_{timestamp}.png'
            self.knowledge_graph.visualize_graph(str(vis_file))
            
            logger.info("知识图谱更新完成")
        except Exception as e:
            logger.error(f"更新知识图谱失败: {str(e)}")
            
    def generate_system_report(self):
        """生成系统报告"""
        try:
            logging.info("开始生成系统报告...")
            report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'database_stats': self._get_database_stats(),
                'system_stats': self._get_system_stats()
            }
            
            # 确保报告目录存在
            report_dir = os.path.join(project_root, 'reports')
            os.makedirs(report_dir, exist_ok=True)
            
            # 生成报告文件名
            report_file = os.path.join(report_dir, 
                f'system_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            
            # 自定义 JSON 编码器处理 numpy arrays
            class NumpyEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, np.ndarray):
                        return obj.tolist()
                    return json.JSONEncoder.default(self, obj)
            
            # 保存报告
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)
            
            logging.info(f"系统报告已生成: {report_file}")
            return report
        except Exception as e:
            logging.error(f"生成系统报告失败: {str(e)}")
            return None
            
    def _get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {}
        try:
            # 获取各表的记录数
            tables = [
                'questions',
                'answers',
                'answer_history',
                'question_tags'
            ]
            
            for table in tables:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.db_manager.execute_query(query)
                stats[f'{table}_count'] = result[0]['count'] if result else 0
                
            # 获取数据库大小
            query = """
                SELECT table_schema as database_name,
                       ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables
                WHERE table_schema = 'mysql_exercise_db'
                GROUP BY table_schema
            """
            result = self.db_manager.execute_query(query)
            stats['database_size_mb'] = result[0]['size_mb'] if result else 0
            
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {str(e)}")
            
        return stats
        
    def _get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {}
        try:
            # 获取API调用统计
            stats['api_calls'] = {
                'total': 0,  # 需要实现计数器
                'success_rate': 0.0,
                'average_response_time': 0.0
            }
            
            # 获取用户活动统计
            query = """
                SELECT 
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(*) as total_answers,
                    ROUND(AVG(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100, 2) as average_accuracy
                FROM answer_history
                WHERE answer_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            result = self.db_manager.execute_query(query)
            if result:
                stats['user_activity'] = {
                    'active_users': result[0]['active_users'],
                    'total_answers': result[0]['total_answers'],
                    'average_accuracy': result[0]['average_accuracy']
                }
                
        except Exception as e:
            logger.error(f"获取系统统计信息失败: {str(e)}")
            
        return stats
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = {}
        try:
            # 获取数据库性能指标
            query = """
                SHOW GLOBAL STATUS
                WHERE Variable_name IN (
                    'Questions',
                    'Slow_queries',
                    'Threads_connected',
                    'Threads_running'
                )
            """
            result = self.db_manager.execute_query(query)
            if result:
                stats['database_performance'] = {
                    row['Variable_name']: row['Value']
                    for row in result
                }
                
            # 获取系统资源使用情况
            import psutil
            stats['system_resources'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent
            }
            
        except Exception as e:
            logger.error(f"获取性能统计信息失败: {str(e)}")
            
        return stats
        
    def schedule_tasks(self):
        """调度定时任务"""
        # 每天凌晨3点进行数据库维护
        schedule.every().day.at("03:00").do(self.run_database_maintenance)
        
        # 每6小时更新一次知识图谱
        schedule.every(6).hours.do(self.update_knowledge_graph)
        
        # 每小时生成一次系统报告
        schedule.every(1).hours.do(self.generate_system_report)
        
        logger.info("定时任务已调度")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("自动化任务已停止")
                break
            except Exception as e:
                logger.error(f"执行定时任务时出错: {str(e)}")
                time.sleep(300)  # 发生错误时等待5分钟后继续
                
def main():
    """主函数"""
    try:
        automation = AutomationManager()
        
        # 立即执行一次系统报告生成
        logger.info("生成初始系统报告...")
        automation.generate_system_report()
        
        # 立即执行一次知识图谱更新
        logger.info("执行初始知识图谱更新...")
        automation.update_knowledge_graph()
        
        # 启动定时任务调度
        logger.info("启动定时任务调度...")
        automation.schedule_tasks()
    except Exception as e:
        logger.error(f"自动化管理器启动失败: {str(e)}")
        
if __name__ == "__main__":
    main() 