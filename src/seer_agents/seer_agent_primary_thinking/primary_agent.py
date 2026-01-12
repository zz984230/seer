from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm
from datetime import datetime
from .models import StockAnalysisRequest, StockAnalysisResult
from .analysis_agent import (
    FundamentalAnalysisAgent, TechnicalAnalysisAgent, 
    IndustryAnalysisAgent, RiskAssessmentAgent
)
from .knowledge_base import KnowledgeBase
from .data_fetcher import StockDataFetcher
from .technical_analyzer import TechnicalAnalyzer
from seer.logger import logger

tqdm.set_lock(threading.Lock())


class PrimaryThinkingAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.config = config or {}
        
        self.knowledge_base = KnowledgeBase()
        self.data_fetcher = StockDataFetcher(config)
        self.technical_analyzer = TechnicalAnalyzer()
        
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        self.agents['fundamental'] = FundamentalAnalysisAgent(
            self.knowledge_base, 
            self.data_fetcher
        )
        self.agents['technical'] = TechnicalAnalysisAgent(
            self.knowledge_base,
            self.technical_analyzer
        )
        self.agents['industry'] = IndustryAnalysisAgent(
            self.knowledge_base,
            self.data_fetcher
        )
        self.agents['risk'] = RiskAssessmentAgent(
            self.knowledge_base
        )
        
        self.logger.info(f"初始化 {len(self.agents)} 个分析Agent")
    
    def _run_single_agent(self, agent_name: str, request: StockAnalysisRequest, 
                        context: Dict[str, Any]) -> Tuple[str, Tuple[bool, str, Optional[Dict[str, Any]]]]:
        agent = self.agents.get(agent_name)
        if not agent:
            return agent_name, (False, "Agent不存在", None)
        
        try:
            result = agent.analyze(request, context)
            return agent_name, result
        except Exception as e:
            self.logger.error(f"Agent执行失败: {agent_name}, 错误: {str(e)}")
            return agent_name, (False, str(e), None)
    
    def coordinate_analysis(self, request: StockAnalysisRequest) -> Tuple[bool, str, List[Dict[str, Any]]]:
        try:
            self.logger.info("开始协调多Agent分析...")
            
            results = []
            
            with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
                future_to_agent = {
                    executor.submit(self._run_single_agent, agent_name, request, {}): agent_name
                    for agent_name in self.agents.keys()
                }
                
                with tqdm(total=len(self.agents), desc="Agent分析进度", unit="个") as pbar:
                    for future in as_completed(future_to_agent):
                        agent_name = future_to_agent[future]
                        try:
                            _, (success, msg, analysis) = future.result()
                            if success and analysis:
                                results.append(analysis)
                                self.logger.info(f"{agent_name} 分析完成，建议: {analysis.get('recommendation', '未知')}")
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
    
    def _calculate_weighted_recommendation(self, analyses: List[Dict[str, Any]]) -> str:
        if not analyses:
            return "持有"
        
        buy_votes = sum(1 for a in analyses if a.get('recommendation') == "买入")
        sell_votes = sum(1 for a in analyses if a.get('recommendation') == "卖出")
        hold_votes = sum(1 for a in analyses if a.get('recommendation') == "持有")
        
        total_votes = len(analyses)
        
        if total_votes == 0:
            return "持有"
        
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
    
    def _calculate_confidence_weighted(self, analyses: List[Dict[str, Any]]) -> float:
        if not analyses:
            return 0.5
        
        weighted_confidence = sum(
            a.get('confidence', 0.5) * a.get('confidence', 0.5) 
            for a in analyses
        )
        total_weight = sum(a.get('confidence', 0.5) for a in analyses)
        
        if total_weight == 0:
            return sum(a.get('confidence', 0.5) for a in analyses) / len(analyses)
        
        return weighted_confidence / total_weight
    
    def _calculate_risk_level(self, analyses: List[Dict[str, Any]]) -> str:
        if not analyses:
            return "中"
        
        risk_scores = {"低": 1, "中": 2, "高": 3}
        total_score = sum(
            risk_scores.get(a.get('risk_level', '中'), 2) 
            for a in analyses
        )
        avg_score = total_score / len(analyses)
        
        if avg_score < 1.5:
            return "低"
        elif avg_score < 2.5:
            return "中"
        else:
            return "高"
    
    def _generate_key_points(self, analyses: List[Dict[str, Any]]) -> List[str]:
        key_points = []
        
        for analysis in analyses:
            agent_name = analysis.get('agent_name', '')
            agent_key_points = analysis.get('key_points', [])
            
            for point in agent_key_points[:3]:
                key_points.append(f"[{agent_name}] {point}")
        
        return key_points
    
    def _generate_opportunities(self, analyses: List[Dict[str, Any]]) -> List[str]:
        opportunities = []
        
        for analysis in analyses:
            agent_name = analysis.get('agent_name', '')
            agent_opportunities = analysis.get('opportunities', [])
            
            for opp in agent_opportunities[:2]:
                opportunities.append(f"[{agent_name}] {opp}")
        
        return opportunities
    
    def _generate_risks(self, analyses: List[Dict[str, Any]]) -> List[str]:
        risks = []
        
        for analysis in analyses:
            agent_name = analysis.get('agent_name', '')
            agent_risks = analysis.get('risks', [])
            
            for risk in agent_risks[:2]:
                risks.append(f"[{agent_name}] {risk}")
        
        return risks
    
    def _generate_reasoning(self, analyses: List[Dict[str, Any]], 
                          context: Dict[str, Any]) -> str:
        reasoning_parts = []
        
        reasoning_parts.append("## 综合分析逻辑")
        reasoning_parts.append("")
        reasoning_parts.append("基于B站投资专家思维模式，从以下维度进行分析：")
        reasoning_parts.append("")
        
        for analysis in analyses:
            agent_name = analysis.get('agent_name', '')
            recommendation = analysis.get('recommendation', '')
            confidence = analysis.get('confidence', 0)
            risk_level = analysis.get('risk_level', '')
            
            reasoning_parts.append(f"### {agent_name}")
            reasoning_parts.append(f"- 建议: {recommendation}")
            reasoning_parts.append(f"- 置信度: {confidence:.2f}")
            reasoning_parts.append(f"- 风险等级: {risk_level}")
            reasoning_parts.append("")
        
        reasoning_parts.append("## 综合判断")
        
        weighted_recommendation = self._calculate_weighted_recommendation(analyses)
        weighted_confidence = self._calculate_confidence_weighted(analyses)
        weighted_risk_level = self._calculate_risk_level(analyses)
        
        reasoning_parts.append(f"综合建议: {weighted_recommendation}")
        reasoning_parts.append(f"综合置信度: {weighted_confidence:.2f}")
        reasoning_parts.append(f"综合风险等级: {weighted_risk_level}")
        reasoning_parts.append("")
        
        reasoning_parts.append("## 关键分析要点")
        key_points = self._generate_key_points(analyses)
        for point in key_points:
            reasoning_parts.append(f"- {point}")
        
        reasoning_parts.append("")
        reasoning_parts.append("## 投资机会")
        opportunities = self._generate_opportunities(analyses)
        for opp in opportunities:
            reasoning_parts.append(f"- {opp}")
        
        reasoning_parts.append("")
        reasoning_parts.append("## 风险提示")
        risks = self._generate_risks(analyses)
        for risk in risks:
            reasoning_parts.append(f"- {risk}")
        
        reasoning_parts.append("")
        reasoning_parts.append("## 专家思维应用")
        reasoning_parts.append("本分析基于B站投资专家'领居大爷'的核心思维模式：")
        reasoning_parts.append("- 主力行为分析：识别主力资金在不同阶段的操作手法")
        reasoning_parts.append("- 技术形态识别：通过关键技术形态判断买卖时机")
        reasoning_parts.append("- 量价关系分析：分析成交量与价格的关系判断资金流向")
        reasoning_parts.append("- 风险控制评估：评估投资风险并制定合理的风控策略")
        reasoning_parts.append("- 时间节点决策：利用关键时间节点提高资金效率")
        
        return "\n".join(reasoning_parts)
    
    def synthesize_analysis(self, request: StockAnalysisRequest, 
                         agent_analyses: List[Dict[str, Any]], 
                         context: Dict[str, Any]) -> Tuple[bool, str, Optional[StockAnalysisResult]]:
        try:
            if not agent_analyses:
                return False, "没有Agent分析结果", None
            
            self.logger.info("开始综合分析...")
            
            overall_recommendation = self._calculate_weighted_recommendation(agent_analyses)
            overall_confidence = self._calculate_confidence_weighted(agent_analyses)
            overall_risk_level = self._calculate_risk_level(agent_analyses)
            
            key_points = self._generate_key_points(agent_analyses)
            opportunities = self._generate_opportunities(agent_analyses)
            risks = self._generate_risks(agent_analyses)
            reasoning = self._generate_reasoning(agent_analyses, context)
            
            technical_data = context.get('technical_data', {})
            fundamental_data = context.get('fundamental_data', {})
            industry_data = context.get('industry_data', {})
            
            main_force_status = technical_data.get('main_force', {}).get('main_force_status', '')
            trading_phase = technical_data.get('main_force', {}).get('current_phase', '')
            
            result = StockAnalysisResult(
                stock_code=request.stock_code,
                stock_name=request.stock_name or '',
                analysis_date=datetime.now().strftime("%Y-%m-%d"),
                fundamental_analysis=fundamental_data,
                technical_analysis=technical_data,
                industry_analysis=industry_data,
                risk_assessment={'overall_risk_level': overall_risk_level},
                main_force_status=main_force_status,
                trading_phase=trading_phase,
                recommendation=overall_recommendation,
                confidence=overall_confidence,
                risk_level=overall_risk_level,
                key_points=key_points,
                opportunities=opportunities,
                risks=risks,
                reasoning=reasoning
            )
            
            self.logger.info(f"综合分析完成，建议: {overall_recommendation}，置信度: {overall_confidence:.2f}")
            
            return True, "综合分析完成", result
            
        except Exception as e:
            self.logger.error(f"综合分析失败: {str(e)}")
            return False, str(e), None
    
    def run_full_analysis(self, request: StockAnalysisRequest) -> Tuple[bool, str, Optional[StockAnalysisResult]]:
        try:
            self.logger.info("开始完整分析流程...")
            
            success, msg, stock_data = self.data_fetcher.get_stock_daily_data(
                request.stock_code,
                request.start_date,
                request.end_date
            )
            
            if not success or not stock_data:
                self.logger.warning(f"获取股票数据失败: {msg}")
                return False, msg, None
            
            technical_analysis = self.technical_analyzer.comprehensive_analysis(stock_data)
            
            success, msg, fundamental_data = self.data_fetcher.get_stock_fundamental_data(request.stock_code)
            
            if not success:
                self.logger.warning(f"获取基本面数据失败: {msg}")
                fundamental_data = {}
            
            context = {
                'stock_data': stock_data,
                'technical_data': technical_analysis,
                'fundamental_data': fundamental_data
            }
            
            success, msg, agent_analyses = self.coordinate_analysis(request)
            
            if not success or not agent_analyses:
                self.logger.warning(f"Agent分析失败: {msg}")
                return False, msg, None
            
            success, msg, result = self.synthesize_analysis(request, agent_analyses, context)
            
            if not success:
                return False, msg, None
            
            return True, "完整分析完成", result
            
        except Exception as e:
            self.logger.error(f"完整分析流程失败: {str(e)}")
            return False, str(e), None
    
    def add_agent(self, agent_name: str, agent):
        if agent_name in self.agents:
            self.logger.warning(f"Agent已存在: {agent_name}")
            return
        
        self.agents[agent_name] = agent
        self.logger.info(f"添加Agent: {agent_name}")
    
    def remove_agent(self, agent_name: str):
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"移除Agent: {agent_name}")
    
    def get_agent_list(self) -> List[str]:
        return list(self.agents.keys())
    
    def load_knowledge_from_quotes(self, quotes_file_path: str) -> Tuple[bool, str]:
        try:
            from .data_processor import DataProcessor
            
            processor = DataProcessor(self.config.get('src_data_dir', './src_data'))
            success, msg, quotes = processor.process_all_files()
            
            if not success:
                return False, msg
            
            success, msg = self.knowledge_base.add_knowledge_from_quotes(quotes)
            
            return success, msg
            
        except Exception as e:
            self.logger.error(f"从语录加载知识失败: {str(e)}")
            return False, str(e)
    
    def save_knowledge_base(self, output_path: str) -> Tuple[bool, str]:
        return self.knowledge_base.save_knowledge_base(output_path)
