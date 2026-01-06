import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime, timedelta
from .models import StockInfo, DividendRecord
from .config import settings
from seer.logger import logger


class DataFetcher:
    def __init__(self):
        self.logger = logger
        self.config = settings.data_source
        self.cache_enabled = self.config.use_cache
        self.cache_dir = settings.storage.cache_dir
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}_{v}")
        return "_".join(key_parts)
    
    def _get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存加载数据"""
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
        """保存数据到缓存"""
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
    
    def get_stock_indicator(self, stock_code: str) -> Optional[StockInfo]:
        """
        获取股票估值指标
        
        :param stock_code: 股票代码（如 '600519'）
        :return: StockInfo对象
        """
        cache_key = self._get_cache_key("stock_indicator", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return StockInfo(**cached_data)
        
        try:
            self.logger.info(f"获取股票估值指标: {stock_code}")
            
            df = ak.stock_a_indicator(symbol=stock_code)
            
            if df.empty:
                self.logger.warning(f"未获取到股票数据: {stock_code}")
                return None
            
            latest = df.iloc[0]
            
            stock_info = StockInfo(
                stock_code=stock_code,
                stock_name=latest.get('股票名称', ''),
                current_price=float(latest.get('最新价', 0)),
                market_cap=float(latest.get('总市值', 0)) / 100000000 if latest.get('总市值') else None,
                pe_ratio=float(latest.get('市盈率-动态', 0)) if latest.get('市盈率-动态') else None,
                pb_ratio=float(latest.get('市净率', 0)) if latest.get('市净率') else None,
                ps_ratio=float(latest.get('市销率', 0)) if latest.get('市销率') else None
            )
            
            self._save_to_cache(cache_key, stock_info.model_dump())
            return stock_info
            
        except Exception as e:
            self.logger.error(f"获取股票估值指标失败: {stock_code}, 错误: {str(e)}")
            return None
    
    def get_stock_spot_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情数据
        
        :param stock_code: 股票代码
        :return: 行情数据字典
        """
        cache_key = self._get_cache_key("stock_spot", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            self.logger.info(f"获取股票实时行情: {stock_code}")
            
            df = ak.stock_zh_a_spot_em()
            
            stock_data = df[df['代码'] == stock_code]
            
            if stock_data.empty:
                self.logger.warning(f"未获取到股票行情数据: {stock_code}")
                return None
            
            data = stock_data.iloc[0].to_dict()
            self._save_to_cache(cache_key, data)
            return data
            
        except Exception as e:
            self.logger.error(f"获取股票实时行情失败: {stock_code}, 错误: {str(e)}")
            return None
    
    def get_dividend_records(self, stock_code: str) -> List[DividendRecord]:
        """
        获取股票分红记录
        
        :param stock_code: 股票代码
        :return: 分红记录列表
        """
        cache_key = self._get_cache_key("dividend_records", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return [DividendRecord(**record) for record in cached_data]
        
        try:
            self.logger.info(f"获取股票分红记录: {stock_code}")
            
            df = ak.stock_dividend_detail_sina(symbol=stock_code)
            
            if df.empty:
                self.logger.warning(f"未获取到分红记录: {stock_code}")
                return []
            
            records = []
            for _, row in df.iterrows():
                record = DividendRecord(
                    year=int(row.get('年度', 0)),
                    dividend_per_share=float(row.get('每10股派息', 0)) / 10,
                    dividend_yield=None,
                    record_date=row.get('股权登记日'),
                    ex_dividend_date=row.get('除权除息日'),
                    payout_date=row.get('派息日')
                )
                records.append(record)
            
            self._save_to_cache(cache_key, [record.model_dump() for record in records])
            return records
            
        except Exception as e:
            self.logger.error(f"获取分红记录失败: {stock_code}, 错误: {str(e)}")
            return []
    
    def get_all_stock_list(self) -> List[str]:
        """
        获取所有A股股票代码列表
        
        :return: 股票代码列表
        """
        cache_key = self._get_cache_key("all_stock_list")
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            self.logger.info("获取所有A股股票列表")
            
            df = ak.stock_zh_a_spot_em()
            stock_codes = df['代码'].tolist()
            
            self._save_to_cache(cache_key, stock_codes)
            return stock_codes
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {str(e)}")
            return []
    
    def get_batch_stock_indicators(self, stock_codes: List[str]) -> List[StockInfo]:
        """
        批量获取股票估值指标
        
        :param stock_codes: 股票代码列表
        :return: StockInfo对象列表
        """
        results = []
        
        for stock_code in stock_codes:
            stock_info = self.get_stock_indicator(stock_code)
            if stock_info:
                results.append(stock_info)
        
        self.logger.info(f"批量获取股票指标完成: {len(results)}/{len(stock_codes)}")
        return results
    
    def get_dividend_yield_from_indicator(self, stock_code: str) -> Optional[float]:
        """
        从估值指标中获取股息率
        
        :param stock_code: 股票代码
        :return: 股息率(%)
        """
        try:
            df = ak.stock_a_indicator(symbol=stock_code)
            
            if df.empty:
                return None
            
            latest = df.iloc[0]
            dividend_yield = latest.get('股息率', None)
            
            if dividend_yield is not None:
                return float(dividend_yield)
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取股息率失败: {stock_code}, 错误: {str(e)}")
            return None
    
    def clear_cache(self, stock_code: Optional[str] = None):
        """
        清除缓存
        
        :param stock_code: 股票代码，如果为None则清除所有缓存
        """
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