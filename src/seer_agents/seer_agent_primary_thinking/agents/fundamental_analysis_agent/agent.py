from typing import Dict, Any, Optional, List, Tuple
from google.adk.agents import LlmAgent
from ...models import (
    StockAnalysisRequest, StockAnalysisResult, 
    KnowledgeEntry
)
from ...knowledge_base import KnowledgeBase
from ...data_fetcher import StockDataFetcher
from ...adk_config import adk_config
from ...adk_runner import get_adk_runner
from seer.logger import logger


class FundamentalAnalysisAgent:
    def __init__(self, knowledge_base: KnowledgeBase, data_fetcher: StockDataFetcher):
        self.agent_name = "基本面分析Agent"
        self.knowledge_base = knowledge_base
        self.data_fetcher = data_fetcher
        self.logger = logger
        self.config = adk_config
        
        self.description = "负责分析股票的基本面数据，包括估值指标、财务数据等"
        self.instructions = """你是一个专业的股票基本面分析专家。你的任务是：
1. 分析股票的估值指标（市盈率、市净率等）
2. 分析财务数据（营收、利润、现金流等）
3. 评估股票的投资价值和风险
4. 提供买入、持有或观望的建议
5. 给出置信度（0-1之间）
6. 识别风险等级（低、中、高）
7. 列出关键分析要点
8. 识别投资机会
9. 提示潜在风险

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
            
            stock_code = request.stock_code
            
            success, msg, fundamental_data = self.data_fetcher.get_stock_fundamental_data(stock_code)
            
            if not success or not fundamental_data:
                return False, f"获取基本面数据失败: {msg}", None
            
            success, msg, financial_data = self.data_fetcher.get_stock_financial_data(stock_code)
            
            if not success or not financial_data:
                return False, f"获取财务数据失败: {msg}", None
            
            analysis = self._analyze_fundamental_with_llm(fundamental_data, financial_data, request)
            
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
    
    def _analyze_fundamental_with_llm(self, fundamental_data: Dict[str, Any], 
                                     financial_data: Dict[str, Any],
                                     request: StockAnalysisRequest) -> Dict[str, Any]:
        try:
            prompt = f"""请分析以下股票的基本面数据：

股票代码：{request.stock_code}
股票名称：{request.stock_name or '未知'}

基本面数据：
- 市盈率(PE)：{fundamental_data.get('pe', 'N/A')}
- 市净率(PB)：{fundamental_data.get('pb', 'N/A')}
- 市值：{fundamental_data.get('total_mv', 'N/A')}
- 总股本：{fundamental_data.get('total_share', 'N/A')}
- 流通股本：{fundamental_data.get('float_share', 'N/A')}

财务数据：
- 营业收入：{financial_data.get('total_operating_revenue', 'N/A')}
- 净利润：{financial_data.get('net_profit', 'N/A')}
- 毛利率：{financial_data.get('gross_profit_margin', 'N/A')}
- 净利率：{financial_data.get('net_profit_margin', 'N/A')}
- ROE：{financial_data.get('roe', 'N/A')}

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
                session_id=f"session_{request.stock_code}_fundamental"
            )
            
            import json
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = self._analyze_fundamental(fundamental_data, financial_data)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM分析失败: {str(e)}")
            return self._analyze_fundamental(fundamental_data, financial_data)
    
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
    
    def _search_knowledge(self, query: str, category: str = None) -> List[KnowledgeEntry]:
        return self.knowledge_base.search_knowledge(query, category, limit=5)
