from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import os
import yaml


class DividendDataSourceConfig(BaseModel):
    source: str = Field(default="eastmoney", description="数据源: eastmoney, sina, tencent")
    api_timeout: int = Field(default=30, description="API请求超时时间(秒)")
    retry_times: int = Field(default=3, description="重试次数")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    cache_expire_hours: int = Field(default=24, description="缓存过期时间(小时)")
    max_workers: int = Field(default=20, description="并发工作进程数")
    request_interval: float = Field(default=0.5, description="请求间隔(秒)")


class DividendCalculationConfig(BaseModel):
    high_dividend_threshold: float = Field(default=4.0, description="高股息率阈值(%)")
    ttm_months: int = Field(default=12, description="TTM计算月数")
    min_dividend_years: int = Field(default=3, description="最少分红年数")
    dividend_growth_threshold: float = Field(default=5.0, description="股息增长阈值(%)")


class DividendFilterConfig(BaseModel):
    default_min_yield: float = Field(default=0.0, description="默认最小股息率(%)")
    default_max_yield: float = Field(default=100.0, description="默认最大股息率(%)")
    default_min_pe: float = Field(default=0.0, description="默认最小市盈率")
    default_max_pe: float = Field(default=1000.0, description="默认最大市盈率")
    default_min_market_cap: float = Field(default=0.0, description="默认最小市值(亿元)")
    default_max_market_cap: float = Field(default=100000.0, description="默认最大市值(亿元)")


class DividendStorageConfig(BaseModel):
    cache_dir: str = Field(default="./cache/dividend", description="缓存目录")
    data_dir: str = Field(default="./data/dividend", description="数据存储目录")
    enable_persistence: bool = Field(default=True, description="是否启用持久化存储")


class DividendRateSettings(BaseSettings):
    data_source: DividendDataSourceConfig = Field(default_factory=DividendDataSourceConfig)
    calculation: DividendCalculationConfig = Field(default_factory=DividendCalculationConfig)
    filter: DividendFilterConfig = Field(default_factory=DividendFilterConfig)
    storage: DividendStorageConfig = Field(default_factory=DividendStorageConfig)
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="DIVIDEND_"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            os.makedirs(self.storage.cache_dir, exist_ok=True)
            os.makedirs(self.storage.data_dir, exist_ok=True)
        except Exception as e:
            print(f"创建目录失败: {e}")
    
    @classmethod
    def from_yaml(cls, config_path: str = "./config/config.yaml"):
        """从YAML文件加载配置"""
        if not os.path.isabs(config_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(project_root, config_path[2:]) if config_path.startswith("./") else os.path.join(project_root, config_path)
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            dividend_rate_config = config_data.get("dividend_rate", {})
            return cls(**dividend_rate_config)
        else:
            return cls()


settings = DividendRateSettings.from_yaml()