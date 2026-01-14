from typing import Dict, Any, Optional
from .models import StockAnalysisRequest, StockAnalysisResult
from .agents import PrimaryThinkingAgent as PrimaryThinkingAgentImpl
from seer.logger import logger


class PrimaryAgentCoordinator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.config = config or {}
        
        src_data_dir = self.config.get('src_data_dir', './src_data')
        
        self.primary_thinking_agent = PrimaryThinkingAgentImpl(
            src_data_dir=src_data_dir,
            config=config
        )
        
        self.logger.info("初始化 PrimaryAgentCoordinator 完成")
    
    def run_full_analysis(self, request: StockAnalysisRequest) -> tuple[bool, str, Optional[StockAnalysisResult]]:
        try:
            self.logger.info("开始完整分析流程...")
            
            success, msg, result = self.primary_thinking_agent.run_full_analysis(request)
            
            if success:
                self.logger.info(f"完整分析完成，建议: {result.recommendation}，置信度: {result.confidence:.2f}")
            else:
                self.logger.warning(f"完整分析失败: {msg}")
            
            return success, msg, result
            
        except Exception as e:
            self.logger.error(f"完整分析流程失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e), None
    
    def analyze(self, request: StockAnalysisRequest, 
                context: Optional[Dict[str, Any]] = None) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            self.logger.info(f"开始分析股票: {request.stock_code}")
            
            success, msg, analysis = self.primary_thinking_agent.analyze(request, context)
            
            if success:
                self.logger.info(f"分析完成，建议: {analysis.get('recommendation', '未知')}")
            else:
                self.logger.warning(f"分析失败: {msg}")
            
            return success, msg, analysis
            
        except Exception as e:
            self.logger.error(f"分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e), None
    
    def reload_knowledge(self, src_data_dir: str = None):
        try:
            self.logger.info("重新加载知识库...")
            self.primary_thinking_agent.reload_knowledge(src_data_dir)
            self.logger.info("知识库重新加载完成")
        except Exception as e:
            self.logger.error(f"重新加载知识库失败: {str(e)}")
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        try:
            return self.primary_thinking_agent.get_knowledge_stats()
        except Exception as e:
            self.logger.error(f"获取知识库统计信息失败: {str(e)}")
            return {}


PrimaryThinkingAgent = PrimaryAgentCoordinator