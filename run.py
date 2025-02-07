import os
import sys
import logging
from typing import Dict, Any, List
import json
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import PracticeSystem

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can import from src
from src.main import main
from src.services.deep_learning_manager import DeepLearningManager
from src.database.db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProgramTester:
    """程序测试类"""
    def __init__(self):
        self.dl_manager = DeepLearningManager()
        self.db_manager = DatabaseManager()
        self.test_results = {}
        
    def analyze_code_structure(self) -> Dict[str, Any]:
        """分析代码结构"""
        modules_to_analyze = [
            ('src/ui/main_window.py', '主界面模块'),
            ('src/services/deep_learning_manager.py', 'AI服务模块'),
            ('src/database/db_manager.py', '数据库模块'),
            ('src/services/knowledge_graph.py', '知识图谱模块'),
            ('src/services/recommendation_system.py', '推荐系统模块')
        ]
        
        analysis_results = {}
        for file_path, module_name in modules_to_analyze:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    
                logger.info(f"正在分析{module_name}的代码结构...")
                # 使用新的analyze_code方法
                analysis = self.dl_manager.analyze_code(
                    code,
                    system_prompt="""请分析以下代码的结构和潜在问题：
1. 代码结构是否清晰
2. 是否存在代码重复
3. 是否遵循设计模式
4. 是否存在潜在的性能问题
5. 是否有安全隐患
6. 提供具体的改进建议"""
                )
                analysis_results[module_name] = analysis
                
            except Exception as e:
                logger.error(f"分析{module_name}时出错: {str(e)}")
                analysis_results[module_name] = f"分析失败: {str(e)}"
                
        return analysis_results
        
    def test_database_operations(self) -> Dict[str, Any]:
        """测试数据库操作"""
        logger.info("测试数据库操作...")
        results = {}
        
        try:
            # 测试数据库连接
            if self.db_manager.connect():
                results['connection'] = "数据库连接成功"
                
                # 测试查询操作
                query = "SELECT COUNT(*) as count FROM questions"
                query_result = self.db_manager.execute_query(query)
                results['query'] = f"查询成功，题目总数: {query_result[0]['count'] if query_result else 0}"
                
                # 测试事务操作
                test_query = """
                    INSERT INTO questions (type_id, difficulty_level, content, is_active)
                    VALUES (%s, %s, %s, %s)
                """
                test_params = (1, 1, "测试题目", False)
                if self.db_manager.execute_transaction([(test_query, test_params)]):
                    results['transaction'] = "事务测试成功"
                else:
                    results['transaction'] = "事务测试失败"
                    
            else:
                results['connection'] = "数据库连接失败"
                
        except Exception as e:
            logger.error(f"数据库测试失败: {str(e)}")
            results['error'] = str(e)
            
        return results
        
    def test_api_functionality(self) -> Dict[str, Any]:
        """测试API功能"""
        logger.info("测试API功能...")
        results = {}
        
        try:
            # 测试内容生成
            test_prompt = "生成一个简单的MySQL查询示例"
            response = self.dl_manager.generate_content(
                test_prompt,
                system_prompt="你是一个MySQL专家，请生成一个简单但实用的SQL查询示例。"
            )
            results['content_generation'] = "内容生成测试成功" if response else "内容生成测试失败"
            
            # 测试代码分析
            test_code = "SELECT * FROM users WHERE id = 1"
            analysis = self.dl_manager.analyze_code(
                test_code,
                system_prompt="请分析这个SQL查询的性能和最佳实践。"
            )
            results['code_analysis'] = "代码分析测试成功" if analysis else "代码分析测试失败"
            
            # 测试答案评估
            correct_answer = "SELECT * FROM users"
            student_answer = "select * from users"
            score, feedback = self.dl_manager.evaluate_answer(
                student_answer,
                correct_answer,
                criteria="""请根据以下标准评估SQL查询答案：
1. 语法正确性
2. 代码风格
3. 最佳实践遵循度"""
            )
            results['answer_evaluation'] = {
                'score': score,
                'feedback': feedback
            }
            
        except Exception as e:
            logger.error(f"API功能测试失败: {str(e)}")
            results['error'] = str(e)
            
        return results
        
    def generate_improvement_suggestions(self) -> str:
        """生成改进建议"""
        logger.info("生成改进建议...")
        try:
            # 收集所有测试结果
            all_results = {
                'code_structure': self.test_results.get('code_structure', {}),
                'database_operations': self.test_results.get('database_operations', {}),
                'api_functionality': self.test_results.get('api_functionality', {})
            }
            
            # 使用新的generate_content方法生成综合建议
            suggestions = self.dl_manager.generate_content(
                json.dumps(all_results, ensure_ascii=False, indent=2),
                system_prompt="""基于测试结果，请提供详细的改进建议，包括：
1. 代码质量改进
2. 性能优化
3. 安全性增强
4. 功能完善
5. 用户体验提升
6. 可维护性提升"""
            )
            return suggestions
            
        except Exception as e:
            logger.error(f"生成改进建议失败: {str(e)}")
            return f"生成改进建议失败: {str(e)}"
            
    def run_tests(self) -> None:
        """运行所有测试"""
        logger.info("开始运行测试...")
        
        # 运行代码结构分析
        self.test_results['code_structure'] = self.analyze_code_structure()
        
        # 运行数据库测试
        self.test_results['database_operations'] = self.test_database_operations()
        
        # 运行API功能测试
        self.test_results['api_functionality'] = self.test_api_functionality()
        
        # 生成改进建议
        self.test_results['improvement_suggestions'] = self.generate_improvement_suggestions()
        
        # 保存测试结果
        self.save_test_results()
        
        # 显示测试结果
        self.display_test_results()
        
    def save_test_results(self) -> None:
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            logger.info(f"测试结果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存测试结果失败: {str(e)}")
            
    def display_test_results(self) -> None:
        """显示测试结果"""
        print("\n=== 程序测试结果 ===\n")
        
        # 显示代码结构分析结果
        print("=== 代码结构分析 ===")
        for module, analysis in self.test_results['code_structure'].items():
            print(f"\n--- {module} ---")
            print(analysis)
            print("-" * 50)
            
        # 显示数据库测试结果
        print("\n=== 数据库测试结果 ===")
        for key, value in self.test_results['database_operations'].items():
            print(f"{key}: {value}")
            
        # 显示API测试结果
        print("\n=== API功能测试结果 ===")
        for key, value in self.test_results['api_functionality'].items():
            print(f"{key}: {value}")
            
        # 显示改进建议
        print("\n=== 改进建议 ===")
        print(self.test_results['improvement_suggestions'])

def main():
    try:
        app = QApplication(sys.argv)
        window = PracticeSystem()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if "--test" in sys.argv:
        logger.info("启动程序测试...")
        tester = ProgramTester()
        tester.run_tests()
    else:
        main() 