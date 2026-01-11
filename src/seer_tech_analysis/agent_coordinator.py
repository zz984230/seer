from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm
from .llm_agent import LLMAgent
from .models import AgentAnalysis, ComprehensiveAnalysis
from .config import settings
from seer.logger import logger

tqdm.set_lock(threading.Lock())


class AgentCoordinator:
    def __init__(self):
        self.logger = logger
        self.config = settings.llm
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        if not self.config.enable_multi_agent:
            self.logger.info("多Agent模式未启用")
            return
        
        for agent_type in self.config.agent_types:
            agent_name = f"{agent_type}_agent"
            self.agents[agent_name] = LLMAgent(
                agent_name=agent_name,
                agent_type=agent_type
            )
            self.logger.info(f"初始化Agent: {agent_name}")
    
    def _run_single_agent(self, agent_name: str, context: Dict[str, Any]) -> Tuple[str, Tuple[bool, str, Optional[AgentAnalysis]]]:
        agent = self.agents.get(agent_name)
        if not agent:
            return agent_name, (False, "Agent不存在", None)
        
        try:
            result = agent.analyze(context)
            return agent_name, result
        except Exception as e:
            self.logger.error(f"Agent执行失败: {agent_name}, 错误: {str(e)}")
            return agent_name, (False, str(e), None)
    
    def coordinate_analysis(self, context: Dict[str, Any]) -> Tuple[bool, str, List[AgentAnalysis]]:
        if not self.config.enable_multi_agent:
            return False, "多Agent模式未启用", []
        
        try:
            self.logger.info("开始多Agent协调分析...")
            
            results = []
            
            with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
                future_to_agent = {
                    executor.submit(self._run_single_agent, agent_name, context): agent_name
                    for agent_name in self.agents.keys()
                }
                
                with tqdm(total=len(self.agents), desc="Agent分析进度", unit="个") as pbar:
                    for future in as_completed(future_to_agent):
                        agent_name = future_to_agent[future]
                        try:
                            _, (success, msg, analysis) = future.result()
                            if success and analysis:
                                results.append(analysis)
                                self.logger.info(f"{agent_name} 分析完成，建议: {analysis.recommendation}")
                            else:
                                self.logger.warning(f"{agent_name} 分析失败: {msg}")
                        except Exception as e:
                            self.logger.error(f"Agent执行异常: {agent_name}, 错误: {str(e)}")
                        finally:
                            pbar.update(1)
            
            self.logger.info(f"多Agent协调分析完成，共{len(results)}个Agent返回结果")
            
            return True, "多Agent分析完成", results
            
        except Exception as e:
            self.logger.error(f"多Agent协调分析失败: {str(e)}")
            return False, str(e), []
    
    def _calculate_weighted_recommendation(self, analyses: List[AgentAnalysis]) -> str:
        if not analyses:
            return "持有"
        
        buy_votes = sum(1 for a in analyses if a.recommendation == "买入")
        sell_votes = sum(1 for a in analyses if a.recommendation == "卖出")
        hold_votes = sum(1 for a in analyses if a.recommendation == "持有")
        
        total_votes = len(analyses)
        
        buy_weight = buy_votes / total_votes
        sell_weight = sell_votes / total_votes
        hold_weight = hold_votes / total_votes
        
        if buy_weight > 0.6:
            return "买入"
        elif sell_weight > 0.6:
            return "卖出"
        elif buy_weight > 0.4 and buy_weight > sell_weight:
            return "偏多"
        elif sell_weight > 0.4 and sell_weight > buy_weight:
            return "偏空"
        else:
            return "持有"
    
    def _calculate_confidence_weighted(self, analyses: List[AgentAnalysis]) -> float:
        if not analyses:
            return 0.5
        
        weighted_confidence = sum(a.confidence * a.confidence for a in analyses)
        total_weight = sum(a.confidence for a in analyses)
        
        if total_weight == 0:
            return sum(a.confidence for a in analyses) / len(analyses)
        
        return weighted_confidence / total_weight
    
    def _calculate_risk_level(self, analyses: List[AgentAnalysis]) -> str:
        if not analyses:
            return "中"
        
        risk_scores = {"低": 1, "中": 2, "高": 3}
        total_score = sum(risk_scores.get(a.risk_level, 2) for a in analyses)
        avg_score = total_score / len(analyses)
        
        if avg_score < 1.5:
            return "低"
        elif avg_score < 2.5:
            return "中"
        else:
            return "高"
    
    def _generate_key_points(self, analyses: List[AgentAnalysis]) -> List[str]:
        key_points = []
        
        for analysis in analyses:
            if analysis.reasoning:
                key_points.append(f"[{analysis.agent_name}] {analysis.reasoning[:100]}...")
        
        return key_points[:10]
    
    def _generate_warnings(self, analyses: List[AgentAnalysis]) -> List[str]:
        warnings = []
        
        high_risk_agents = [a for a in analyses if a.risk_level == "高"]
        if high_risk_agents:
            warnings.append(f"以下Agent评估为高风险: {', '.join([a.agent_name for a in high_risk_agents])}")
        
        low_confidence_agents = [a for a in analyses if a.confidence < 0.5]
        if low_confidence_agents:
            warnings.append(f"以下Agent置信度较低: {', '.join([a.agent_name for a in low_confidence_agents])}")
        
        conflicting_recommendations = len(set(a.recommendation for a in analyses)) > 1
        if conflicting_recommendations:
            warnings.append("各Agent建议存在分歧，请谨慎决策")
        
        return warnings
    
    def synthesize_analysis(self, context: Dict[str, Any], agent_analyses: List[AgentAnalysis]) -> Tuple[bool, str, Optional[ComprehensiveAnalysis]]:
        try:
            if not agent_analyses:
                return False, "没有Agent分析结果", None
            
            self.logger.info("开始综合分析...")
            
            overall_recommendation = self._calculate_weighted_recommendation(agent_analyses)
            overall_confidence = self._calculate_confidence_weighted(agent_analyses)
            overall_risk_level = self._calculate_risk_level(agent_analyses)
            
            key_points = self._generate_key_points(agent_analyses)
            warnings = self._generate_warnings(agent_analyses)
            
            stock_code = context.get('stock_code', '')
            stock_name = context.get('stock_name', '')
            analysis_date = context.get('analysis_date', '')
            
            comprehensive = ComprehensiveAnalysis(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_date=analysis_date,
                stock_data=context.get('stock_data', []),
                technical_indicators=context.get('technical_indicators', {}),
                macd=context.get('macd'),
                rsi=context.get('rsi'),
                kdj=context.get('kdj'),
                patterns=context.get('patterns', []),
                volume_price_relations=context.get('volume_price_relations', []),
                agent_analyses=agent_analyses,
                overall_recommendation=overall_recommendation,
                overall_confidence=overall_confidence,
                overall_risk_level=overall_risk_level,
                key_points=key_points,
                warnings=warnings
            )
            
            self.logger.info(f"综合分析完成，建议: {overall_recommendation}，置信度: {overall_confidence:.2f}")
            
            return True, "综合分析完成", comprehensive
            
        except Exception as e:
            self.logger.error(f"综合分析失败: {str(e)}")
            return False, str(e), None
    
    def run_full_analysis(self, context: Dict[str, Any]) -> Tuple[bool, str, Optional[ComprehensiveAnalysis]]:
        try:
            self.logger.info("开始完整分析流程...")
            
            success, msg, agent_analyses = self.coordinate_analysis(context)
            
            if not success or not agent_analyses:
                self.logger.warning(f"Agent分析失败: {msg}")
                return False, msg, None
            
            success, msg, comprehensive = self.synthesize_analysis(context, agent_analyses)
            
            if not success:
                return False, msg, None
            
            return True, "完整分析完成", comprehensive
            
        except Exception as e:
            self.logger.error(f"完整分析流程失败: {str(e)}")
            return False, str(e), None
    
    def add_agent(self, agent_name: str, agent_type: str):
        if agent_name in self.agents:
            self.logger.warning(f"Agent已存在: {agent_name}")
            return
        
        self.agents[agent_name] = LLMAgent(
            agent_name=agent_name,
            agent_type=agent_type
        )
        self.logger.info(f"添加Agent: {agent_name}")
    
    def remove_agent(self, agent_name: str):
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"移除Agent: {agent_name}")
    
    def get_agent_list(self) -> List[str]:
        return list(self.agents.keys())
