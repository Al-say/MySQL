"""
MySQL练习系统测试包
包含单元测试、集成测试和性能测试
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root) 