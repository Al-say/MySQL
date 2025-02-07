import logging
import os
import sys
import io
import codecs
from dotenv import load_dotenv
from src.services.deep_learning_manager import DeepLearningManager
import time
import locale
import json
import unittest

# 设置系统默认编码
if sys.platform.startswith('win'):
    try:
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF8')
        except:
            pass

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置默认编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def safe_print(text):
    """安全打印，处理编码问题"""
    try:
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        elif isinstance(text, str):
            text = text.encode('utf-8', errors='replace').decode('utf-8')
        print(text)
    except Exception as e:
        print(f"打印失败: {str(e)}")

def test_api_instance(api_key: str, instance_name: str, prompt: str):
    """测试特定的API实例"""
    try:
        safe_print(f"\n测试 {instance_name} API实例...")
        
        # 初始化API管理器
        manager = DeepLearningManager(api_key)
        
        # 测试内容生成
        safe_print(f"发送请求: {prompt[:50]}...")
        response = manager.generate_content(prompt)
        
        if response:
            safe_print(f"✓ {instance_name} 测试成功")
            safe_print(f"响应预览: {response[:100]}...")
            return True
        else:
            safe_print(f"✗ {instance_name} 测试失败: 未能生成内容")
            return False
            
    except Exception as e:
        safe_print(f"✗ {instance_name} 测试错误: {str(e)}")
        return False
    finally:
        if 'manager' in locals():
            del manager

def test_all_instances():
    """测试所有API实例"""
    # 加载环境变量
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=env_path)
    
    # 测试配置
    test_cases = [
        {
            'name': '项目管理',
            'key_env': 'DEEPSEEK_API_KEY_ALSAY',
            'prompt': "解释敏捷开发方法论在项目管理中的应用。"
        },
        {
            'name': '数据库管理',
            'key_env': 'DEEPSEEK_API_KEY_AL',
            'prompt': "描述数据库索引的工作原理。"
        },
        {
            'name': '界面设计',
            'key_env': 'DEEPSEEK_API_KEY_SAY',
            'prompt': "提供用户界面设计的最佳实践列表。"
        }
    ]
    
    results = {}
    safe_print("\n=== 开始DeepSeek API测试 ===")
    
    for test_case in test_cases:
        safe_print(f"\n{'='*50}")
        api_key = os.getenv(test_case['key_env'])
        
        if not api_key:
            safe_print(f"✗ 错误: 未找到 {test_case['key_env']} 的API密钥")
            results[test_case['name']] = False
            continue
            
        # 确保API密钥是有效的字符串
        api_key = api_key.strip()
        if not api_key:
            safe_print(f"✗ 错误: {test_case['key_env']} 的API密钥为空")
            results[test_case['name']] = False
            continue
            
        try:
            success = test_api_instance(
                api_key=api_key,
                instance_name=test_case['name'],
                prompt=test_case['prompt']
            )
            results[test_case['name']] = success
        except Exception as e:
            safe_print(f"✗ 错误: 测试 {test_case['name']} 时发生错误: {str(e)}")
            results[test_case['name']] = False
            
        time.sleep(2)
        
    # 打印总结
    safe_print("\n=== 测试结果总结 ===")
    all_passed = True
    for name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        safe_print(f"{name}: {status}")
        all_passed = all_passed and success
        
    safe_print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")
    return all_passed

class TestDeepSeekAPI(unittest.TestCase):
    """测试DeepSeek API的功能"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        load_dotenv()
        # 尝试使用不同的API密钥
        api_keys = [
            os.getenv("DEEPSEEK_API_KEY_ALSAY"),  # 整体项目管理
            os.getenv("DEEPSEEK_API_KEY_AL"),     # 数据库管理
            os.getenv("DEEPSEEK_API_KEY_SAY"),    # UI界面管理
            os.getenv("DEEPSEEK_API_KEY_TEST")    # 测试专用
        ]
        
        # 找到第一个有效的API密钥
        for api_key in api_keys:
            if api_key:
                cls.test_api_key = api_key
                break
        
        if not cls.test_api_key:
            raise ValueError("未找到任何有效的API密钥环境变量")
        
        # 打印使用的API Key前8位，便于调试
        safe_print(f"DeepSeek API Key (前8位): {cls.test_api_key[:8]}")
        
        # 设置Base URL
        cls.base_url = "https://api.deepseek.com/v1"
        safe_print(f"Base URL: {cls.base_url}")
        
        # 初始化API管理器，使用最新的deepseek-chat模型
        cls.api = DeepLearningManager(cls.test_api_key, base_url=cls.base_url)

    def test_project_management(self):
        """测试项目管理相关的API调用"""
        try:
            prompt = "请帮我写一个Python项目的README.md文件，项目名称是'智能助手'，主要功能是通过API调用大语言模型来实现智能对话。"
            response = self.api.generate_content(prompt)
            self.assertIsNotNone(response, "API返回为空")
            safe_print("\n=== 项目管理API测试结果 ===")
            safe_print(response)
            safe_print("========================")
        except Exception as e:
            self.fail(f"项目管理API测试失败: {str(e)}")

    def test_database_management(self):
        """测试数据库管理相关的API调用"""
        try:
            prompt = "请帮我设计一个用于存储用户对话历史的MySQL数据库表结构。"
            response = self.api.generate_content(prompt)
            self.assertIsNotNone(response, "API返回为空")
            safe_print("\n=== 数据库管理API测试结果 ===")
            safe_print(response)
            safe_print("========================")
        except Exception as e:
            self.fail(f"数据库管理API测试失败: {str(e)}")

    def test_interface_design(self):
        """测试接口设计相关的API调用"""
        try:
            prompt = "请帮我设计一个RESTful API接口，用于实现用户注册和登录功能。"
            response = self.api.generate_content(prompt)
            self.assertIsNotNone(response, "API返回为空")
            safe_print("\n=== 接口设计API测试结果 ===")
            safe_print(response)
            safe_print("========================")
        except Exception as e:
            self.fail(f"接口设计API测试失败: {str(e)}")

if __name__ == '__main__':
    unittest.main()