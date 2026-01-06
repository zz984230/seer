from .models import (
    StockInfo,
    DividendRecord,
    DividendYield,
    DividendTrend,
    StockFilter,
    DividendAnalysisResult,
    BatchDividendResult
)

from .data_fetcher import DataFetcher

from .dividend_calculator import DividendCalculator

from .config import settings

__version__ = "0.1.0"

__all__ = [
    "models",
    "StockInfo",
    "DividendRecord",
    "DividendYield",
    "DividendTrend",
    "StockFilter",
    "DividendAnalysisResult",
    "BatchDividendResult",
    "DataFetcher",
    "DividendCalculator",
    "settings",
]

calculator = DividendCalculator()
fetcher = DataFetcher()


def get_dividend_yield(stock_code: str):
    """
    获取单只股票的股息率
    
    :param stock_code: 股票代码
    :return: DividendYield对象
    """
    return calculator.calculate_dividend_yield(stock_code)


def get_batch_dividend_yields(stock_codes: list):
    """
    批量获取股息率
    
    :param stock_codes: 股票代码列表
    :return: BatchDividendResult对象
    """
    return calculator.get_batch_dividend_yields(stock_codes)


def get_high_dividend_stocks(stock_codes: list = None, threshold: float = None):
    """
    获取高股息率股票
    
    :param stock_codes: 股票代码列表
    :param threshold: 股息率阈值
    :return: 高股息率股票列表
    """
    return calculator.get_high_dividend_stocks(stock_codes, threshold)


def get_dividend_trend(stock_code: str, years: int = 5):
    """
    获取股息率趋势
    
    :param stock_code: 股票代码
    :param years: 分析年数
    :return: DividendTrend对象
    """
    return calculator.calculate_dividend_trend(stock_code, years)


def calculate_custom_yield(stock_code: str, dividend_amount: float):
    """
    自定义股息率计算
    
    :param stock_code: 股票代码
    :param dividend_amount: 自定义分红金额
    :return: DividendYield对象
    """
    return calculator.calculate_custom_yield(stock_code, dividend_amount)


def analyze_dividend(stock_code: str):
    """
    综合分析股息率
    
    :param stock_code: 股票代码
    :return: DividendAnalysisResult对象
    """
    return calculator.analyze_dividend(stock_code)