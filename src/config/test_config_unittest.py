import os
import json
import unittest
from config import config, ConfigError, ConfigEncryptionError

class TestConfig(unittest.TestCase):
    def setUp(self):
        # 重置配置到默认状态
        config.reset_to_default()
        # 临时导出文件
        self.export_file = 'temp_config_export.json'
        # 清除已有监听器
        config._listeners.clear()

    def tearDown(self) -> None:
        # 清理导出的测试文件
        if os.path.exists(self.export_file):
            os.remove(self.export_file)
        # 清除加密密钥，避免全局状态副作用
        config.set_encryption_key("")

    def test_basic_config(self):
        # 测试基础配置加载
        self.assertIn('database', config.to_dict())
        self.assertEqual(config.get_value('ui', 'theme'), 'light')
        self.assertTrue(isinstance(config.db_url, str))

    def test_update_config(self):
        # 测试配置更新并触发监听器
        events = []
        def listener(e):
            events.append(e)
        config.add_listener(listener)
        old_theme = config.get_value('ui', 'theme')
        config.update_config('ui', 'theme', 'dark')
        self.assertEqual(config.get_value('ui', 'theme'), 'dark')
        self.assertGreater(len(events), 0)
        # 恢复配置
        config.update_config('ui', 'theme', old_theme)

    def test_encryption(self):
        # 测试设置加密密钥与加密/解密操作
        try:
            config.set_encryption_key("YourSecretKey12345678901234567890123=")
        except ConfigEncryptionError as e:
            self.fail(f"设置加密密钥失败: {e}")
        config.update_config('database', 'password', 'test_password')
        encrypted = config.get_config_group('database')['password']
        self.assertIn('test_password', config._decrypt_value(encrypted))

    def test_export_import(self):
        # 测试导出与导入配置
        config.update_config('ui', 'theme', 'dark')
        config.export_to_file(self.export_file)
        # 修改后导入
        config.update_config('ui', 'theme', 'light')
        config.import_from_file(self.export_file)
        self.assertEqual(config.get_value('ui', 'theme'), 'dark')

    def test_create_group(self):
        # 测试新配置组的创建与获取
        new_group = 'email'
        defaults = {'smtp_server': 'smtp.example.com', 'smtp_port': 587}
        config.create_group(new_group, defaults)
        self.assertEqual(config.get_value(new_group, 'smtp_server'), defaults['smtp_server'])
        with self.assertRaises(ConfigError):
            config.create_group(new_group, defaults)

if __name__ == '__main__':
    unittest.main()
