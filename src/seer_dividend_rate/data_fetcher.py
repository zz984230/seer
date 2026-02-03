import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional
import json
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from tqdm import tqdm
import threading
from .models import StockInfo, DividendRecord
from .config import settings
from seer.logger import logger

tqdm.set_lock(threading.Lock())


def _fetch_stock_indicator_worker(stock_code: str, config_dict: Dict[str, Any], cache_dir: str) -> Optional[Dict[str, Any]]:
    """
    工作进程函数：获取单个股票的估值指标
    
    :param stock_code: 股票代码
    :param config_dict: 配置字典
    :param cache_dir: 缓存目录
    :return: 股票信息字典
    """
    try:
        cache_key = f"stock_indicator_stock_code_{stock_code}"
        cache_path = os.path.join(cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            expire_time = cache_time + timedelta(hours=config_dict['cache_expire_hours'])
            
            if datetime.now() <= expire_time:
                return cache_data['data']
            else:
                os.remove(cache_path)
        
        time.sleep(config_dict['request_interval'])
        
        interfaces = [
            lambda: ak.stock_zh_a_spot_em(),
            lambda: ak.stock_individual_info_em(symbol=stock_code),
            lambda: ak.stock_zh_a_spot_em()
        ]
        
        df = None
        for i, interface in enumerate(interfaces):
            try:
                df = interface()
                if df is not None and not df.empty:
                    break
            except Exception:
                continue
        
        if df is None or df.empty:
            return None
        
        data = {}
        if 'item' in df.columns and 'value' in df.columns:
            for _, row in df.iterrows():
                key = row.get('item', '')
                value = row.get('value', '')
                data[key] = value
        else:
            stock_data = df[df['代码'] == stock_code] if '代码' in df.columns else df
            if not stock_data.empty:
                data = stock_data.iloc[0].to_dict()
        
        if not data:
            return None
        
        pe_ratio = data.get('市盈率-动态') or data.get('市盈率-动态')
        if pe_ratio is not None:
            try:
                pe_ratio = float(pe_ratio)
                if pe_ratio <= 0:
                    pe_ratio = None
            except (ValueError, TypeError):
                pe_ratio = None
        
        current_price = data.get('最新价') or data.get('最新')
        if current_price is not None:
            try:
                current_price = float(current_price)
            except (ValueError, TypeError):
                current_price = 0.0
        else:
            current_price = 0.0
        
        market_cap = data.get('总市值') or data.get('总市值')
        if market_cap is not None:
            try:
                market_cap = float(market_cap) / 100000000
            except (ValueError, TypeError):
                market_cap = None
        else:
            market_cap = None
        
        pb_ratio = data.get('市净率') or data.get('市净率')
        if pb_ratio is not None:
            try:
                pb_ratio = float(pb_ratio)
            except (ValueError, TypeError):
                pb_ratio = None
        else:
            pb_ratio = None
        
        stock_info = {
            'stock_code': stock_code,
            'stock_name': data.get('名称') or data.get('股票简称') or '',
            'current_price': current_price,
            'market_cap': market_cap,
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'ps_ratio': None
        }
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': stock_info
        }
        
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        return stock_info
        
    except Exception as e:
        return None


def _fetch_dividend_records_worker(stock_code: str, config_dict: Dict[str, Any], cache_dir: str) -> Optional[List[Dict[str, Any]]]:
    """
    工作进程函数：获取单个股票的分红记录
    
    :param stock_code: 股票代码
    :param config_dict: 配置字典
    :param cache_dir: 缓存目录
    :return: 分红记录列表
    """
    try:
        cache_key = f"dividend_records_stock_code_{stock_code}"
        cache_path = os.path.join(cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            expire_time = cache_time + timedelta(hours=config_dict['cache_expire_hours'])
            
            if datetime.now() <= expire_time:
                return cache_data['data']
            else:
                os.remove(cache_path)
        
        time.sleep(config_dict['request_interval'])
        
        df = ak.stock_dividend_cninfo(symbol=stock_code)
        
        if df.empty:
            return None
        
        yearly_dividends = {}
        
        for _, row in df.iterrows():
            dividend_ratio = row.get('派息比例', 0)
            if pd.isna(dividend_ratio) or dividend_ratio == 0:
                continue
            
            report_time = row.get('报告时间', '')
            year = 0
            if report_time:
                try:
                    year = int(report_time[:4])
                except (ValueError, IndexError):
                    continue
            
            if year == 0:
                continue
            
            if year not in yearly_dividends:
                yearly_dividends[year] = {
                    'year': year,
                    'dividend_per_share': 0.0,
                    'record_date': None,
                    'ex_dividend_date': None,
                    'payout_date': None
                }
            
            yearly_dividends[year]['dividend_per_share'] += float(dividend_ratio)
            
            record_date = row.get('实施方案公告日期', '')
            if record_date and not yearly_dividends[year]['record_date']:
                yearly_dividends[year]['record_date'] = record_date
            
            ex_date = row.get('除权除息日', '')
            if ex_date and not yearly_dividends[year]['ex_dividend_date']:
                yearly_dividends[year]['ex_dividend_date'] = ex_date
            
            payout_date = row.get('派息日', '')
            if payout_date and not yearly_dividends[year]['payout_date']:
                yearly_dividends[year]['payout_date'] = payout_date
        
        records = [yearly_dividends[year] for year in sorted(yearly_dividends.keys(), reverse=True)]
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': records
        }
        
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        return records
        
    except Exception as e:
        return None


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
    
    def _fetch_spot_data_with_fallback(self, stock_code: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        获取实时行情数据，支持备用接口
        
        :param stock_code: 股票代码，如果为None则获取所有股票
        :return: 行情数据DataFrame
        """
        if stock_code:
            interfaces = [
                lambda: ak.stock_zh_a_spot_em(),
                lambda: ak.stock_individual_info_em(symbol=stock_code),
                lambda: ak.stock_zh_a_spot_em()
            ]
        else:
            interfaces = [
                lambda: ak.stock_zh_a_spot_em(),
                lambda: ak.stock_info_a_code_name(),
                lambda: ak.stock_zh_a_spot_em()
            ]
        
        for i, interface in enumerate(interfaces):
            try:
                self.logger.info(f"尝试使用接口 {i+1} 获取数据")
                df = interface()
                if df is not None and not df.empty:
                    self.logger.info(f"接口 {i+1} 成功获取数据")
                    return df
            except Exception as e:
                self.logger.warning(f"接口 {i+1} 失败: {str(e)}")
                continue
        
        self.logger.error("所有接口均失败")
        return None
    
    def _normalize_stock_data(self, df: pd.DataFrame, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """
        标准化股票数据格式，处理不同接口返回的不同格式
        
        :param df: 原始DataFrame
        :param stock_code: 股票代码
        :return: 标准化后的数据字典
        """
        if df.empty:
            return {}
        
        if 'item' in df.columns and 'value' in df.columns:
            data_dict = {}
            for _, row in df.iterrows():
                key = row.get('item', '')
                value = row.get('value', '')
                data_dict[key] = value
            return data_dict
        elif 'code' in df.columns and 'name' in df.columns:
            if stock_code:
                stock_data = df[df['code'] == stock_code]
                if not stock_data.empty:
                    return stock_data.iloc[0].to_dict()
            return df.iloc[0].to_dict() if len(df) > 0 else {}
        else:
            return df.iloc[0].to_dict() if len(df) > 0 else {}
    
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
            
            time.sleep(self.config.request_interval)
            
            df = self._fetch_spot_data_with_fallback(stock_code)
            
            if df is None or df.empty:
                self.logger.warning(f"未获取到股票数据: {stock_code}")
                return None
            
            data = self._normalize_stock_data(df, stock_code)
            
            if not data:
                self.logger.warning(f"未获取到股票数据: {stock_code}")
                return None
            
            pe_ratio = data.get('市盈率-动态') or data.get('市盈率-动态')
            if pe_ratio is not None:
                try:
                    pe_ratio = float(pe_ratio)
                    if pe_ratio <= 0:
                        pe_ratio = None
                except (ValueError, TypeError):
                    pe_ratio = None
            
            current_price = data.get('最新价') or data.get('最新')
            if current_price is not None:
                try:
                    current_price = float(current_price)
                except (ValueError, TypeError):
                    current_price = 0.0
            else:
                current_price = 0.0
            
            market_cap = data.get('总市值') or data.get('总市值')
            if market_cap is not None:
                try:
                    market_cap = float(market_cap) / 100000000
                except (ValueError, TypeError):
                    market_cap = None
            else:
                market_cap = None
            
            pb_ratio = data.get('市净率') or data.get('市净率')
            if pb_ratio is not None:
                try:
                    pb_ratio = float(pb_ratio)
                except (ValueError, TypeError):
                    pb_ratio = None
            else:
                pb_ratio = None
            
            stock_info = StockInfo(
                stock_code=stock_code,
                stock_name=data.get('名称') or data.get('股票简称') or '',
                current_price=current_price,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
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
            
            time.sleep(self.config.request_interval)
            
            df = self._fetch_spot_data_with_fallback(stock_code)
            
            if df is None or df.empty:
                self.logger.warning(f"未获取到股票行情数据: {stock_code}")
                return None
            
            data = self._normalize_stock_data(df, stock_code)
            
            if not data:
                self.logger.warning(f"未获取到股票行情数据: {stock_code}")
                return None
            
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
            
            time.sleep(self.config.request_interval)
            
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
                        if '半年报' in report_time:
                            year = int(report_time.split('半年报')[0]) - 1
                        elif '三季报' in report_time:
                            year = int(report_time.split('三季报')[0]) - 1
                        elif '年报' in report_time:
                            year = int(report_time.split('年报')[0])
                    except (ValueError, AttributeError):
                        pass
                
                if year == 0:
                    try:
                        announce_date = row.get('实施方案公告日期', '')
                        if announce_date:
                            year = int(announce_date.split('-')[0])
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
        for fiscal_year in sorted(fiscal_year_dividends.keys(), reverse=True):
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
            
            time.sleep(self.config.request_interval)
            
            df = self._fetch_spot_data_with_fallback()
            
            if df is None or df.empty:
                self.logger.error("获取股票列表失败")
                return []
            
            if '代码' in df.columns:
                stock_codes = df['代码'].tolist()
            elif 'code' in df.columns:
                stock_codes = df['code'].tolist()
            else:
                self.logger.error("无法识别股票代码列")
                return []
            
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
            
            time.sleep(self.config.request_interval)
            
            df = self._fetch_spot_data_with_fallback()
            
            if df is None or df.empty:
                self.logger.error("获取股票名称和代码映射失败")
                return {}
            
            mapping = {}
            for _, row in df.iterrows():
                stock_name = row.get('名称') or row.get('name')
                stock_code = row.get('代码') or row.get('code')
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
        批量获取股票估值指标（进程池并发拉取）
        
        :param stock_codes: 股票代码列表
        :return: StockInfo对象列表
        """
        results = []
        config_dict = self.config.model_dump()
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_code = {
                executor.submit(_fetch_stock_indicator_worker, stock_code, config_dict, self.cache_dir): stock_code
                for stock_code in stock_codes
            }
            
            with tqdm(total=len(stock_codes), desc="批量获取股票指标", unit="只") as pbar:
                for future in as_completed(future_to_code):
                    stock_code = future_to_code[future]
                    try:
                        stock_info_dict = future.result()
                        if stock_info_dict:
                            stock_info = StockInfo(**stock_info_dict)
                            results.append(stock_info)
                    except Exception as e:
                        self.logger.error(f"获取股票指标失败: {stock_code}, 错误: {str(e)}")
                    finally:
                        pbar.update(1)
        
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