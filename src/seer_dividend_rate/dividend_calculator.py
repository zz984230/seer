from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from .models import (
    StockInfo, DividendRecord, DividendYield, 
    DividendTrend, StockFilter, DividendAnalysisResult, BatchDividendResult
)
from .data_fetcher import DataFetcher
from .config import settings
from seer.logger import logger


class DividendCalculator:
    def __init__(self):
        self.logger = logger
        self.config = settings.calculation
        self.filter_config = settings.filter
        self.fetcher = DataFetcher()
        self._name_code_mapping: Optional[Dict[str, str]] = None
    
    def _get_stock_code(self, stock_identifier: str) -> Optional[str]:
        """
        根据股票名称或代码获取股票代码
        
        :param stock_identifier: 股票名称或代码
        :return: 股票代码，如果未找到则返回None
        """
        try:
            if stock_identifier.isdigit():
                return stock_identifier
            
            if self._name_code_mapping is None:
                self._name_code_mapping = self.fetcher.get_stock_name_code_mapping()
            
            stock_code = self._name_code_mapping.get(stock_identifier)
            if stock_code:
                return stock_code
            
            self.logger.warning(f"未找到股票: {stock_identifier}")
            return None
        except Exception as e:
            self.logger.error(f"获取股票代码失败: {stock_identifier}, 错误: {str(e)}")
            return None
    
    def calculate_dividend_yield(self, stock_identifier: str) -> Optional[DividendYield]:
        """
        计算单只股票的股息率
        
        :param stock_identifier: 股票名称或代码
        :return: DividendYield对象
        """
        try:
            stock_code = self._get_stock_code(stock_identifier)
            if not stock_code:
                self.logger.warning(f"无法识别股票: {stock_identifier}")
                return None
            
            self.logger.info(f"计算股息率: {stock_identifier} ({stock_code})")
            
            stock_info = self.fetcher.get_stock_indicator(stock_code)
            if not stock_info or not stock_info.current_price:
                self.logger.warning(f"无法获取股票信息或股价: {stock_code}")
                return None
            
            dividend_records = self.fetcher.get_dividend_records(stock_code)
            if not dividend_records:
                self.logger.warning(f"无分红记录: {stock_code}")
                return None
            
            current_price = stock_info.current_price
            
            latest_record = dividend_records[0]
            annual_dividend = latest_record.dividend_per_share
            
            dividend_yield = (annual_dividend / current_price) * 100 if current_price > 0 else 0
            
            ttm_dividend_yield = self._calculate_ttm_dividend_yield(
                dividend_records, current_price
            )
            
            dividend_yield_obj = DividendYield(
                stock_code=stock_code,
                stock_name=stock_info.stock_name,
                current_price=current_price,
                dividend_yield=round(dividend_yield, 2),
                annual_dividend=round(annual_dividend, 4),
                ttm_dividend_yield=round(ttm_dividend_yield, 2) if ttm_dividend_yield else None,
                dividend_records=dividend_records
            )
            
            self.logger.info(f"股息率计算完成: {stock_identifier}, 股息率: {dividend_yield:.2f}%")
            return dividend_yield_obj
            
        except Exception as e:
            self.logger.error(f"计算股息率失败: {stock_identifier}, 错误: {str(e)}")
            return None
    
    def _calculate_ttm_dividend_yield(self, dividend_records: List[DividendRecord], current_price: float) -> Optional[float]:
        """
        计算TTM（过去12个月）股息率
        
        :param dividend_records: 分红记录列表
        :param current_price: 当前股价
        :return: TTM股息率(%)
        """
        if not dividend_records or current_price <= 0:
            return None
        
        try:
            current_year = datetime.now().year
            ttm_dividend = 0.0
            
            for record in dividend_records:
                if record.year >= current_year - 1:
                    ttm_dividend += record.dividend_per_share
            
            ttm_yield = (ttm_dividend / current_price) * 100
            return ttm_yield
            
        except Exception as e:
            self.logger.error(f"计算TTM股息率失败: {str(e)}")
            return None
    
    def calculate_dividend_trend(self, stock_identifier: str, years: int = 5) -> Optional[DividendTrend]:
        """
        计算股息率趋势
        
        :param stock_identifier: 股票名称或代码
        :param years: 分析年数
        :return: DividendTrend对象
        """
        try:
            stock_code = self._get_stock_code(stock_identifier)
            if not stock_code:
                self.logger.warning(f"无法识别股票: {stock_identifier}")
                return None
            
            self.logger.info(f"计算股息率趋势: {stock_identifier} ({stock_code}), 年数: {years}")
            
            stock_info = self.fetcher.get_stock_indicator(stock_code)
            if not stock_info:
                return None
            
            dividend_records = self.fetcher.get_dividend_records(stock_code)
            if not dividend_records:
                return None
            
            recent_records = dividend_records[:years]
            
            years_list = [record.year for record in recent_records]
            dividends_per_share = [record.dividend_per_share for record in recent_records]
            
            current_price = stock_info.current_price
            dividend_yields = [
                (dividend / current_price) * 100 if current_price > 0 else 0
                for dividend in dividends_per_share
            ]
            
            avg_dividend_yield = sum(dividend_yields) / len(dividend_yields) if dividend_yields else 0
            
            dividend_growth_rate = self._calculate_dividend_growth_rate(dividends_per_share)
            
            trend = DividendTrend(
                stock_code=stock_code,
                stock_name=stock_info.stock_name,
                years=years_list,
                dividend_yields=[round(yield_val, 2) for yield_val in dividend_yields],
                dividends_per_share=[round(dividend, 4) for dividend in dividends_per_share],
                avg_dividend_yield=round(avg_dividend_yield, 2),
                dividend_growth_rate=round(dividend_growth_rate, 2) if dividend_growth_rate else None
            )
            
            self.logger.info(f"股息率趋势计算完成: {stock_identifier}")
            return trend
            
        except Exception as e:
            self.logger.error(f"计算股息率趋势失败: {stock_identifier}, 错误: {str(e)}")
            return None
    
    def _calculate_dividend_growth_rate(self, dividends: List[float]) -> Optional[float]:
        """
        计算股息增长率
        
        :param dividends: 分红金额列表
        :return: 增长率(%)
        """
        if len(dividends) < 2:
            return None
        
        try:
            first_dividend = dividends[-1]
            last_dividend = dividends[0]
            
            if first_dividend <= 0:
                return None
            
            years = len(dividends) - 1
            growth_rate = ((last_dividend / first_dividend) ** (1 / years) - 1) * 100
            
            return growth_rate
            
        except Exception as e:
            self.logger.error(f"计算股息增长率失败: {str(e)}")
            return None
    
    def calculate_custom_yield(self, stock_identifier: str, dividend_amount: float) -> Optional[DividendYield]:
        """
        自定义股息率计算
        
        :param stock_identifier: 股票名称或代码
        :param dividend_amount: 自定义分红金额
        :return: DividendYield对象
        """
        try:
            stock_code = self._get_stock_code(stock_identifier)
            if not stock_code:
                self.logger.warning(f"无法识别股票: {stock_identifier}")
                return None
            
            self.logger.info(f"自定义股息率计算: {stock_identifier} ({stock_code}), 分红金额: {dividend_amount}")
            
            stock_info = self.fetcher.get_stock_indicator(stock_code)
            if not stock_info or not stock_info.current_price:
                return None
            
            current_price = stock_info.current_price
            dividend_yield = (dividend_amount / current_price) * 100 if current_price > 0 else 0
            
            dividend_yield_obj = DividendYield(
                stock_code=stock_code,
                stock_name=stock_info.stock_name,
                current_price=current_price,
                dividend_yield=round(dividend_yield, 2),
                annual_dividend=round(dividend_amount, 4),
                ttm_dividend_yield=None,
                dividend_records=[]
            )
            
            self.logger.info(f"自定义股息率计算完成: {stock_identifier}, 股息率: {dividend_yield:.2f}%")
            return dividend_yield_obj
            
        except Exception as e:
            self.logger.error(f"自定义股息率计算失败: {stock_identifier}, 错误: {str(e)}")
            return None
    
    def get_batch_dividend_yields(self, stock_identifiers: List[str]) -> BatchDividendResult:
        """
        批量获取股息率
        
        :param stock_identifiers: 股票名称或代码列表
        :return: BatchDividendResult对象
        """
        self.logger.info(f"批量获取股息率: {len(stock_identifiers)}只股票")
        
        dividend_yields = []
        
        for stock_identifier in stock_identifiers:
            try:
                dividend_yield = self.calculate_dividend_yield(stock_identifier)
                if dividend_yield:
                    dividend_yields.append(dividend_yield)
            except Exception as e:
                self.logger.error(f"获取股息率失败: {stock_identifier}, 错误: {str(e)}")
                continue
        
        if not dividend_yields:
            return BatchDividendResult(
                total_stocks=len(stock_identifiers),
                dividend_yields=[],
                high_dividend_stocks=[],
                avg_dividend_yield=0.0,
                max_dividend_yield=0.0,
                min_dividend_yield=0.0
            )
        
        yields_list = [dy.dividend_yield for dy in dividend_yields]
        avg_yield = sum(yields_list) / len(yields_list)
        max_yield = max(yields_list)
        min_yield = min(yields_list)
        
        high_dividend_stocks = [
            dy for dy in dividend_yields 
            if dy.dividend_yield >= self.config.high_dividend_threshold
        ]
        
        result = BatchDividendResult(
            total_stocks=len(stock_identifiers),
            dividend_yields=dividend_yields,
            high_dividend_stocks=high_dividend_stocks,
            avg_dividend_yield=round(avg_yield, 2),
            max_dividend_yield=round(max_yield, 2),
            min_dividend_yield=round(min_yield, 2)
        )
        
        self.logger.info(f"批量获取完成: {len(dividend_yields)}/{len(stock_identifiers)}, 高股息股票: {len(high_dividend_stocks)}")
        return result
    
    def get_high_dividend_stocks(self, stock_identifiers: Optional[List[str]] = None, threshold: Optional[float] = None) -> List[DividendYield]:
        """
        获取高股息率股票
        
        :param stock_identifiers: 股票名称或代码列表，如果为None则获取所有股票
        :param threshold: 股息率阈值，如果为None则使用配置中的阈值
        :return: 高股息率股票列表
        """
        try:
            threshold = threshold or self.config.high_dividend_threshold
            
            if stock_identifiers is None:
                stock_identifiers = self.fetcher.get_all_stock_list()
            
            self.logger.info(f"获取高股息率股票: 阈值={threshold}%, 股票数={len(stock_identifiers)}")
            
            high_dividend_stocks = []
            
            for stock_identifier in stock_identifiers:
                try:
                    dividend_yield = self.calculate_dividend_yield(stock_identifier)
                    if dividend_yield and dividend_yield.dividend_yield >= threshold:
                        high_dividend_stocks.append(dividend_yield)
                except Exception as e:
                    self.logger.error(f"处理股票失败: {stock_identifier}, 错误: {str(e)}")
                    continue
            
            high_dividend_stocks.sort(key=lambda x: x.dividend_yield, reverse=True)
            
            self.logger.info(f"找到高股息率股票: {len(high_dividend_stocks)}只")
            return high_dividend_stocks
            
        except Exception as e:
            self.logger.error(f"获取高股息率股票失败: {str(e)}")
            return []
    
    def filter_stocks(self, dividend_yields: List[DividendYield], stock_filter: StockFilter) -> List[DividendYield]:
        """
        根据条件筛选股票
        
        :param dividend_yields: 股息率列表
        :param stock_filter: 筛选条件
        :return: 筛选后的股票列表
        """
        try:
            filtered = dividend_yields
            
            if stock_filter.min_dividend_yield is not None:
                filtered = [dy for dy in filtered if dy.dividend_yield >= stock_filter.min_dividend_yield]
            
            if stock_filter.max_dividend_yield is not None:
                filtered = [dy for dy in filtered if dy.dividend_yield <= stock_filter.max_dividend_yield]
            
            if stock_filter.stock_codes:
                filtered = [dy for dy in filtered if dy.stock_code in stock_filter.stock_codes]
            
            if stock_filter.exclude_st:
                filtered = [dy for dy in filtered if 'ST' not in dy.stock_name and '*ST' not in dy.stock_name]
            
            self.logger.info(f"筛选结果: {len(filtered)}/{len(dividend_yields)}")
            return filtered
            
        except Exception as e:
            self.logger.error(f"筛选股票失败: {str(e)}")
            return dividend_yields
    
    def analyze_dividend(self, stock_identifier: str) -> Optional[DividendAnalysisResult]:
        """
        综合分析股息率
        
        :param stock_identifier: 股票名称或代码
        :return: DividendAnalysisResult对象
        """
        try:
            self.logger.info(f"综合分析股息率: {stock_identifier}")
            
            dividend_yield = self.calculate_dividend_yield(stock_identifier)
            if not dividend_yield:
                return None
            
            dividend_trend = self.calculate_dividend_trend(stock_identifier)
            
            is_high_dividend = dividend_yield.dividend_yield >= self.config.high_dividend_threshold
            
            risk_level = self._assess_risk_level(dividend_yield, dividend_trend)
            recommendation = self._generate_recommendation(dividend_yield, dividend_trend, risk_level)
            
            result = DividendAnalysisResult(
                stock_code=dividend_yield.stock_code,
                stock_name=dividend_yield.stock_name,
                dividend_yield=dividend_yield,
                dividend_trend=dividend_trend,
                is_high_dividend=is_high_dividend,
                risk_level=risk_level,
                recommendation=recommendation
            )
            
            self.logger.info(f"综合分析完成: {stock_identifier}")
            return result
            
        except Exception as e:
            self.logger.error(f"综合分析失败: {stock_identifier}, 错误: {str(e)}")
            return None
    
    def _assess_risk_level(self, dividend_yield: DividendYield, dividend_trend: Optional[DividendTrend]) -> str:
        """
        评估风险等级
        
        :param dividend_yield: 股息率信息
        :param dividend_trend: 股息率趋势
        :return: 风险等级
        """
        try:
            if dividend_yield.dividend_yield > 10:
                return "高"
            elif dividend_yield.dividend_yield < 2:
                return "高"
            elif dividend_trend and dividend_trend.dividend_growth_rate and dividend_trend.dividend_growth_rate < -5:
                return "高"
            elif dividend_yield.dividend_yield > 6:
                return "中"
            else:
                return "低"
        except Exception as e:
            self.logger.error(f"评估风险等级失败: {str(e)}")
            return "中"
    
    def _generate_recommendation(self, dividend_yield: DividendYield, dividend_trend: Optional[DividendTrend], risk_level: str) -> str:
        """
        生成投资建议
        
        :param dividend_yield: 股息率信息
        :param dividend_trend: 股息率趋势
        :param risk_level: 风险等级
        :return: 投资建议
        """
        try:
            if risk_level == "高":
                return "建议谨慎投资，注意风险"
            elif dividend_yield.dividend_yield >= self.config.high_dividend_threshold:
                if dividend_trend and dividend_trend.dividend_growth_rate and dividend_trend.dividend_growth_rate > 0:
                    return "高股息且增长稳定，可考虑投资"
                else:
                    return "高股息但需关注分红稳定性"
            else:
                return "股息率一般，建议综合其他指标考虑"
        except Exception as e:
            self.logger.error(f"生成投资建议失败: {str(e)}")
            return "建议进一步分析"