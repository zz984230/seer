import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from seer_agents.seer_agent_primary_thinking.models import StockAnalysisRequest
from seer_agents.seer_agent_primary_thinking.primary_agent import PrimaryThinkingAgent
from seer.logger import logger


def test_primary_thinking_agent():
    logger.info("=" * 60)
    logger.info("测试: PrimaryThinkingAgent 初始化")
    logger.info("=" * 60)
    
    try:
        config = {
            'src_data_dir': './src/seer_agents/seer_agent_primary_thinking/src_data'
        }
        
        agent = PrimaryThinkingAgent(config=config)
        
        logger.info("✓ PrimaryThinkingAgent 初始化成功")
        
        stats = agent.get_knowledge_stats()
        logger.info(f"知识库统计: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_analysis():
    logger.info("=" * 60)
    logger.info("测试: 股票分析")
    logger.info("=" * 60)
    
    try:
        config = {
            'src_data_dir': './src/seer_agents/seer_agent_primary_thinking/src_data'
        }
        
        agent = PrimaryThinkingAgent(config=config)
        
        request = StockAnalysisRequest(
            stock_code="000001",
            stock_name="平安银行",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        
        logger.info(f"开始分析股票: {request.stock_code} {request.stock_name}")
        
        success, msg, result = agent.run_full_analysis(request)
        
        if success and result:
            logger.info(f"✓ 分析成功")
            logger.info(f"  建议: {result.recommendation}")
            logger.info(f"  置信度: {result.confidence:.2f}")
            logger.info(f"  风险等级: {result.risk_level}")
            logger.info(f"  关键要点数量: {len(result.key_points)}")
            logger.info(f"  投资机会数量: {len(result.opportunities)}")
            logger.info(f"  风险提示数量: {len(result.risks)}")
            return True
        else:
            logger.warning(f"✗ 分析失败: {msg}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test1 = test_primary_thinking_agent()
    test2 = test_stock_analysis()
    
    logger.info("=" * 60)
    logger.info(f"测试结果: {'全部通过' if test1 and test2 else '部分失败'}")
    logger.info("=" * 60)
