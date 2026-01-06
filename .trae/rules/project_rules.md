# Seer 项目规范

## 项目概述

Seer 是一个小红书爬虫应用，用于获取、清洗、分析和存储小红书平台的数据。

## 项目结构

```
seer/
├── config/                 # 配置文件目录
│   └── config.yaml        # 主配置文件
├── src/                   # 源代码目录
│   ├── seer/             # 主包
│   │   ├── analyzer/     # 数据分析模块
│   │   ├── cleaner/      # 数据清洗模块
│   │   ├── config/       # 配置管理模块
│   │   ├── crawler/      # 爬虫模块
│   │   │   ├── apis/     # API接口
│   │   │   ├── static/  # 静态资源（JS文件）
│   │   │   └── utils/   # 工具函数
│   │   ├── logger/       # 日志模块
│   │   ├── parser/       # 数据解析模块
│   │   ├── reporter/     # 报告生成模块
│   │   └── storage/      # 数据存储模块
│   ├── seer_dividend_rate/  # 股息率计算模块
│   └── main.py           # 主入口文件
├── tests/                 # 测试目录
├── .gitignore            # Git忽略文件
├── pyproject.toml        # 项目配置和依赖
└── README.md             # 项目说明
```

## 技术栈

### 核心依赖
- **Python**: 3.11+
- **playwright**: 浏览器自动化
- **beautifulsoup4**: HTML解析
- **pydantic-settings**: 配置管理
- **requests**: HTTP请求
- **pyyaml**: YAML配置文件解析
- **pyexecjs**: JavaScript执行
- **loguru**: 日志记录
- **python-dotenv**: 环境变量管理
- **retry**: 重试机制
- **openpyxl**: Excel文件处理
- **akshare**: 金融数据获取
- **pandas**: 数据分析

### 开发依赖
- **pytest**: 单元测试框架

## 代码规范

### 命名规范
- **类名**: 使用 PascalCase（如 `XiaohongshuCrawler`）
- **函数和方法名**: 使用 snake_case（如 `get_note_info`）
- **变量名**: 使用 snake_case（如 `user_id`）
- **常量名**: 使用 UPPER_SNAKE_CASE（如 `MAX_RETRIES`）
- **私有方法**: 以单下划线开头（如 `_clean_id`）
- **模块名**: 使用小写字母和下划线（如 `xhs_crawler.py`）

### 类型注解
- 所有函数参数和返回值必须添加类型注解
- 使用 `typing` 模块中的类型（如 `Dict`, `List`, `Optional`, `Any`）
- 示例：
```python
def get_note_info(self, note_url: str, cookies_str: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    pass
```

### 文档字符串
- 所有类和公共方法必须使用 docstring
- 使用 Google 风格或 reStructuredText 风格
- 示例：
```python
class XiaohongshuCrawler:
    def get_note_info(self, note_url: str, cookies_str: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        获取笔记详细信息

        :param note_url: 笔记URL
        :param cookies_str: Cookie字符串
        :return: (成功状态, 消息, 笔记信息)
        """
        pass
```

### 代码风格
- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 每行代码不超过 100 字符
- 避免不必要的注释
- 使用有意义的变量和函数名

## 架构设计

### 分层架构
项目采用分层架构，数据流向如下：
```
Crawler (爬虫) → Parser (解析) → Cleaner (清洗) → Analyzer (分析) → Reporter (报告) → Storage (存储)
```

### 模块职责
- **crawler**: 负责从小红书平台获取原始数据
- **parser**: 负责解析HTML/JSON数据，提取结构化信息
- **cleaner**: 负责数据清洗、验证和格式化
- **analyzer**: 负责数据分析和统计
- **reporter**: 负责生成分析报告
- **storage**: 负责数据持久化存储
- **logger**: 负责日志记录
- **config**: 负责配置管理

### 设计模式
- **单例模式**: 全局配置（`settings`）和日志（`logger`）使用单例模式
- **工厂模式**: 通过配置文件创建实例
- **策略模式**: 不同的数据清洗和分析策略

## 配置管理

### 配置文件
- 主配置文件：`config/config.yaml`
- 环境变量文件：`.env`（不提交到版本控制）

### 配置加载
- 使用 `pydantic-settings` 进行配置验证和加载
- 配置类继承 `BaseSettings`
- 支持从 YAML 文件和环境变量加载配置
- 示例：
```python
class Settings(BaseSettings):
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    xhs_cookies: Optional[str] = Field(default=None, alias="XHS_COOKIES")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )
```

### 敏感信息管理
- Cookie、API密钥等敏感信息必须存储在 `.env` 文件中
- `.env` 文件必须添加到 `.gitignore`
- 使用环境变量访问敏感信息

## 日志规范

### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 日志使用
- 使用 `loguru` 进行日志记录
- 所有模块使用全局 `logger` 实例
- 日志配置在 `config/config.yaml` 中定义
- 示例：
```python
from seer.logger import logger

logger.info("开始执行任务")
logger.error(f"任务执行失败: {error_message}")
```

### 日志格式
- 时间戳 - 模块名 - 日志级别 - 消息
- 示例：`2024-01-06 10:30:00 - seer.crawler - INFO - 开始爬取笔记`

## 错误处理

### 异常捕获
- 所有可能抛出异常的代码必须使用 try-except 捕获
- 记录详细的错误日志
- 返回统一的错误格式

### 返回值规范
- 使用元组返回：`(success: bool, message: str, data: Optional[Any])`
- `success`: 操作是否成功
- `message`: 操作结果消息
- `data`: 返回的数据（成功时）或 None（失败时）
- 示例：
```python
def get_note_info(self, note_url: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    try:
        # 业务逻辑
        return True, "获取成功", note_data
    except Exception as e:
        logger.error(f"获取笔记信息失败: {str(e)}")
        return False, str(e), None
```

## 测试规范

### 测试文件
- 测试文件以 `test_` 开头
- 测试文件放在 `tests/` 目录下
- 示例：`tests/test_crawler.py`

### 测试函数
- 测试函数以 `test_` 开头
- 使用 `pytest` 框架
- 示例：
```python
def test_crawler_initialization():
    """测试爬虫初始化"""
    crawler = XiaohongshuCrawler()
    assert crawler is not None
```

### 测试覆盖
- 核心功能必须有单元测试
- 测试覆盖率应达到 80% 以上

## 数据验证

### 数据清洗
- 所有原始数据必须经过清洗
- 使用 `Cleaner` 模块进行数据清洗
- 清洗后的数据必须符合预定义的数据结构

### 数据验证
- 使用 Pydantic 模型进行数据验证
- 验证数据的完整性和有效性
- 示例：
```python
def _validate_note_data(self, note_data: Dict[str, Any]) -> bool:
    """验证笔记数据的完整性和有效性"""
    required_fields = ["note_id", "title", "author_id", "author_name"]
    return all(field in note_data for field in required_fields)
```

## 性能优化

### 缓存机制
- 使用内存缓存减少重复请求
- 缓存过期时间可配置
- 示例：
```python
def _cache_get(self, key: str) -> Optional[Any]:
    """从缓存中获取数据"""
    return self.cache.get(key)

def _cache_set(self, key: str, value: Any, expiration: int = 3600) -> None:
    """将数据存入缓存"""
    self.cache[key] = {
        "value": value,
        "expiration": time.time() + expiration
    }
```

### 并发处理
- 使用线程池进行并发请求
- 使用 `asyncio` 进行异步操作
- 示例：
```python
from concurrent.futures import ThreadPoolExecutor

self.executor = ThreadPoolExecutor(max_workers=settings.crawler.max_workers)
```

### 请求限制
- 设置请求间隔，避免被封禁
- 使用随机延迟模拟真实用户行为
- 示例：
```python
def _random_delay(self):
    """随机延迟，避免被反爬"""
    delay = random.uniform(self.config.delay_range["min"], self.config.delay_range["max"])
    time.sleep(delay)
```

## 安全规范

### 敏感信息保护
- Cookie、API密钥等敏感信息不得硬编码在代码中
- 使用环境变量管理敏感信息
- `.env` 文件必须添加到 `.gitignore`

### 反爬虫策略
- 使用随机 User-Agent
- 设置合理的请求间隔
- 使用代理池（可选）
- 遵守 robots.txt 协议

## 专有名词规范

以下专有名词不进行翻译，保持原文：
- **view**: 区域（简写：v）
- **parseGroup**: 解析组（简写：pg、p）
- **lake**: 节点

## 交互规范

- 所有交互使用中文
- 日志消息使用中文
- 文档使用中文编写
- 代码注释使用中文（如需添加）

## 版本控制

### Git 规范
- 不进行 git 提交操作（除非用户明确要求）
- 使用 `.gitignore` 忽略不必要的文件
- 提交信息使用中文

### .gitignore
- `.env` 文件
- `__pycache__` 目录
- `*.pyc` 文件
- `logs/` 目录
- `data/` 目录
- IDE 配置文件

## 开发流程

### 新功能开发
1. 创建任务列表（使用 TodoWrite 工具）
2. 分析现有代码结构
3. 遵循现有代码风格和模式
4. 编写单元测试
5. 运行测试确保通过
6. 更新相关文档

### 代码审查
- 遵循项目代码规范
- 确保类型注解完整
- 确保错误处理完善
- 确保日志记录合理

### 问题修复
1. 使用搜索工具定位问题代码
2. 分析问题原因
3. 编写测试用例复现问题
4. 修复问题
5. 运行测试确保修复有效

## 常用命令

### 安装依赖
```bash
uv sync
```

### 运行测试
```bash
pytest tests/
```

### 运行主程序
```bash
python src/main.py --url <小红书用户主页URL>
```

## 注意事项

1. **不进行 git 提交**：除非用户明确要求，否则不执行 git 提交操作
2. **使用中文交互**：所有与用户的交互使用中文
3. **遵循现有模式**：新代码必须遵循项目现有的代码风格和架构模式
4. **优先编辑现有文件**：避免创建新文件，优先编辑现有文件
5. **不主动创建文档**：除非用户明确要求，否则不创建文档文件

## 更新日志

本规范文档将随着项目的发展不断更新和完善。
