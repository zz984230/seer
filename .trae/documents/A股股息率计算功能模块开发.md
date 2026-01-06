# A股股息率计算功能模块开发计划

## 1. 模块结构设计
在 `/Users/zero/Project/seer/src/seer_dividend_rate/` 目录下创建以下文件：
- `__init__.py` - 模块初始化文件，导出主要接口
- `dividend_calculator.py` - 核心计算类，实现股息率计算逻辑
- `data_fetcher.py` - 数据获取类，基于akshare获取股票数据
- `models.py` - 数据模型定义，使用pydantic定义数据结构
- `config.py` - 配置管理，继承项目配置体系

## 2. 核心功能实现

### 2.1 数据获取 (data_fetcher.py)
- 使用akshare.stock_a_indicator()获取A股估值指标
- 使用akshare.stock_a_spot_em()获取实时股价数据
- 使用akshare.stock_dividend_detail_sina()获取分红详情
- 实现批量获取和单只股票获取接口
- 添加数据缓存机制，避免重复请求

### 2.2 股息率计算 (dividend_calculator.py)
- 实现基础股息率计算：股息率 = 年度每股股息 / 当前股价
- 支持TTM（过去12个月）股息率计算
- 支持历史股息率计算
- 实现股息率趋势分析
- 提供股息率排名和筛选功能

### 2.3 数据模型 (models.py)
- StockInfo: 股票基本信息模型
- DividendInfo: 分红信息模型
- DividendYield: 股息率结果模型
- 使用pydantic进行数据验证

### 2.4 配置管理 (config.py)
- 扩展项目配置，添加股息率相关配置
- 数据源配置（akshare接口选择）
- 缓存配置
- 日志配置

## 3. 依赖管理
- 在pyproject.toml中添加akshare依赖
- 添加pandas用于数据处理
- 添加requests用于网络请求（如果需要）

## 4. 接口设计
提供以下主要接口：
- `get_dividend_yield(stock_code)` - 获取单只股票股息率
- `get_batch_dividend_yields(stock_codes)` - 批量获取股息率
- `get_high_dividend_stocks(threshold)` - 获取高股息率股票
- `get_dividend_trend(stock_code, years)` - 获取股息率趋势
- `calculate_custom_yield(stock_code, dividend_amount)` - 自定义股息率计算

## 5. 异常处理和日志
- 集成项目现有的logger系统
- 完善的异常处理机制
- 数据验证和错误提示

## 6. 测试支持
- 创建测试用例示例
- 提供mock数据用于测试