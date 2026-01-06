# A股股息率计算模块

基于akshare库的A股股息率计算功能模块，提供准确的股息率计算、趋势分析和股票筛选功能。

## 功能特性

- **股息率计算**: 支持单只股票和批量股票的股息率计算
- **TTM股息率**: 计算过去12个月的滚动股息率
- **趋势分析**: 分析股息率的历史趋势和增长率
- **高股息筛选**: 根据阈值筛选高股息率股票
- **自定义计算**: 支持自定义分红金额的股息率计算
- **综合分析**: 提供风险等级评估和投资建议
- **数据缓存**: 智能缓存机制，减少API请求
- **配置管理**: 灵活的配置系统，支持YAML和环境变量

## 安装依赖

```bash
pip install akshare>=1.12.0 pandas>=2.0.0
```

## 快速开始

### 基本使用

```python
from seer_dividend_rate import get_dividend_yield

# 获取单只股票的股息率
dividend_yield = get_dividend_yield("600519")  # 贵州茅台

print(f"股票代码: {dividend_yield.stock_code}")
print(f"股票名称: {dividend_yield.stock_name}")
print(f"当前股价: {dividend_yield.current_price}元")
print(f"股息率: {dividend_yield.dividend_yield}%")
print(f"年度每股股息: {dividend_yield.annual_dividend}元")
```

### 批量获取股息率

```python
from seer_dividend_rate import get_batch_dividend_yields

stock_codes = ["600519", "000858", "600036", "601318", "000001"]
result = get_batch_dividend_yields(stock_codes)

print(f"平均股息率: {result.avg_dividend_yield}%")
print(f"最高股息率: {result.max_dividend_yield}%")
print(f"高股息股票数: {len(result.high_dividend_stocks)}")
```

### 获取高股息率股票

```python
from seer_dividend_rate import get_high_dividend_stocks

# 获取股息率超过4%的股票
high_dividend_stocks = get_high_dividend_stocks(threshold=4.0)

for stock in high_dividend_stocks:
    print(f"{stock.stock_code} {stock.stock_name}: {stock.dividend_yield}%")
```

### 股息率趋势分析

```python
from seer_dividend_rate import get_dividend_trend

# 分析过去5年的股息率趋势
trend = get_dividend_trend("600519", years=5)

print(f"平均股息率: {trend.avg_dividend_yield}%")
print(f"股息增长率: {trend.dividend_growth_rate}%")

for year, yield_val in zip(trend.years, trend.dividend_yields):
    print(f"{year}年: {yield_val}%")
```

### 综合分析

```python
from seer_dividend_rate import analyze_dividend

# 综合分析股票股息率
analysis = analyze_dividend("600519")

print(f"股息率: {analysis.dividend_yield.dividend_yield}%")
print(f"是否为高股息股票: {analysis.is_high_dividend}")
print(f"风险等级: {analysis.risk_level}")
print(f"投资建议: {analysis.recommendation}")
```

### 自定义股息率计算

```python
from seer_dividend_rate import calculate_custom_yield

# 假设每股分红25元
custom_yield = calculate_custom_yield("600519", 25.0)

print(f"计算股息率: {custom_yield.dividend_yield}%")
```

## API 接口

### 主要接口

- `get_dividend_yield(stock_code: str)` - 获取单只股票的股息率
- `get_batch_dividend_yields(stock_codes: list)` - 批量获取股息率
- `get_high_dividend_stocks(stock_codes: list, threshold: float)` - 获取高股息率股票
- `get_dividend_trend(stock_code: str, years: int)` - 获取股息率趋势
- `calculate_custom_yield(stock_code: str, dividend_amount: float)` - 自定义股息率计算
- `analyze_dividend(stock_code: str)` - 综合分析股息率

### 核心类

- `DataFetcher` - 数据获取类，负责从akshare获取股票数据
- `DividendCalculator` - 股息率计算类，提供各种计算功能
- `StockInfo` - 股票基本信息模型
- `DividendYield` - 股息率结果模型
- `DividendTrend` - 股息率趋势模型

## 配置说明

配置文件位于 `config/config.yaml`，包含以下配置项：

```yaml
dividend_rate:
  data_source:
    source: "eastmoney"  # 数据源: eastmoney, sina, tencent
    api_timeout: 30
    retry_times: 3
    use_cache: true
    cache_expire_hours: 24
  calculation:
    high_dividend_threshold: 4.0  # 高股息率阈值(%)
    ttm_months: 12  # TTM计算月数
    min_dividend_years: 3  # 最少分红年数
    dividend_growth_threshold: 5.0  # 股息增长阈值(%)
  storage:
    cache_dir: "./cache/dividend"
    data_dir: "./data/dividend"
    enable_persistence: true
```

## 数据模型

### StockInfo
- `stock_code`: 股票代码
- `stock_name`: 股票名称
- `current_price`: 当前股价
- `market_cap`: 市值
- `pe_ratio`: 市盈率
- `pb_ratio`: 市净率
- `ps_ratio`: 市销率

### DividendYield
- `stock_code`: 股票代码
- `stock_name`: 股票名称
- `current_price`: 当前股价
- `dividend_yield`: 股息率(%)
- `annual_dividend`: 年度每股股息
- `ttm_dividend_yield`: TTM股息率(%)
- `dividend_records`: 分红记录列表

### DividendTrend
- `stock_code`: 股票代码
- `stock_name`: 股票名称
- `years`: 年份列表
- `dividend_yields`: 股息率列表(%)
- `dividends_per_share`: 每股分红列表
- `avg_dividend_yield`: 平均股息率(%)
- `dividend_growth_rate`: 股息增长率(%)

## 测试

运行测试示例：

```bash
python tests/test_dividend_rate.py
```

测试示例包含以下功能：
- 单只股票股息率计算
- 批量股息率获取
- 高股息股票筛选
- 股息率趋势分析
- 自定义股息率计算
- 综合分析
- 股票筛选
- 数据获取器测试

## 注意事项

1. **数据源限制**: akshare库的数据源可能有访问频率限制，建议合理使用缓存
2. **数据时效性**: 股票数据实时变化，建议定期更新缓存
3. **网络依赖**: 模块需要网络连接来获取实时数据
4. **股票代码格式**: 使用6位数字股票代码，如"600519"
5. **异常处理**: 建议在使用时添加适当的异常处理

## 性能优化

- **缓存机制**: 默认启用缓存，缓存时间为24小时
- **批量处理**: 批量获取股票数据时，建议分批处理
- **异步请求**: 对于大量股票，可以考虑异步请求（待实现）

## 扩展功能

可以基于此模块扩展以下功能：
- 股息率预测
- 行业股息率对比
- 股息率与股价相关性分析
- 股息率投资组合构建
- 股息率历史回测

## 许可证

本模块遵循项目的开源许可证。

## 贡献

欢迎提交问题和改进建议。