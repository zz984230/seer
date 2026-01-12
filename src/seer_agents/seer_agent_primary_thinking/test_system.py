import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from seer_agents.seer_agent_primary_thinking.data_processor import DataProcessor
from seer_agents.seer_agent_primary_thinking.knowledge_base import KnowledgeBase
from seer_agents.seer_agent_primary_thinking.data_fetcher import StockDataFetcher
from seer_agents.seer_agent_primary_thinking.technical_analyzer import TechnicalAnalyzer
from seer_agents.seer_agent_primary_thinking.primary_agent import PrimaryThinkingAgent
from seer_agents.seer_agent_primary_thinking.models import StockAnalysisRequest
from seer.logger import logger


def test_data_processor():
    logger.info("=" * 60)
    logger.info("测试1: 数据处理器")
    logger.info("=" * 60)
    
    src_data_dir = project_root / "src" / "seer_agents" / "seer_agent_primary_thinking" / "src_data"
    
    if not src_data_dir.exists():
        logger.error(f"源数据目录不存在: {src_data_dir}")
        return False
    
    processor = DataProcessor(str(src_data_dir))
    
    success, msg, quotes = processor.process_all_files()
    
    if not success:
        logger.error(f"数据处理失败: {msg}")
        return False
    
    logger.info(f"✓ 成功处理 {len(quotes)} 条专家语录")
    
    stats = processor.get_statistics()
    logger.info(f"✓ 专家数量: {len(stats['expert_names'])}")
    logger.info(f"✓ 关键点总数: {stats['total_key_points']}")
    logger.info(f"✓ 技术形态数: {stats['total_technical_patterns']}")
    logger.info(f"✓ 交易策略数: {stats['total_trading_strategies']}")
    
    return True


def test_knowledge_base():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试2: 知识库")
    logger.info("=" * 60)
    
    src_data_dir = project_root / "src" / "seer_agents" / "seer_agent_primary_thinking" / "src_data"
    
    processor = DataProcessor(str(src_data_dir))
    success, msg, quotes = processor.process_all_files()
    
    if not success:
        logger.error(f"数据处理失败: {msg}")
        return False
    
    knowledge_base = KnowledgeBase()
    success, msg = knowledge_base.add_knowledge_from_quotes(quotes)
    
    if not success:
        logger.error(f"知识库构建失败: {msg}")
        return False
    
    logger.info(f"✓ 成功添加知识到知识库")
    
    stats = knowledge_base.get_statistics()
    logger.info(f"✓ 知识条目数: {stats['knowledge_entries']}")
    logger.info(f"✓ 分析维度数: {stats['analysis_dimensions']}")
    logger.info(f"✓ 分析框架数: {stats['analysis_frameworks']}")
    logger.info(f"✓ 主力行为数: {stats['main_force_behaviors']}")
    logger.info(f"✓ 交易策略数: {stats['trading_strategies']}")
    
    dimensions = knowledge_base.get_analysis_dimensions()
    logger.info(f"✓ 分析维度示例: {dimensions[0].dimension_name if dimensions else '无'}")
    
    return True


def test_data_fetcher():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试3: 数据采集器")
    logger.info("=" * 60)
    
    config = {
        'use_cache': True,
        'cache_dir': './cache/test',
        'data_dir': './data/test',
        'max_workers': 5,
        'request_interval': 0.5,
        'api_timeout': 30,
        'cache_expire_hours': 1
    }
    
    fetcher = StockDataFetcher(config)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    logger.info(f"测试获取股票数据: 000001, {start_date} ~ {end_date}")
    
    success, msg, data = fetcher.get_stock_daily_data("000001", start_date, end_date)
    
    if not success:
        logger.error(f"获取股票数据失败: {msg}")
        return False
    
    logger.info(f"✓ 成功获取 {len(data)} 条股票数据")
    
    success, msg = fetcher.validate_data_quality(data)
    
    if not success:
        logger.error(f"数据质量校验失败: {msg}")
        return False
    
    logger.info(f"✓ 数据质量校验通过")
    
    return True


def test_technical_analyzer():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试4: 技术分析器")
    logger.info("=" * 60)
    
    config = {
        'use_cache': True,
        'cache_dir': './cache/test',
        'data_dir': './data/test',
        'max_workers': 5,
        'request_interval': 0.5,
        'api_timeout': 30,
        'cache_expire_hours': 1
    }
    
    fetcher = StockDataFetcher(config)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    success, msg, data = fetcher.get_stock_daily_data("000001", start_date, end_date)
    
    if not success or not data:
        logger.error(f"获取股票数据失败: {msg}")
        return False
    
    analyzer = TechnicalAnalyzer()
    
    logger.info("测试技术分析功能...")
    
    analysis_result = analyzer.comprehensive_analysis(data)
    
    logger.info(f"✓ 成功完成技术分析")
    logger.info(f"✓ 计算了 {len(analysis_result.get('ma', {}))} 个均线指标")
    logger.info(f"✓ 计算了MACD指标")
    logger.info(f"✓ 计算了RSI指标")
    logger.info(f"✓ 计算了KDJ指标")
    logger.info(f"✓ 检测了 {len(analysis_result.get('patterns', {}))} 种形态")
    
    main_force = analysis_result.get('main_force', {})
    logger.info(f"✓ 主力状态: {main_force.get('main_force_status', '未知')}")
    logger.info(f"✓ 当前阶段: {main_force.get('current_phase', '未知')}")
    
    return True


def test_primary_agent():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试5: 主Agent")
    logger.info("=" * 60)
    
    config = {
        'use_cache': True,
        'cache_dir': './cache/test',
        'data_dir': './data/test',
        'max_workers': 5,
        'request_interval': 0.5,
        'api_timeout': 30,
        'cache_expire_hours': 1,
        'src_data_dir': str(project_root / "src" / "seer_agents" / "seer_agent_primary_thinking" / "src_data")
    }
    
    agent = PrimaryThinkingAgent(config)
    
    logger.info("测试Agent初始化...")
    logger.info(f"✓ Agent数量: {len(agent.get_agent_list())}")
    
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
    
    logger.info(f"测试分析请求: {request.stock_code}")
    
    logger.info("开始完整分析流程...")
    success, msg, result = agent.run_full_analysis(request)
    
    if not success or not result:
        logger.error(f"分析失败: {msg}")
        return False
    
    logger.info(f"✓ 成功完成分析")
    logger.info(f"✓ 综合建议: {result.recommendation}")
    logger.info(f"✓ 综合置信度: {result.confidence:.2f}")
    logger.info(f"✓ 综合风险等级: {result.risk_level}")
    logger.info(f"✓ 关键点数: {len(result.key_points)}")
    logger.info(f"✓ 机会点数: {len(result.opportunities)}")
    logger.info(f"✓ 风险点数: {len(result.risks)}")
    
    return True


def test_knowledge_search():
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试6: 知识检索")
    logger.info("=" * 60)
    
    src_data_dir = project_root / "src" / "seer_agents" / "seer_agent_primary_thinking" / "src_data"
    
    processor = DataProcessor(str(src_data_dir))
    success, msg, quotes = processor.process_all_files()
    
    if not success:
        logger.error(f"数据处理失败: {msg}")
        return False
    
    knowledge_base = KnowledgeBase()
    success, msg = knowledge_base.add_knowledge_from_quotes(quotes)
    
    if not success:
        logger.error(f"知识库构建失败: {msg}")
        return False
    
    test_queries = [
        ("主力洗盘", "技术分析"),
        ("颈线突破", "技术分析"),
        ("拖拉机单", "技术分析"),
        ("风险控制", "风险控制"),
        ("量增价涨", "技术分析")
    ]
    
    for query, category in test_queries:
        results = knowledge_base.search_knowledge(query, category, limit=3)
        logger.info(f"✓ 查询 '{query}' (分类: {category}) - 找到 {len(results)} 条相关知识")
        
        if results:
            for i, entry in enumerate(results[:2], 1):
                logger.info(f"    {i}. {entry.title[:50]}...")
    
    return True


def run_all_tests():
    logger.info("")
    logger.info("*" * 80)
    logger.info("开始系统测试")
    logger.info("*" * 80)
    logger.info("")
    
    test_results = []
    
    try:
        result = test_data_processor()
        test_results.append(("数据处理器", result))
    except Exception as e:
        logger.error(f"数据处理器测试失败: {str(e)}")
        test_results.append(("数据处理器", False))
    
    try:
        result = test_knowledge_base()
        test_results.append(("知识库", result))
    except Exception as e:
        logger.error(f"知识库测试失败: {str(e)}")
        test_results.append(("知识库", False))
    
    try:
        result = test_data_fetcher()
        test_results.append(("数据采集器", result))
    except Exception as e:
        logger.error(f"数据采集器测试失败: {str(e)}")
        test_results.append(("数据采集器", False))
    
    try:
        result = test_technical_analyzer()
        test_results.append(("技术分析器", result))
    except Exception as e:
        logger.error(f"技术分析器测试失败: {str(e)}")
        test_results.append(("技术分析器", False))
    
    try:
        result = test_primary_agent()
        test_results.append(("主Agent", result))
    except Exception as e:
        logger.error(f"主Agent测试失败: {str(e)}")
        test_results.append(("主Agent", False))
    
    try:
        result = test_knowledge_search()
        test_results.append(("知识检索", result))
    except Exception as e:
        logger.error(f"知识检索测试失败: {str(e)}")
        test_results.append(("知识检索", False))
    
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
        logger.info("🎉 所有测试通过！系统功能正常。")
        logger.info("")
        logger.info("下一步:")
        logger.info("  1. 运行 build_knowledge_base.py 构建知识库")
        logger.info("  2. 运行 main.py 进行个股分析")
    else:
        logger.warning("")
        logger.warning(f"⚠️  {total_count - passed_count} 个测试失败，请检查相关模块。")
    
    logger.info("")
    logger.info("*" * 80)


if __name__ == "__main__":
    run_all_tests()
