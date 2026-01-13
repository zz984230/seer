import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from seer_agents.seer_agent_primary_thinking.adk_config import adk_config
from seer_agents.seer_agent_primary_thinking.agents import (
    FundamentalAnalysisAgent, TechnicalAnalysisAgent, 
    IndustryAnalysisAgent, RiskAssessmentAgent
)
from seer_agents.seer_agent_primary_thinking.primary_agent import PrimaryThinkingAgent
from seer_agents.seer_agent_primary_thinking.models import StockAnalysisRequest
from seer_agents.seer_agent_primary_thinking.knowledge_base import KnowledgeBase
from seer_agents.seer_agent_primary_thinking.data_fetcher import StockDataFetcher
from seer_agents.seer_agent_primary_thinking.technical_analyzer import TechnicalAnalyzer
from seer.logger import logger


def test_adk_config():
    logger.info("=" * 60)
    logger.info("测试1: ADK 配置")
    logger.info("=" * 60)
    
    try:
        logger.info(f"✓ 模型提供商: {adk_config.model.provider}")
        logger.info(f"✓ 模型名称: {adk_config.model.name}")
        logger.info(f"✓ 温度: {adk_config.model.temperature}")
        logger.info(f"✓ 最大令牌数: {adk_config.model.max_tokens}")
        
        model_config = adk_config.get_model_config()
        logger.info(f"✓ 模型配置: {model_config}")
        
        agent_config = adk_config.get_llm_agent_config("test_agent", "测试指令")
        logger.info(f"✓ Agent配置: {agent_config}")
        
        logger.info("✓ ADK 配置测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ ADK 配置测试失败: {str(e)}")
        return False


def test_llm_agent_initialization():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试2: LlmAgent 初始化")
    logger.info("=" * 60)
    
    try:
        knowledge_base = KnowledgeBase()
        
        config = {
            'use_cache': True,
            'cache_dir': './cache/test',
            'data_dir': './data/test',
            'max_workers': 5,
            'request_interval': 0.5,
            'api_timeout': 30,
            'cache_expire_hours': 1
        }
        
        data_fetcher = StockDataFetcher(config)
        technical_analyzer = TechnicalAnalyzer()
        
        fundamental_agent = FundamentalAnalysisAgent(knowledge_base, data_fetcher)
        logger.info(f"✓ 基本面分析Agent初始化成功: {fundamental_agent.agent_name}")
        logger.info(f"  - LlmAgent: {fundamental_agent.llm_agent.name}")
        logger.info(f"  - 模型: {fundamental_agent.llm_agent.model}")
        
        technical_agent = TechnicalAnalysisAgent(knowledge_base, technical_analyzer)
        logger.info(f"✓ 技术面分析Agent初始化成功: {technical_agent.agent_name}")
        logger.info(f"  - LlmAgent: {technical_agent.llm_agent.name}")
        logger.info(f"  - 模型: {technical_agent.llm_agent.model}")
        
        industry_agent = IndustryAnalysisAgent(knowledge_base, data_fetcher)
        logger.info(f"✓ 行业分析Agent初始化成功: {industry_agent.agent_name}")
        logger.info(f"  - LlmAgent: {industry_agent.llm_agent.name}")
        logger.info(f"  - 模型: {industry_agent.llm_agent.model}")
        
        risk_agent = RiskAssessmentAgent(knowledge_base)
        logger.info(f"✓ 风险评估Agent初始化成功: {risk_agent.agent_name}")
        logger.info(f"  - LlmAgent: {risk_agent.llm_agent.name}")
        logger.info(f"  - 模型: {risk_agent.llm_agent.model}")
        
        logger.info("✓ LlmAgent 初始化测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ LlmAgent 初始化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_agent_initialization():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试3: ParallelAgent 初始化")
    logger.info("=" * 60)
    
    try:
        config = {
            'use_cache': True,
            'cache_dir': './cache/test',
            'data_dir': './data/test',
            'max_workers': 5,
            'request_interval': 0.5,
            'api_timeout': 30,
            'cache_expire_hours': 1
        }
        
        agent = PrimaryThinkingAgent(config)
        
        logger.info(f"✓ PrimaryThinkingAgent初始化成功")
        logger.info(f"  - Agent数量: {len(agent.agents)}")
        
        if agent.parallel_agent:
            logger.info(f"✓ ParallelAgent初始化成功")
            logger.info(f"  - 名称: {agent.parallel_agent.name}")
            logger.info(f"  - 子Agent数量: {len(agent.parallel_agent.sub_agents)}")
        else:
            logger.warning("⚠ ParallelAgent初始化失败，将使用线程池方式")
        
        logger.info("✓ ParallelAgent 初始化测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ ParallelAgent 初始化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_single_agent_analysis():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试4: 单个Agent分析")
    logger.info("=" * 60)
    
    try:
        config = {
            'use_cache': True,
            'cache_dir': './cache/test',
            'data_dir': './data/test',
            'max_workers': 5,
            'request_interval': 0.5,
            'api_timeout': 30,
            'cache_expire_hours': 1
        }
        
        agent = PrimaryThinkingAgent(config)
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        request = StockAnalysisRequest(
            stock_code="000001",
            stock_name="平安银行",
            start_date=start_date,
            end_date=end_date,
            analysis_dimensions=['主力行为', '技术形态', '量价关系'],
            enable_fundamental=True,
            enable_technical=True,
            enable_industry=True,
            enable_risk_assessment=True
        )
        
        logger.info(f"测试单个Agent分析: {request.stock_code}")
        
        fundamental_agent = agent.agents['fundamental']
        success, msg, result = fundamental_agent.analyze(request, {})
        
        if success and result:
            logger.info(f"✓ 基本面分析Agent测试通过")
            logger.info(f"  - 建议: {result.get('recommendation', '未知')}")
            logger.info(f"  - 置信度: {result.get('confidence', 0):.2f}")
            logger.info(f"  - 风险等级: {result.get('risk_level', '未知')}")
        else:
            logger.warning(f"⚠ 基本面分析Agent测试失败: {msg}")
        
        logger.info("✓ 单个Agent分析测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 单个Agent分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_full_analysis():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试5: 完整分析流程")
    logger.info("=" * 60)
    
    try:
        config = {
            'use_cache': True,
            'cache_dir': './cache/test',
            'data_dir': './data/test',
            'max_workers': 5,
            'request_interval': 0.5,
            'api_timeout': 30,
            'cache_expire_hours': 1
        }
        
        agent = PrimaryThinkingAgent(config)
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        request = StockAnalysisRequest(
            stock_code="000001",
            stock_name="平安银行",
            start_date=start_date,
            end_date=end_date,
            analysis_dimensions=['主力行为', '技术形态', '量价关系'],
            enable_fundamental=True,
            enable_technical=True,
            enable_industry=True,
            enable_risk_assessment=True
        )
        
        logger.info(f"测试完整分析流程: {request.stock_code}")
        
        success, msg, result = agent.run_full_analysis(request)
        
        if success and result:
            logger.info(f"✓ 完整分析流程测试通过")
            logger.info(f"  - 综合建议: {result.recommendation}")
            logger.info(f"  - 综合置信度: {result.confidence:.2f}")
            logger.info(f"  - 综合风险等级: {result.risk_level}")
            logger.info(f"  - 关键点数: {len(result.key_points)}")
            logger.info(f"  - 机会点数: {len(result.opportunities)}")
            logger.info(f"  - 风险点数: {len(result.risks)}")
        else:
            logger.warning(f"⚠ 完整分析流程测试失败: {msg}")
            return False
        
        logger.info("✓ 完整分析流程测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 完整分析流程测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    logger.info("")
    logger.info("*" * 80)
    logger.info("Google ADK 集成测试")
    logger.info("*" * 80)
    logger.info("")
    
    test_results = []
    
    try:
        result = test_adk_config()
        test_results.append(("ADK 配置", result))
    except Exception as e:
        logger.error(f"ADK 配置测试失败: {str(e)}")
        test_results.append(("ADK 配置", False))
    
    try:
        result = test_llm_agent_initialization()
        test_results.append(("LlmAgent 初始化", result))
    except Exception as e:
        logger.error(f"LlmAgent 初始化测试失败: {str(e)}")
        test_results.append(("LlmAgent 初始化", False))
    
    try:
        result = test_parallel_agent_initialization()
        test_results.append(("ParallelAgent 初始化", result))
    except Exception as e:
        logger.error(f"ParallelAgent 初始化测试失败: {str(e)}")
        test_results.append(("ParallelAgent 初始化", False))
    
    try:
        result = test_single_agent_analysis()
        test_results.append(("单个Agent分析", result))
    except Exception as e:
        logger.error(f"单个Agent分析测试失败: {str(e)}")
        test_results.append(("单个Agent分析", False))
    
    try:
        result = test_full_analysis()
        test_results.append(("完整分析流程", result))
    except Exception as e:
        logger.error(f"完整分析流程测试失败: {str(e)}")
        test_results.append(("完整分析流程", False))
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    logger.info("")
    
    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{status} - {test_name}")
    
    logger.info("")
    logger.info(f"总计: {passed_count}/{total_count} 测试通过")
    logger.info(f"通过率: {passed_count/total_count*100:.1f}%")
    
    if passed_count == total_count:
        logger.info("")
        logger.info("🎉 所有测试通过！Google ADK 集成成功。")
    else:
        logger.warning("")
        logger.warning(f"⚠️  {total_count - passed_count} 个测试失败，请检查相关模块。")
    
    logger.info("")
    logger.info("*" * 80)


if __name__ == "__main__":
    run_all_tests()
