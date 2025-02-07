import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
from dataclasses import dataclass
import logging
from datetime import datetime

class ConfigError(Exception):
    """配置相关的基础异常类"""
    pass

class ConfigValidationError(ConfigError):
    """配置验证异常"""
    pass

class ConfigEncryptionError(ConfigError):
    """配置加密/解密异常"""
    pass

# 默认配置常量
DEFAULT_CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'name': 'mysql_practice'
    },
    'api': {
        'deepseek_key': None,
        'deepseek_url': None
    },
    'system': {
        'log_level': 'INFO',
        'log_file': 'app.log'
    },
    'ui': {
        'theme': 'light',
        'font_size': 12
    }
}

class ConfigChangeEvent:
    def __init__(self, group: str, key: str, old_value: Any, new_value: Any):
        self.group = group
        self.key = key
        self.old_value = old_value
        self.new_value = new_value

class ConfigMigration:
    """配置版本迁移处理器"""
    def __init__(self, old_version: str, new_version: str):
        self.old_version = old_version
        self.new_version = new_version
        
    def migrate(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行配置迁移"""
        # 在这里实现具体的迁移逻辑
        return config_data

class Config:
    VERSION = "1.0.0"
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._listeners: List[Callable[[ConfigChangeEvent], None]] = []
        self._encryption_key: Optional[bytes] = None
        self._config_file = Path(__file__).parent / 'config.json'
        self._load_env()
        self._init_configs()
        self._load_saved_config()
        self._validate_configs()

    def _load_env(self) -> None:
        env_path = Path(__file__).parent.parent.parent / '.env'
        if (env_path.exists()):
            load_dotenv(env_path)

    def _init_configs(self) -> None:
        # 数据库配置组
        self.database = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'name': os.getenv('DB_NAME', 'mysql_practice'),
        }

        # API 配置组
        self.api = {
            'deepseek_key': os.getenv('DEEPSEEK_API_KEY'),
            'deepseek_url': os.getenv('DEEPSEEK_API_URL'),
        }

        # 系统配置组
        self.system = {
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE', 'app.log'),
        }

        # UI 配置组
        self.ui = {
            'theme': os.getenv('THEME', 'light'),
            'font_size': int(os.getenv('FONT_SIZE', 12)),
        }

    def _load_saved_config(self) -> None:
        """从文件加载保存的配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                if saved_config.get('version') == self.VERSION:
                    self.from_dict(saved_config.get('data', {}))
            except Exception as e:
                self._logger.error(f"加载配置文件失败: {e}")

    def save_config(self) -> None:
        """保存配置到文件，采用原子写入方式"""
        try:
            config_data = {
                'version': self.VERSION,
                'data': self.to_dict()
            }
            temp_file = self._config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self._config_file)
        except Exception as e:
            raise RuntimeError(f"保存配置文件失败: {e}")

    def add_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """添加配置变更监听器"""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """移除配置变更监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def set_encryption_key(self, key: str) -> None:
        """设置配置加密密钥"""
        try:
            if key:
                # 建议：检查密钥长度或格式，或考虑使用 Fernet.generate_key() 自动生成密钥
                if len(key.encode()) != 32:
                    raise ConfigEncryptionError("加密密钥必须是32字节长")
                test_fernet = Fernet(key.encode())
                self._encryption_key = key.encode()
            else:
                self._encryption_key = None
        except Exception as e:
            raise ConfigEncryptionError(f"无效的加密密钥: {e}")

    def _validate_configs(self) -> None:
        """验证配置有效性"""
        try:
            # 数据库配置验证
            if not all(k in self.database for k in ['host', 'port', 'user', 'password', 'name']):
                raise ConfigValidationError("数据库配置缺少必要字段")
            
            if not isinstance(self.database['port'], int):
                raise ConfigValidationError("数据库端口必须是整数")
            
            if not isinstance(self.database['host'], str):
                raise ConfigValidationError("数据库主机必须是字符串")

            # API配置验证
            if self.api.get('deepseek_key') and not isinstance(self.api['deepseek_key'], str):
                raise ConfigValidationError("API密钥必须是字符串")

            # UI配置验证
            if not isinstance(self.ui['font_size'], int):
                raise ConfigValidationError("字体大小必须是整数")
            
            if self.ui['theme'] not in ['light', 'dark']:
                raise ConfigValidationError("主题必须是 'light' 或 'dark'")

        except KeyError as e:
            raise ConfigValidationError(f"缺少必要的配置项: {e}")
        except Exception as e:
            raise ConfigValidationError(f"配置验证失败: {e}")

    @property
    def db_url(self) -> str:
        db = self.database
        return f"mysql+pymysql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"

    def get_config_group(self, group: str) -> Dict[str, Any]:
        """获取解密后的配置组"""
        config_group = getattr(self, group, {})
        if self._encryption_key:
            return {k: self._decrypt_value(v) for k, v in config_group.items()}
        return config_group.copy()

    def update_config(self, group: str, key: str, value: Any) -> None:
        """更新配置项并触发变更事件"""
        config_group = getattr(self, group, None)
        if config_group is None:
            raise ConfigError(f"配置组 {group} 不存在")
        if key not in config_group:
            raise ConfigError(f"配置项 {key} 在组 {group} 中不存在")
        
        try:
            old_value = config_group[key]
            config_group[key] = value
            self._validate_configs()  # 验证新配置是否有效
            
            event = ConfigChangeEvent(group, key, old_value, value)
            self._notify_listeners(event)
            
            self.save_config()
        except Exception as e:
            # 恢复原值
            config_group[key] = old_value
            raise ConfigError(f"更新配置失败: {e}")

    def _notify_listeners(self, event: ConfigChangeEvent) -> None:
        """通知所有配置变更监听器"""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                self._logger.error(f"配置变更监听器执行失败: {e}")

    def _encrypt_value(self, value: str) -> str:
        """加密配置值"""
        if not self._encryption_key or not isinstance(value, str):
            return value
        try:
            f = Fernet(self._encryption_key)
            return f.encrypt(value.encode()).decode()
        except Exception as e:
            raise ConfigEncryptionError(f"加密失败: {e}")

    def _decrypt_value(self, value: str) -> str:
        """解密配置值"""
        if not self._encryption_key or not isinstance(value, str):
            return value
        try:
            f = Fernet(self._encryption_key)
            return f.decrypt(value.encode()).decode()
        except Exception as e:
            self._logger.warning(f"解密失败: {e}")
            return value

    def to_dict(self) -> Dict[str, Any]:
        """导出配置为字典"""
        return {
            'database': self.database,
            'api': self.api,
            'system': self.system,
            'ui': self.ui
        }

    def to_json(self) -> str:
        """导出配置为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2)

    def from_dict(self, config_dict: Dict[str, Any]) -> None:
        """从字典导入配置"""
        for group, values in config_dict.items():
            if hasattr(self, group):
                current_group = getattr(self, group)
                current_group.update(values)

    def reset_to_default(self, group: Optional[str] = None) -> None:
        """重置配置到默认值"""
        if group:
            if group in DEFAULT_CONFIG:
                setattr(self, group, DEFAULT_CONFIG[group].copy())
        else:
            self._init_configs()

    def get_value(self, group: str, key: str, default: Any = None, value_type: Optional[type] = None) -> Any:
        """获取配置值，支持默认值和类型转换"""
        try:
            value = getattr(self, group, {})[key]
            if value is None:
                return default
            if value_type:
                return value_type(value)
            return value
        except (KeyError, ValueError, TypeError):
            return default
            
    def export_to_file(self, filepath: str) -> None:
        """导出配置到指定文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': self.VERSION,
                    'data': self.to_dict(),
                    'export_time': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigError(f"导出配置失败: {e}")
            
    def import_from_file(self, filepath: str) -> None:
        """从文件导入配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('version') != self.VERSION:
                    migration = ConfigMigration(data.get('version'), self.VERSION)
                    data['data'] = migration.migrate(data.get('data', {}))
                self.from_dict(data.get('data', {}))
                self._validate_configs()
                self.save_config()
        except Exception as e:
            raise ConfigError(f"导入配置失败: {e}")
            
    def get_groups(self) -> List[str]:
        """获取所有配置组名称"""
        return [g for g in DEFAULT_CONFIG.keys()]
        
    def has_group(self, group: str) -> bool:
        """检查配置组是否存在"""
        return group in self.get_groups()
        
    def create_group(self, group: str, default_values: Dict[str, Any]) -> None:
        """创建新的配置组"""
        if self.has_group(group):
            raise ConfigError(f"配置组 {group} 已存在")
        setattr(self, group, default_values.copy())
        DEFAULT_CONFIG[group] = default_values.copy()

# 建议：将加密 / 解密逻辑封装到单独的类中，以提高代码复用性和可测试性
class EncryptionHelper:
    @staticmethod
    def encrypt_value(key: bytes, value: str) -> str:
        try:
            f = Fernet(key)
            return f.encrypt(value.encode()).decode()
        except Exception as e:
            raise ConfigEncryptionError(f"加密失败: {e}")
            
    @staticmethod
    def decrypt_value(key: bytes, value: str) -> str:
        try:
            f = Fernet(key)
            return f.decrypt(value.encode()).decode()
        except Exception as e:
            logging.getLogger(__name__).warning(f"解密失败: {e}")
            return value

config = Config()
