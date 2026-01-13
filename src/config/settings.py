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
    request_interval: int = Field(default=1)  # 请求间隔时间（秒）
    max_pages: int = Field(default=1)  # 最大爬取页面数
    user_agents: List[str] = Field(default_factory=list)
    proxies: List[str] = Field(default_factory=list)
    max_workers: int = Field(default=5)
    # cookies_str 已迁移到环境变量 XHS_COOKIES 中

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

# 股息率配置模型（简化版，避免循环导入）
class DividendRateConfig(BaseModel):
    data_source: dict = Field(default_factory=dict)
    calculation: dict = Field(default_factory=dict)
    filter: dict = Field(default_factory=dict)
    storage: dict = Field(default_factory=dict)

# ADK 模型配置
class ADKModelConfig(BaseModel):
    provider: str = Field(default="openai")
    name: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4096)

# ADK Agent 配置
class ADKAgentConfig(BaseModel):
    name: str = Field(default="primary_thinking_agent")
    description: str = Field(default="基于B站投资专家思维模式的个股分析Agent")
    instructions: str = Field(default="你是一个专业的股票投资分析专家，请基于提供的数据进行客观分析，给出合理的投资建议。")

# ADK 配置
class ADKConfig(BaseModel):
    model: ADKModelConfig = Field(default_factory=ADKModelConfig)
    agent: ADKAgentConfig = Field(default_factory=ADKAgentConfig)

# 主配置模型
class Settings(BaseSettings):
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    dividend_rate: DividendRateConfig = Field(default_factory=DividendRateConfig)
    adk: ADKConfig = Field(default_factory=ADKConfig)
    xhs_cookies: Optional[str] = Field(default=None, alias="XHS_COOKIES")  # 从环境变量加载小红书cookies
    
    # ADK 模型配置（从环境变量加载）
    adk_model_provider: Optional[str] = Field(default=None, alias="ADK_MODEL_PROVIDER")
    adk_model_name: Optional[str] = Field(default=None, alias="ADK_MODEL_NAME")
    adk_model_temperature: Optional[float] = Field(default=None, alias="ADK_MODEL_TEMPERATURE")
    adk_model_max_tokens: Optional[int] = Field(default=None, alias="ADK_MODEL_MAX_TOKENS")
    
    # OpenAI 配置（从环境变量加载）
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default=None, alias="OPENAI_API_BASE")
    
    # Anthropic 配置（从环境变量加载）
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    
    # Google 配置（从环境变量加载）
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
    # Agent 配置（从环境变量加载）
    stock_analysis_agent_name: Optional[str] = Field(default=None, alias="STOCK_ANALYSIS_AGENT_NAME")
    stock_analysis_agent_description: Optional[str] = Field(default=None, alias="STOCK_ANALYSIS_AGENT_DESCRIPTION")
    stock_analysis_agent_instructions: Optional[str] = Field(default=None, alias="STOCK_ANALYSIS_AGENT_INSTRUCTIONS")
    
    model_config = ConfigDict(
        env_file = ".env",
        case_sensitive = False,
        extra = "ignore"
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
