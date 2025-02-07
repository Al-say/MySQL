import logging
from typing import Optional, Dict, Any, List
from .deep_learning_manager import DeepLearningManager

logger = logging.getLogger(__name__)

class ProjectManager:
    """项目管理器，负责整体项目的管理和协调"""
    
    def __init__(self):
        """初始化项目管理器"""
        self.dl_manager = DeepLearningManager(api_key_type='ALSAY')
        
    async def generate_project_plan(self, project_name: str, description: str) -> Optional[Dict[str, Any]]:
        """生成项目计划
        
        Args:
            project_name: 项目名称
            description: 项目描述
            
        Returns:
            Optional[Dict[str, Any]]: 项目计划，包含任务列表、时间线等
        """
        prompt = f"""请为以下项目生成一个详细的项目计划：

项目名称：{project_name}
项目描述：{description}

请包含以下内容：
1. 项目目标和范围
2. 主要任务分解
3. 时间线规划
4. 资源需求
5. 风险评估

输出格式：
{{
    "project_goals": ["目标1", "目标2", ...],
    "tasks": [
        {{
            "name": "任务名称",
            "description": "任务描述",
            "duration": "预计时长",
            "dependencies": ["依赖任务1", "依赖任务2"]
        }},
        ...
    ],
    "timeline": {{
        "start_date": "开始日期",
        "end_date": "结束日期",
        "milestones": [
            {{
                "name": "里程碑名称",
                "date": "预计日期",
                "deliverables": ["交付物1", "交付物2"]
            }},
            ...
        ]
    }},
    "resources": [
        {{
            "type": "资源类型",
            "name": "资源名称",
            "quantity": "数量"
        }},
        ...
    ],
    "risks": [
        {{
            "description": "风险描述",
            "impact": "影响程度",
            "probability": "发生概率",
            "mitigation": "缓解措施"
        }},
        ...
    ]
}}"""
        
        try:
            response = await self.dl_manager.generate_content(prompt)
            if response:
                return response
            logger.error("生成项目计划失败：API返回空响应")
            return None
        except Exception as e:
            logger.error(f"生成项目计划时发生错误: {str(e)}")
            return None
            
    async def analyze_project_status(self, project_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析项目状态
        
        Args:
            project_data: 项目数据，包含任务完成情况、资源使用情况等
            
        Returns:
            Optional[Dict[str, Any]]: 项目状态分析结果
        """
        prompt = f"""请分析以下项目的当前状态：

项目数据：
{project_data}

请提供以下分析：
1. 项目进度评估
2. 资源使用情况
3. 风险状态
4. 问题和建议

输出格式：
{{
    "progress_status": {{
        "overall_progress": "整体进度百分比",
        "on_track": true/false,
        "delay_reasons": ["原因1", "原因2"]
    }},
    "resource_usage": {{
        "utilization": "资源利用率",
        "bottlenecks": ["瓶颈1", "瓶颈2"]
    }},
    "risk_status": [
        {{
            "risk": "风险描述",
            "status": "状态",
            "action_needed": "需要采取的行动"
        }},
        ...
    ],
    "recommendations": [
        {{
            "issue": "问题描述",
            "recommendation": "建议",
            "priority": "优先级"
        }},
        ...
    ]
}}"""
        
        try:
            response = await self.dl_manager.generate_content(prompt)
            if response:
                return response
            logger.error("分析项目状态失败：API返回空响应")
            return None
        except Exception as e:
            logger.error(f"分析项目状态时发生错误: {str(e)}")
            return None
            
    async def generate_project_report(self, project_data: Dict[str, Any], report_type: str) -> Optional[str]:
        """生成项目报告
        
        Args:
            project_data: 项目数据
            report_type: 报告类型（'weekly', 'monthly', 'status'）
            
        Returns:
            Optional[str]: 格式化的项目报告
        """
        prompt = f"""请根据以下项目数据生成一份{report_type}报告：

项目数据：
{project_data}

请包含以下内容：
1. 报告摘要
2. 主要成就
3. 关键指标
4. 问题和风险
5. 下一步计划

输出格式：使用Markdown格式"""
        
        try:
            response = await self.dl_manager.generate_content(prompt)
            if response:
                return response
            logger.error("生成项目报告失败：API返回空响应")
            return None
        except Exception as e:
            logger.error(f"生成项目报告时发生错误: {str(e)}")
            return None 