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
from .models import StockData
from .config import settings
from seer.logger import logger

tqdm.set_lock(threading.Lock())


class DataFetcher:
    def __init__(self):
        self.logger = logger
        self.config = settings.data_source
        self.cache_enabled = self.config.use_cache
        self.cache_dir = settings.storage.cache_dir
        self.data_dir = settings.storage.data_dir
    
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
            expire_time = cache_time + timedelta(hours=self.config.cache_expire_hours)
            
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
            
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据已缓存: {cache_key}")
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")
    
    def _save_to_storage(self, stock_code: str, data: List[StockData], data_type: str = "daily"):
        try:
            if not settings.storage.enable_persistence:
                return
            
            os.makedirs(self.data_dir, exist_ok=True)
            
            file_path = os.path.join(self.data_dir, f"{stock_code}_{data_type}.json")
            
            data_dicts = [item.model_dump() for item in data]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_dicts, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据已保存: {file_path}")
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
    
    def _load_from_storage(self, stock_code: str, data_type: str = "daily") -> Optional[List[StockData]]:
        try:
            file_path = os.path.join(self.data_dir, f"{stock_code}_{data_type}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data_dicts = json.load(f)
            
            return [StockData(**item) for item in data_dicts]
        except Exception as e:
            self.logger.error(f"从存储加载数据失败: {e}")
            return None
    
    def get_stock_daily_data(self, stock_code: str, start_date: str, end_date: str) -> Tuple[bool, str, Optional[List[StockData]]]:
        cache_key = self._get_cache_key("stock_daily", stock_code=stock_code, start=start_date, end=end_date)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            stock_data_list = [StockData(**item) for item in cached_data]
            return True, "从缓存加载成功", stock_data_list
        
        try:
            self.logger.info(f"获取股票日线数据: {stock_code}, {start_date} ~ {end_date}")
            
            time.sleep(self.config.request_interval)
            
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df.empty:
                self.logger.warning(f"未获取到股票数据: {stock_code}")
                return False, "未获取到股票数据", None
            
            stock_data_list = []
            for _, row in df.iterrows():
                try:
                    stock_data = StockData(
                        stock_code=stock_code,
                        stock_name=row.get('股票名称', ''),
                        date=str(row['日期']),
                        open_price=float(row['开盘']),
                        high_price=float(row['最高']),
                        low_price=float(row['最低']),
                        close_price=float(row['收盘']),
                        volume=float(row['成交量']),
                        amount=float(row['成交额']),
                        turnover_rate=float(row['换手率']) if pd.notna(row.get('换手率')) else None
                    )
                    stock_data_list.append(stock_data)
                except Exception as e:
                    self.logger.warning(f"解析股票数据失败: {row['日期']}, 错误: {str(e)}")
                    continue
            
            if not stock_data_list:
                return False, "解析后的数据为空", None
            
            self._save_to_cache(cache_key, [item.model_dump() for item in stock_data_list])
            self._save_to_storage(stock_code, stock_data_list)
            
            self.logger.info(f"成功获取 {len(stock_data_list)} 条股票数据")
            return True, "获取成功", stock_data_list
            
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
            
            time.sleep(self.config.request_interval)
            
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
    
    def get_stock_info(self, stock_code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            success, msg, realtime_data = self.get_stock_realtime_data(stock_code)
            
            if not success or not realtime_data:
                return False, msg, None
            
            stock_info = {
                'stock_code': stock_code,
                'stock_name': realtime_data.get('名称', ''),
                'current_price': float(realtime_data.get('最新价', 0)),
                'change_percent': float(realtime_data.get('涨跌幅', 0)),
                'change_amount': float(realtime_data.get('涨跌额', 0)),
                'volume': float(realtime_data.get('成交量', 0)),
                'amount': float(realtime_data.get('成交额', 0)),
                'turnover_rate': float(realtime_data.get('换手率', 0)) if pd.notna(realtime_data.get('换手率')) else None,
                'pe_ratio': float(realtime_data.get('市盈率-动态', 0)) if pd.notna(realtime_data.get('市盈率-动态')) else None,
                'pb_ratio': float(realtime_data.get('市净率', 0)) if pd.notna(realtime_data.get('市净率')) else None,
                'market_cap': float(realtime_data.get('总市值', 0)) / 100000000 if pd.notna(realtime_data.get('总市值')) else None,
                'high': float(realtime_data.get('最高', 0)),
                'low': float(realtime_data.get('最低', 0)),
                'open': float(realtime_data.get('今开', 0)),
                'pre_close': float(realtime_data.get('昨收', 0))
            }
            
            return True, "获取成功", stock_info
            
        except Exception as e:
            self.logger.error(f"获取股票信息失败: {stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
    def get_batch_stock_data(self, stock_codes: List[str], start_date: str, end_date: str) -> Dict[str, Tuple[bool, str, Optional[List[StockData]]]]:
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
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
    
    def update_data(self, stock_code: str, days: int = 30) -> Tuple[bool, str, Optional[List[StockData]]]:
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            success, msg, data = self.get_stock_daily_data(stock_code, start_date, end_date)
            
            return success, msg, data
            
        except Exception as e:
            self.logger.error(f"更新数据失败: {stock_code}, 错误: {str(e)}")
            return False, str(e), None
    
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
    
    def validate_data_integrity(self, stock_data_list: List[StockData]) -> Tuple[bool, str]:
        try:
            if not stock_data_list:
                return False, "数据列表为空"
            
            sorted_data = sorted(stock_data_list, key=lambda x: x.date)
            
            for i in range(1, len(sorted_data)):
                prev = sorted_data[i - 1]
                curr = sorted_data[i]
                
                if curr.high_price < curr.low_price:
                    return False, f"数据异常: {curr.date} 最高价低于最低价"
                
                if curr.high_price < max(prev.open_price, prev.close_price):
                    pass
                
                if curr.low_price > min(prev.open_price, prev.close_price):
                    pass
            
            return True, "数据完整性校验通过"
            
        except Exception as e:
            self.logger.error(f"数据完整性校验失败: {str(e)}")
            return False, str(e)
