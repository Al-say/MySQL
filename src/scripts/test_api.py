import sys
import os
import logging
import asyncio
from dotenv import load_dotenv
import traceback
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.services.deep_learning_manager import DeepLearningManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api():
    """测试API连接"""
    try:
        # 初始化 DeepLearningManager
        dl_manager = DeepLearningManager(api_key_type='ALSAY')
        
        # 准备测试消息
        messages = [
            {"role": "system", "content": "You are a MySQL expert. Be concise and precise."},
            {"role": "user", "content": """Generate a MySQL multiple-choice question about Index Optimization.
Format:
{
    "content": "Brief, clear question",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A/B/C/D",
    "explanation": "Brief explanation",
    "doc_reference": "MySQL doc reference",
    "version_info": "MySQL version"
}"""}
        ]
        
        # 调用API
        response = await dl_manager.generate_content(messages)
        
        if response:
            logger.info("API测试成功!")
            logger.info(f"原始响应: {response}")
            try:
                # 尝试解析JSON
                question = json.loads(response)
                logger.info("JSON格式正确!")
                logger.info(f"问题内容: {question['content']}")
                logger.info(f"选项: {question['options']}")
                logger.info(f"正确答案: {question['correct_answer']}")
                logger.info(f"解释: {question['explanation']}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
        else:
            logger.error("API返回空响应")
            
    except Exception as e:
        logger.error(f"API测试失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_api()) 