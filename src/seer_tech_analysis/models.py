from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class StockData(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    date: str = Field(..., description="日期")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    
    @field_validator('open_price', 'high_price', 'low_price', 'close_price', 'volume', 'amount', 'turnover_rate')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError('数值必须为正数')
        return v


class TechnicalIndicator(BaseModel):
    name: str = Field(..., description="指标名称")
    values: List[float] = Field(..., description="指标值列表")
    signals: List[str] = Field(default_factory=list, description="交易信号列表")
    description: Optional[str] = Field(None, description="指标描述")


class MACDIndicator(BaseModel):
    dif: List[float] = Field(..., description="DIF值")
    dea: List[float] = Field(..., description="DEA值")
    macd: List[float] = Field(..., description="MACD柱状图")
    signals: List[str] = Field(default_factory=list, description="交易信号")
    description: Optional[str] = Field(None, description="分析描述")


class RSIIndicator(BaseModel):
    rsi6: List[float] = Field(..., description="RSI(6)")
    rsi12: List[float] = Field(..., description="RSI(12)")
    rsi24: List[float] = Field(..., description="RSI(24)")
    signals: List[str] = Field(default_factory=list, description="交易信号")
    description: Optional[str] = Field(None, description="分析描述")


class KDJIndicator(BaseModel):
    k: List[float] = Field(..., description="K值")
    d: List[float] = Field(..., description="D值")
    j: List[float] = Field(..., description="J值")
    signals: List[str] = Field(default_factory=list, description="交易信号")
    description: Optional[str] = Field(None, description="分析描述")


class PatternInfo(BaseModel):
    pattern_type: str = Field(..., description="形态类型")
    pattern_name: str = Field(..., description="形态名称")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    confidence: float = Field(..., description="置信度(0-1)")
    target_price: Optional[float] = Field(None, description="目标价格")
    stop_loss: Optional[float] = Field(None, description="止损价格")
    description: Optional[str] = Field(None, description="形态描述")


class VolumePriceRelation(BaseModel):
    date: str = Field(..., description="日期")
    price_change: float = Field(..., description="价格变化率(%)")
    volume_change: float = Field(..., description="成交量变化率(%)")
    relation_type: str = Field(..., description="关系类型: 量增价涨/量增价跌/量减价涨/量减价跌")
    strength: str = Field(..., description="强度: 强/中/弱")
    description: Optional[str] = Field(None, description="描述")


class AgentAnalysis(BaseModel):
    agent_name: str = Field(..., description="Agent名称")
    agent_type: str = Field(..., description="Agent类型: technical/pattern/volume")
    analysis_result: Dict[str, Any] = Field(..., description="分析结果")
    confidence: float = Field(..., description="置信度(0-1)")
    recommendation: str = Field(..., description="建议: 买入/卖出/持有")
    risk_level: str = Field(default="中", description="风险等级: 低/中/高")
    reasoning: Optional[str] = Field(None, description="推理过程")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="分析时间")


class ComprehensiveAnalysis(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    analysis_date: str = Field(..., description="分析日期")
    
    stock_data: List[StockData] = Field(..., description="股票数据")
    
    technical_indicators: Dict[str, TechnicalIndicator] = Field(default_factory=dict, description="技术指标")
    macd: Optional[MACDIndicator] = Field(None, description="MACD指标")
    rsi: Optional[RSIIndicator] = Field(None, description="RSI指标")
    kdj: Optional[KDJIndicator] = Field(None, description="KDJ指标")
    
    patterns: List[PatternInfo] = Field(default_factory=list, description="形态识别结果")
    volume_price_relations: List[VolumePriceRelation] = Field(default_factory=list, description="量价关系")
    
    agent_analyses: List[AgentAnalysis] = Field(default_factory=list, description="Agent分析结果")
    
    overall_recommendation: str = Field(..., description="综合建议: 买入/卖出/持有")
    overall_confidence: float = Field(..., description="综合置信度(0-1)")
    overall_risk_level: str = Field(default="中", description="综合风险等级: 低/中/高")
    
    key_points: List[str] = Field(default_factory=list, description="关键点")
    warnings: List[str] = Field(default_factory=list, description="风险提示")
    
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")


class AnalysisRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    start_date: str = Field(..., description="开始日期(YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期(YYYY-MM-DD)")
    indicators: List[str] = Field(default_factory=lambda: ["MACD", "RSI", "KDJ"], description="需要计算的技术指标")
    enable_pattern_recognition: bool = Field(default=True, description="是否启用形态识别")
    enable_volume_analysis: bool = Field(default=True, description="是否启用量价分析")
    use_llm_analysis: bool = Field(default=True, description="是否使用LLM分析")
    llm_model: Optional[str] = Field(None, description="LLM模型名称")


class AnalysisReport(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    report_date: str = Field(..., description="报告日期")
    
    summary: str = Field(..., description="分析摘要")
    technical_analysis: str = Field(..., description="技术面分析")
    pattern_analysis: str = Field(..., description="形态分析")
    volume_price_analysis: str = Field(..., description="量价分析")
    
    key_indicators: Dict[str, Any] = Field(default_factory=dict, description="关键指标")
    recommendations: List[str] = Field(default_factory=list, description="投资建议")
    risk_warnings: List[str] = Field(default_factory=list, description="风险提示")
    
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="图表数据")
    
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="生成时间")


class LLMConfig(BaseModel):
    provider: str = Field(default="openai", description="LLM提供商: openai/anthropic/google")
    model_name: str = Field(default="gpt-4", description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大token数")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('温度参数必须在0-2之间')
        return v
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v):
        if v <= 0:
            raise ValueError('最大token数必须为正数')
        return v
