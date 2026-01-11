"""
股票技术面分析主入口

本模块提供基于股票数据的LLM技术面分析功能，包括：
1. 股票数据获取与存储
2. 技术指标计算（MACD、RSI、KDJ等）
3. 趋势模式识别（头肩顶、双底等）
4. 量价关系分析
5. LLM多Agent分析
6. 报告生成（HTML、PDF、JSON）

使用方法：
    python src/main_tech_analysis.py --code <股票代码> --start <开始日期> --end <结束日期>

示例：
    python src/main_tech_analysis.py --code 600519 --start 20240101 --end 20241231
"""

import argparse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from seer_tech_analysis import analyze_stock, generate_reports
from seer_tech_analysis.models import AnalysisRequest
from seer.logger import logger


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="股票技术面分析工具")
    parser.add_argument("--code", type=str, required=True, help="股票代码（如：600519）")
    parser.add_argument("--name", type=str, default=None, help="股票名称（可选）")
    parser.add_argument("--start", type=str, required=True, help="开始日期（YYYYMMDD）")
    parser.add_argument("--end", type=str, required=True, help="结束日期（YYYYMMDD）")
    parser.add_argument("--days", type=int, default=90, help="分析天数（默认：90天）")
    parser.add_argument("--no-llm", action="store_true", help="不使用LLM分析")
    parser.add_argument("--no-pattern", action="store_true", help="不进行形态识别")
    parser.add_argument("--no-volume", action="store_true", help="不进行量价分析")
    parser.add_argument("--indicators", type=str, nargs="+", default=["MACD", "RSI", "KDJ"], 
                       help="技术指标列表（默认：MACD RSI KDJ）")
    parser.add_argument("--no-reports", action="store_true", help="不生成报告")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("股票技术面分析工具启动")
    logger.info("=" * 60)
    logger.info(f"股票代码: {args.code}")
    logger.info(f"股票名称: {args.name or '自动获取'}")
    logger.info(f"分析日期范围: {args.start} ~ {args.end}")
    logger.info(f"技术指标: {', '.join(args.indicators)}")
    logger.info(f"LLM分析: {'禁用' if args.no_llm else '启用'}")
    logger.info(f"形态识别: {'禁用' if args.no_pattern else '启用'}")
    logger.info(f"量价分析: {'禁用' if args.no_volume else '启用'}")
    logger.info("=" * 60)
    
    try:
        request = AnalysisRequest(
            stock_code=args.code,
            stock_name=args.name,
            start_date=args.start,
            end_date=args.end,
            indicators=args.indicators,
            enable_pattern_recognition=not args.no_pattern,
            enable_volume_analysis=not args.no_volume,
            use_llm_analysis=not args.no_llm
        )
        
        logger.info("开始股票分析...")
        success, msg, analysis = analyze_stock(
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
            stock_name=request.stock_name,
            indicators=request.indicators,
            enable_pattern_recognition=request.enable_pattern_recognition,
            enable_volume_analysis=request.enable_volume_analysis,
            use_llm_analysis=request.use_llm_analysis
        )
        
        if not success or not analysis:
            logger.error(f"股票分析失败: {msg}")
            return
        
        logger.info("=" * 60)
        logger.info("分析结果摘要")
        logger.info("=" * 60)
        logger.info(f"股票: {analysis.stock_name}({analysis.stock_code})")
        logger.info(f"分析日期: {analysis.analysis_date}")
        logger.info(f"综合建议: {analysis.overall_recommendation}")
        logger.info(f"综合置信度: {analysis.overall_confidence:.2f}")
        logger.info(f"风险等级: {analysis.overall_risk_level}")
        
        if analysis.key_points:
            logger.info("\n关键点:")
            for i, point in enumerate(analysis.key_points, 1):
                logger.info(f"  {i}. {point}")
        
        if analysis.warnings:
            logger.info("\n风险提示:")
            for i, warning in enumerate(analysis.warnings, 1):
                logger.info(f"  {i}. {warning}")
        
        if analysis.agent_analyses:
            logger.info("\nAgent分析结果:")
            for agent_analysis in analysis.agent_analyses:
                logger.info(f"  {agent_analysis.agent_name}:")
                logger.info(f"    建议: {agent_analysis.recommendation}")
                logger.info(f"    置信度: {agent_analysis.confidence:.2f}")
                logger.info(f"    风险等级: {agent_analysis.risk_level}")
        
        if not args.no_reports:
            logger.info("\n开始生成报告...")
            reports = generate_reports(analysis)
            
            if reports:
                logger.info("报告生成完成:")
                for report_type, report_path in reports.items():
                    logger.info(f"  {report_type.upper()}: {report_path}")
            else:
                logger.warning("未生成任何报告")
        
        logger.info("=" * 60)
        logger.info("分析完成")
        logger.info("=" * 60)
    
    except KeyboardInterrupt:
        logger.info("用户中断分析")
    except Exception as e:
        logger.error(f"分析过程发生错误: {str(e)}")
        raise


def analyze_by_date_range(stock_code: str, days: int = 90):
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    
    success, msg, analysis = analyze_stock(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date
    )
    
    if success and analysis:
        reports = generate_reports(analysis)
        return analysis, reports
    
    return None, None


def batch_analyze(stock_codes: list, days: int = 90):
    results = {}
    
    for stock_code in stock_codes:
        logger.info(f"分析股票: {stock_code}")
        analysis, reports = analyze_by_date_range(stock_code, days)
        
        if analysis:
            results[stock_code] = {
                'analysis': analysis,
                'reports': reports
            }
        else:
            results[stock_code] = None
    
    return results


if __name__ == "__main__":
    main()
