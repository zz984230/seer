from typing import Dict, Any, Optional, List, Tuple
from google.adk.agents import LlmAgent
from ...models import (
    StockAnalysisRequest, StockAnalysisResult, 
    KnowledgeEntry
)
from ...knowledge_base import KnowledgeBase
from ...technical_analyzer import TechnicalAnalyzer
from ...adk_config import adk_config
from ...adk_runner import get_adk_runner
from seer.logger import logger


class TechnicalAnalysisAgent:
    def __init__(self, knowledge_base: KnowledgeBase, technical_analyzer: TechnicalAnalyzer):
        self.agent_name = "技术面分析Agent"
        self.knowledge_base = knowledge_base
        self.technical_analyzer = technical_analyzer
        self.logger = logger
        self.config = adk_config
        
        self.description = "负责分析股票的技术面数据，包括技术指标、形态识别等"
        self.instructions = """你是一个专业的股票技术分析专家。你的任务是：
1. 分析技术指标（MACD、RSI、KDJ等）
2. 识别技术形态（头肩顶/底、双顶/底、三角形等）
3. 分析量价关系
4. 识别主力资金流向
5. 评估当前交易阶段
6. 提供买入、持有或观望的建议
7. 给出置信度（0-1之间）
8. 识别风险等级（低、中、高）
9. 列出关键分析要点
10. 识别投资机会
11. 提示潜在风险

请基于提供的数据进行客观分析，给出合理的投资建议。"""
        
        self._init_llm_agent()
    
    def _init_llm_agent(self):
        agent_config = self.config.get_llm_agent_config(
            self.agent_name,
            self.instructions
        )
        
        self.llm_agent = LlmAgent(
            name=agent_config["name"],
            model=agent_config["model"],
            instruction=agent_config["instruction"],
            generate_content_config=agent_config["generate_content_config"]
        )
        
        self.logger.info(f"初始化 {self.agent_name} LlmAgent")
    
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"{self.agent_name} 开始分析: {request.stock_code}")
            
            stock_data = context.get('stock_data', [])
            
            if not stock_data:
                return False, "缺少股票数据", None
            
            analysis_result = self.technical_analyzer.comprehensive_analysis(stock_data)
            
            knowledge = self._search_knowledge("技术形态", "技术分析")
            
            analysis = self._analyze_technical_with_llm(analysis_result, knowledge, request)
            
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
    
    def _analyze_technical_with_llm(self, technical_data: Dict[str, Any], 
                                    knowledge: List[KnowledgeEntry],
                                    request: StockAnalysisRequest) -> Dict[str, Any]:
        try:
            main_force = technical_data.get('main_force', {})
            indicators = technical_data.get('indicators', {})
            patterns = technical_data.get('patterns', [])
            
            prompt = f"""请分析以下股票的技术面数据：

股票代码：{request.stock_code}
股票名称：{request.stock_name or '未知'}

主力资金分析：
- 主力状态：{main_force.get('main_force_status', 'N/A')}
- 当前阶段：{main_force.get('current_phase', 'N/A')}
- 主力净流入：{main_force.get('net_inflow', 'N/A')}
- 主力净占比：{main_force.get('net_inflow_ratio', 'N/A')}

技术指标：
- MACD：{indicators.get('macd', 'N/A')}
- RSI：{indicators.get('rsi', 'N/A')}
- KDJ：{indicators.get('kdj', 'N/A')}
- MA5：{indicators.get('ma5', 'N/A')}
- MA10：{indicators.get('ma10', 'N/A')}
- MA20：{indicators.get('ma20', 'N/A')}
- MA60：{indicators.get('ma60', 'N/A')}

技术形态：
{', '.join(patterns) if patterns else '无明显形态'}

请基于以上数据，提供分析结果，包括：
1. 推荐建议（买入/持有/观望）
2. 置信度（0-1之间的数值）
3. 风险等级（低/中/高）
4. 关键分析要点（3-5条）
5. 投资机会（2-3条）
6. 潜在风险（2-3条）

请以JSON格式返回结果，格式如下：
{{
    "recommendation": "买入/持有/观望",
    "confidence": 0.8,
    "risk_level": "低/中/高",
    "key_points": ["要点1", "要点2", "要点3"],
    "opportunities": ["机会1", "机会2"],
    "risks": ["风险1", "风险2"]
}}"""
            
            runner = get_adk_runner()
            response_text = runner.run_agent_sync(
                self.llm_agent,
                prompt,
                user_id=f"user_{request.stock_code}",
                session_id=f"session_{request.stock_code}_technical"
            )
            
            import json
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = self._analyze_technical(technical_data, knowledge)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM分析失败: {str(e)}")
            return self._analyze_technical(technical_data, knowledge)
    
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
    
    def _search_knowledge(self, query: str, category: str = None) -> List[KnowledgeEntry]:
        return self.knowledge_base.search_knowledge(query, category, limit=5)
