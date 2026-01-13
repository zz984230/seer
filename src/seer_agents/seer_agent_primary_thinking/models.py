from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExpertQuote(BaseModel):
    expert_name: str = Field(..., description="专家名称")
    video_title: str = Field(..., description="视频标题")
    video_date: str = Field(..., description="视频日期")
    summary: str = Field(..., description="主要内容摘要")
    key_points: List[str] = Field(default_factory=list, description="关键信息要点")
    core_concepts: List[str] = Field(default_factory=list, description="核心概念")
    analysis_framework: Optional[str] = Field(None, description="分析框架")
    technical_patterns: List[str] = Field(default_factory=list, description="技术形态")
    trading_strategies: List[str] = Field(default_factory=list, description="交易策略")
    risk_warnings: List[str] = Field(default_factory=list, description="风险提示")
    main_force_behavior: List[str] = Field(default_factory=list, description="主力行为特征")
    market_logic: List[str] = Field(default_factory=list, description="市场逻辑")


class AnalysisDimension(BaseModel):
    dimension_name: str = Field(..., description="分析维度名称")
    indicators: List[str] = Field(default_factory=list, description="相关指标")
    importance: float = Field(..., description="重要性权重(0-1)")
    description: str = Field(..., description="维度描述")


class AnalysisFramework(BaseModel):
    framework_name: str = Field(..., description="框架名称")
    phases: List[str] = Field(default_factory=list, description="分析阶段")
    decision_logic: str = Field(..., description="决策逻辑")
    key_factors: List[str] = Field(default_factory=list, description="关键因素")


class MainForceBehavior(BaseModel):
    behavior_type: str = Field(..., description="行为类型: 建仓/洗盘/拉升/出货")
    characteristics: List[str] = Field(default_factory=list, description="特征描述")
    identification_methods: List[str] = Field(default_factory=list, description="识别方法")
    countermeasures: List[str] = Field(default_factory=list, description="应对策略")


class TradingStrategy(BaseModel):
    strategy_name: str = Field(..., description="策略名称")
    entry_conditions: List[str] = Field(default_factory=list, description="入场条件")
    exit_conditions: List[str] = Field(default_factory=list, description="出场条件")
    risk_control: List[str] = Field(default_factory=list, description="风险控制")
    success_rate: Optional[float] = Field(None, description="成功率")


class KnowledgeEntry(BaseModel):
    entry_id: str = Field(..., description="知识条目ID")
    category: str = Field(..., description="分类: 技术分析/主力行为/交易策略/风险控制")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    tags: List[str] = Field(default_factory=list, description="标签")
    source: str = Field(..., description="来源")
    confidence: float = Field(default=0.8, description="置信度")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")


class StockAnalysisRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    start_date: Optional[str] = Field(None, description="分析开始日期")
    end_date: Optional[str] = Field(None, description="分析结束日期")
    analysis_dimensions: List[str] = Field(default_factory=list, description="分析维度列表")
    enable_fundamental: bool = Field(default=True, description="是否启用基本面分析")
    enable_technical: bool = Field(default=True, description="是否启用技术面分析")
    enable_industry: bool = Field(default=True, description="是否启用行业分析")
    enable_risk_assessment: bool = Field(default=True, description="是否启用风险评估")


class StockAnalysisResult(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    analysis_date: str = Field(..., description="分析日期")
    
    fundamental_analysis: Optional[Dict[str, Any]] = Field(None, description="基本面分析结果")
    technical_analysis: Optional[Dict[str, Any]] = Field(None, description="技术面分析结果")
    industry_analysis: Optional[Dict[str, Any]] = Field(None, description="行业分析结果")
    risk_assessment: Optional[Dict[str, Any]] = Field(None, description="风险评估结果")
    
    main_force_status: Optional[str] = Field(None, description="主力状态")
    trading_phase: Optional[str] = Field(None, description="交易阶段")
    
    recommendation: str = Field(..., description="投资建议: 买入/卖出/持有/观望")
    confidence: float = Field(..., description="置信度(0-1)")
    risk_level: str = Field(..., description="风险等级: 低/中/高")
    
    key_points: List[str] = Field(default_factory=list, description="关键点")
    opportunities: List[str] = Field(default_factory=list, description="机会点")
    risks: List[str] = Field(default_factory=list, description="风险点")
    
    reasoning: str = Field(..., description="推理过程")
    
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
