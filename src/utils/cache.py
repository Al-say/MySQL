import json
from datetime import datetime
from typing import Any, Optional
import logging
from src.config.constants import Constants

logger = logging.getLogger(__name__)

class Cache:
    """缓存管理类"""
    def __init__(self, cache_dir = Constants.CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
            
        try:
            data = json.loads(cache_file.read_text(encoding='utf-8'))
            # 检查缓存是否过期
            if datetime.now().timestamp() - data['timestamp'] > Constants.CACHE_DURATION:
                cache_file.unlink()
                return None
            return data['value']
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return None
            
    def set(self, key: str, value: Any) -> None:
        """设置缓存数据"""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            data = {
                'timestamp': datetime.now().timestamp(),
                'value': value
            }
            cache_file.write_text(json.dumps(data), encoding='utf-8')
        except Exception as e:
            logger.error(f"写入缓存失败: {e}")
            
    def clear(self) -> None:
        """清除所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"清除缓存失败: {e}") 