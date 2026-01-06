from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class StockInfo(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: Optional[float] = Field(None, description="当前股价")
    market_cap: Optional[float] = Field(None, description="市值")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    ps_ratio: Optional[float] = Field(None, description="市销率")
    
    @field_validator('current_price', 'market_cap', 'pe_ratio', 'pb_ratio', 'ps_ratio')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError('数值必须为正数')
        return v


class DividendRecord(BaseModel):
    year: int = Field(..., description="分红年度")
    dividend_per_share: float = Field(..., description="每股分红金额")
    dividend_yield: Optional[float] = Field(None, description="股息率")
    record_date: Optional[str] = Field(None, description="股权登记日")
    ex_dividend_date: Optional[str] = Field(None, description="除权除息日")
    payout_date: Optional[str] = Field(None, description="派息日")
    
    @field_validator('dividend_per_share')
    @classmethod
    def validate_dividend_amount(cls, v):
        if v < 0:
            raise ValueError('分红金额必须为正数')
        return v


class DividendYield(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前股价")
    dividend_yield: float = Field(..., description="股息率(%)")
    annual_dividend: float = Field(..., description="年度每股股息")
    ttm_dividend_yield: Optional[float] = Field(None, description="TTM股息率(%)")
    dividend_records: List[DividendRecord] = Field(default_factory=list, description="分红记录")
    calculated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="计算时间")
    
    @field_validator('current_price', 'dividend_yield', 'annual_dividend')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v < 0:
            raise ValueError('数值必须为正数')
        return v


class DividendTrend(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    years: List[int] = Field(..., description="年份列表")
    dividend_yields: List[float] = Field(..., description="股息率列表(%)")
    dividends_per_share: List[float] = Field(..., description="每股分红列表")
    avg_dividend_yield: float = Field(..., description="平均股息率(%)")
    dividend_growth_rate: Optional[float] = Field(None, description="股息增长率(%)")
    
    @field_validator('dividend_yields', 'dividends_per_share', 'avg_dividend_yield')
    @classmethod
    def validate_positive_numbers(cls, v):
        if isinstance(v, list):
            for item in v:
                if item < 0:
                    raise ValueError('数值必须为正数')
        elif v < 0:
            raise ValueError('数值必须为正数')
        return v


class StockFilter(BaseModel):
    min_dividend_yield: Optional[float] = Field(None, description="最小股息率(%)")
    max_dividend_yield: Optional[float] = Field(None, description="最大股息率(%)")
    min_pe_ratio: Optional[float] = Field(None, description="最小市盈率")
    max_pe_ratio: Optional[float] = Field(None, description="最大市盈率")
    min_market_cap: Optional[float] = Field(None, description="最小市值(亿元)")
    max_market_cap: Optional[float] = Field(None, description="最大市值(亿元)")
    stock_codes: Optional[List[str]] = Field(None, description="股票代码列表")
    exclude_st: bool = Field(default=True, description="排除ST股票")
    
    @field_validator('min_dividend_yield', 'max_dividend_yield', 'min_pe_ratio', 'max_pe_ratio', 'min_market_cap', 'max_market_cap')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError('数值必须为正数')
        return v


class DividendAnalysisResult(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    dividend_yield: DividendYield = Field(..., description="股息率信息")
    dividend_trend: Optional[DividendTrend] = Field(None, description="股息率趋势")
    is_high_dividend: bool = Field(default=False, description="是否为高股息股票")
    risk_level: str = Field(default="中", description="风险等级")
    recommendation: Optional[str] = Field(None, description="投资建议")


class BatchDividendResult(BaseModel):
    total_stocks: int = Field(..., description="总股票数")
    dividend_yields: List[DividendYield] = Field(default_factory=list, description="股息率列表")
    high_dividend_stocks: List[DividendYield] = Field(default_factory=list, description="高股息股票列表")
    avg_dividend_yield: float = Field(..., description="平均股息率(%)")
    max_dividend_yield: float = Field(..., description="最高股息率(%)")
    min_dividend_yield: float = Field(..., description="最低股息率(%)")
    calculated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="计算时间")