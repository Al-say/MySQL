import mysql.connector
from mysql.connector import Error, errorcode
import logging
from typing import List, Tuple, Any, Optional, Dict
from ..config.constants import Constants
from ..utils.cache import Cache

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理类"""
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.cache = Cache()
        
    def connect(self) -> bool:
        """连接数据库"""
        try:
            if self.conn:
                self.close()
                
            self.conn = mysql.connector.connect(**Constants.DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            logger.info("数据库连接成功")
            return True
            
        except mysql.connector.Error as e:
            error_msg = self.get_error_message(e)
            logger.error(f"数据库连接失败: {error_msg}")
            return False
            
    def close(self) -> None:
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接时出错: {e}")
            
    @staticmethod
    def get_error_message(error: mysql.connector.Error) -> str:
        """获取数据库错误信息"""
        error_messages = {
            errorcode.ER_ACCESS_DENIED_ERROR: "数据库用户名或密码错误",
            errorcode.ER_BAD_DB_ERROR: "数据库不存在",
            1370: "存储过程访问被拒绝",  # ER_PROC_ACCESS_DENIED
            1305: "存储过程不存在"  # ER_SP_DOES_NOT_EXIST
        }
        return error_messages.get(error.errno, str(error))
        
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """执行查询"""
        try:
            if not self.conn or not self.conn.is_connected():
                if not self.connect():
                    return None
                    
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except mysql.connector.Error as e:
            logger.error(f"执行查询失败: {self.get_error_message(e)}")
            return None
            
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """执行事务"""
        try:
            if not self.conn or not self.conn.is_connected():
                if not self.connect():
                    return False
                    
            self.conn.start_transaction()
            for query, params in queries:
                self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except mysql.connector.Error as e:
            self.conn.rollback()
            logger.error(f"执行事务失败: {self.get_error_message(e)}")
            return False 

    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """执行查询并返回单条记录"""
        try:
            if not self.conn or not self.conn.is_connected():
                if not self.connect():
                    return None
                    
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result
        except mysql.connector.Error as e:
            logger.error(f"执行查询失败: {self.get_error_message(e)}")
            return None

    def insert(self, query: str, params: tuple = None) -> Optional[int]:
        """执行插入操作并返回最后插入的ID"""
        try:
            if not self.conn or not self.conn.is_connected():
                if not self.connect():
                    return None
                    
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except mysql.connector.Error as e:
            logger.error(f"执行插入失败: {self.get_error_message(e)}")
            return None 