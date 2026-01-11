import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .models import StockData, VolumePriceRelation
from .config import settings
from seer.logger import logger


class VolumePriceAnalysis:
    def __init__(self):
        self.logger = logger
        self.config = settings.volume
    
    def _prepare_dataframe(self, stock_data_list: List[StockData]) -> pd.DataFrame:
        df = pd.DataFrame([item.model_dump() for item in stock_data_list])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    
    def _calculate_volume_ma(self, df: pd.DataFrame, period: int) -> pd.Series:
        return df['volume'].rolling(window=period).mean()
    
    def _determine_relation_type(self, price_change: float, volume_change: float) -> str:
        if price_change > 0:
            if volume_change > 0:
                return "量增价涨"
            else:
                return "量减价涨"
        else:
            if volume_change > 0:
                return "量增价跌"
            else:
                return "量减价跌"
    
    def _determine_strength(self, price_change: float, volume_change: float) -> str:
        abs_price_change = abs(price_change)
        abs_volume_change = abs(volume_change)
        
        if abs_price_change > 3 and abs_volume_change > 1.5:
            return "强"
        elif abs_price_change > 1.5 and abs_volume_change > 0.8:
            return "中"
        else:
            return "弱"
    
    def _generate_description(self, relation_type: str, strength: str, price_change: float, volume_change: float) -> str:
        descriptions = {
            "量增价涨": {
                "强": f"量价齐升，强势上涨，价格涨幅{price_change:.2f}%，成交量放大{volume_change:.2f}%，多头力量强劲",
                "中": f"量价齐升，温和上涨，价格涨幅{price_change:.2f}%，成交量放大{volume_change:.2f}%，多头力量较强",
                "弱": f"量价齐升，弱势上涨，价格涨幅{price_change:.2f}%，成交量放大{volume_change:.2f}%，多头力量一般"
            },
            "量增价跌": {
                "强": f"量增价跌，恐慌性抛售，价格跌幅{abs(price_change):.2f}%，成交量放大{volume_change:.2f}%，空头力量强劲",
                "中": f"量增价跌，主动抛售，价格跌幅{abs(price_change):.2f}%，成交量放大{volume_change:.2f}%，空头力量较强",
                "弱": f"量增价跌，被动抛售，价格跌幅{abs(price_change):.2f}%，成交量放大{volume_change:.2f}%，空头力量一般"
            },
            "量减价涨": {
                "强": f"量减价涨，缩量上涨，价格涨幅{price_change:.2f}%，成交量萎缩{abs(volume_change):.2f}%，上涨动力不足",
                "中": f"量减价涨，缩量上涨，价格涨幅{price_change:.2f}%，成交量萎缩{abs(volume_change):.2f}%，上涨动力一般",
                "弱": f"量减价涨，缩量上涨，价格涨幅{price_change:.2f}%，成交量萎缩{abs(volume_change):.2f}%，上涨动力较弱"
            },
            "量减价跌": {
                "强": f"量减价跌，缩量下跌，价格跌幅{abs(price_change):.2f}%，成交量萎缩{abs(volume_change):.2f}%，下跌动力不足",
                "中": f"量减价跌，缩量下跌，价格跌幅{abs(price_change):.2f}%，成交量萎缩{abs(volume_change):.2f}%，下跌动力一般",
                "弱": f"量减价跌，缩量下跌，价格跌幅{abs(price_change):.2f}%，成交量萎缩{abs(volume_change):.2f}%，下跌动力较弱"
            }
        }
        
        return descriptions.get(relation_type, {}).get(strength, "")
    
    def analyze_daily_volume_price(self, df: pd.DataFrame) -> List[VolumePriceRelation]:
        relations = []
        
        try:
            df['price_change'] = df['close_price'].pct_change() * 100
            df['volume_change'] = df['volume'].pct_change() * 100
            df['volume_ma'] = self._calculate_volume_ma(df, self.config.volume_ma_period)
            
            for i in range(1, len(df)):
                price_change = df['price_change'].iloc[i]
                volume_change = df['volume_change'].iloc[i]
                
                if pd.isna(price_change) or pd.isna(volume_change):
                    continue
                
                relation_type = self._determine_relation_type(price_change, volume_change)
                strength = self._determine_strength(price_change, volume_change)
                description = self._generate_description(relation_type, strength, price_change, volume_change)
                
                volume_surge = volume_change > (self.config.volume_surge_threshold - 1) * 100
                volume_shrink = volume_change < -(self.config.volume_shrink_threshold - 1) * 100
                
                if volume_surge:
                    description += "，成交量显著放大"
                elif volume_shrink:
                    description += "，成交量显著萎缩"
                
                relation = VolumePriceRelation(
                    date=df['date'].iloc[i].strftime("%Y-%m-%d"),
                    price_change=round(price_change, 2),
                    volume_change=round(volume_change, 2),
                    relation_type=relation_type,
                    strength=strength,
                    description=description
                )
                relations.append(relation)
        
        except Exception as e:
            self.logger.error(f"量价关系分析失败: {str(e)}")
        
        return relations
    
    def analyze_volume_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        trend_analysis = {}
        
        try:
            volume_ma = self._calculate_volume_ma(df, self.config.volume_ma_period)
            
            recent_volume = df['volume'].tail(5).mean()
            avg_volume = df['volume'].mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio > self.config.volume_surge_threshold:
                trend_analysis['volume_trend'] = "放量"
                trend_analysis['volume_description'] = f"近期成交量显著放大，是平均成交量的{volume_ratio:.2f}倍"
            elif volume_ratio < self.config.volume_shrink_threshold:
                trend_analysis['volume_trend'] = "缩量"
                trend_analysis['volume_description'] = f"近期成交量显著萎缩，是平均成交量的{volume_ratio:.2f}倍"
            else:
                trend_analysis['volume_trend'] = "平稳"
                trend_analysis['volume_description'] = f"近期成交量平稳，是平均成交量的{volume_ratio:.2f}倍"
            
            volume_slope = np.polyfit(range(len(volume_ma)), volume_ma.fillna(0), 1)[0]
            
            if volume_slope > 0:
                trend_analysis['volume_direction'] = "上升"
                trend_analysis['volume_direction_description'] = "成交量呈上升趋势，市场活跃度提升"
            elif volume_slope < 0:
                trend_analysis['volume_direction'] = "下降"
                trend_analysis['volume_direction_description'] = "成交量呈下降趋势，市场活跃度下降"
            else:
                trend_analysis['volume_direction'] = "平稳"
                trend_analysis['volume_direction_description'] = "成交量保持平稳"
            
            self.logger.info(f"成交量趋势分析完成: {trend_analysis['volume_trend']}, {trend_analysis['volume_direction']}")
            
        except Exception as e:
            self.logger.error(f"成交量趋势分析失败: {str(e)}")
        
        return trend_analysis
    
    def analyze_price_volume_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        correlation_analysis = {}
        
        try:
            price_changes = df['close_price'].pct_change().dropna()
            volume_changes = df['volume'].pct_change().dropna()
            
            min_length = min(len(price_changes), len(volume_changes))
            price_changes = price_changes.tail(min_length)
            volume_changes = volume_changes.tail(min_length)
            
            correlation = price_changes.corr(volume_changes)
            
            if correlation > 0.5:
                correlation_analysis['correlation_type'] = "正相关"
                correlation_analysis['correlation_description'] = f"价格与成交量呈强正相关，相关系数{correlation:.2f}，量价配合良好"
            elif correlation > 0.2:
                correlation_analysis['correlation_type'] = "正相关"
                correlation_analysis['correlation_description'] = f"价格与成交量呈弱正相关，相关系数{correlation:.2f}，量价配合一般"
            elif correlation < -0.5:
                correlation_analysis['correlation_type'] = "负相关"
                correlation_analysis['correlation_description'] = f"价格与成交量呈强负相关，相关系数{correlation:.2f}，量价背离"
            elif correlation < -0.2:
                correlation_analysis['correlation_type'] = "负相关"
                correlation_analysis['correlation_description'] = f"价格与成交量呈弱负相关，相关系数{correlation:.2f}，量价背离"
            else:
                correlation_analysis['correlation_type'] = "无相关"
                correlation_analysis['correlation_description'] = f"价格与成交量无明显相关，相关系数{correlation:.2f}，量价关系不明确"
            
            correlation_analysis['correlation_coefficient'] = round(correlation, 4)
            
            self.logger.info(f"量价相关性分析完成: {correlation_analysis['correlation_type']}")
            
        except Exception as e:
            self.logger.error(f"量价相关性分析失败: {str(e)}")
        
        return correlation_analysis
    
    def analyze_accumulation_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        ad_analysis = {}
        
        try:
            df['money_flow_multiplier'] = ((df['close_price'] - df['low_price']) - (df['high_price'] - df['close_price'])) / (df['high_price'] - df['low_price'])
            df['money_flow_multiplier'] = df['money_flow_multiplier'].fillna(0)
            
            df['money_flow_volume'] = df['money_flow_multiplier'] * df['volume']
            
            df['ad_line'] = df['money_flow_volume'].cumsum()
            
            recent_ad = df['ad_line'].tail(5).mean()
            avg_ad = df['ad_line'].mean()
            ad_ratio = recent_ad / avg_ad if avg_ad != 0 else 1
            
            if ad_ratio > 1.2:
                ad_analysis['accumulation_status'] = "资金流入"
                ad_analysis['accumulation_description'] = f"近期资金持续流入，累积/派发线上升，AD比值{ad_ratio:.2f}"
            elif ad_ratio < 0.8:
                ad_analysis['accumulation_status'] = "资金流出"
                ad_analysis['accumulation_description'] = f"近期资金持续流出，累积/派发线下降，AD比值{ad_ratio:.2f}"
            else:
                ad_analysis['accumulation_status'] = "资金平衡"
                ad_analysis['accumulation_description'] = f"近期资金流入流出平衡，AD比值{ad_ratio:.2f}"
            
            ad_slope = np.polyfit(range(len(df['ad_line'])), df['ad_line'].fillna(0), 1)[0]
            
            if ad_slope > 0:
                ad_analysis['ad_trend'] = "上升"
                ad_analysis['ad_trend_description'] = "累积/派发线呈上升趋势，资金面偏多"
            elif ad_slope < 0:
                ad_analysis['ad_trend'] = "下降"
                ad_analysis['ad_trend_description'] = "累积/派发线呈下降趋势，资金面偏空"
            else:
                ad_analysis['ad_trend'] = "平稳"
                ad_analysis['ad_trend_description'] = "累积/派发线保持平稳"
            
            self.logger.info(f"资金累积分布分析完成: {ad_analysis['accumulation_status']}, {ad_analysis['ad_trend']}")
            
        except Exception as e:
            self.logger.error(f"资金累积分布分析失败: {str(e)}")
        
        return ad_analysis
    
    def analyze_all(self, stock_data_list: List[StockData]) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            df = self._prepare_dataframe(stock_data_list)
            
            daily_relations = self.analyze_daily_volume_price(df)
            
            volume_trend = self.analyze_volume_trend(df)
            
            correlation = self.analyze_price_volume_correlation(df)
            
            accumulation = self.analyze_accumulation_distribution(df)
            
            result = {
                'daily_relations': daily_relations,
                'volume_trend': volume_trend,
                'correlation': correlation,
                'accumulation': accumulation
            }
            
            self.logger.info("量价关系分析完成")
            
            return True, "量价关系分析完成", result
            
        except Exception as e:
            self.logger.error(f"量价关系分析失败: {str(e)}")
            return False, str(e), None
