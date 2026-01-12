from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
import json
from datetime import datetime
from .models import (
    StockAnalysisRequest, StockAnalysisResult, 
    KnowledgeEntry, AnalysisDimension, AnalysisFramework,
    MainForceBehavior, TradingStrategy
)
from .knowledge_base import KnowledgeBase
from .data_fetcher import StockDataFetcher
from .technical_analyzer import TechnicalAnalyzer
from seer.logger import logger


class AnalysisAgent(ABC):
    def __init__(self, agent_name: str, knowledge_base: KnowledgeBase):
        self.agent_name = agent_name
        self.knowledge_base = knowledge_base
        self.logger = logger
    
    @abstractmethod
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        pass
    
    def _search_knowledge(self, query: str, category: str = None) -> List[KnowledgeEntry]:
        return self.knowledge_base.search_knowledge(query, category, limit=5)
    
    def _get_analysis_dimensions(self) -> List[AnalysisDimension]:
        return self.knowledge_base.get_analysis_dimensions()
    
    def _get_analysis_frameworks(self) -> List[AnalysisFramework]:
        return self.knowledge_base.get_analysis_frameworks()


class FundamentalAnalysisAgent(AnalysisAgent):
    def __init__(self, knowledge_base: KnowledgeBase, data_fetcher: StockDataFetcher):
        super().__init__("基本面分析Agent", knowledge_base)
        self.data_fetcher = data_fetcher
    
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"{self.agent_name} 开始分析: {request.stock_code}")
            
            stock_code = request.stock_code
            
            success, msg, fundamental_data = self.data_fetcher.get_stock_fundamental_data(stock_code)
            
            if not success or not fundamental_data:
                return False, f"获取基本面数据失败: {msg}", None
            
            success, msg, financial_data = self.data_fetcher.get_stock_financial_data(stock_code)
            
            if not success or not financial_data:
                return False, f"获取财务数据失败: {msg}", None
            
            analysis = self._analyze_fundamental(fundamental_data, financial_data)
            
            result = {
                'agent_name': self.agent_name,
                'analysis_type': 'fundamental',
                'fundamental_data': fundamental_data,
                'financial_data': financial_data,
                'analysis': analysis,
                'recommendation': analysis.get('recommendation', '观望'),
                'confidence': analysis.get('confidence', 0.6),
                'risk_level': analysis.get('risk_level', '中'),
                'key_points': analysis.get('key_points', []),
                'opportunities': analysis.get('opportunities', []),
                'risks': analysis.get('risks', [])
            }
            
            self.logger.info(f"{self.agent_name} 分析完成")
            return True, "分析成功", result
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 分析失败: {str(e)}")
            return False, str(e), None
    
    def _analyze_fundamental(self, fundamental_data: Dict[str, Any], 
                           financial_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = {
            'key_points': [],
            'opportunities': [],
            'risks': [],
            'recommendation': '观望',
            'confidence': 0.6,
            'risk_level': '中'
        }
        
        pe_ratio = fundamental_data.get('pe', 0)
        pb_ratio = fundamental_data.get('pb', 0)
        market_cap = fundamental_data.get('total_mv', 0)
        
        if pe_ratio and pe_ratio > 0:
            if pe_ratio < 15:
                analysis['key_points'].append(f"市盈率({pe_ratio:.2f})较低，估值合理")
                analysis['opportunities'].append("估值偏低，具备投资价值")
                analysis['confidence'] += 0.1
            elif pe_ratio > 50:
                analysis['key_points'].append(f"市盈率({pe_ratio:.2f})较高，估值偏高")
                analysis['risks'].append("估值偏高，注意回调风险")
                analysis['risk_level'] = '高'
                analysis['confidence'] -= 0.1
            else:
                analysis['key_points'].append(f"市盈率({pe_ratio:.2f})处于正常区间")
        
        if pb_ratio and pb_ratio > 0:
            if pb_ratio < 2:
                analysis['key_points'].append(f"市净率({pb_ratio:.2f})较低，安全边际较高")
                analysis['opportunities'].append("市净率低，具备安全边际")
                analysis['confidence'] += 0.05
            elif pb_ratio > 5:
                analysis['key_points'].append(f"市净率({pb_ratio:.2f})较高，估值偏高")
                analysis['risks'].append("市净率偏高，注意风险")
                analysis['confidence'] -= 0.05
        
        if market_cap and market_cap > 0:
            if market_cap < 100000000000:
                analysis['key_points'].append(f"市值({market_cap/100000000:.2f}亿)较小，弹性较大")
                analysis['opportunities'].append("小市值股票，具备成长弹性")
            elif market_cap > 1000000000000:
                analysis['key_points'].append(f"市值({market_cap/100000000:.2f}亿)较大，稳定性较好")
                analysis['risks'].append("大市值股票，成长性相对较弱")
        
        if analysis['confidence'] > 0.75:
            analysis['recommendation'] = '买入'
        elif analysis['confidence'] > 0.65:
            analysis['recommendation'] = '持有'
        else:
            analysis['recommendation'] = '观望'
        
        analysis['confidence'] = max(0, min(1, analysis['confidence']))
        
        return analysis


class TechnicalAnalysisAgent(AnalysisAgent):
    def __init__(self, knowledge_base: KnowledgeBase, technical_analyzer: TechnicalAnalyzer):
        super().__init__("技术面分析Agent", knowledge_base)
        self.technical_analyzer = technical_analyzer
    
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"{self.agent_name} 开始分析: {request.stock_code}")
            
            stock_data = context.get('stock_data', [])
            
            if not stock_data:
                return False, "缺少股票数据", None
            
            analysis_result = self.technical_analyzer.comprehensive_analysis(stock_data)
            
            knowledge = self._search_knowledge("技术形态", "技术分析")
            
            analysis = self._analyze_technical(analysis_result, knowledge)
            
            result = {
                'agent_name': self.agent_name,
                'analysis_type': 'technical',
                'technical_data': analysis_result,
                'knowledge': knowledge,
                'analysis': analysis,
                'recommendation': analysis.get('recommendation', '观望'),
                'confidence': analysis.get('confidence', 0.6),
                'risk_level': analysis.get('risk_level', '中'),
                'key_points': analysis.get('key_points', []),
                'opportunities': analysis.get('opportunities', []),
                'risks': analysis.get('risks', [])
            }
            
            self.logger.info(f"{self.agent_name} 分析完成")
            return True, "分析成功", result
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 分析失败: {str(e)}")
            return False, str(e), None
    
    def _analyze_technical(self, technical_data: Dict[str, Any], 
                       knowledge: List[KnowledgeEntry]) -> Dict[str, Any]:
        analysis = {
            'key_points': [],
            'opportunities': [],
            'risks': [],
            'recommendation': '观望',
            'confidence': 0.6,
            'risk_level': '中'
        }
        
        main_force = technical_data.get('main_force', {})
        current_phase = main_force.get('current_phase', '')
        
        analysis['key_points'].append(f"当前阶段: {current_phase}")
        
        patterns = technical_data.get('patterns', {})
        
        if patterns.get('neckline_breakthrough', {}).get('detected'):
            analysis['key_points'].append("检测到颈线突破形态")
            analysis['opportunities'].append("颈线突破，可考虑跟进")
            analysis['confidence'] += 0.15
            analysis['recommendation'] = '买入'
        
        if patterns.get('box_breakthrough', {}).get('detected'):
            analysis['key_points'].append("检测到箱体突破形态")
            analysis['opportunities'].append("箱体突破，可考虑加仓")
            analysis['confidence'] += 0.1
        
        if patterns.get('bottom_patterns', {}).get('detected'):
            analysis['key_points'].append("检测到底部形态")
            analysis['opportunities'].append("底部形态，可考虑逢低吸纳")
            analysis['confidence'] += 0.1
        
        if patterns.get('top_patterns', {}).get('detected'):
            analysis['key_points'].append("检测到顶部形态")
            analysis['risks'].append("顶部形态，建议减仓或离场")
            analysis['confidence'] -= 0.15
            analysis['recommendation'] = '卖出'
            analysis['risk_level'] = '高'
        
        volume_price = technical_data.get('volume_price', {})
        relation_type = volume_price.get('relation_type', '')
        
        if relation_type == "量增价涨":
            analysis['key_points'].append("量增价涨，多头力量强劲")
            analysis['opportunities'].append("量价齐升，可持股待涨")
            analysis['confidence'] += 0.1
        elif relation_type == "量增价跌":
            analysis['key_points'].append("量增价跌，恐慌性抛售")
            analysis['risks'].append("量增价跌，恐慌抛售，建议观望")
            analysis['confidence'] -= 0.1
        elif relation_type == "量减价涨":
            analysis['key_points'].append("量减价涨，上涨动力不足")
            analysis['risks'].append("量减价涨，动力不足，注意风险")
            analysis['confidence'] -= 0.05
        
        macd = technical_data.get('macd', {})
        if macd.get('description'):
            analysis['key_points'].append(f"MACD: {macd['description']}")
        
        rsi = technical_data.get('rsi', {})
        if rsi.get('description'):
            analysis['key_points'].append(f"RSI: {rsi['description']}")
        
        kdj = technical_data.get('kdj', {})
        if kdj.get('description'):
            analysis['key_points'].append(f"KDJ: {kdj['description']}")
        
        for entry in knowledge:
            if '机会' in entry.content or '买入' in entry.content:
                analysis['opportunities'].append(entry.content)
            elif '风险' in entry.content or '卖出' in entry.content:
                analysis['risks'].append(entry.content)
        
        if analysis['confidence'] > 0.75:
            analysis['recommendation'] = '买入'
        elif analysis['confidence'] > 0.65:
            analysis['recommendation'] = '持有'
        elif analysis['confidence'] < 0.55:
            analysis['recommendation'] = '卖出'
        
        analysis['confidence'] = max(0, min(1, analysis['confidence']))
        
        return analysis


class IndustryAnalysisAgent(AnalysisAgent):
    def __init__(self, knowledge_base: KnowledgeBase, data_fetcher: StockDataFetcher):
        super().__init__("行业分析Agent", knowledge_base)
        self.data_fetcher = data_fetcher
    
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"{self.agent_name} 开始分析: {request.stock_code}")
            
            stock_code = request.stock_code
            
            success, msg, fundamental_data = self.data_fetcher.get_stock_fundamental_data(stock_code)
            
            if not success or not fundamental_data:
                return False, f"获取基本面数据失败: {msg}", None
            
            industry_name = fundamental_data.get('industry', '')
            
            if not industry_name:
                return False, "未获取到行业信息", None
            
            success, msg, industry_data = self.data_fetcher.get_industry_data(industry_name)
            
            if not success or not industry_data:
                return False, f"获取行业数据失败: {msg}", None
            
            analysis = self._analyze_industry(industry_data, fundamental_data)
            
            result = {
                'agent_name': self.agent_name,
                'analysis_type': 'industry',
                'industry_data': industry_data,
                'fundamental_data': fundamental_data,
                'analysis': analysis,
                'recommendation': analysis.get('recommendation', '观望'),
                'confidence': analysis.get('confidence', 0.6),
                'risk_level': analysis.get('risk_level', '中'),
                'key_points': analysis.get('key_points', []),
                'opportunities': analysis.get('opportunities', []),
                'risks': analysis.get('risks', [])
            }
            
            self.logger.info(f"{self.agent_name} 分析完成")
            return True, "分析成功", result
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 分析失败: {str(e)}")
            return False, str(e), None
    
    def _analyze_industry(self, industry_data: Dict[str, Any], 
                       fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = {
            'key_points': [],
            'opportunities': [],
            'risks': [],
            'recommendation': '观望',
            'confidence': 0.6,
            'risk_level': '中'
        }
        
        total_stocks = industry_data.get('total_stocks', 0)
        stocks = industry_data.get('stocks', [])
        
        analysis['key_points'].append(f"所属行业共有 {total_stocks} 只股票")
        
        if total_stocks > 0:
            analysis['key_points'].append(f"行业规模较大，竞争激烈")
            analysis['risks'].append("行业竞争激烈，需关注个股竞争力")
        elif total_stocks > 50:
            analysis['key_points'].append(f"行业规模适中")
            analysis['opportunities'].append("行业规模适中，具备发展空间")
        else:
            analysis['key_points'].append(f"行业规模较小")
            analysis['opportunities'].append("行业规模较小，成长空间较大")
        
        market_cap = fundamental_data.get('total_mv', 0)
        
        if stocks:
            industry_market_caps = [s.get('total_mv', 0) for s in stocks if s.get('total_mv', 0) > 0]
            if industry_market_caps:
                avg_market_cap = sum(industry_market_caps) / len(industry_market_caps)
                
                if market_cap > avg_market_cap * 1.5:
                    analysis['key_points'].append(f"市值({market_cap/100000000:.2f}亿)高于行业平均")
                    analysis['risks'].append("市值高于行业平均，需关注估值合理性")
                    analysis['confidence'] -= 0.05
                elif market_cap < avg_market_cap * 0.5:
                    analysis['key_points'].append(f"市值({market_cap/100000000:.2f}亿)低于行业平均")
                    analysis['opportunities'].append("市值低于行业平均，具备成长空间")
                    analysis['confidence'] += 0.05
        
        knowledge = self._search_knowledge("行业轮动", "市场环境")
        for entry in knowledge:
            if '机会' in entry.content:
                analysis['opportunities'].append(entry.content)
            elif '风险' in entry.content:
                analysis['risks'].append(entry.content)
        
        if analysis['confidence'] > 0.7:
            analysis['recommendation'] = '买入'
        elif analysis['confidence'] > 0.6:
            analysis['recommendation'] = '持有'
        
        analysis['confidence'] = max(0, min(1, analysis['confidence']))
        
        return analysis


class RiskAssessmentAgent(AnalysisAgent):
    def __init__(self, knowledge_base: KnowledgeBase):
        super().__init__("风险评估Agent", knowledge_base)
    
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"{self.agent_name} 开始分析: {request.stock_code}")
            
            technical_data = context.get('technical_data', {})
            fundamental_data = context.get('fundamental_data', {})
            
            analysis = self._assess_risk(technical_data, fundamental_data)
            
            result = {
                'agent_name': self.agent_name,
                'analysis_type': 'risk',
                'technical_data': technical_data,
                'fundamental_data': fundamental_data,
                'analysis': analysis,
                'recommendation': analysis.get('recommendation', '观望'),
                'confidence': analysis.get('confidence', 0.6),
                'risk_level': analysis.get('risk_level', '中'),
                'key_points': analysis.get('key_points', []),
                'opportunities': analysis.get('opportunities', []),
                'risks': analysis.get('risks', [])
            }
            
            self.logger.info(f"{self.agent_name} 分析完成")
            return True, "分析成功", result
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 分析失败: {str(e)}")
            return False, str(e), None
    
    def _assess_risk(self, technical_data: Dict[str, Any], 
                     fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = {
            'key_points': [],
            'opportunities': [],
            'risks': [],
            'recommendation': '观望',
            'confidence': 0.6,
            'risk_level': '中'
        }
        
        risk_score = 0
        
        main_force = technical_data.get('main_force', {})
        risk_level = main_force.get('risk_level', '中')
        
        if risk_level == '高':
            risk_score += 3
            analysis['key_points'].append("技术面评估风险等级为高")
            analysis['risks'].append("技术面风险较高，建议谨慎操作")
        elif risk_level == '低':
            risk_score -= 1
            analysis['key_points'].append("技术面评估风险等级为低")
            analysis['opportunities'].append("技术面风险较低，可考虑介入")
        
        patterns = technical_data.get('patterns', {})
        
        if patterns.get('top_patterns', {}).get('detected'):
            risk_score += 2
            analysis['key_points'].append("检测到顶部形态")
            analysis['risks'].append("顶部形态，注意见顶风险")
        
        volume_price = technical_data.get('volume_price', {})
        relation_type = volume_price.get('relation_type', '')
        
        if relation_type == "量增价跌":
            risk_score += 2
            analysis['key_points'].append("量增价跌，恐慌性抛售")
            analysis['risks'].append("量增价跌，恐慌抛售，风险较高")
        elif relation_type == "量减价跌":
            risk_score += 1
            analysis['key_points'].append("量减价跌，下跌动力不足")
            analysis['risks'].append("量减价跌，下跌动力不足")
        
        pe_ratio = fundamental_data.get('pe', 0)
        
        if pe_ratio and pe_ratio > 50:
            risk_score += 1
            analysis['key_points'].append(f"市盈率({pe_ratio:.2f})较高")
            analysis['risks'].append("估值偏高，注意回调风险")
        elif pe_ratio and pe_ratio < 15:
            risk_score -= 1
            analysis['key_points'].append(f"市盈率({pe_ratio:.2f})较低")
            analysis['opportunities'].append("估值较低，具备安全边际")
        
        if risk_score >= 4:
            analysis['risk_level'] = '高'
            analysis['recommendation'] = '卖出'
            analysis['confidence'] = 0.4
        elif risk_score >= 2:
            analysis['risk_level'] = '中'
            analysis['recommendation'] = '持有'
            analysis['confidence'] = 0.6
        else:
            analysis['risk_level'] = '低'
            analysis['recommendation'] = '买入'
            analysis['confidence'] = 0.8
        
        knowledge = self._search_knowledge("风险控制", "风险控制")
        for entry in knowledge:
            if '机会' in entry.content:
                analysis['opportunities'].append(entry.content)
            elif '风险' in entry.content:
                analysis['risks'].append(entry.content)
        
        return analysis
