import logging
logging.basicConfig(level=logging.INFO)
from config import config

def config_change_listener(event):
    logging.info(f"配置变更: 组={event.group}, 键={event.key}")
    logging.info(f"原值: {event.old_value}")
    logging.info(f"新值: {event.new_value}")

def test_config():
    # 建议：使用 logging 替换 print
    logging.info("=== 基本配置测试 ===")
    logging.info(f"数据库 URL: {config.db_url}")
    logging.info(f"当前主题: {config.get_value('ui', 'theme')}")
    
    logging.info("=== 配置更新测试 ===")
    config.add_listener(config_change_listener)
    config.update_config('ui', 'theme', 'dark')
    
    logging.info("=== 配置加密测试 ===")
    try:
        config.set_encryption_key("YourSecretKey12345678901234567890123=")
        config.update_config('database', 'password', 'test_password')
        encrypted_config = config.get_config_group('database')
        logging.info(f"加密后的配置: {encrypted_config}")
    except Exception as e:
        logging.error(f"加密测试失败: {e}")
    
    logging.info("=== 配置导出导入测试 ===")
    try:
        config.export_to_file('test_config_export.json')
        logging.info("配置已导出")
        
        old_theme = config.get_value('ui', 'theme')
        config.update_config('ui', 'theme', 'light')
        config.import_from_file('test_config_export.json')
        logging.info(f"配置已导入，主题从 {old_theme} 恢复为 {config.get_value('ui', 'theme')}")
    except Exception as e:
        logging.error(f"导出导入测试失败: {e}")
    
    logging.info("=== 新配置组测试 ===")
    try:
        config.create_group('email', {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587
        })
        logging.info("邮件配置组创建成功")
        logging.info(f"SMTP服务器: {config.get_value('email', 'smtp_server')}")
    except Exception as e:
        logging.error(f"创建配置组失败: {e}")

if __name__ == "__main__":
    test_config()
