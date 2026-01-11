from typing import Tuple, Optional
from seer.logger import logger

from .models import (
    StockData,
    TechnicalIndicator,
    MACDIndicator,
    RSIIndicator,
    KDJIndicator,
    PatternInfo,
    VolumePriceRelation,
    AgentAnalysis,
    ComprehensiveAnalysis,
    AnalysisRequest,
    AnalysisReport,
    LLMConfig
)

from .config import settings

from .data_fetcher import DataFetcher

from .technical_indicators import TechnicalIndicators

from .pattern_recognition import PatternRecognition

from .volume_price_analysis import VolumePriceAnalysis

from .llm_agent import LLMAgent, LLMFactory

from .agent_coordinator import AgentCoordinator

from .reporter import TechAnalysisReporter

__version__ = "0.1.0"

__all__ = [
    "models",
    "StockData",
    "TechnicalIndicator",
    "MACDIndicator",
    "RSIIndicator",
    "KDJIndicator",
    "PatternInfo",
    "VolumePriceRelation",
    "AgentAnalysis",
    "ComprehensiveAnalysis",
    "AnalysisRequest",
    "AnalysisReport",
    "LLMConfig",
    "config",
    "settings",
    "DataFetcher",
    "TechnicalIndicators",
    "PatternRecognition",
    "VolumePriceAnalysis",
    "LLMAgent",
    "LLMFactory",
    "AgentCoordinator",
    "TechAnalysisReporter"
]


class TechAnalysisEngine:
    def __init__(self):
        self.logger = logger
        self.data_fetcher = DataFetcher()
        self.technical_indicators = TechnicalIndicators()
        self.pattern_recognition = PatternRecognition()
        self.volume_price_analysis = VolumePriceAnalysis()
        self.agent_coordinator = AgentCoordinator()
        self.reporter = TechAnalysisReporter()
    
    def analyze_stock(self, request: AnalysisRequest) -> Tuple[bool, str, Optional[ComprehensiveAnalysis]]:
        try:
            self.logger.info(f"开始分析股票: {request.stock_code}")
            
            success, msg, stock_data = self.data_fetcher.get_stock_daily_data(
                request.stock_code,
                request.start_date,
                request.end_date
            )
            
            if not success or not stock_data:
                return False, f"获取股票数据失败: {msg}", None
            
            success, msg = self.data_fetcher.validate_data_integrity(stock_data)
            if not success:
                return False, f"数据完整性校验失败: {msg}", None
            
            context = {
                'stock_code': request.stock_code,
                'stock_name': request.stock_name or stock_data[0].stock_name,
                'analysis_date': request.end_date,
                'stock_data': stock_data
            }
            
            if request.indicators:
                success, msg, indicators = self.technical_indicators.calculate_all_indicators(stock_data)
                if success:
                    context['technical_indicators'] = indicators
                    context['macd'] = indicators.get('macd')
                    context['rsi'] = indicators.get('rsi')
                    context['kdj'] = indicators.get('kdj')
                    self.logger.info("技术指标计算完成")
            
            if request.enable_pattern_recognition:
                success, msg, patterns = self.pattern_recognition.detect_all_patterns(stock_data)
                if success:
                    context['patterns'] = patterns
                    self.logger.info("形态识别完成")
            
            if request.enable_volume_analysis:
                success, msg, volume_price = self.volume_price_analysis.analyze_all(stock_data)
                if success:
                    context['volume_price'] = volume_price
                    context['volume_price_relations'] = volume_price.get('daily_relations', [])
                    self.logger.info("量价分析完成")
            
            if request.use_llm_analysis:
                success, msg, comprehensive = self.agent_coordinator.run_full_analysis(context)
                if success:
                    comprehensive.stock_data = stock_data
                    comprehensive.technical_indicators = context.get('technical_indicators', {})
                    comprehensive.macd = context.get('macd')
                    comprehensive.rsi = context.get('rsi')
                    comprehensive.kdj = context.get('kdj')
                    comprehensive.patterns = context.get('patterns', [])
                    comprehensive.volume_price_relations = context.get('volume_price_relations', [])
                    
                    self.logger.info(f"股票分析完成: {request.stock_code}")
                    return True, "分析完成", comprehensive
                else:
                    return False, f"LLM分析失败: {msg}", None
            else:
                from .models import ComprehensiveAnalysis
                comprehensive = ComprehensiveAnalysis(
                    stock_code=context['stock_code'],
                    stock_name=context['stock_name'],
                    analysis_date=context['analysis_date'],
                    stock_data=stock_data,
                    technical_indicators=context.get('technical_indicators', {}),
                    macd=context.get('macd'),
                    rsi=context.get('rsi'),
                    kdj=context.get('kdj'),
                    patterns=context.get('patterns', []),
                    volume_price_relations=context.get('volume_price_relations', []),
                    agent_analyses=[],
                    overall_recommendation="持有",
                    overall_confidence=0.5,
                    overall_risk_level="中",
                    key_points=[],
                    warnings=["未启用LLM分析"]
                )
                
                self.logger.info(f"股票分析完成(无LLM): {request.stock_code}")
                return True, "分析完成", comprehensive
            
        except Exception as e:
            self.logger.error(f"股票分析失败: {request.stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def generate_reports(self, analysis: ComprehensiveAnalysis) -> Dict[str, str]:
        try:
            reports = self.reporter.generate_all_reports(analysis)
            self.logger.info(f"报告生成完成: {len(reports)}个")
            return reports
        except Exception as e:
            self.logger.error(f"报告生成失败: {str(e)}")
            return {}


engine = TechAnalysisEngine()


def analyze_stock(stock_code: str, start_date: str, end_date: str, **kwargs) -> Tuple[bool, str, Optional[ComprehensiveAnalysis]]:
    request = AnalysisRequest(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )
    return engine.analyze_stock(request)


def generate_reports(analysis: ComprehensiveAnalysis) -> Dict[str, str]:
    return engine.generate_reports(analysis)
