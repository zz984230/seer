import argparse
from seer_dividend_rate import (
    get_dividend_yield,
    get_batch_dividend_yields,
    get_high_dividend_stocks,
    get_dividend_trend,
    calculate_custom_yield,
    analyze_dividend
)
from seer.logger import logger


def main():
    """股息率计算模块主入口"""
    parser = argparse.ArgumentParser(description="A股股息率计算应用")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 单只股票股息率命令
    single_parser = subparsers.add_parser("single", help="获取单只股票的股息率")
    single_parser.add_argument("stock_code", type=str, help="股票代码（如：600519）")
    
    # 批量股息率命令
    batch_parser = subparsers.add_parser("batch", help="批量获取股票股息率")
    batch_parser.add_argument("stock_codes", type=str, nargs="+", help="股票代码列表（如：600519 000858 600036）")
    
    # 高股息率股票命令
    high_parser = subparsers.add_parser("high", help="获取高股息率股票")
    high_parser.add_argument("--stock-codes", type=str, nargs="+", help="股票代码列表（可选）")
    high_parser.add_argument("--threshold", type=float, default=4.0, help="股息率阈值（默认：4.0%）")
    
    # 股息率趋势命令
    trend_parser = subparsers.add_parser("trend", help="获取股息率趋势")
    trend_parser.add_argument("stock_code", type=str, help="股票代码")
    trend_parser.add_argument("--years", type=int, default=5, help="分析年数（默认：5年）")
    
    # 自定义股息率计算命令
    custom_parser = subparsers.add_parser("custom", help="自定义股息率计算")
    custom_parser.add_argument("stock_code", type=str, help="股票代码")
    custom_parser.add_argument("dividend_amount", type=float, help="自定义分红金额")
    
    # 综合分析命令
    analyze_parser = subparsers.add_parser("analyze", help="综合分析股息率")
    analyze_parser.add_argument("stock_code", type=str, help="股票代码")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "single":
            handle_single(args.stock_code)
        elif args.command == "batch":
            handle_batch(args.stock_codes)
        elif args.command == "high":
            handle_high(args.stock_codes, args.threshold)
        elif args.command == "trend":
            handle_trend(args.stock_code, args.years)
        elif args.command == "custom":
            handle_custom(args.stock_code, args.dividend_amount)
        elif args.command == "analyze":
            handle_analyze(args.stock_code)
    
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        raise


def handle_single(stock_code: str):
    """处理单只股票股息率查询"""
    logger.info(f"获取股票 {stock_code} 的股息率...")
    
    dividend_yield = get_dividend_yield(stock_code)
    
    if dividend_yield:
        print("\n" + "=" * 50)
        print("股票股息率信息")
        print("=" * 50)
        print(f"股票代码: {dividend_yield.stock_code}")
        print(f"股票名称: {dividend_yield.stock_name}")
        print(f"当前股价: {dividend_yield.current_price}元")
        print(f"股息率: {dividend_yield.dividend_yield}%")
        print(f"年度每股股息: {dividend_yield.annual_dividend}元")
        print(f"TTM股息率: {dividend_yield.ttm_dividend_yield}%")
        print(f"分红记录数: {len(dividend_yield.dividend_records)}")
        print("=" * 50)
        logger.info(f"获取成功: {stock_code}")
    else:
        print(f"无法获取股票 {stock_code} 的股息率")
        logger.warning(f"获取失败: {stock_code}")


def handle_batch(stock_codes: list):
    """处理批量股息率查询"""
    logger.info(f"批量获取 {len(stock_codes)} 只股票的股息率...")
    
    result = get_batch_dividend_yields(stock_codes)
    
    if result and result.dividend_yields:
        print("\n" + "=" * 60)
        print("批量股息率信息")
        print("=" * 60)
        print(f"查询股票数: {len(stock_codes)}")
        print(f"成功获取数: {len(result.dividend_yields)}")
        print(f"平均股息率: {result.avg_dividend_yield}%")
        print(f"最高股息率: {result.max_dividend_yield}%")
        print(f"最低股息率: {result.min_dividend_yield}%")
        print(f"高股息股票数: {len(result.high_dividend_stocks)}")
        print("\n股票详情:")
        print("-" * 60)
        
        for dividend_yield in result.dividend_yields:
            print(f"{dividend_yield.stock_code} {dividend_yield.stock_name}: "
                  f"{dividend_yield.dividend_yield}% (股价: {dividend_yield.current_price}元)")
        
        print("=" * 60)
        logger.info(f"批量获取成功")
    else:
        print("批量获取失败")
        logger.warning("批量获取失败")


def handle_high(stock_codes: list, threshold: float):
    """处理高股息率股票查询"""
    logger.info(f"获取股息率超过 {threshold}% 的高股息股票...")
    
    high_dividend_stocks = get_high_dividend_stocks(stock_codes, threshold)
    
    if high_dividend_stocks:
        print("\n" + "=" * 60)
        print(f"高股息率股票（股息率 > {threshold}%）")
        print("=" * 60)
        print(f"找到 {len(high_dividend_stocks)} 只高股息率股票\n")
        
        for stock in high_dividend_stocks:
            print(f"{stock.stock_code} {stock.stock_name}: {stock.dividend_yield}%")
            print(f"  当前股价: {stock.current_price}元")
            print(f"  年度每股股息: {stock.annual_dividend}元")
            print(f"  TTM股息率: {stock.ttm_dividend_yield}%")
            print("-" * 60)
        
        logger.info(f"找到 {len(high_dividend_stocks)} 只高股息率股票")
    else:
        print(f"未找到股息率超过 {threshold}% 的股票")
        logger.info(f"未找到高股息率股票")


def handle_trend(stock_code: str, years: int):
    """处理股息率趋势查询"""
    logger.info(f"获取股票 {stock_code} 过去 {years} 年的股息率趋势...")
    
    trend = get_dividend_trend(stock_code, years)
    
    if trend:
        print("\n" + "=" * 60)
        print("股息率趋势分析")
        print("=" * 60)
        print(f"股票代码: {trend.stock_code}")
        print(f"股票名称: {trend.stock_name}")
        print(f"平均股息率: {trend.avg_dividend_yield}%")
        print(f"股息增长率: {trend.dividend_growth_rate}%")
        print("\n历年股息率:")
        print("-" * 60)
        
        for year, yield_val, dividend in zip(trend.years, trend.dividend_yields, trend.dividends_per_share):
            print(f"{year}年: 股息率 {yield_val}%, 每股分红 {dividend}元")
        
        print("=" * 60)
        logger.info(f"趋势分析完成: {stock_code}")
    else:
        print(f"无法获取股票 {stock_code} 的股息率趋势")
        logger.warning(f"趋势分析失败: {stock_code}")


def handle_custom(stock_code: str, dividend_amount: float):
    """处理自定义股息率计算"""
    logger.info(f"计算股票 {stock_code} 的自定义股息率（每股分红 {dividend_amount}元）...")
    
    custom_yield = calculate_custom_yield(stock_code, dividend_amount)
    
    if custom_yield:
        print("\n" + "=" * 60)
        print("自定义股息率计算结果")
        print("=" * 60)
        print(f"股票代码: {custom_yield.stock_code}")
        print(f"股票名称: {custom_yield.stock_name}")
        print(f"当前股价: {custom_yield.current_price}元")
        print(f"自定义每股分红: {dividend_amount}元")
        print(f"计算股息率: {custom_yield.dividend_yield}%")
        print("=" * 60)
        logger.info(f"自定义计算完成: {stock_code}")
    else:
        print(f"无法计算股票 {stock_code} 的自定义股息率")
        logger.warning(f"自定义计算失败: {stock_code}")


def handle_analyze(stock_code: str):
    """处理综合分析"""
    logger.info(f"综合分析股票 {stock_code} 的股息率...")
    
    analysis = analyze_dividend(stock_code)
    
    if analysis:
        print("\n" + "=" * 60)
        print("股息率综合分析")
        print("=" * 60)
        print(f"股票代码: {analysis.stock_code}")
        print(f"股票名称: {analysis.stock_name}")
        print(f"股息率: {analysis.dividend_yield.dividend_yield}%")
        print(f"是否为高股息股票: {'是' if analysis.is_high_dividend else '否'}")
        print(f"风险等级: {analysis.risk_level}")
        print(f"投资建议: {analysis.recommendation}")
        
        if analysis.dividend_trend:
            print(f"平均股息率: {analysis.dividend_trend.avg_dividend_yield}%")
            print(f"股息增长率: {analysis.dividend_trend.dividend_growth_rate}%")
        
        print("=" * 60)
        logger.info(f"综合分析完成: {stock_code}")
    else:
        print(f"无法分析股票 {stock_code} 的股息率")
        logger.warning(f"综合分析失败: {stock_code}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("A股股息率计算应用")
    print("=" * 60)
    print("\n使用说明：")
    print("  python src/main_dividend_rate.py <命令> [参数]\n")
    print("可用命令：")
    print("  single <股票代码>              - 获取单只股票的股息率")
    print("  batch <股票代码列表>          - 批量获取股票股息率")
    print("  high [--threshold <阈值>]      - 获取高股息率股票")
    print("  trend <股票代码> [--years <年数>] - 获取股息率趋势")
    print("  custom <股票代码> <分红金额>   - 自定义股息率计算")
    print("  analyze <股票代码>             - 综合分析股息率\n")
    print("示例：")
    print("  python src/main_dividend_rate.py single 600519")
    print("  python src/main_dividend_rate.py batch 600519 000858 600036")
    print("  python src/main_dividend_rate.py high --threshold 4.0")
    print("  python src/main_dividend_rate.py trend 600519 --years 5")
    print("  python src/main_dividend_rate.py custom 600519 25.0")
    print("  python src/main_dividend_rate.py analyze 600519")
    print("=" * 60 + "\n")
    
    main()
