import sys
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import PracticeSystem

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('practice_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.debug("正在初始化应用程序...")
        app = QApplication(sys.argv)
        
        logger.debug("正在创建主窗口...")
        window = PracticeSystem()
        
        logger.debug("正在显示主窗口...")
        window.show()
        
        logger.debug("开始事件循环...")
        return app.exec()
    except KeyboardInterrupt:
        logger.info("\n程序继续运行中...")
        return 0
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main()) 