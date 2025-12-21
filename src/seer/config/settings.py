from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import yaml
import os

# 爬虫配置模型
class CrawlerConfig(BaseModel):
    timeout: int = Field(default=30)
    retry_times: int = Field(default=3)
    delay_range: dict = Field(default_factory=lambda: {"min": 1, "max": 5})
    user_agents: List[str] = Field(default_factory=list)
    proxies: List[str] = Field(default_factory=list)
    max_workers: int = Field(default=5)

# 解析器配置模型
class ParserConfig(BaseModel):
    max_comments: int = Field(default=100)
    max_notes: int = Field(default=10)

# 存储配置模型
class StorageConfig(BaseModel):
    base_dir: str = Field(default="./data")

# 日志配置模型
class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    file: str = Field(default="./logs/seer.log")
    max_bytes: int = Field(default=10485760)
    backup_count: int = Field(default=5)

# 主配置模型
class Settings(BaseSettings):
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = ConfigDict(
        env_file = ".env",
        case_sensitive = False
    )
    
    @classmethod
    def from_yaml(cls, config_path: str = "./config/config.yaml"):
        """从YAML文件加载配置"""
        # 确保路径是绝对路径或相对于项目根目录
        if not os.path.isabs(config_path):
            # 获取当前文件所在目录的父目录的父目录的父目录的父目录（即项目根目录）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(project_root, config_path[2:])  # 移除./前缀
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        else:
            # 如果配置文件不存在，使用默认值
            return cls()

# 创建全局配置实例
settings = Settings.from_yaml()
