import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from seer_agents.seer_agent_primary_thinking.models import StockAnalysisRequest
from seer_agents.seer_agent_primary_thinking.primary_agent import PrimaryThinkingAgent
from seer.logger import logger


def main():
    logger.info("=" * 60)
    logger.info("股票智能分析系统")
    logger.info("=" * 60)
    
    config = {
        'src_data_dir': './src/seer_agents/seer_agent_primary_thinking/src_data'
    }
    
    agent = PrimaryThinkingAgent(config=config)
    
    stats = agent.get_knowledge_stats()
    logger.info(f"知识库统计: {stats}")
    
    request = StockAnalysisRequest(
        stock_code="000001",
        stock_name="平安银行",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    logger.info(f"开始分析股票: {request.stock_code} {request.stock_name}")
    
    success, msg, result = agent.run_full_analysis(request)
    
    if success and result:
        logger.info("=" * 60)
        logger.info("分析结果")
        logger.info("=" * 60)
        logger.info(f"股票代码: {result.stock_code}")
        logger.info(f"股票名称: {result.stock_name}")
        logger.info(f"分析日期: {result.analysis_date}")
        logger.info(f"投资建议: {result.recommendation}")
        logger.info(f"置信度: {result.confidence:.2%}")
        logger.info(f"风险等级: {result.risk_level}")
        logger.info("")
        logger.info("关键要点:")
        for point in result.key_points:
            logger.info(f"  - {point}")
        logger.info("")
        logger.info("投资机会:")
        for opp in result.opportunities:
            logger.info(f"  - {opp}")
        logger.info("")
        logger.info("风险提示:")
        for risk in result.risks:
            logger.info(f"  - {risk}")
        logger.info("")
        logger.info("分析逻辑:")
        logger.info(f"  {result.reasoning}")
        logger.info("=" * 60)
    else:
        logger.error(f"分析失败: {msg}")


if __name__ == "__main__":
    main()
