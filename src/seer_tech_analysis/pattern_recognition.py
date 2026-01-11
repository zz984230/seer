import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from scipy import signal
from scipy.stats import linregress
from .models import StockData, PatternInfo
from .config import settings
from seer.logger import logger


class PatternRecognition:
    def __init__(self):
        self.logger = logger
        self.config = settings.pattern
    
    def _prepare_dataframe(self, stock_data_list: List[StockData]) -> pd.DataFrame:
        df = pd.DataFrame([item.model_dump() for item in stock_data_list])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    
    def _find_peaks_and_valleys(self, prices: np.ndarray, distance: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        peaks, _ = signal.find_peaks(prices, distance=distance)
        valleys, _ = signal.find_peaks(-prices, distance=distance)
        return peaks, valleys
    
    def _calculate_trend(self, prices: np.ndarray) -> Tuple[float, float]:
        x = np.arange(len(prices))
        slope, intercept, r_value, p_value, std_err = linregress(x, prices)
        return slope, r_value ** 2
    
    def _calculate_confidence(self, pattern_data: Dict[str, Any]) -> float:
        confidence = 0.5
        
        if 'symmetry' in pattern_data:
            confidence += pattern_data['symmetry'] * 0.2
        
        if 'volume_confirmation' in pattern_data:
            confidence += pattern_data['volume_confirmation'] * 0.2
        
        if 'trend_strength' in pattern_data:
            confidence += pattern_data['trend_strength'] * 0.1
        
        return min(confidence, 1.0)
    
    def detect_head_shoulders_top(self, df: pd.DataFrame) -> List[PatternInfo]:
        patterns = []
        
        if not self.config.enable_head_shoulders:
            return patterns
        
        try:
            prices = df['close_price'].values
            peaks, valleys = self._find_peaks_and_valleys(prices, distance=self.config.min_pattern_days)
            
            if len(peaks) < 3:
                return patterns
            
            for i in range(len(peaks) - 2):
                left_shoulder = peaks[i]
                head = peaks[i + 1]
                right_shoulder = peaks[i + 2]
                
                left_price = prices[left_shoulder]
                head_price = prices[head]
                right_price = prices[right_shoulder]
                
                if head_price > left_price and head_price > right_price:
                    price_diff_left = abs(head_price - left_price) / head_price
                    price_diff_right = abs(head_price - right_price) / head_price
                    
                    if price_diff_left < 0.1 and price_diff_right < 0.1:
                        symmetry = 1.0 - abs(price_diff_left - price_diff_right)
                        
                        neckline = min(prices[left_shoulder:right_shoulder + 1])
                        neckline_idx = np.argmin(prices[left_shoulder:right_shoulder + 1]) + left_shoulder
                        
                        target_price = neckline - (head_price - neckline)
                        stop_loss = head_price
                        
                        pattern_data = {
                            'symmetry': symmetry,
                            'volume_confirmation': 0.8,
                            'trend_strength': 0.7
                        }
                        
                        confidence = self._calculate_confidence(pattern_data)
                        
                        if confidence >= self.config.min_confidence:
                            pattern = PatternInfo(
                                pattern_type="reversal",
                                pattern_name="头肩顶",
                                start_date=df.iloc[left_shoulder]['date'].strftime("%Y-%m-%d"),
                                end_date=df.iloc[right_shoulder]['date'].strftime("%Y-%m-%d"),
                                confidence=confidence,
                                target_price=target_price,
                                stop_loss=stop_loss,
                                description=f"头肩顶形态，头部价格{head_price:.2f}，左肩{left_price:.2f}，右肩{right_price:.2f}，颈线{neckline:.2f}"
                            )
                            patterns.append(pattern)
                            self.logger.info(f"检测到头肩顶形态: {df.iloc[left_shoulder]['date']} ~ {df.iloc[right_shoulder]['date']}")
        
        except Exception as e:
            self.logger.error(f"头肩顶检测失败: {str(e)}")
        
        return patterns
    
    def detect_head_shoulders_bottom(self, df: pd.DataFrame) -> List[PatternInfo]:
        patterns = []
        
        if not self.config.enable_head_shoulders:
            return patterns
        
        try:
            prices = df['close_price'].values
            peaks, valleys = self._find_peaks_and_valleys(prices, distance=self.config.min_pattern_days)
            
            if len(valleys) < 3:
                return patterns
            
            for i in range(len(valleys) - 2):
                left_shoulder = valleys[i]
                head = valleys[i + 1]
                right_shoulder = valleys[i + 2]
                
                left_price = prices[left_shoulder]
                head_price = prices[head]
                right_price = prices[right_shoulder]
                
                if head_price < left_price and head_price < right_price:
                    price_diff_left = abs(head_price - left_price) / head_price
                    price_diff_right = abs(head_price - right_price) / head_price
                    
                    if price_diff_left < 0.1 and price_diff_right < 0.1:
                        symmetry = 1.0 - abs(price_diff_left - price_diff_right)
                        
                        neckline = max(prices[left_shoulder:right_shoulder + 1])
                        neckline_idx = np.argmax(prices[left_shoulder:right_shoulder + 1]) + left_shoulder
                        
                        target_price = neckline + (neckline - head_price)
                        stop_loss = head_price
                        
                        pattern_data = {
                            'symmetry': symmetry,
                            'volume_confirmation': 0.8,
                            'trend_strength': 0.7
                        }
                        
                        confidence = self._calculate_confidence(pattern_data)
                        
                        if confidence >= self.config.min_confidence:
                            pattern = PatternInfo(
                                pattern_type="reversal",
                                pattern_name="头肩底",
                                start_date=df.iloc[left_shoulder]['date'].strftime("%Y-%m-%d"),
                                end_date=df.iloc[right_shoulder]['date'].strftime("%Y-%m-%d"),
                                confidence=confidence,
                                target_price=target_price,
                                stop_loss=stop_loss,
                                description=f"头肩底形态，头部价格{head_price:.2f}，左肩{left_price:.2f}，右肩{right_price:.2f}，颈线{neckline:.2f}"
                            )
                            patterns.append(pattern)
                            self.logger.info(f"检测到头肩底形态: {df.iloc[left_shoulder]['date']} ~ {df.iloc[right_shoulder]['date']}")
        
        except Exception as e:
            self.logger.error(f"头肩底检测失败: {str(e)}")
        
        return patterns
    
    def detect_double_top(self, df: pd.DataFrame) -> List[PatternInfo]:
        patterns = []
        
        if not self.config.enable_double_top_bottom:
            return patterns
        
        try:
            prices = df['close_price'].values
            peaks, _ = self._find_peaks_and_valleys(prices, distance=self.config.min_pattern_days)
            
            if len(peaks) < 2:
                return patterns
            
            for i in range(len(peaks) - 1):
                left_peak = peaks[i]
                right_peak = peaks[i + 1]
                
                left_price = prices[left_peak]
                right_price = prices[right_peak]
                
                price_diff = abs(left_price - right_price) / left_price
                
                if price_diff < 0.03:
                    valley_between = prices[left_peak:right_peak + 1]
                    neckline = min(valley_between)
                    
                    target_price = neckline - (left_price - neckline)
                    stop_loss = left_price * 1.02
                    
                    pattern_data = {
                        'symmetry': 1.0 - price_diff,
                        'volume_confirmation': 0.7,
                        'trend_strength': 0.6
                    }
                    
                    confidence = self._calculate_confidence(pattern_data)
                    
                    if confidence >= self.config.min_confidence:
                        pattern = PatternInfo(
                            pattern_type="reversal",
                            pattern_name="双顶",
                            start_date=df.iloc[left_peak]['date'].strftime("%Y-%m-%d"),
                            end_date=df.iloc[right_peak]['date'].strftime("%Y-%m-%d"),
                            confidence=confidence,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            description=f"双顶形态，左顶{left_price:.2f}，右顶{right_price:.2f}，颈线{neckline:.2f}"
                        )
                        patterns.append(pattern)
                        self.logger.info(f"检测到双顶形态: {df.iloc[left_peak]['date']} ~ {df.iloc[right_peak]['date']}")
        
        except Exception as e:
            self.logger.error(f"双顶检测失败: {str(e)}")
        
        return patterns
    
    def detect_double_bottom(self, df: pd.DataFrame) -> List[PatternInfo]:
        patterns = []
        
        if not self.config.enable_double_top_bottom:
            return patterns
        
        try:
            prices = df['close_price'].values
            _, valleys = self._find_peaks_and_valleys(prices, distance=self.config.min_pattern_days)
            
            if len(valleys) < 2:
                return patterns
            
            for i in range(len(valleys) - 1):
                left_valley = valleys[i]
                right_valley = valleys[i + 1]
                
                left_price = prices[left_valley]
                right_price = prices[right_valley]
                
                price_diff = abs(left_price - right_price) / left_price
                
                if price_diff < 0.03:
                    peak_between = prices[left_valley:right_valley + 1]
                    neckline = max(peak_between)
                    
                    target_price = neckline + (neckline - left_price)
                    stop_loss = left_price * 0.98
                    
                    pattern_data = {
                        'symmetry': 1.0 - price_diff,
                        'volume_confirmation': 0.7,
                        'trend_strength': 0.6
                    }
                    
                    confidence = self._calculate_confidence(pattern_data)
                    
                    if confidence >= self.config.min_confidence:
                        pattern = PatternInfo(
                            pattern_type="reversal",
                            pattern_name="双底",
                            start_date=df.iloc[left_valley]['date'].strftime("%Y-%m-%d"),
                            end_date=df.iloc[right_valley]['date'].strftime("%Y-%m-%d"),
                            confidence=confidence,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            description=f"双底形态，左底{left_price:.2f}，右底{right_price:.2f}，颈线{neckline:.2f}"
                        )
                        patterns.append(pattern)
                        self.logger.info(f"检测到双底形态: {df.iloc[left_valley]['date']} ~ {df.iloc[right_valley]['date']}")
        
        except Exception as e:
            self.logger.error(f"双底检测失败: {str(e)}")
        
        return patterns
    
    def detect_triangle_patterns(self, df: pd.DataFrame) -> List[PatternInfo]:
        patterns = []
        
        if not self.config.enable_triangle:
            return patterns
        
        try:
            prices = df['close_price'].values
            
            window_size = min(30, len(prices) // 3)
            
            for i in range(0, len(prices) - window_size, window_size // 2):
                window_prices = prices[i:i + window_size]
                
                slope, r_squared = self._calculate_trend(window_prices)
                
                if abs(slope) < 0.01 and r_squared > 0.7:
                    start_date = df.iloc[i]['date'].strftime("%Y-%m-%d")
                    end_date = df.iloc[i + window_size - 1]['date'].strftime("%Y-%m-%d")
                    
                    min_price = np.min(window_prices)
                    max_price = np.max(window_prices)
                    
                    target_price = max_price + (max_price - min_price) * 0.5
                    stop_loss = min_price
                    
                    pattern_data = {
                        'symmetry': 0.8,
                        'volume_confirmation': 0.6,
                        'trend_strength': r_squared
                    }
                    
                    confidence = self._calculate_confidence(pattern_data)
                    
                    if confidence >= self.config.min_confidence:
                        pattern = PatternInfo(
                            pattern_type="continuation",
                            pattern_name="三角形整理",
                            start_date=start_date,
                            end_date=end_date,
                            confidence=confidence,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            description=f"三角形整理形态，价格区间{min_price:.2f}-{max_price:.2f}"
                        )
                        patterns.append(pattern)
                        self.logger.info(f"检测到三角形形态: {start_date} ~ {end_date}")
        
        except Exception as e:
            self.logger.error(f"三角形检测失败: {str(e)}")
        
        return patterns
    
    def detect_wedge_patterns(self, df: pd.DataFrame) -> List[PatternInfo]:
        patterns = []
        
        if not self.config.enable_wedge:
            return patterns
        
        try:
            prices = df['close_price'].values
            
            window_size = min(20, len(prices) // 4)
            
            for i in range(0, len(prices) - window_size, window_size // 2):
                window_prices = prices[i:i + window_size]
                
                slope, r_squared = self._calculate_trend(window_prices)
                
                if abs(slope) > 0.01 and r_squared > 0.6:
                    pattern_name = "上升楔形" if slope > 0 else "下降楔形"
                    pattern_type = "reversal" if slope > 0 else "reversal"
                    
                    start_date = df.iloc[i]['date'].strftime("%Y-%m-%d")
                    end_date = df.iloc[i + window_size - 1]['date'].strftime("%Y-%m-%d")
                    
                    min_price = np.min(window_prices)
                    max_price = np.max(window_prices)
                    
                    if slope > 0:
                        target_price = min_price - (max_price - min_price) * 0.5
                        stop_loss = max_price
                    else:
                        target_price = max_price + (max_price - min_price) * 0.5
                        stop_loss = min_price
                    
                    pattern_data = {
                        'symmetry': 0.7,
                        'volume_confirmation': 0.6,
                        'trend_strength': r_squared
                    }
                    
                    confidence = self._calculate_confidence(pattern_data)
                    
                    if confidence >= self.config.min_confidence:
                        pattern = PatternInfo(
                            pattern_type=pattern_type,
                            pattern_name=pattern_name,
                            start_date=start_date,
                            end_date=end_date,
                            confidence=confidence,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            description=f"{pattern_name}形态，斜率{slope:.4f}"
                        )
                        patterns.append(pattern)
                        self.logger.info(f"检测到{pattern_name}形态: {start_date} ~ {end_date}")
        
        except Exception as e:
            self.logger.error(f"楔形检测失败: {str(e)}")
        
        return patterns
    
    def detect_all_patterns(self, stock_data_list: List[StockData]) -> Tuple[bool, str, List[PatternInfo]]:
        try:
            df = self._prepare_dataframe(stock_data_list)
            
            all_patterns = []
            
            if self.config.enable_head_shoulders:
                all_patterns.extend(self.detect_head_shoulders_top(df))
                all_patterns.extend(self.detect_head_shoulders_bottom(df))
            
            if self.config.enable_double_top_bottom:
                all_patterns.extend(self.detect_double_top(df))
                all_patterns.extend(self.detect_double_bottom(df))
            
            if self.config.enable_triangle:
                all_patterns.extend(self.detect_triangle_patterns(df))
            
            if self.config.enable_wedge:
                all_patterns.extend(self.detect_wedge_patterns(df))
            
            all_patterns.sort(key=lambda x: x.confidence, reverse=True)
            
            self.logger.info(f"共检测到 {len(all_patterns)} 个形态")
            
            return True, "形态识别完成", all_patterns
            
        except Exception as e:
            self.logger.error(f"形态识别失败: {str(e)}")
            return False, str(e), []
