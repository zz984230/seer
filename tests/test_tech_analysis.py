"""
股票技术面分析模块测试

本文件提供了使用seer_tech_analysis模块的单元测试
"""

import pytest
from datetime import datetime, timedelta
from seer_tech_analysis import (
    analyze_stock,
    generate_reports,
    DataFetcher,
    TechnicalIndicators,
    PatternRecognition,
    VolumePriceAnalysis,
    AgentCoordinator,
    TechAnalysisReporter,
    settings
)
from seer_tech_analysis.models import (
    StockData,
    AnalysisRequest,
    MACDIndicator,
    RSIIndicator,
    KDJIndicator,
    PatternInfo,
    VolumePriceRelation
)
from seer.logger import logger


class TestDataFetcher:
    """测试数据获取模块"""
    
    def test_data_fetcher_initialization(self):
        """测试数据获取器初始化"""
        fetcher = DataFetcher()
        assert fetcher is not None
        assert fetcher.config is not None
        assert fetcher.cache_enabled is not None
        logger.info("测试通过: 数据获取器初始化")
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        fetcher = DataFetcher()
        key1 = fetcher._get_cache_key("stock_daily", stock_code="600519", start="20240101", end="20241231")
        key2 = fetcher._get_cache_key("stock_daily", stock_code="600519", start="20240101", end="20241231")
        assert key1 == key2
        logger.info("测试通过: 缓存键生成")
    
    def test_cache_path_generation(self):
        """测试缓存路径生成"""
        fetcher = DataFetcher()
        key = "stock_daily_stock_code_600519_start_20240101_end_20241231"
        path = fetcher._get_cache_path(key)
        assert key in path
        assert path.endswith(".json")
        logger.info("测试通过: 缓存路径生成")
    
    def test_stock_data_validation(self):
        """测试股票数据验证"""
        fetcher = DataFetcher()
        
        valid_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date="2024-01-01",
                open_price=1800.0,
                high_price=1850.0,
                low_price=1790.0,
                close_price=1820.0,
                volume=1000000.0,
                amount=1820000000.0,
                turnover_rate=0.5
            )
        ]
        
        success, msg = fetcher.validate_data_integrity(valid_data)
        assert success is True
        assert "校验通过" in msg
        logger.info("测试通过: 股票数据验证")
    
    def test_invalid_stock_data_validation(self):
        """测试无效股票数据验证"""
        fetcher = DataFetcher()
        
        invalid_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date="2024-01-01",
                open_price=1800.0,
                high_price=1750.0,
                low_price=1790.0,
                close_price=1820.0,
                volume=1000000.0,
                amount=1820000000.0,
                turnover_rate=0.5
            )
        ]
        
        success, msg = fetcher.validate_data_integrity(invalid_data)
        assert success is False
        logger.info("测试通过: 无效股票数据验证")


class TestTechnicalIndicators:
    """测试技术指标计算模块"""
    
    def test_technical_indicators_initialization(self):
        """测试技术指标计算器初始化"""
        indicators = TechnicalIndicators()
        assert indicators is not None
        assert indicators.config is not None
        logger.info("测试通过: 技术指标计算器初始化")
    
    def test_macd_calculation(self):
        """测试MACD计算"""
        indicators = TechnicalIndicators()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0 + i * 10,
                high_price=1820.0 + i * 10,
                low_price=1790.0 + i * 10,
                close_price=1810.0 + i * 10,
                volume=1000000.0,
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, macd = indicators.calculate_macd(stock_data)
        assert success is True
        assert macd is not None
        assert len(macd.dif) == len(stock_data)
        assert len(macd.dea) == len(stock_data)
        assert len(macd.macd) == len(stock_data)
        logger.info("测试通过: MACD计算")
    
    def test_rsi_calculation(self):
        """测试RSI计算"""
        indicators = TechnicalIndicators()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0 + i * 10,
                high_price=1820.0 + i * 10,
                low_price=1790.0 + i * 10,
                close_price=1810.0 + i * 10,
                volume=1000000.0,
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, rsi = indicators.calculate_rsi(stock_data)
        assert success is True
        assert rsi is not None
        assert len(rsi.rsi6) == len(stock_data)
        assert len(rsi.rsi12) == len(stock_data)
        assert len(rsi.rsi24) == len(stock_data)
        logger.info("测试通过: RSI计算")
    
    def test_kdj_calculation(self):
        """测试KDJ计算"""
        indicators = TechnicalIndicators()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0 + i * 10,
                high_price=1820.0 + i * 10,
                low_price=1790.0 + i * 10,
                close_price=1810.0 + i * 10,
                volume=1000000.0,
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, kdj = indicators.calculate_kdj(stock_data)
        assert success is True
        assert kdj is not None
        assert len(kdj.k) == len(stock_data)
        assert len(kdj.d) == len(stock_data)
        assert len(kdj.j) == len(stock_data)
        logger.info("测试通过: KDJ计算")
    
    def test_all_indicators_calculation(self):
        """测试所有技术指标计算"""
        indicators = TechnicalIndicators()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0 + i * 10,
                high_price=1820.0 + i * 10,
                low_price=1790.0 + i * 10,
                close_price=1810.0 + i * 10,
                volume=1000000.0,
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, result = indicators.calculate_all_indicators(stock_data)
        assert success is True
        assert result is not None
        assert 'macd' in result
        assert 'rsi' in result
        assert 'kdj' in result
        assert 'ma' in result
        logger.info("测试通过: 所有技术指标计算")


class TestPatternRecognition:
    """测试形态识别模块"""
    
    def test_pattern_recognition_initialization(self):
        """测试形态识别器初始化"""
        recognizer = PatternRecognition()
        assert recognizer is not None
        assert recognizer.config is not None
        logger.info("测试通过: 形态识别器初始化")
    
    def test_head_shoulders_detection(self):
        """测试头肩形态检测"""
        recognizer = PatternRecognition()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0,
                high_price=1820.0,
                low_price=1790.0,
                close_price=1810.0,
                volume=1000000.0,
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, patterns = recognizer.detect_all_patterns(stock_data)
        assert success is True
        assert isinstance(patterns, list)
        logger.info("测试通过: 头肩形态检测")
    
    def test_double_top_bottom_detection(self):
        """测试双顶双底检测"""
        recognizer = PatternRecognition()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0,
                high_price=1820.0,
                low_price=1790.0,
                close_price=1810.0,
                volume=1000000.0,
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, patterns = recognizer.detect_all_patterns(stock_data)
        assert success is True
        assert isinstance(patterns, list)
        logger.info("测试通过: 双顶双底检测")


class TestVolumePriceAnalysis:
    """测试量价关系分析模块"""
    
    def test_volume_price_analysis_initialization(self):
        """测试量价关系分析器初始化"""
        analyzer = VolumePriceAnalysis()
        assert analyzer is not None
        assert analyzer.config is not None
        logger.info("测试通过: 量价关系分析器初始化")
    
    def test_volume_price_relation_determination(self):
        """测试量价关系判断"""
        analyzer = VolumePriceAnalysis()
        
        relation_type = analyzer._determine_relation_type(5.0, 10.0)
        assert relation_type == "量增价涨"
        
        relation_type = analyzer._determine_relation_type(-5.0, 10.0)
        assert relation_type == "量增价跌"
        
        relation_type = analyzer._determine_relation_type(5.0, -10.0)
        assert relation_type == "量减价涨"
        
        relation_type = analyzer._determine_relation_type(-5.0, -10.0)
        assert relation_type == "量减价跌"
        
        logger.info("测试通过: 量价关系判断")
    
    def test_strength_determination(self):
        """测试强度判断"""
        analyzer = VolumePriceAnalysis()
        
        strength = analyzer._determine_strength(5.0, 2.0)
        assert strength in ["强", "中", "弱"]
        
        strength = analyzer._determine_strength(0.5, 0.3)
        assert strength in ["强", "中", "弱"]
        
        logger.info("测试通过: 强度判断")
    
    def test_volume_price_analysis(self):
        """测试量价关系分析"""
        analyzer = VolumePriceAnalysis()
        
        stock_data = [
            StockData(
                stock_code="600519",
                stock_name="贵州茅台",
                date=f"2024-{i:02d}-01",
                open_price=1800.0 + i * 10,
                high_price=1820.0 + i * 10,
                low_price=1790.0 + i * 10,
                close_price=1810.0 + i * 10,
                volume=1000000.0 * (1 + i * 0.1),
                amount=1810000000.0,
                turnover_rate=0.5
            )
            for i in range(30)
        ]
        
        success, msg, result = analyzer.analyze_all(stock_data)
        assert success is True
        assert result is not None
        assert 'daily_relations' in result
        assert 'volume_trend' in result
        assert 'correlation' in result
        assert 'accumulation' in result
        logger.info("测试通过: 量价关系分析")


class TestAgentCoordinator:
    """测试多Agent协调器"""
    
    def test_agent_coordinator_initialization(self):
        """测试Agent协调器初始化"""
        coordinator = AgentCoordinator()
        assert coordinator is not None
        assert coordinator.config is not None
        logger.info("测试通过: Agent协调器初始化")
    
    def test_agent_list(self):
        """测试Agent列表"""
        coordinator = AgentCoordinator()
        agent_list = coordinator.get_agent_list()
        assert isinstance(agent_list, list)
        logger.info("测试通过: Agent列表获取")
    
    def test_weighted_recommendation_calculation(self):
        """测试加权建议计算"""
        coordinator = AgentCoordinator()
        
        from seer_tech_analysis.models import AgentAnalysis
        analyses = [
            AgentAnalysis(
                agent_name="technical_agent",
                agent_type="technical",
                analysis_result={},
                confidence=0.8,
                recommendation="买入",
                risk_level="中",
                reasoning="技术指标显示买入信号"
            ),
            AgentAnalysis(
                agent_name="pattern_agent",
                agent_type="pattern",
                analysis_result={},
                confidence=0.7,
                recommendation="买入",
                risk_level="中",
                reasoning="形态识别显示买入信号"
            ),
            AgentAnalysis(
                agent_name="volume_agent",
                agent_type="volume",
                analysis_result={},
                confidence=0.6,
                recommendation="持有",
                risk_level="低",
                reasoning="量价关系显示持有"
            )
        ]
        
        recommendation = coordinator._calculate_weighted_recommendation(analyses)
        assert recommendation in ["买入", "卖出", "持有", "偏多", "偏空"]
        logger.info("测试通过: 加权建议计算")


class TestTechAnalysisReporter:
    """测试报告生成模块"""
    
    def test_reporter_initialization(self):
        """测试报告生成器初始化"""
        reporter = TechAnalysisReporter()
        assert reporter is not None
        assert reporter.config is not None
        logger.info("测试通过: 报告生成器初始化")
    
    def test_technical_analysis_text_generation(self):
        """测试技术分析文本生成"""
        reporter = TechAnalysisReporter()
        
        from seer_tech_analysis.models import MACDIndicator, RSIIndicator, KDJIndicator
        macd = MACDIndicator(
            dif=[1.0, 2.0, 3.0],
            dea=[0.8, 1.6, 2.4],
            macd=[0.4, 0.8, 1.2],
            signals=[],
            description="MACD显示上涨趋势"
        )
        rsi = RSIIndicator(
            rsi6=[50.0, 55.0, 60.0],
            rsi12=[45.0, 50.0, 55.0],
            rsi24=[40.0, 45.0, 50.0],
            signals=[],
            description="RSI处于正常区间"
        )
        kdj = KDJIndicator(
            k=[50.0, 55.0, 60.0],
            d=[48.0, 53.0, 58.0],
            j=[54.0, 59.0, 64.0],
            signals=[],
            description="KDJ显示上涨趋势"
        )
        
        from seer_tech_analysis.models import ComprehensiveAnalysis
        analysis = ComprehensiveAnalysis(
            stock_code="600519",
            stock_name="贵州茅台",
            analysis_date="2024-12-31",
            stock_data=[],
            technical_indicators={},
            macd=macd,
            rsi=rsi,
            kdj=kdj,
            patterns=[],
            volume_price_relations=[],
            agent_analyses=[],
            overall_recommendation="买入",
            overall_confidence=0.75,
            overall_risk_level="中",
            key_points=[],
            warnings=[]
        )
        
        text = reporter._generate_technical_analysis_text(analysis)
        assert text is not None
        assert len(text) > 0
        logger.info("测试通过: 技术分析文本生成")


class TestConfig:
    """测试配置模块"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        assert settings is not None
        assert settings.data_source is not None
        assert settings.indicators is not None
        assert settings.pattern is not None
        assert settings.volume is not None
        assert settings.llm is not None
        assert settings.report is not None
        assert settings.storage is not None
        logger.info("测试通过: 配置初始化")
    
    def test_config_values(self):
        """测试配置值"""
        assert settings.data_source.source in ["akshare", "tushare"]
        assert settings.indicators.macd_fast_period > 0
        assert settings.indicators.rsi_period > 0
        assert settings.indicators.kdj_period > 0
        assert settings.pattern.min_pattern_days > 0
        assert settings.pattern.max_pattern_days > settings.pattern.min_pattern_days
        assert settings.volume.volume_ma_period > 0
        assert settings.llm.temperature >= 0 and settings.llm.temperature <= 2
        assert settings.llm.max_tokens > 0
        logger.info("测试通过: 配置值验证")


class TestIntegration:
    """集成测试"""
    
    def test_analysis_request_creation(self):
        """测试分析请求创建"""
        request = AnalysisRequest(
            stock_code="600519",
            stock_name="贵州茅台",
            start_date="20240101",
            end_date="20241231",
            indicators=["MACD", "RSI", "KDJ"],
            enable_pattern_recognition=True,
            enable_volume_analysis=True,
            use_llm_analysis=False
        )
        
        assert request.stock_code == "600519"
        assert request.stock_name == "贵州茅台"
        assert request.start_date == "20240101"
        assert request.end_date == "20241231"
        assert "MACD" in request.indicators
        assert "RSI" in request.indicators
        assert "KDJ" in request.indicators
        assert request.enable_pattern_recognition is True
        assert request.enable_volume_analysis is True
        assert request.use_llm_analysis is False
        logger.info("测试通过: 分析请求创建")
    
    def test_module_import(self):
        """测试模块导入"""
        from seer_tech_analysis import (
            StockData,
            TechnicalIndicator,
            MACDIndicator,
            RSIIndicator,
            KDJIndicator,
            PatternInfo,
            VolumePriceRelation,
            AgentAnalysis,
            ComprehensiveAnalysis,
            AnalysisRequest,
            AnalysisReport,
            LLMConfig,
            DataFetcher,
            TechnicalIndicators,
            PatternRecognition,
            VolumePriceAnalysis,
            LLMAgent,
            LLMFactory,
            AgentCoordinator,
            TechAnalysisReporter,
            TechAnalysisEngine,
            analyze_stock,
            generate_reports
        )
        logger.info("测试通过: 模块导入")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("股票技术面分析模块测试")
    print("=" * 60)
    
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
