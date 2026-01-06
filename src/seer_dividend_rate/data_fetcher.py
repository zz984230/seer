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
            
            df = ak.stock_zh_a_spot_em()
            
            stock_data = df[df['代码'] == stock_code]
            
            if stock_data.empty:
                self.logger.warning(f"未获取到股票数据: {stock_code}")
                return None
            
            latest = stock_data.iloc[0]
            
            stock_info = StockInfo(
                stock_code=stock_code,
                stock_name=latest.get('名称', ''),
                current_price=float(latest.get('最新价', 0)),
                market_cap=float(latest.get('总市值', 0)) / 100000000 if latest.get('总市值') else None,
                pe_ratio=float(latest.get('市盈率-动态', 0)) if latest.get('市盈率-动态') else None,
                pb_ratio=float(latest.get('市净率', 0)) if latest.get('市净率') else None,
                ps_ratio=None
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
        获取股票分红记录（合并年度分红和中期分红）
        
        :param stock_code: 股票代码
        :return: 分红记录列表（按年度合并）
        """
        cache_key = self._get_cache_key("dividend_records", stock_code=stock_code)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return [DividendRecord(**record) for record in cached_data]
        
        try:
            self.logger.info(f"获取股票分红记录: {stock_code}")
            
            df = ak.stock_dividend_cninfo(symbol=stock_code)
            
            if df.empty:
                self.logger.warning(f"未获取到分红记录: {stock_code}")
                return []
            
            records = []
            for _, row in df.iterrows():
                dividend_ratio = row.get('派息比例', 0)
                if pd.isna(dividend_ratio) or dividend_ratio == 0:
                    continue
                
                report_time = row.get('报告时间', '')
                year = 0
                if report_time:
                    try:
                        year = int(report_time.split('年')[0])
                    except (ValueError, AttributeError):
                        pass
                
                def date_to_str(date_val):
                    if pd.isna(date_val):
                        return None
                    if isinstance(date_val, str):
                        return date_val
                    return str(date_val)
                
                record = DividendRecord(
                    year=year,
                    dividend_per_share=float(dividend_ratio) / 10,
                    dividend_yield=None,
                    record_date=date_to_str(row.get('股权登记日')),
                    ex_dividend_date=date_to_str(row.get('除权日')),
                    payout_date=date_to_str(row.get('派息日'))
                )
                records.append(record)
            
            merged_records = self._merge_dividend_records(records)
            
            self._save_to_cache(cache_key, [record.model_dump() for record in merged_records])
            return merged_records
            
        except Exception as e:
            self.logger.error(f"获取分红记录失败: {stock_code}, 错误: {str(e)}")
            return []
    
    def _merge_dividend_records(self, records: List[DividendRecord]) -> List[DividendRecord]:
        """
        合并年度分红和中期分红
        
        :param records: 原始分红记录列表
        :return: 合并后的年度分红记录列表（年份为财年）
        """
        from collections import defaultdict
        
        fiscal_year_dividends = defaultdict(list)
        
        for record in records:
            fiscal_year = record.year
            if fiscal_year > 0:
                fiscal_year_dividends[fiscal_year].append(record)
        
        merged_records = []
        for fiscal_year in sorted(fiscal_year_dividends.keys()):
            year_records = fiscal_year_dividends[fiscal_year]
            total_dividend = sum(r.dividend_per_share for r in year_records)
            
            latest_record = max(year_records, key=lambda r: r.payout_date or '')
            
            merged_record = DividendRecord(
                year=fiscal_year,
                dividend_per_share=round(total_dividend, 3),
                dividend_yield=None,
                record_date=latest_record.record_date,
                ex_dividend_date=latest_record.ex_dividend_date,
                payout_date=latest_record.payout_date
            )
            merged_records.append(merged_record)
        
        return merged_records
    
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
    
    def get_stock_name_code_mapping(self) -> Dict[str, str]:
        """
        获取股票名称到代码的映射
        
        :return: 股票名称到代码的映射字典
        """
        cache_key = self._get_cache_key("stock_name_code_mapping")
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            self.logger.info("获取股票名称和代码映射")
            
            df = ak.stock_zh_a_spot_em()
            
            mapping = {}
            for _, row in df.iterrows():
                stock_name = row.get('名称', '')
                stock_code = row.get('代码', '')
                if stock_name and stock_code:
                    mapping[stock_name] = stock_code
            
            self._save_to_cache(cache_key, mapping)
            return mapping
            
        except Exception as e:
            self.logger.error(f"获取股票名称和代码映射失败: {str(e)}")
            return {}
    
    def get_code_from_name(self, stock_name: str) -> Optional[str]:
        """
        根据股票名称获取股票代码
        
        :param stock_name: 股票名称
        :return: 股票代码，如果未找到则返回None
        """
        try:
            mapping = self.get_stock_name_code_mapping()
            return mapping.get(stock_name)
        except Exception as e:
            self.logger.error(f"根据名称获取代码失败: {stock_name}, 错误: {str(e)}")
            return None
    
    def get_name_from_code(self, stock_code: str) -> Optional[str]:
        """
        根据股票代码获取股票名称
        
        :param stock_code: 股票代码
        :return: 股票名称，如果未找到则返回None
        """
        try:
            mapping = self.get_stock_name_code_mapping()
            code_to_name = {v: k for k, v in mapping.items()}
            return code_to_name.get(stock_code)
        except Exception as e:
            self.logger.error(f"根据代码获取名称失败: {stock_code}, 错误: {str(e)}")
            return None
    
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