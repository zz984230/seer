import logging
from logging.handlers import RotatingFileHandler
import os
from config import settings

class Logger:
    def __init__(self):
        self.logger = logging.getLogger("seer")
        self.setup_logger()
    
    def setup_logger(self):
        # 获取日志配置
        log_config = settings.logging
        
        # 设置日志级别
        level = getattr(logging, log_config.level.upper())
        self.logger.setLevel(level)
        
        # 创建日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # 控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件日志处理器
        log_file = log_config.file
        max_bytes = log_config.max_bytes
        backup_count = log_config.backup_count
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self):
        return self.logger

# 创建全局日志实例
logger_instance = Logger()
logger = logger_instance.get_logger()
