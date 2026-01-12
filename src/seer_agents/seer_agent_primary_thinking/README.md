# 基于B站投资专家思维模式的个股分析Agent

## 项目概述

本项目是一个基于B站投资专家"领居大爷"思维模式的个股投资分析系统，通过结构化知识库和多Agent协调分析，为用户提供专业的个股投资分析报告。

## 核心功能

### 1. 数据资源整合
- 处理Markdown格式的投资专家原始语录文件
- 提取关键信息、核心概念、技术形态、交易策略、风险提示等
- 自动去重和格式标准化

### 2. 知识库构建
- 结构化知识库系统，包含：
  - 分析维度（主力行为、技术形态、量价关系、技术指标、市场环境、风险控制）
  - 分析框架（主力行为、技术形态、主升浪、时间周期）
  - 主力行为（建仓、洗盘、拉升、出货）
  - 交易策略（起涨结构、主力行为、时间节点、风险控制）
- 支持知识检索和分类查询

### 3. 数据采集模块
- 基于akshare金融数据接口
- 多维度数据采集：
  - 股票日线数据
  - 股票实时数据
  - 股票基本面数据
  - 股票财务数据
  - 行业数据
  - 市场指数数据
- 数据质量校验与异常处理
- 数据缓存与更新策略

### 4. 智能分析Agent
- 基本面分析Agent：评估估值、市值等基本面指标
- 技术面分析Agent：技术指标计算、形态识别、主力行为分析
- 行业分析Agent：行业对比、竞争格局分析
- 风险评估Agent：综合风险评估和风控建议
- 多Agent协调分析：综合各Agent结果，生成综合建议

### 5. 系统集成
- 统一的配置管理
- 模块化架构设计
- 完整的日志系统
- 端到端功能测试

## 项目结构

```
seer_agent_primary_thinking/
├── __init__.py                 # 模块入口
├── models.py                   # 数据模型定义
├── data_processor.py           # 数据处理器
├── knowledge_base.py           # 知识库
├── data_fetcher.py            # 数据采集器
├── technical_analyzer.py       # 技术分析器
├── analysis_agent.py           # 分析Agent
├── primary_agent.py            # 主Agent
├── build_knowledge_base.py     # 知识库构建脚本
├── main.py                    # 主程序入口
├── test_system.py             # 系统测试脚本
└── src_data/                  # 专家语录数据目录
```

## 使用说明

### 1. 构建知识库

首先需要处理专家语录文件并构建知识库：

```bash
python src/seer_agents/seer_agent_primary_thinking/build_knowledge_base.py
```

该脚本会：
- 读取 `src_data/` 目录下的所有Markdown文件
- 提取专家语录的关键信息
- 构建结构化知识库
- 生成 `processed_quotes.json` 和 `knowledge_base.json` 文件

### 2. 运行个股分析

使用主程序进行个股分析：

```bash
python src/seer_agents/seer_agent_primary_thinking/main.py --stock-code 000001 --stock-name 平安银行 --days 90
```

参数说明：
- `--stock-code`: 股票代码（必需）
- `--stock-name`: 股票名称（可选）
- `--days`: 分析天数（默认90天）
- `--output-dir`: 报告输出目录（默认：./data/primary_thinking/reports）
- `--enable-fundamental`: 启用基本面分析（默认启用）
- `--enable-technical`: 启用技术面分析（默认启用）
- `--enable-industry`: 启用行业分析（默认启用）
- `--enable-risk`: 启用风险评估（默认启用）
- `--load-knowledge`: 加载知识库文件路径（可选）
- `--config`: 配置文件路径（可选）

### 3. 系统测试

运行系统测试脚本验证功能：

```bash
python src/seer_agents/seer_agent_primary_thinking/test_system.py
```

测试内容包括：
- 数据处理器测试
- 知识库测试
- 数据采集器测试
- 技术分析器测试
- 主Agent测试
- 知识检索测试

## 分析报告

分析完成后，系统会生成包含以下内容的详细报告：

### 基本信息
- 股票代码和名称
- 分析日期
- 主力状态
- 交易阶段

### 分析维度
1. **基本面分析**
   - 市盈率、市净率评估
   - 市值分析
   - 估值合理性判断

2. **技术面分析**
   - 均线系统（MA5、MA10、MA20、MA60）
   - MACD指标（DIF、DEA、MACD）
   - RSI指标（RSI6、RSI12、RSI24）
   - KDJ指标（K、D、J）
   - 技术形态识别（颈线突破、大长腿、N型结构等）
   - 量价关系分析
   - 主力行为分析

3. **行业分析**
   - 行业规模分析
   - 行业对比分析
   - 竞争格局评估

4. **风险评估**
   - 综合风险等级
   - 风险因素分析
   - 风控建议

### 综合建议
- 投资建议（买入/卖出/持有/观望）
- 综合置信度（0-1）
- 综合风险等级（低/中/高）
- 关键分析要点
- 投资机会
- 风险提示
- 详细推理过程

## 专家思维模式

本系统基于B站投资专家"领居大爷"的核心思维模式：

### 1. 主力行为分析
- 识别主力资金在不同阶段的操作手法
- 判断主力意图（建仓、洗盘、拉升、出货）
- 分析拖拉机单、主动补货区、拦截吃货等特征

### 2. 技术形态识别
- 识别关键技术形态判断买卖时机
- 起涨结构（颈线突破、大长腿、N型结构、阳包阴）
- 逃顶结构（缩量加速、放量大阳线、高位分歧、吊颈线）
- 形态位置判断（底部起涨 vs 上涨途中）

### 3. 量价关系分析
- 分析成交量与价格的关系判断资金流向
- 量增价涨：多头力量强劲
- 量增价跌：恐慌性抛售
- 量减价涨：上涨动力不足
- 量减价跌：下跌动力不足

### 4. 风险控制评估
- 评估投资风险并制定合理的风控策略
- 严格设置止损位
- 分批建仓控制风险
- 不盲目抄底
- 优先保住本金

### 5. 时间节点决策
- 利用关键时间节点提高资金效率
- 上午10点前：观察市场风险
- 下午2点半后：判断主力资金动向
- 次日早盘：确认趋势延续性

## 技术架构

### 数据模型
- 使用Pydantic进行数据验证和序列化
- 类型注解确保代码可维护性
- 清晰的数据结构定义

### 数据采集
- 基于akshare金融数据接口
- 支持数据缓存减少重复请求
- 多线程并发采集提高效率
- 数据质量校验确保数据可靠性

### 知识库
- 结构化知识存储
- 支持知识检索和分类
- 基于专家语录构建专业知识体系
- 可扩展的知识条目管理

### 多Agent架构
- 模块化Agent设计
- 并发执行提高分析效率
- 综合分析结果生成建议
- 可扩展的Agent类型

### 技术分析
- 完整的技术指标计算（MACD、RSI、KDJ）
- 技术形态识别算法
- 量价关系分析
- 主力行为判断逻辑

## 配置管理

系统支持通过配置文件进行配置：

```yaml
# 示例配置
data_source:
  use_cache: true
  cache_expire_hours: 24
  max_workers: 10
  request_interval: 0.5

analysis:
  enable_fundamental: true
  enable_technical: true
  enable_industry: true
  enable_risk_assessment: true
```

## 依赖要求

### 核心依赖
- Python 3.11+
- akshare: 金融数据接口
- pandas: 数据处理
- numpy: 数值计算
- pydantic: 数据验证
- pydantic-settings: 配置管理
- tqdm: 进度显示

### 可选依赖
- openai: OpenAI LLM支持
- anthropic: Anthropic LLM支持
- google-generativeai: Google Gemini LLM支持

## 注意事项

1. **投资风险提示**
   - 本系统分析结果仅供参考，不构成投资建议
   - 投资有风险，请谨慎决策
   - 建议结合自身风险承受能力和投资目标进行决策

2. **数据来源**
   - 股票数据来源于akshare金融数据接口
   - 数据可能存在延迟或错误
   - 请以实际市场数据为准

3. **知识库更新**
   - 专家语录需要定期更新以保持知识库时效性
   - 建议定期运行 `build_knowledge_base.py` 更新知识库

4. **系统性能**
   - 数据采集受网络状况影响
   - 建议在网络稳定时运行
   - 可通过调整并发数优化性能

## 扩展开发

### 添加新的分析Agent

1. 在 `analysis_agent.py` 中创建新的Agent类
2. 继承 `AnalysisAgent` 基类
3. 实现 `analyze` 方法
4. 在 `primary_agent.py` 中注册新Agent

### 添加新的技术指标

1. 在 `technical_analyzer.py` 中添加计算方法
2. 更新 `comprehensive_analysis` 方法
3. 在分析结果中包含新指标

### 扩展知识库

1. 更新 `knowledge_base.py` 中的初始化方法
2. 添加新的分析维度、框架或策略
3. 重新构建知识库

## 故障排除

### 常见问题

1. **数据采集失败**
   - 检查网络连接
   - 检查akshare接口状态
   - 查看日志中的错误信息

2. **知识库构建失败**
   - 检查src_data目录是否存在
   - 检查Markdown文件格式是否正确
   - 查看日志中的错误信息

3. **分析结果异常**
   - 检查股票代码是否正确
   - 检查数据是否完整
   - 查看日志中的警告信息

## 版本信息

- 版本：1.0.0
- 发布日期：2026-01-12
- 作者：Seer Team

## 许可证

本项目遵循Seer项目的开源许可证。

## 联系方式

- 项目地址：d:\code\seer
- 文档目录：src/seer_agents/seer_agent_primary_thinking/
- 日志目录：./logs/seer.log
