import sys
import os
import logging
from typing import Optional, Dict, Any
import asyncio
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.services.deep_learning_manager import DeepLearningManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ask_api_for_guidance() -> Optional[Dict[str, Any]]:
    """向API询问项目开发指导建议"""
    dl_manager = DeepLearningManager(api_key_type='ALSAY')
    
    prompt = """作为项目开发顾问，请为MySQL答题系统提供开发建议。

背景：这是一个个人使用的MySQL答题系统，用于自测MySQL知识，需要题目管理和答题功能，不需要登录注册。

请提供以下方面的建议：

1. 项目概述
   - 项目描述和目标
   - 核心功能列表
   - 技术栈选择及理由

2. 系统架构
   - 主要模块及其功能
   - 系统数据流程

3. 数据库设计
   - 主要数据表结构
   - 字段设计
   - 索引优化建议

4. 开发步骤
   - 优先级排序
   - 具体任务列表
   - 时间估算

5. 测试策略
   - 单元测试要点
   - 集成测试场景
   - 性能测试指标

6. 可能的挑战
   - 技术难点
   - 解决方案

请提供详细且可执行的建议。"""

    try:
        response = await dl_manager.generate_content(prompt)
        if response:
            logger.info("成功获取API建议")
            return response
        logger.error("获取API建议失败：API返回空响应")
        return None
    except Exception as e:
        logger.error(f"获取API建议时发生错误: {str(e)}")
        return None

async def main():
    """主函数"""
    logger.info("开始询问API获取项目开发指导...")
    guidance = await ask_api_for_guidance()
    
    if guidance:
        logger.info("\nAPI提供的建议：")
        logger.info("=" * 80)
        logger.info(guidance)
        logger.info("=" * 80)
    else:
        logger.error("未能获取API建议")

if __name__ == "__main__":
    asyncio.run(main()) 