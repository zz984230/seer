import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import json
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading
from .models import StockAnalysisRequest
from seer.logger import logger

tqdm.set_lock(threading.Lock())


class StockDataFetcher:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.config = config or {}
        self.cache_enabled = self.config.get('use_cache', True)
        self.cache_dir = self.config.get('cache_dir', './cache/primary_thinking')
        self.data_dir = self.config.get('data_dir', './data/primary_thinking')
        self.max_workers = self.config.get('max_workers', 10)
        self.request_interval = self.config.get('request_interval', 0.5)
        self.api_timeout = self.config.get('api_timeout', 30)
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            os.makedirs(self.data_dir, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        key_parts = [method]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}_{v}")
        return "_".join(key_parts)
    
    def _get_cache_path(self, cache_key: str) -> str:
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(cache_key)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            expire_time = cache_time + timedelta(hours=self.config.get('cache_expire_hours', 24))
            
            if datetime.now() > expire_time:
                os.remove(cache_path)
                return None
            
            self.logger.info(f"从缓存加载数据: {cache_key}")
            return cache_data['data']
        except Exception as e:
            self.logger.error(f"加载缓存失败: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Any):
        if not self.cache_enabled:
            return
        
        try:
            cache_path = self._get_cache_path(cache_key)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据已缓存: {cache_key}")
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")
    
    def get_stock_daily_data(self, stock_code: str, start_date: str, end_date: str) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        cache_key = self._get_cache_key("stock_daily", stock_code=stock_code, start=start_date, end=end_date)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return True, "从缓存加载成功", cached_data
        
        try:
            self.logger.info(f"获取股票日线数据: {stock_code}, {start_date} ~ {end_date}")
            
            time.sleep(self.request_interval)
            
            df = ak.stock_zh_a_hist(
                symbol=stock_code, 
                period="daily", 
                start_date=start_date.replace('-', ''), 
                end_date=end_date.replace('-', ''), 
                adjust="qfq"
            )
            
            if df.empty:
                self.logger.warning(f"未获取到股票数据: {stock_code}")
                return False, "未获取到股票数据", None
            
            data_list = []
            for _, row in df.iterrows():
                try:
                    data = {
                        'stock_code': stock_code,
                        'date': str(row['日期']),
                        'open': float(row['开盘']),
                        'high': float(row['最高']),
                        'low': float(row['最低']),
                        'close': float(row['收盘']),
                        'volume': float(row['成交量']),
                        'amount': float(row['成交额']),
                        'turnover_rate': float(row['换手率']) if pd.notna(row.get('换手率')) else None,
                        'pct_chg': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None
                    }
                    data_list.append(data)
                except Exception as e:
                    self.logger.warning(f"解析股票数据失败: {row['日期']}, 错误: {str(e)}")
                    continue
            
            if not data_list:
                return False, "解析后的数据为空", None
            
            self._save_to_cache(cache_key, data_list)
            
            self.logger.info(f"成功获取 {len(data_list)} 条股票数据")
            return True, "获取成功", data_list
            
        except Exception as e:
            self.logger.error(f"获取股票日线数据失败: {stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_stock_realtime_data(self, stock_code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        cache_key = self._get_cache_key("stock_realtime", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return True, "从缓存加载成功", cached_data
        
        try:
            self.logger.info(f"获取股票实时数据: {stock_code}")
            
            time.sleep(self.request_interval)
            
            df = ak.stock_zh_a_spot_em()
            
            stock_data = df[df['代码'] == stock_code]
            
            if stock_data.empty:
                self.logger.warning(f"未获取到股票实时数据: {stock_code}")
                return False, "未获取到股票实时数据", None
            
            data = stock_data.iloc[0].to_dict()
            
            self._save_to_cache(cache_key, data)
            
            return True, "获取成功", data
            
        except Exception as e:
            self.logger.error(f"获取股票实时数据失败: {stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_stock_fundamental_data(self, stock_code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        cache_key = self._get_cache_key("stock_fundamental", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return True, "从缓存加载成功", cached_data
        
        try:
            self.logger.info(f"获取股票基本面数据: {stock_code}")
            
            time.sleep(self.request_interval)
            
            df = ak.stock_individual_info_em(symbol=stock_code)
            
            if df.empty:
                self.logger.warning(f"未获取到股票基本面数据: {stock_code}")
                return False, "未获取到股票基本面数据", None
            
            data = df.iloc[0].to_dict()
            
            self._save_to_cache(cache_key, data)
            
            return True, "获取成功", data
            
        except Exception as e:
            self.logger.error(f"获取股票基本面数据失败: {stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_stock_financial_data(self, stock_code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        cache_key = self._get_cache_key("stock_financial", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return True, "从缓存加载成功", cached_data
        
        try:
            self.logger.info(f"获取股票财务数据: {stock_code}")
            
            time.sleep(self.request_interval)
            
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            if df.empty:
                self.logger.warning(f"未获取到股票财务数据: {stock_code}")
                return False, "未获取到股票财务数据", None
            
            data = df.iloc[0].to_dict()
            
            self._save_to_cache(cache_key, data)
            
            return True, "获取成功", data
            
        except Exception as e:
            self.logger.error(f"获取股票财务数据失败: {stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_industry_data(self, industry_name: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        cache_key = self._get_cache_key("industry", industry=industry_name)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return True, "从缓存加载成功", cached_data
        
        try:
            self.logger.info(f"获取行业数据: {industry_name}")
            
            time.sleep(self.request_interval)
            
            df = ak.stock_board_industry_name_em(industry=industry_name)
            
            if df.empty:
                self.logger.warning(f"未获取到行业数据: {industry_name}")
                return False, "未获取到行业数据", None
            
            data = {
                'industry_name': industry_name,
                'stocks': df.to_dict('records'),
                'total_stocks': len(df)
            }
            
            self._save_to_cache(cache_key, data)
            
            return True, "获取成功", data
            
        except Exception as e:
            self.logger.error(f"获取行业数据失败: {industry_name}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_market_index_data(self, index_code: str = "000001", start_date: str = None, 
                            end_date: str = None) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        cache_key = self._get_cache_key("market_index", index=index_code, start=start_date, end=end_date)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return True, "从缓存加载成功", cached_data
        
        try:
            self.logger.info(f"获取市场指数数据: {index_code}")
            
            time.sleep(self.request_interval)
            
            df = ak.stock_zh_index_daily(
                symbol=f"sh{index_code}", 
                start_date=start_date.replace('-', '') if start_date else "20200101",
                end_date=end_date.replace('-', '') if end_date else datetime.now().strftime("%Y%m%d")
            )
            
            if df.empty:
                self.logger.warning(f"未获取到市场指数数据: {index_code}")
                return False, "未获取到市场指数数据", None
            
            data_list = []
            for _, row in df.iterrows():
                try:
                    data = {
                        'index_code': index_code,
                        'date': str(row['date']),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume']),
                        'amount': float(row['amount'])
                    }
                    data_list.append(data)
                except Exception as e:
                    self.logger.warning(f"解析指数数据失败: {row['date']}, 错误: {str(e)}")
                    continue
            
            self._save_to_cache(cache_key, data_list)
            
            self.logger.info(f"成功获取 {len(data_list)} 条指数数据")
            return True, "获取成功", data_list
            
        except Exception as e:
            self.logger.error(f"获取市场指数数据失败: {index_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_batch_stock_data(self, stock_codes: List[str], start_date: str, end_date: str) -> Dict[str, Tuple[bool, str, Optional[List[Dict[str, Any]]]]]:
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_code = {
                executor.submit(self.get_stock_daily_data, stock_code, start_date, end_date): stock_code
                for stock_code in stock_codes
            }
            
            with tqdm(total=len(stock_codes), desc="批量获取股票数据", unit="只") as pbar:
                for future in as_completed(future_to_code):
                    stock_code = future_to_code[future]
                    try:
                        success, msg, data = future.result()
                        results[stock_code] = (success, msg, data)
                    except Exception as e:
                        self.logger.error(f"获取股票数据失败: {stock_code}, 错误: {str(e)}")
                        results[stock_code] = (False, str(e), None)
                    finally:
                        pbar.update(1)
        
        return results
    
    def validate_data_quality(self, data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        try:
            if not data:
                return False, "数据为空"
            
            for i, item in enumerate(data):
                if 'high' in item and 'low' in item:
                    if item['high'] < item['low']:
                        return False, f"第{i}条数据异常: 最高价低于最低价"
                
                if 'close' in item and 'open' in item:
                    if item['close'] < 0 or item['open'] < 0:
                        return False, f"第{i}条数据异常: 价格为负数"
                
                if 'volume' in item:
                    if item['volume'] < 0:
                        return False, f"第{i}条数据异常: 成交量为负数"
            
            return True, "数据质量校验通过"
            
        except Exception as e:
            self.logger.error(f"数据质量校验失败: {str(e)}")
            return False, str(e)
    
    def clear_cache(self, stock_code: Optional[str] = None):
        try:
            if stock_code:
                cache_files = [f for f in os.listdir(self.cache_dir) if stock_code in f]
                for cache_file in cache_files:
                    cache_path = os.path.join(self.cache_dir, cache_file)
                    os.remove(cache_path)
                    self.logger.info(f"清除缓存: {cache_file}")
            else:
                for cache_file in os.listdir(self.cache_dir):
                    cache_path = os.path.join(self.cache_dir, cache_file)
                    os.remove(cache_path)
                self.logger.info("清除所有缓存")
                
        except Exception as e:
            self.logger.error(f"清除缓存失败: {str(e)}")
