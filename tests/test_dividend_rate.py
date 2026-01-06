"""
A股股息率计算模块测试示例

本文件提供了使用seer_dividend_rate模块的示例代码
"""

from seer_dividend_rate import (
    get_dividend_yield,
    get_batch_dividend_yields,
    get_high_dividend_stocks,
    get_dividend_trend,
    calculate_custom_yield,
    analyze_dividend,
    calculator,
    fetcher,
    StockFilter
)


def test_single_stock_dividend_yield():
    """
    测试1: 获取单只股票的股息率
    """
    print("\n=== 测试1: 获取单只股票的股息率 ===")
    
    stock_code = "600519"  # 贵州茅台
    
    dividend_yield = get_dividend_yield(stock_code)
    
    if dividend_yield:
        print(f"股票代码: {dividend_yield.stock_code}")
        print(f"股票名称: {dividend_yield.stock_name}")
        print(f"当前股价: {dividend_yield.current_price}元")
        print(f"股息率: {dividend_yield.dividend_yield}%")
        print(f"年度每股股息: {dividend_yield.annual_dividend}元")
        print(f"TTM股息率: {dividend_yield.ttm_dividend_yield}%")
        print(f"分红记录数: {len(dividend_yield.dividend_records)}")
    else:
        print(f"无法获取股票 {stock_code} 的股息率")


def test_batch_dividend_yields():
    """
    测试2: 批量获取股息率
    """
    print("\n=== 测试2: 批量获取股息率 ===")
    
    stock_codes = ["600519", "000858", "600036", "601318", "000001"]
    
    result = get_batch_dividend_yields(stock_codes)
    
    print(f"总股票数: {result.total_stocks}")
    print(f"平均股息率: {result.avg_dividend_yield}%")
    print(f"最高股息率: {result.max_dividend_yield}%")
    print(f"最低股息率: {result.min_dividend_yield}%")
    print(f"高股息股票数: {len(result.high_dividend_stocks)}")
    
    print("\n高股息股票列表:")
    for stock in result.high_dividend_stocks:
        print(f"  {stock.stock_code} {stock.stock_name}: {stock.dividend_yield}%")


def test_high_dividend_stocks():
    """
    测试3: 获取高股息率股票
    """
    print("\n=== 测试3: 获取高股息率股票 ===")
    
    stock_codes = ["600519", "000858", "600036", "601318", "000001", "601398", "601939"]
    threshold = 3.0  # 3%以上
    
    high_dividend_stocks = get_high_dividend_stocks(stock_codes, threshold)
    
    print(f"阈值: {threshold}%")
    print(f"找到高股息股票数: {len(high_dividend_stocks)}")
    
    print("\n高股息股票详情:")
    for stock in high_dividend_stocks:
        print(f"  {stock.stock_code} {stock.stock_name}: {stock.dividend_yield}%, 股价: {stock.current_price}元")


def test_dividend_trend():
    """
    测试4: 获取股息率趋势
    """
    print("\n=== 测试4: 获取股息率趋势 ===")
    
    stock_code = "600519"
    years = 5
    
    trend = get_dividend_trend(stock_code, years)
    
    if trend:
        print(f"股票代码: {trend.stock_code}")
        print(f"股票名称: {trend.stock_name}")
        print(f"平均股息率: {trend.avg_dividend_yield}%")
        print(f"股息增长率: {trend.dividend_growth_rate}%")
        
        print("\n历年股息率:")
        for year, yield_val in zip(trend.years, trend.dividend_yields):
            print(f"  {year}年: {yield_val}%")
    else:
        print(f"无法获取股票 {stock_code} 的股息率趋势")


def test_custom_yield():
    """
    测试5: 自定义股息率计算
    """
    print("\n=== 测试5: 自定义股息率计算 ===")
    
    stock_code = "600519"
    custom_dividend = 25.0  # 假设每股分红25元
    
    custom_yield = calculate_custom_yield(stock_code, custom_dividend)
    
    if custom_yield:
        print(f"股票代码: {custom_yield.stock_code}")
        print(f"股票名称: {custom_yield.stock_name}")
        print(f"当前股价: {custom_yield.current_price}元")
        print(f"自定义分红金额: {custom_dividend}元")
        print(f"计算股息率: {custom_yield.dividend_yield}%")
    else:
        print(f"无法计算股票 {stock_code} 的自定义股息率")


def test_dividend_analysis():
    """
    测试6: 综合分析股息率
    """
    print("\n=== 测试6: 综合分析股息率 ===")
    
    stock_code = "600519"
    
    analysis = analyze_dividend(stock_code)
    
    if analysis:
        print(f"股票代码: {analysis.stock_code}")
        print(f"股票名称: {analysis.stock_name}")
        print(f"股息率: {analysis.dividend_yield.dividend_yield}%")
        print(f"是否为高股息股票: {analysis.is_high_dividend}")
        print(f"风险等级: {analysis.risk_level}")
        print(f"投资建议: {analysis.recommendation}")
        
        if analysis.dividend_trend:
            print(f"股息增长率: {analysis.dividend_trend.dividend_growth_rate}%")
    else:
        print(f"无法分析股票 {stock_code} 的股息率")


def test_stock_filter():
    """
    测试7: 股票筛选
    """
    print("\n=== 测试7: 股票筛选 ===")
    
    stock_codes = ["600519", "000858", "600036", "601318", "000001"]
    
    batch_result = get_batch_dividend_yields(stock_codes)
    
    filter_config = StockFilter(
        min_dividend_yield=2.0,
        max_dividend_yield=10.0,
        exclude_st=True
    )
    
    filtered_stocks = calculator.filter_stocks(
        batch_result.high_dividend_stocks or 
        [dy for dy in [get_dividend_yield(code) for code in stock_codes] if dy],
        filter_config
    )
    
    print(f"筛选条件:")
    print(f"  最小股息率: {filter_config.min_dividend_yield}%")
    print(f"  最大股息率: {filter_config.max_dividend_yield}%")
    print(f"  排除ST股票: {filter_config.exclude_st}")
    print(f"\n筛选结果: {len(filtered_stocks)}只股票")
    
    for stock in filtered_stocks:
        print(f"  {stock.stock_code} {stock.stock_name}: {stock.dividend_yield}%")


def test_data_fetcher():
    """
    测试8: 数据获取器
    """
    print("\n=== 测试8: 数据获取器 ===")
    
    stock_code = "600519"
    
    stock_info = fetcher.get_stock_indicator(stock_code)
    if stock_info:
        print(f"股票信息:")
        print(f"  代码: {stock_info.stock_code}")
        print(f"  名称: {stock_info.stock_name}")
        print(f"  当前股价: {stock_info.current_price}元")
        print(f"  市盈率: {stock_info.pe_ratio}")
        print(f"  市净率: {stock_info.pb_ratio}")
    
    dividend_records = fetcher.get_dividend_records(stock_code)
    print(f"\n分红记录数: {len(dividend_records)}")
    if dividend_records:
        latest = dividend_records[0]
        print(f"最新分红: {latest.year}年, 每股{latest.dividend_per_share}元")


def main():
    """
    运行所有测试
    """
    print("=" * 60)
    print("A股股息率计算模块测试")
    print("=" * 60)
    
    try:
        test_single_stock_dividend_yield()
        test_batch_dividend_yields()
        test_high_dividend_stocks()
        test_dividend_trend()
        test_custom_yield()
        test_dividend_analysis()
        test_stock_filter()
        test_data_fetcher()
        
        print("\n" + "=" * 60)
        print("所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()