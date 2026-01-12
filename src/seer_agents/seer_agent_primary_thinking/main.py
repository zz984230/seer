import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from seer_agents.seer_agent_primary_thinking.primary_agent import PrimaryThinkingAgent
from seer_agents.seer_agent_primary_thinking.models import StockAnalysisRequest
from seer.logger import logger


def parse_arguments():
    parser = argparse.ArgumentParser(description='基于B站投资专家思维模式的个股分析Agent')
    
    parser.add_argument('--stock-code', type=str, required=True,
                       help='股票代码（如：000001）')
    parser.add_argument('--stock-name', type=str, default=None,
                       help='股票名称（可选）')
    parser.add_argument('--days', type=int, default=90,
                       help='分析天数（默认：90天）')
    parser.add_argument('--output-dir', type=str, default='./data/primary_thinking/reports',
                       help='报告输出目录（默认：./data/primary_thinking/reports）')
    parser.add_argument('--enable-fundamental', action='store_true', default=True,
                       help='启用基本面分析')
    parser.add_argument('--enable-technical', action='store_true', default=True,
                       help='启用技术面分析')
    parser.add_argument('--enable-industry', action='store_true', default=True,
                       help='启用行业分析')
    parser.add_argument('--enable-risk', action='store_true', default=True,
                       help='启用风险评估')
    parser.add_argument('--load-knowledge', type=str, default=None,
                       help='加载知识库文件路径（可选）')
    parser.add_argument('--config', type=str, default=None,
                       help='配置文件路径（可选）')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    logger.info("=" * 80)
    logger.info("基于B站投资专家思维模式的个股分析Agent")
    logger.info("=" * 80)
    logger.info("")
    
    config = {}
    if args.config and os.path.exists(args.config):
        import json
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"加载配置文件: {args.config}")
    
    agent = PrimaryThinkingAgent(config)
    
    if args.load_knowledge and os.path.exists(args.load_knowledge):
        logger.info(f"加载知识库: {args.load_knowledge}")
        success, msg = agent.load_knowledge_from_quotes(args.load_knowledge)
        if success:
            logger.info("知识库加载成功")
        else:
            logger.error(f"知识库加载失败: {msg}")
            return
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    request = StockAnalysisRequest(
        stock_code=args.stock_code,
        stock_name=args.stock_name,
        analysis_dimensions=['主力行为', '技术形态', '量价关系', '基本面', '行业', '风险'],
        enable_fundamental=args.enable_fundamental,
        enable_technical=args.enable_technical,
        enable_industry=args.enable_industry,
        enable_risk_assessment=args.enable_risk
    )
    
    logger.info("")
    logger.info("分析请求信息:")
    logger.info(f"  股票代码: {request.stock_code}")
    logger.info(f"  股票名称: {request.stock_name or '未知'}")
    logger.info(f"  分析日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"  分析天数: {args.days}")
    logger.info(f"  启用分析维度: {', '.join(request.analysis_dimensions)}")
    logger.info("")
    
    logger.info("开始分析...")
    logger.info("-" * 80)
    
    success, msg, result = agent.run_full_analysis(request)
    
    if not success or not result:
        logger.error(f"分析失败: {msg}")
        return
    
    logger.info("-" * 80)
    logger.info("")
    logger.info("分析完成！")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("分析结果摘要")
    logger.info("=" * 80)
    logger.info("")
    
    logger.info(f"股票代码: {result.stock_code}")
    logger.info(f"股票名称: {result.stock_name}")
    logger.info(f"分析日期: {result.analysis_date}")
    logger.info("")
    
    logger.info(f"综合建议: {result.recommendation}")
    logger.info(f"综合置信度: {result.confidence:.2f}")
    logger.info(f"综合风险等级: {result.risk_level}")
    logger.info("")
    
    logger.info("主力状态:")
    logger.info(f"  {result.main_force_status or '未知'}")
    logger.info("")
    
    logger.info("交易阶段:")
    logger.info(f"  {result.trading_phase or '未知'}")
    logger.info("")
    
    logger.info("关键分析要点:")
    for i, point in enumerate(result.key_points[:10], 1):
        logger.info(f"  {i}. {point}")
    logger.info("")
    
    logger.info("投资机会:")
    for i, opp in enumerate(result.opportunities[:5], 1):
        logger.info(f"  {i}. {opp}")
    logger.info("")
    
    logger.info("风险提示:")
    for i, risk in enumerate(result.risks[:5], 1):
        logger.info(f"  {i}. {risk}")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("详细推理过程:")
    logger.info("=" * 80)
    logger.info("")
    logger.info(result.reasoning)
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("保存分析结果...")
    logger.info("=" * 80)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    output_file = os.path.join(
        args.output_dir,
        f"{result.stock_code}_{result.analysis_date.replace('-', '')}_analysis.json"
    )
    
    result_dict = result.model_dump()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    logger.info(f"分析结果已保存: {output_file}")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("分析完成！")
    logger.info("=" * 80)
    logger.info("")
    
    logger.info("使用说明:")
    logger.info("  1. 本Agent基于B站投资专家'领居大爷'的核心思维模式")
    logger.info("  2. 分析结果仅供参考，不构成投资建议")
    logger.info("  3. 投资有风险，请谨慎决策")
    logger.info("  4. 建议结合自身风险承受能力和投资目标进行决策")
    logger.info("")


if __name__ == "__main__":
    main()
