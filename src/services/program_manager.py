import logging
from typing import Optional, Dict, Any, List
from .deep_learning_manager import DeepLearningManager

logger = logging.getLogger(__name__)

class ProgramManager:
    """程序管理器，负责程序功能和界面的管理"""
    
    def __init__(self):
        """初始化程序管理器"""
        self.dl_manager = DeepLearningManager(api_key_type='SAY')
        
    async def analyze_code(self, code: str, language: str) -> Optional[Dict[str, Any]]:
        """分析代码
        
        Args:
            code: 源代码
            language: 编程语言
            
        Returns:
            Optional[Dict[str, Any]]: 代码分析结果
        """
        prompt = f"""请分析以下{language}代码：

源代码：
{code}

请提供以下分析：
1. 代码结构和功能
2. 代码质量评估
3. 潜在问题
4. 改进建议

输出格式：
{{
    "code_analysis": {{
        "structure": {{
            "components": ["组件1", "组件2"],
            "dependencies": ["依赖1", "依赖2"],
            "main_functions": ["函数1", "函数2"]
        }},
        "functionality": {{
            "purpose": "代码目的",
            "features": ["功能1", "功能2"],
            "limitations": ["限制1", "限制2"]
        }}
    }},
    "quality_assessment": {{
        "readability": "可读性评分",
        "maintainability": "可维护性评分",
        "complexity": "复杂度评分",
        "test_coverage": "测试覆盖率建议"
    }},
    "issues": [
        {{
            "type": "问题类型",
            "description": "问题描述",
            "severity": "严重程度",
            "location": "问题位置"
        }},
        ...
    ],
    "recommendations": [
        {{
            "category": "改进类别",
            "suggestion": "改进建议",
            "benefit": "预期收益",
            "effort": "实施难度"
        }},
        ...
    ]
}}"""
        
        try:
            response = await self.dl_manager.generate_content(prompt)
            if response:
                return response
            logger.error("分析代码失败：API返回空响应")
            return None
        except Exception as e:
            logger.error(f"分析代码时发生错误: {str(e)}")
            return None
            
    async def generate_code(self, requirements: str, language: str) -> Optional[Dict[str, Any]]:
        """生成代码
        
        Args:
            requirements: 需求描述
            language: 编程语言
            
        Returns:
            Optional[Dict[str, Any]]: 生成的代码和说明
        """
        prompt = f"""请根据以下需求生成{language}代码：

需求描述：
{requirements}

请提供：
1. 完整的代码实现
2. 代码说明
3. 使用示例
4. 测试用例

输出格式：
{{
    "code": {{
        "implementation": "源代码",
        "imports": ["导入1", "导入2"],
        "dependencies": ["依赖1", "依赖2"]
    }},
    "documentation": {{
        "description": "代码说明",
        "parameters": [
            {{
                "name": "参数名",
                "type": "参数类型",
                "description": "参数说明"
            }},
            ...
        ],
        "returns": {{
            "type": "返回类型",
            "description": "返回值说明"
        }},
        "examples": [
            {{
                "description": "示例说明",
                "code": "示例代码",
                "output": "预期输出"
            }},
            ...
        ]
    }},
    "tests": [
        {{
            "name": "测试名称",
            "input": "测试输入",
            "expected": "预期输出",
            "description": "测试说明"
        }},
        ...
    ]
}}"""
        
        try:
            response = await self.dl_manager.generate_content(prompt)
            if response:
                return response
            logger.error("生成代码失败：API返回空响应")
            return None
        except Exception as e:
            logger.error(f"生成代码时发生错误: {str(e)}")
            return None
            
    async def refactor_code(self, code: str, requirements: str) -> Optional[Dict[str, Any]]:
        """重构代码
        
        Args:
            code: 原始代码
            requirements: 重构需求
            
        Returns:
            Optional[Dict[str, Any]]: 重构后的代码和说明
        """
        prompt = f"""请根据以下需求重构代码：

原始代码：
{code}

重构需求：
{requirements}

请提供：
1. 重构后的代码
2. 重构说明
3. 改进对比

输出格式：
{{
    "refactored_code": {{
        "implementation": "重构后的代码",
        "changes": [
            {{
                "type": "修改类型",
                "description": "修改说明",
                "before": "修改前代码",
                "after": "修改后代码"
            }},
            ...
        ]
    }},
    "improvements": [
        {{
            "aspect": "改进方面",
            "description": "改进说明",
            "metrics": {{
                "before": "改进前指标",
                "after": "改进后指标"
            }}
        }},
        ...
    ],
    "migration_guide": {{
        "steps": [
            {{
                "step": "步骤说明",
                "details": "具体操作",
                "warnings": ["注意事项1", "注意事项2"]
            }},
            ...
        ],
        "breaking_changes": ["不兼容变更1", "不兼容变更2"]
    }}
}}"""
        
        try:
            response = await self.dl_manager.generate_content(prompt)
            if response:
                return response
            logger.error("重构代码失败：API返回空响应")
            return None
        except Exception as e:
            logger.error(f"重构代码时发生错误: {str(e)}")
            return None 