from typing import Dict, Any, Optional, List, Tuple
from google.adk.agents import LlmAgent
from ...models import (
    StockAnalysisRequest, StockAnalysisResult, 
    KnowledgeEntry
)
from ...knowledge_base import KnowledgeBase
from ...adk_config import adk_config
from ...adk_runner import get_adk_runner
from seer.logger import logger


class RiskAssessmentAgent:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.agent_name = "风险评估Agent"
        self.knowledge_base = knowledge_base
        self.logger = logger
        self.config = adk_config
        
        self.description = "负责评估股票的投资风险，包括技术面风险和基本面风险"
        self.instructions = """你是一个专业的风险评估专家。你的任务是：
1. 评估技术面风险（价格波动、技术形态等）
2. 评估基本面风险（财务风险、经营风险等）
3. 评估行业风险（政策风险、竞争风险等）
4. 评估市场风险（系统性风险、流动性风险等）
5. 综合评估整体风险等级
6. 提供风险控制建议
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
            
            technical_data = context.get('technical_data', {})
            fundamental_data = context.get('fundamental_data', {})
            
            analysis = self._assess_risk_with_llm(technical_data, fundamental_data, request)
            
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
    
    def _assess_risk_with_llm(self, technical_data: Dict[str, Any], 
                               fundamental_data: Dict[str, Any],
                               request: StockAnalysisRequest) -> Dict[str, Any]:
        try:
            main_force = technical_data.get('main_force', {})
            indicators = technical_data.get('indicators', {})
            patterns = technical_data.get('patterns', [])
            
            prompt = f"""请评估以下股票的投资风险：

股票代码：{request.stock_code}
股票名称：{request.stock_name or '未知'}

技术面数据：
- 主力状态：{main_force.get('main_force_status', 'N/A')}
- 当前阶段：{main_force.get('current_phase', 'N/A')}
- 主力净流入：{main_force.get('net_inflow', 'N/A')}
- 主力净占比：{main_force.get('net_inflow_ratio', 'N/A')}
- MACD：{indicators.get('macd', 'N/A')}
- RSI：{indicators.get('rsi', 'N/A')}
- KDJ：{indicators.get('kdj', 'N/A')}
- 技术形态：{', '.join(patterns) if patterns else '无明显形态'}

基本面数据：
- 市盈率：{fundamental_data.get('pe', 'N/A')}
- 市净率：{fundamental_data.get('pb', 'N/A')}
- 市值：{fundamental_data.get('total_mv', 'N/A')}
- 营业收入：{fundamental_data.get('total_operating_revenue', 'N/A')}
- 净利润：{fundamental_data.get('net_profit', 'N/A')}
- ROE：{fundamental_data.get('roe', 'N/A')}

请基于以上数据，提供风险评估结果，包括：
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
                session_id=f"session_{request.stock_code}_risk"
            )
            
            import json
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = self._assess_risk(technical_data, fundamental_data)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM分析失败: {str(e)}")
            return self._assess_risk(technical_data, fundamental_data)
    
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
            analysis['key_points'].append(f"市盈率({pe_ratio:.2f})较高，估值风险")
            analysis['risks'].append("市盈率偏高，估值风险较大")
        
        if risk_score >= 5:
            analysis['risk_level'] = '高'
            analysis['recommendation'] = '卖出'
            analysis['confidence'] = 0.5
        elif risk_score >= 3:
            analysis['risk_level'] = '中高'
            analysis['recommendation'] = '观望'
            analysis['confidence'] = 0.6
        elif risk_score >= 1:
            analysis['risk_level'] = '中'
            analysis['recommendation'] = '持有'
            analysis['confidence'] = 0.65
        else:
            analysis['risk_level'] = '低'
            analysis['recommendation'] = '买入'
            analysis['confidence'] = 0.75
        
        return analysis
    
    def _search_knowledge(self, query: str, category: str = None) -> List[KnowledgeEntry]:
        return self.knowledge_base.search_knowledge(query, category, limit=5)
