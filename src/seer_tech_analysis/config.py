from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import os
import yaml


class TechAnalysisDataSourceConfig(BaseModel):
    source: str = Field(default="akshare", description="数据源: akshare/tushare")
    api_timeout: int = Field(default=30, description="API请求超时时间(秒)")
    retry_times: int = Field(default=3, description="重试次数")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    cache_expire_hours: int = Field(default=24, description="缓存过期时间(小时)")
    max_workers: int = Field(default=10, description="并发工作进程数")
    request_interval: float = Field(default=0.5, description="请求间隔(秒)")


class TechAnalysisIndicatorConfig(BaseModel):
    macd_fast_period: int = Field(default=12, description="MACD快线周期")
    macd_slow_period: int = Field(default=26, description="MACD慢线周期")
    macd_signal_period: int = Field(default=9, description="MACD信号线周期")
    
    rsi_period: int = Field(default=14, description="RSI周期")
    rsi_overbought: float = Field(default=70.0, description="RSI超买阈值")
    rsi_oversold: float = Field(default=30.0, description="RSI超卖阈值")
    
    kdj_period: int = Field(default=9, description="KDJ周期")
    kdj_m1: int = Field(default=3, description="KDJ M1")
    kdj_m2: int = Field(default=3, description="KDJ M2")
    
    ma_periods: List[int] = Field(default_factory=lambda: [5, 10, 20, 60], description="均线周期列表")


class TechAnalysisPatternConfig(BaseModel):
    enable_pattern_recognition: bool = Field(default=True, description="是否启用形态识别")
    min_pattern_days: int = Field(default=5, description="最小形态天数")
    max_pattern_days: int = Field(default=60, description="最大形态天数")
    min_confidence: float = Field(default=0.6, description="最小置信度")
    
    enable_head_shoulders: bool = Field(default=True, description="是否识别头肩形态")
    enable_double_top_bottom: bool = Field(default=True, description="是否识别双顶双底")
    enable_triangle: bool = Field(default=True, description="是否识别三角形")
    enable_wedge: bool = Field(default=True, description="是否识别楔形")


class TechAnalysisVolumeConfig(BaseModel):
    enable_volume_analysis: bool = Field(default=True, description="是否启用量价分析")
    volume_ma_period: int = Field(default=20, description="成交量均线周期")
    volume_surge_threshold: float = Field(default=2.0, description="成交量放量阈值(倍数)")
    volume_shrink_threshold: float = Field(default=0.5, description="成交量缩量阈值(倍数)")


class TechAnalysisLLMConfig(BaseModel):
    enable_llm_analysis: bool = Field(default=True, description="是否启用LLM分析")
    provider: str = Field(default="openai", description="LLM提供商: openai/anthropic/google")
    model_name: str = Field(default="gpt-4", description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大token数")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    
    enable_multi_agent: bool = Field(default=True, description="是否启用多Agent")
    agent_types: List[str] = Field(default_factory=lambda: ["technical", "pattern", "volume"], description="Agent类型列表")


class TechAnalysisReportConfig(BaseModel):
    report_dir: str = Field(default="./reports/tech_analysis", description="报告输出目录")
    enable_html_report: bool = Field(default=True, description="是否生成HTML报告")
    enable_pdf_report: bool = Field(default=True, description="是否生成PDF报告")
    enable_json_report: bool = Field(default=True, description="是否生成JSON报告")
    enable_charts: bool = Field(default=True, description="是否生成图表")
    
    chart_width: int = Field(default=1200, description="图表宽度(像素)")
    chart_height: int = Field(default=600, description="图表高度(像素)")
    chart_dpi: int = Field(default=100, description="图表DPI")


class TechAnalysisStorageConfig(BaseModel):
    cache_dir: str = Field(default="./cache/tech_analysis", description="缓存目录")
    data_dir: str = Field(default="./data/tech_analysis", description="数据存储目录")
    enable_persistence: bool = Field(default=True, description="是否启用持久化存储")
    auto_update_interval: int = Field(default=24, description="自动更新间隔(小时)")


class TechAnalysisSettings(BaseSettings):
    data_source: TechAnalysisDataSourceConfig = Field(default_factory=TechAnalysisDataSourceConfig)
    indicators: TechAnalysisIndicatorConfig = Field(default_factory=TechAnalysisIndicatorConfig)
    pattern: TechAnalysisPatternConfig = Field(default_factory=TechAnalysisPatternConfig)
    volume: TechAnalysisVolumeConfig = Field(default_factory=TechAnalysisVolumeConfig)
    llm: TechAnalysisLLMConfig = Field(default_factory=TechAnalysisLLMConfig)
    report: TechAnalysisReportConfig = Field(default_factory=TechAnalysisReportConfig)
    storage: TechAnalysisStorageConfig = Field(default_factory=TechAnalysisStorageConfig)
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="TECH_ANALYSIS_"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        try:
            os.makedirs(self.storage.cache_dir, exist_ok=True)
            os.makedirs(self.storage.data_dir, exist_ok=True)
            os.makedirs(self.report.report_dir, exist_ok=True)
        except Exception as e:
            print(f"创建目录失败: {e}")
    
    @classmethod
    def from_yaml(cls, config_path: str = "./config/config.yaml"):
        if not os.path.isabs(config_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(project_root, config_path[2:]) if config_path.startswith("./") else os.path.join(project_root, config_path)
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            tech_analysis_config = config_data.get("tech_analysis", {})
            return cls(**tech_analysis_config)
        else:
            return cls()


settings = TechAnalysisSettings.from_yaml()
