from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from seer.logger import logger
from ...vector_store import VectorStore
from ...embedding_model import EmbeddingModel
from ...data_fetcher import StockDataFetcher
from ...technical_analyzer import TechnicalAnalyzer
from ...adk_config import adk_config
from ...adk_runner import get_adk_runner
from ...models import StockAnalysisRequest, StockAnalysisResult
from datetime import datetime


class PrimaryThinkingAgent:
    def __init__(self, src_data_dir: str = None, config: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.config = config or {}
        
        src_data_dir = src_data_dir or str(Path(__file__).parent.parent / "src_data")
        
        self.vector_store = VectorStore(**adk_config.get_qdrant_config())
        self.embedding_model = EmbeddingModel(**adk_config.get_embedding_model_config())
        self.data_fetcher = StockDataFetcher(config)
        self.technical_analyzer = TechnicalAnalyzer()
        
        self.llm_agent = self._create_llm_agent()
        self.adk_runner = get_adk_runner()
        
        self.knowledge_loaded = False
        self._load_knowledge(src_data_dir)
    
    def _create_llm_agent(self) -> LiteLlm:
        agent_config = adk_config.get_agent_config()
        
        model_name = adk_config.model.name
        if not model_name.startswith("openai/"):
            model_name = f"openai/{model_name}"
        
        return LiteLlm(
            name=agent_config["name"],
            model=model_name,
            instruction=agent_config["instructions"]
        )
    
    def _load_knowledge(self, src_data_dir: str):
        try:
            self.logger.info(f"开始加载知识库: {src_data_dir}")
            
            success = self.vector_store.build_vector_index(
                src_data_dir,
                self.embedding_model,
                force_rebuild=False
            )
            
            if success:
                self.knowledge_loaded = True
                collection_info = self.vector_store.get_collection_info()
                self.logger.info(f"知识库加载完成: {collection_info}")
            else:
                self.logger.warning("知识库加载失败")
                self.knowledge_loaded = False
            
        except Exception as e:
            self.logger.error(f"加载知识库失败: {str(e)}")
            self.knowledge_loaded = False
    
    def _search_relevant_knowledge(self, query: str, limit: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.embedding_model.get_embedding(query)
            results = self.vector_store.search(query_embedding, limit=limit, score_threshold=score_threshold)
            return results
        except Exception as e:
            self.logger.error(f"搜索相关知识失败: {str(e)}")
            return []
    
    def _prepare_stock_data(self, request: StockAnalysisRequest) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            success, msg, stock_data = self.data_fetcher.get_stock_daily_data(
                request.stock_code,
                request.start_date,
                request.end_date
            )
            
            if not success or not stock_data:
                return False, f"获取股票数据失败: {msg}", {}
            
            technical_analysis = self.technical_analyzer.comprehensive_analysis(stock_data)
            
            success, msg, fundamental_data = self.data_fetcher.get_stock_fundamental_data(request.stock_code)
            
            if not success:
                fundamental_data = {}
            
            stock_info = {
                'stock_code': request.stock_code,
                'stock_name': request.stock_name or '',
                'stock_data': stock_data,
                'technical_analysis': technical_analysis,
                'fundamental_data': fundamental_data,
                'current_price': technical_analysis.get('current_price'),
                'price_change': technical_analysis.get('price_change', 0),
                'volume_change': technical_analysis.get('volume_change', 0)
            }
            
            return True, "股票数据准备完成", stock_info
            
        except Exception as e:
            self.logger.error(f"准备股票数据失败: {str(e)}")
            return False, str(e), {}
    
    def _format_stock_data_for_analysis(self, stock_info: Dict[str, Any]) -> str:
        technical = stock_info.get('technical_analysis', {})
        fundamental = stock_info.get('fundamental_data', {})
        
        info_text = f"""
股票代码：{stock_info.get('stock_code', 'N/A')}
股票名称：{stock_info.get('stock_name', 'N/A')}
当前价格：{stock_info.get('current_price', 'N/A')}
价格变动：{stock_info.get('price_change', 0):.2f}%
成交量变动：{stock_info.get('volume_change', 0):.2f}%

技术分析：
- MA5：{technical.get('ma', {}).get('ma5', 'N/A')}
- MA10：{technical.get('ma', {}).get('ma10', 'N/A')}
- MA20：{technical.get('ma', {}).get('ma20', 'N/A')}
- MACD DIF：{technical.get('macd', {}).get('dif', 'N/A')}
- MACD DEA：{technical.get('macd', {}).get('dea', 'N/A')}
- RSI：{technical.get('rsi', {}).get('rsi', 'N/A')}
- KDJ K：{technical.get('kdj', {}).get('k', 'N/A')}
- KDJ D：{technical.get('kdj', {}).get('d', 'N/A')}
- 主力状态：{technical.get('main_force', {}).get('main_force_status', 'N/A')}
- 交易阶段：{technical.get('main_force', {}).get('current_phase', 'N/A')}

基本面：
- 市盈率(PE)：{fundamental.get('市盈率-动态', 'N/A')}
- 市净率(PB)：{fundamental.get('市净率', 'N/A')}
- 总市值：{fundamental.get('总市值', 'N/A')}
- 换手率：{fundamental.get('换手率', 'N/A')}
"""
        return info_text
    
    def _format_knowledge_for_analysis(self, knowledge_results: List[Dict[str, Any]]) -> str:
        if not knowledge_results:
            return "未找到相关知识"
        
        knowledge_text = "相关知识：\n"
        for i, result in enumerate(knowledge_results, 1):
            knowledge_text += f"\n{i}. {result['content']}\n"
        
        return knowledge_text
    
    def _build_analysis_prompt(self, request: StockAnalysisRequest, 
                               stock_info: Dict[str, Any],
                               knowledge_results: List[Dict[str, Any]]) -> str:
        stock_data_text = self._format_stock_data_for_analysis(stock_info)
        knowledge_text = self._format_knowledge_for_analysis(knowledge_results)
        
        prompt = f"""请基于以下股票数据和相关投资知识，对该股票进行全面分析：

{stock_data_text}

{knowledge_text}

请基于B站投资专家'领居大爷'的思维模式，从以下维度进行分析：

1. 主力行为分析：根据技术指标和成交量，分析主力资金的操作意图
2. 技术形态识别：识别当前的技术形态，判断是否处于关键位置
3. 量价关系分析：分析成交量与价格的关系，判断资金流向
4. 盘整充分性判断：根据相关知识，判断当前盘整是否充分
5. 主升浪判断：根据相关知识，判断是否处于主升浪阶段
6. 风险评估：识别潜在风险点

请以JSON格式返回分析结果，格式如下：
{{
    "recommendation": "买入/持有/观望/卖出",
    "confidence": 0.8,
    "risk_level": "低/中/高",
    "key_points": ["要点1", "要点2", "要点3"],
    "opportunities": ["机会1", "机会2"],
    "risks": ["风险1", "风险2"],
    "reasoning": "详细的分析逻辑说明"
}}
"""
        return prompt
    
    def analyze(self, request: StockAnalysisRequest, 
                context: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"开始分析股票: {request.stock_code}")
            
            if not self.knowledge_loaded:
                self.logger.warning("知识库未加载，分析结果可能不准确")
            
            success, msg, stock_info = self._prepare_stock_data(request)
            
            if not success:
                return False, msg, None
            
            query = f"分析股票 {request.stock_code} 的投资机会"
            knowledge_results = self._search_relevant_knowledge(query, limit=5, score_threshold=0.0)
            
            prompt = self._build_analysis_prompt(request, stock_info, knowledge_results)
            
            response_text = self.adk_runner.run_agent_sync(
                self.llm_agent,
                prompt,
                user_id=f"user_{request.stock_code}",
                session_id=f"session_{request.stock_code}"
            )
            
            try:
                cleaned_response = response_text.strip()
                
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                
                cleaned_response = cleaned_response.strip()
                
                analysis = json.loads(cleaned_response)
                analysis['stock_code'] = request.stock_code
                analysis['stock_name'] = request.stock_name or ''
                analysis['analysis_date'] = datetime.now().strftime("%Y-%m-%d")
                analysis['knowledge_used'] = len(knowledge_results)
                analysis['stock_info'] = stock_info
                
                return True, "分析完成", analysis
                
            except json.JSONDecodeError as e:
                self.logger.error(f"解析分析结果失败: {str(e)}")
                self.logger.debug(f"原始响应: {response_text}")
                
                fallback_analysis = {
                    'recommendation': '观望',
                    'confidence': 0.5,
                    'risk_level': '中',
                    'key_points': ['分析结果解析失败'],
                    'opportunities': [],
                    'risks': ['无法确定风险'],
                    'reasoning': response_text,
                    'stock_code': request.stock_code,
                    'stock_name': request.stock_name or '',
                    'analysis_date': datetime.now().strftime("%Y-%m-%d"),
                    'knowledge_used': len(knowledge_results),
                    'stock_info': stock_info
                }
                
                return True, "分析完成（使用备用结果）", fallback_analysis
                
        except Exception as e:
            self.logger.error(f"分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e), None
    
    def run_full_analysis(self, request: StockAnalysisRequest) -> Tuple[bool, str, Optional[StockAnalysisResult]]:
        try:
            self.logger.info("开始完整分析流程...")
            
            success, msg, analysis = self.analyze(request)
            
            if not success or not analysis:
                return False, msg, None
            
            stock_info = analysis.get('stock_info', {})
            technical_analysis = stock_info.get('technical_analysis', {})
            
            result = StockAnalysisResult(
                stock_code=request.stock_code,
                stock_name=request.stock_name or '',
                analysis_date=analysis.get('analysis_date', datetime.now().strftime("%Y-%m-%d")),
                fundamental_analysis=stock_info.get('fundamental_data', {}),
                technical_analysis=technical_analysis,
                industry_analysis={},
                risk_assessment={'overall_risk_level': analysis.get('risk_level', '中')},
                main_force_status=technical_analysis.get('main_force', {}).get('main_force_status', ''),
                trading_phase=technical_analysis.get('main_force', {}).get('current_phase', ''),
                recommendation=analysis.get('recommendation', '观望'),
                confidence=analysis.get('confidence', 0.5),
                risk_level=analysis.get('risk_level', '中'),
                key_points=analysis.get('key_points', []),
                opportunities=analysis.get('opportunities', []),
                risks=analysis.get('risks', []),
                reasoning=analysis.get('reasoning', '')
            )
            
            self.logger.info(f"完整分析完成，建议: {result.recommendation}，置信度: {result.confidence:.2f}")
            
            return True, "完整分析完成", result
            
        except Exception as e:
            self.logger.error(f"完整分析流程失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e), None
    
    def reload_knowledge(self, src_data_dir: str = None):
        src_data_dir = src_data_dir or str(Path(__file__).parent.parent / "src_data")
        self._load_knowledge(src_data_dir)
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        collection_info = self.vector_store.get_collection_info()
        return {
            'knowledge_loaded': self.knowledge_loaded,
            'collection_info': collection_info
        }
