from openai import OpenAI
import numpy as np
import requests
import logging
import re
from typing import Tuple, Dict, Optional, Union, Any, List
import time
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
import os
import urllib3
from dotenv import load_dotenv
import json
import httpx
from httpx import Timeout, Limits
import backoff
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential
import sys
import codecs
import io
import aiohttp
import asyncio
import traceback

# 加载环境变量
load_dotenv(override=True)

# 确保所有输出使用UTF-8编码
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s'),
    datefmt=os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S'),
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'deep_learning.log'), encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_proxy_availability(proxy: str, timeout: int = 5) -> bool:
    """检查代理服务器是否可用"""
    try:
        # 从代理URL中提取主机和端口
        if proxy.startswith('http://'):
            proxy = proxy[7:]
        elif proxy.startswith('https://'):
            proxy = proxy[8:]
        
        host, port = proxy.split(':')
        port = int(port)
        
        # 尝试建立连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        return result == 0
    except Exception as e:
        logger.warning(f"检查代理可用性时出错: {str(e)}")
        return False

def encode_text(obj: Any) -> Any:
    """
    确保所有文本使用UTF-8编码
    
    Args:
        obj: 需要编码的对象
        
    Returns:
        Any: 编码后的对象
    """
    try:
        if obj is None:
            return None
            
        if isinstance(obj, (int, float, bool)):
            return obj
            
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
            
        if isinstance(obj, str):
            # 直接返回字符串，不进行额外的编码转换
            return obj
                
        if isinstance(obj, dict):
            return {encode_text(k): encode_text(v) for k, v in obj.items()}
            
        if isinstance(obj, (list, tuple)):
            return [encode_text(item) for item in obj]
            
        # 其他类型转换为字符串
        return str(obj)
        
    except Exception as e:
        logger.error(f"编码转换失败: {str(e)}")
        return str(obj)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    安全地将对象转换为JSON字符串
    
    Args:
        obj: 要转换的对象
        **kwargs: 传递给json.dumps的额外参数
        
    Returns:
        str: JSON字符串
    """
    try:
        # 首先确保所有文本都正确编码
        encoded_obj = encode_text(obj)
        
        # 设置默认参数
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('default', str)
        
        # 转换为JSON字符串
        return json.dumps(encoded_obj, **kwargs)
    except Exception as e:
        logger.error(f"JSON序列化失败: {str(e)}")
        # 如果失败，尝试转换为字符串后再序列化
        return json.dumps(str(obj), ensure_ascii=False)

def safe_json_loads(text: Union[str, bytes], **kwargs) -> Optional[Any]:
    """
    安全地解析JSON字符串
    
    Args:
        text: JSON字符串或字节
        **kwargs: 传递给json.loads的额外参数
        
    Returns:
        Optional[Any]: 解析后的对象，失败时返回None
    """
    try:
        # 如果输入是字节，先解码
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
            
        # 解析JSON
        result = json.loads(text, **kwargs)
        
        # 确保结果中的所有文本都正确编码
        return encode_text(result)
    except Exception as e:
        logger.error(f"JSON解析失败: {str(e)}")
        return None

class DeepLearningManager:
    """深度学习管理器，负责与API交互"""
    
    API_KEY_FUNCTIONS = {
        'ALSAY': 'project_management',  # 整体项目管理
        'AL': 'database',               # 数据库相关
        'SAY': 'ui',                    # 界面UI
        'TEST': 'testing'               # 测试功能
    }
    
    def __init__(self, api_key_type: str = 'ALSAY', base_url: Optional[str] = None):
        """初始化深度学习管理器"""
        # 获取API密钥
        api_key = os.getenv(f'DEEPSEEK_API_KEY_{api_key_type}')
        if not api_key:
            raise ValueError(f"未找到{api_key_type}的API密钥")
            
        # 清理API密钥（移除注释和空白字符）
        self.api_key = api_key.split('#')[0].strip()
        
        # 验证API密钥格式
        if not self.api_key.startswith('sk-'):
            raise ValueError(f"API密钥格式不正确: {self.api_key[:8]}...")
            
        # 设置基础URL
        self.base_url = base_url or os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        
        # 设置功能领域
        self.function = self.API_KEY_FUNCTIONS.get(api_key_type, 'general')
        
        # 初始化API客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
    def generate_content_sync(self, messages: Union[str, List[Dict[str, str]]], max_retries: Optional[int] = None) -> Optional[str]:
        """同步方式生成内容"""
        # 如果messages是字符串，转换为消息列表
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
            
        # 获取重试次数
        max_retries = max_retries or int(os.getenv('API_MAX_RETRIES', 1))
        retry_delay = int(os.getenv('API_RETRY_DELAY', 10))
        timeout = int(os.getenv('API_TIMEOUT', 1800))  # 30分钟超时
        
        # 获取模型配置
        model = os.getenv('MODEL_NAME', 'deepseek-chat')
        temperature = float(os.getenv('MODEL_TEMPERATURE', 0.7))
        max_tokens = int(os.getenv('MODEL_MAX_TOKENS', 1024))
        top_p = float(os.getenv('MODEL_TOP_P', 0.9))
        frequency_penalty = float(os.getenv('MODEL_FREQUENCY_PENALTY', 0.1))
        presence_penalty = float(os.getenv('MODEL_PRESENCE_PENALTY', 0.1))
        
        # 准备请求数据
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": False
        }
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 记录请求信息
        logger.info(f"使用的API Key前8位: {self.api_key[:8]}")
        logger.info(f"使用的Base URL: {self.base_url}")
        logger.info(f"使用的模型: {model}")
        logger.info(f"请求头: {headers}")
        logger.info(f"请求数据模型: {model}")
        logger.info(f"请求消息数量: {len(messages)}")
        logger.info(f"请求消息预览: {messages[0]}")
        
        # 创建Session并配置重试
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        try:
            # 发送请求
            response = session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=request_data,
                timeout=timeout,
                verify=False,  # 禁用SSL验证
                stream=True  # 使用流式响应以处理空行
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                logger.error(f"错误响应: {response.text}")
                return None
                
            # 读取并处理响应内容
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:  # 跳过空行
                    if line.startswith(":"):  # 跳过 SSE keep-alive 注释
                        continue
                    full_response += line + "\n"
                    
            # 解析响应
            try:
                if not full_response.strip():
                    logger.error("API返回空响应")
                    return None
                    
                response_data = json.loads(full_response)
                logger.info(f"API响应数据: {json.dumps(response_data, ensure_ascii=False)[:200]}...")
                if response_data and 'choices' in response_data and response_data['choices']:
                    content = response_data['choices'][0]['message']['content']
                    logger.info(f"API响应内容: {content[:200]}...")  # 只打印前200个字符
                    return content
                else:
                    logger.error(f"API响应格式不正确: {json.dumps(response_data, ensure_ascii=False)}")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                logger.error(f"原始响应: {full_response}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return None
        except Exception as e:
            logger.error(f"API请求失败 ({self.function}): {str(e)}")
            return None
        finally:
            session.close()
            
    async def generate_content(self, messages: Union[str, List[Dict[str, str]]], max_retries: Optional[int] = None) -> Optional[str]:
        """异步包装同步方法"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_content_sync, messages, max_retries)
            
    def get_text_embedding(self, text: str) -> np.ndarray:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            np.ndarray: 文本的嵌入向量
        """
        try:
            response = self.client.embeddings.create(
                model="deepseek-chat",
                input=text
            )
            
            if response and response.data:
                return np.array(response.data[0]['embedding'])
            return np.zeros(1024)  # 返回零向量作为默认值
            
        except Exception as e:
            self.logger.error(f"获取文本嵌入失败: {str(e)}")
            return np.zeros(1024)
            
    def evaluate_answer(self, student_answer: str, correct_answer: str) -> Tuple[float, str]:
        """
        评估学生答案
        
        Args:
            student_answer: 学生的答案
            correct_answer: 正确答案
            
        Returns:
            Tuple[float, str]: (得分, 反馈意见)
        """
        try:
            prompt = f"""请评估以下答案的正确性：

正确答案：
{correct_answer}

学生答案：
{student_answer}

请提供：
1. 0-1之间的分数
2. 详细的评分反馈

输出格式：
分数: 0.x
反馈: 你的反馈内容"""
            
            response = self.generate_content(prompt)
            if not response:
                return 0.0, "评估失败"
                
            # 解析响应
            try:
                score_match = re.search(r'分数:\s*(0\.\d+|1\.0|1|0)', response)
                feedback_match = re.search(r'反馈:\s*(.+)', response, re.DOTALL)
                
                score = float(score_match.group(1)) if score_match else 0.0
                feedback = feedback_match.group(1).strip() if feedback_match else "无反馈"
                
                return score, feedback
            except Exception as e:
                self.logger.error(f"解析评估结果失败: {str(e)}")
                return 0.0, "解析评估结果失败"
                
        except Exception as e:
            self.logger.error(f"评估答案失败: {str(e)}")
            return 0.0, f"评估失败: {str(e)}"
            
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'client'):
            pass 