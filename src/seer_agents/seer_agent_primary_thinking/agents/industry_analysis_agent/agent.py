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


class IndustryAnalysisAgent:
    def __init__(self, knowledge_base: KnowledgeBase, data_fetcher: StockDataFetcher):
        self.agent_name = "行业分析Agent"
        self.knowledge_base = knowledge_base
        self.data_fetcher = data_fetcher
        self.logger = logger
        self.config = adk_config
        
        self.description = "负责分析股票所属行业的情况，包括行业规模、竞争格局等"
        self.instructions = """你是一个专业的行业分析专家。你的任务是：
1. 分析行业发展趋势
2. 评估行业竞争格局
3. 分析行业政策环境
4. 评估股票在行业中的地位
5. 识别行业投资机会
6. 评估行业风险
7. 提供买入、持有或观望的建议
8. 给出置信度（0-1之间）
9. 识别风险等级（低、中、高）
10. 列出关键分析要点
11. 识别投资机会
12. 提示潜在风险

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
            
            industry_name = fundamental_data.get('industry', '')
            
            if not industry_name:
                return False, "未获取到行业信息", None
            
            success, msg, industry_data = self.data_fetcher.get_industry_data(industry_name)
            
            if not success or not industry_data:
                return False, f"获取行业数据失败: {msg}", None
            
            analysis = self._analyze_industry_with_llm(industry_data, fundamental_data, request)
            
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
    
    def _analyze_industry_with_llm(self, industry_data: Dict[str, Any], 
                                   fundamental_data: Dict[str, Any],
                                   request: StockAnalysisRequest) -> Dict[str, Any]:
        try:
            prompt = f"""请分析以下股票的行业情况：

股票代码：{request.stock_code}
股票名称：{request.stock_name or '未知'}
所属行业：{fundamental_data.get('industry', 'N/A')}

行业数据：
- 行业规模：{industry_data.get('industry_scale', 'N/A')}
- 行业增长率：{industry_data.get('industry_growth_rate', 'N/A')}
- 行业竞争格局：{industry_data.get('competition_pattern', 'N/A')}
- 行业政策环境：{industry_data.get('policy_environment', 'N/A')}
- 行业投资热度：{industry_data.get('investment_heat', 'N/A')}
- 行业风险因素：{industry_data.get('risk_factors', 'N/A')}

股票在行业中的地位：
- 市值：{fundamental_data.get('total_mv', 'N/A')}
- 市盈率：{fundamental_data.get('pe', 'N/A')}
- 市净率：{fundamental_data.get('pb', 'N/A')}

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
                session_id=f"session_{request.stock_code}_industry"
            )
            
            import json
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = self._analyze_industry(industry_data, fundamental_data)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM分析失败: {str(e)}")
            return self._analyze_industry(industry_data, fundamental_data)
    
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
        
        if total_stocks > 100:
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
    
    def _search_knowledge(self, query: str, category: str = None) -> List[KnowledgeEntry]:
        return self.knowledge_base.search_knowledge(query, category, limit=5)
