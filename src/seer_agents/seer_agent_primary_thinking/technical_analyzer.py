import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .models import StockAnalysisResult
from seer.logger import logger


class TechnicalAnalyzer:
    def __init__(self):
        self.logger = logger
    
    def _prepare_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> Dict[str, List[float]]:
        ma_dict = {}
        for period in periods:
            ma_values = df['close'].rolling(window=period).mean().tolist()
            ma_dict[f'MA{period}'] = ma_values
        return ma_dict
    
    def calculate_macd(self, df: pd.DataFrame, fast_period: int = 12, 
                     slow_period: int = 26, signal_period: int = 9) -> Dict[str, Any]:
        if len(df) < slow_period + signal_period:
            self.logger.warning(f"数据长度不足，无法计算MACD: {len(df)} < {slow_period + signal_period}")
            return {
                'dif': [],
                'dea': [],
                'macd': [],
                'signals': [],
                'description': '数据长度不足，无法计算MACD'
            }
        
        close_prices = df['close'].values
        
        ema_fast = pd.Series(close_prices).ewm(span=fast_period, adjust=False).mean()
        ema_slow = pd.Series(close_prices).ewm(span=slow_period, adjust=False).mean()
        
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal_period, adjust=False).mean()
        macd = (dif - dea) * 2
        
        signals = self._generate_macd_signals(dif, dea, macd)
        
        try:
            description = self._generate_macd_description(dif.iloc[-1], dea.iloc[-1], macd.iloc[-1])
        except (IndexError, KeyError) as e:
            self.logger.warning(f"无法生成MACD描述: {str(e)}")
            description = '无法生成MACD描述'
        
        return {
            'dif': dif.fillna(0).tolist(),
            'dea': dea.fillna(0).tolist(),
            'macd': macd.fillna(0).tolist(),
            'signals': signals,
            'description': description
        }
    
    def _generate_macd_signals(self, dif: pd.Series, dea: pd.Series, macd: pd.Series) -> List[str]:
        signals = []
        
        for i in range(1, len(dif)):
            if dif.iloc[i] > dea.iloc[i] and dif.iloc[i-1] <= dea.iloc[i-1]:
                signals.append(f"第{i}天: DIF上穿DEA，金叉信号")
            elif dif.iloc[i] < dea.iloc[i] and dif.iloc[i-1] >= dea.iloc[i-1]:
                signals.append(f"第{i}天: DIF下穿DEA，死叉信号")
            
            if macd.iloc[i] > 0 and macd.iloc[i-1] <= 0:
                signals.append(f"第{i}天: MACD柱状图由负转正，买入信号")
            elif macd.iloc[i] < 0 and macd.iloc[i-1] >= 0:
                signals.append(f"第{i}天: MACD柱状图由正转负，卖出信号")
        
        return signals
    
    def _generate_macd_description(self, dif: float, dea: float, macd: float) -> str:
        desc_parts = []
        
        if dif > dea:
            desc_parts.append("DIF位于DEA上方，短期趋势向上")
        else:
            desc_parts.append("DIF位于DEA下方，短期趋势向下")
        
        if macd > 0:
            desc_parts.append("MACD柱状图为正值，多头市场")
        else:
            desc_parts.append("MACD柱状图为负值，空头市场")
        
        return "；".join(desc_parts)
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        close_prices = df['close'].values
        
        def calculate_rsi_series(prices: np.ndarray, period: int) -> np.ndarray:
            delta = np.diff(prices)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            avg_gain = pd.Series(gain).rolling(window=period).mean()
            avg_loss = pd.Series(loss).rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50).values
        
        rsi_values = calculate_rsi_series(close_prices, period)
        
        signals = self._generate_rsi_signals(rsi_values)
        description = self._generate_rsi_description(rsi_values[-1])
        
        return {
            'rsi': rsi_values.tolist(),
            'signals': signals,
            'description': description
        }
    
    def _generate_rsi_signals(self, rsi: np.ndarray) -> List[str]:
        signals = []
        
        for i in range(1, len(rsi)):
            if rsi[i] > 70 and rsi[i-1] <= 70:
                signals.append(f"第{i}天: RSI突破70，超买信号")
            elif rsi[i] < 30 and rsi[i-1] >= 30:
                signals.append(f"第{i}天: RSI跌破30，超卖信号")
        
        return signals
    
    def _generate_rsi_description(self, rsi: float) -> str:
        if rsi > 70:
            return f"RSI为{rsi:.2f}，处于超买区域，注意回调风险"
        elif rsi < 30:
            return f"RSI为{rsi:.2f}，处于超卖区域，可能反弹"
        else:
            return f"RSI为{rsi:.2f}，处于正常区间"
    
    def calculate_kdj(self, df: pd.DataFrame, period: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, Any]:
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)
        
        k_values = pd.Series([50] * len(df))
        d_values = pd.Series([50] * len(df))
        j_values = pd.Series([50] * len(df))
        
        for i in range(1, len(df)):
            k_values.iloc[i] = (2/3) * k_values.iloc[i-1] + (1/3) * rsv.iloc[i]
            d_values.iloc[i] = (2/3) * d_values.iloc[i-1] + (1/3) * k_values.iloc[i]
            j_values.iloc[i] = 3 * k_values.iloc[i] - 2 * d_values.iloc[i]
        
        signals = self._generate_kdj_signals(k_values, d_values, j_values)
        
        try:
            description = self._generate_kdj_description(k_values.iloc[-1], d_values.iloc[-1], j_values.iloc[-1])
        except (IndexError, KeyError) as e:
            self.logger.warning(f"无法生成KDJ描述: {str(e)}")
            description = '无法生成KDJ描述'
        
        return {
            'k': k_values.tolist(),
            'd': d_values.tolist(),
            'j': j_values.tolist(),
            'signals': signals,
            'description': description
        }
    
    def _generate_kdj_signals(self, k: pd.Series, d: pd.Series, j: pd.Series) -> List[str]:
        signals = []
        
        for i in range(1, len(k)):
            if k.iloc[i] > d.iloc[i] and k.iloc[i-1] <= d.iloc[i-1]:
                signals.append(f"第{i}天: K线上穿D线，金叉信号")
            elif k.iloc[i] < d.iloc[i] and k.iloc[i-1] >= d.iloc[i-1]:
                signals.append(f"第{i}天: K线下穿D线，死叉信号")
            
            if k.iloc[i] > 80 and k.iloc[i-1] <= 80:
                signals.append(f"第{i}天: K线突破80，超买信号")
            elif k.iloc[i] < 20 and k.iloc[i-1] >= 20:
                signals.append(f"第{i}天: K线跌破20，超卖信号")
        
        return signals
    
    def _generate_kdj_description(self, k: float, d: float, j: float) -> str:
        desc_parts = []
        
        if k > d:
            desc_parts.append(f"K线({k:.2f})位于D线({d:.2f})上方，短期趋势向上")
        else:
            desc_parts.append(f"K线({k:.2f})位于D线({d:.2f})下方，短期趋势向下")
        
        if k > 80:
            desc_parts.append("K线处于超买区域，注意回调风险")
        elif k < 20:
            desc_parts.append("K线处于超卖区域，可能反弹")
        
        if j > 100:
            desc_parts.append(f"J线({j:.2f})超过100，严重超买")
        elif j < 0:
            desc_parts.append(f"J线({j:.2f})低于0，严重超卖")
        
        return "；".join(desc_parts)
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        patterns = {
            'neckline_breakthrough': self._detect_neckline_breakthrough(df),
            'long_leg_buy': self._detect_long_leg_buy(df),
            'n_structure': self._detect_n_structure(df),
            'yang_bao_yin': self._detect_yang_bao_yin(df),
            'box_breakthrough': self._detect_box_breakthrough(df),
            'top_patterns': self._detect_top_patterns(df),
            'bottom_patterns': self._detect_bottom_patterns(df)
        }
        return patterns
    
    def _detect_neckline_breakthrough(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 20:
            return {'detected': False, 'reason': '数据不足'}
        
        recent_data = df.tail(20)
        resistance_level = recent_data['high'].max()
        
        latest_close = df['close'].iloc[-1]
        latest_high = df['high'].iloc[-1]
        latest_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(10).mean()
        
        detected = latest_close > resistance_level * 0.98 and latest_volume > avg_volume * 1.5
        
        return {
            'detected': detected,
            'resistance_level': resistance_level,
            'current_price': latest_close,
            'volume_surge': latest_volume > avg_volume * 1.5,
            'description': '颈线突破形态' if detected else '未检测到颈线突破'
        }
    
    def _detect_long_leg_buy(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 5:
            return {'detected': False, 'reason': '数据不足'}
        
        latest = df.iloc[-1]
        body_length = abs(latest['close'] - latest['open'])
        lower_shadow = latest['open'] - latest['low']
        total_length = latest['high'] - latest['low']
        
        detected = body_length > 0 and lower_shadow > body_length * 2 and lower_shadow > total_length * 0.3
        
        return {
            'detected': detected,
            'body_length': body_length,
            'lower_shadow': lower_shadow,
            'total_length': total_length,
            'description': '大长腿买入形态' if detected else '未检测到大长腿形态'
        }
    
    def _detect_n_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 10:
            return {'detected': False, 'reason': '数据不足'}
        
        recent = df.tail(10).reset_index(drop=True)
        peak_idx = recent['high'].idxmax()
        valley_idx = recent['low'].idxmin()
        
        if peak_idx > valley_idx:
            detected = recent['close'].iloc[-1] > recent['close'].iloc[valley_idx]
        else:
            detected = False
        
        return {
            'detected': detected,
            'peak_price': recent['high'].max(),
            'valley_price': recent['low'].min(),
            'current_price': recent['close'].iloc[-1],
            'description': 'N型结构形态' if detected else '未检测到N型结构'
        }
    
    def _detect_yang_bao_yin(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 3:
            return {'detected': False, 'reason': '数据不足'}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        detected = (prev['close'] < prev['open'] and 
                   latest['close'] > prev['open'] and 
                   latest['close'] > latest['open'])
        
        return {
            'detected': detected,
            'prev_close': prev['close'],
            'prev_open': prev['open'],
            'latest_close': latest['close'],
            'latest_open': latest['open'],
            'description': '阳包阴形态' if detected else '未检测到阳包阴形态'
        }
    
    def _detect_box_breakthrough(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 30:
            return {'detected': False, 'reason': '数据不足'}
        
        recent = df.tail(30)
        upper_band = recent['high'].quantile(0.8)
        lower_band = recent['low'].quantile(0.2)
        
        latest_close = df['close'].iloc[-1]
        latest_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(10).mean()
        
        detected = latest_close > upper_band and latest_volume > avg_volume * 1.5
        
        return {
            'detected': detected,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'current_price': latest_close,
            'volume_surge': latest_volume > avg_volume * 1.5,
            'description': '箱体突破形态' if detected else '未检测到箱体突破'
        }
    
    def _detect_top_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        patterns = []
        
        latest = df.iloc[-1]
        body_length = abs(latest['close'] - latest['open'])
        upper_shadow = latest['high'] - max(latest['open'], latest['close'])
        lower_shadow = min(latest['open'], latest['close']) - latest['low']
        
        if upper_shadow > body_length * 2 and body_length > 0:
            patterns.append({
                'type': '流星线',
                'detected': True,
                'description': '高位流星线，注意见顶风险'
            })
        
        if lower_shadow > body_length * 2 and body_length > 0:
            patterns.append({
                'type': '吊颈线',
                'detected': True,
                'description': '吊颈线形态，注意见顶风险'
            })
        
        if len(df) >= 5:
            recent_volumes = df['volume'].tail(5)
            recent_prices = df['close'].tail(5)
            
            if (recent_prices.iloc[-1] > recent_prices.iloc[-2] > recent_prices.iloc[-3] and
                recent_volumes.iloc[-1] < recent_volumes.iloc[-2] < recent_volumes.iloc[-3]):
                patterns.append({
                    'type': '缩量加速',
                    'detected': True,
                    'description': '缩量加速上涨，注意见顶风险'
                })
        
        return {
            'patterns': patterns,
            'detected': len(patterns) > 0,
            'description': f'检测到 {len(patterns)} 个顶部形态'
        }
    
    def _detect_bottom_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        patterns = []
        
        latest = df.iloc[-1]
        body_length = abs(latest['close'] - latest['open'])
        
        if body_length > 0:
            upper_shadow = latest['high'] - max(latest['open'], latest['close'])
            lower_shadow = min(latest['open'], latest['close']) - latest['low']
            
            if upper_shadow > body_length * 2:
                patterns.append({
                    'type': '上影线试盘',
                    'detected': True,
                    'description': '上影线试盘形态，可能吸筹'
                })
        
        if len(df) >= 3:
            prev = df.iloc[-2]
            if (prev['close'] < prev['open'] and 
                latest['close'] > prev['open'] and 
                latest['close'] > latest['open']):
                patterns.append({
                    'type': '低位阳包阴',
                    'detected': True,
                    'description': '低位阳包阴形态，看涨信号'
                })
        
        return {
            'patterns': patterns,
            'detected': len(patterns) > 0,
            'description': f'检测到 {len(patterns)} 个底部形态'
        }
    
    def analyze_volume_price_relation(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 10:
            return {'error': '数据不足'}
        
        latest = df.iloc[-1]
        
        try:
            price_change = (latest['close'] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100
            volume_change = (latest['volume'] - df['volume'].iloc[-2]) / df['volume'].iloc[-2] * 100
        except (IndexError, ZeroDivisionError) as e:
            self.logger.warning(f"计算价格/成交量变化失败: {str(e)}")
            price_change = 0
            volume_change = 0
        
        avg_volume = df['volume'].tail(20).mean()
        
        if price_change > 5 and volume_change > 50:
            relation_type = "量增价涨"
            strength = "强"
            description = "成交量大幅增加，价格上涨，多头力量强劲"
        elif price_change < -5 and volume_change > 50:
            relation_type = "量增价跌"
            strength = "强"
            description = "成交量大幅增加，价格下跌，恐慌性抛售"
        elif price_change > 5 and volume_change < -20:
            relation_type = "量减价涨"
            strength = "弱"
            description = "成交量减少，价格上涨，上涨动力不足"
        elif price_change < -5 and volume_change < -20:
            relation_type = "量减价跌"
            strength = "弱"
            description = "成交量减少，价格下跌，下跌动力不足"
        else:
            relation_type = "量价平衡"
            strength = "中"
            description = "量价关系平衡，趋势不明"
        
        return {
            'relation_type': relation_type,
            'strength': strength,
            'price_change': price_change,
            'volume_change': volume_change,
            'current_volume': latest['volume'],
            'avg_volume': avg_volume,
            'volume_ratio': latest['volume'] / avg_volume,
            'description': description
        }
    
    def analyze_main_force_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 30:
            return {'error': '数据不足'}
        
        patterns = self.detect_patterns(df)
        volume_price = self.analyze_volume_price_relation(df)
        
        behavior_analysis = {
            'current_phase': self._determine_current_phase(df, patterns),
            'main_force_status': self._determine_main_force_status(df, patterns, volume_price),
            'risk_level': self._assess_risk_level(df, patterns, volume_price),
            'trading_signals': self._generate_trading_signals(df, patterns, volume_price)
        }
        
        return behavior_analysis
    
    def _determine_current_phase(self, df: pd.DataFrame, patterns: Dict[str, Any]) -> str:
        latest_close = df['close'].iloc[-1]
        
        try:
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
        except (IndexError, KeyError) as e:
            self.logger.warning(f"计算均线失败: {str(e)}")
            return "震荡整理阶段"
        
        if latest_close > ma20 > ma60:
            if patterns['top_patterns']['detected']:
                return "拉升后期/出货阶段"
            elif patterns['neckline_breakthrough']['detected']:
                return "拉升阶段"
            else:
                return "洗盘阶段"
        elif latest_close < ma20 < ma60:
            if patterns['bottom_patterns']['detected']:
                return "建仓阶段"
            else:
                return "震荡筑底阶段"
        else:
            return "震荡整理阶段"
    
    def _determine_main_force_status(self, df: pd.DataFrame, patterns: Dict[str, Any], 
                                  volume_price: Dict[str, Any]) -> str:
        phase = self._determine_current_phase(df, patterns)
        
        if phase == "拉升阶段":
            return "主力拉升中"
        elif phase == "洗盘阶段":
            return "主力洗盘中"
        elif phase == "建仓阶段":
            return "主力建仓中"
        elif phase == "拉升后期/出货阶段":
            if patterns['top_patterns']['detected']:
                return "主力出货中"
            else:
                return "主力拉升后期"
        else:
            return "主力观望中"
    
    def _assess_risk_level(self, df: pd.DataFrame, patterns: Dict[str, Any], 
                         volume_price: Dict[str, Any]) -> str:
        risk_score = 0
        
        if patterns['top_patterns']['detected']:
            risk_score += 3
        
        if volume_price.get('relation_type') == "量增价跌":
            risk_score += 2
        
        if volume_price.get('relation_type') == "量减价跌":
            risk_score += 1
        
        try:
            latest_close = df['close'].iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            
            if latest_close < ma20 * 0.95:
                risk_score += 2
        except (IndexError, KeyError) as e:
            self.logger.warning(f"计算风险等级失败: {str(e)}")
        
        if risk_score >= 4:
            return "高"
        elif risk_score >= 2:
            return "中"
        else:
            return "低"
    
    def _generate_trading_signals(self, df: pd.DataFrame, patterns: Dict[str, Any], 
                              volume_price: Dict[str, Any]) -> List[str]:
        signals = []
        
        if patterns['bottom_patterns']['detected']:
            signals.append("检测到底部形态，可考虑逢低吸纳")
        
        if patterns['neckline_breakthrough']['detected']:
            signals.append("检测到颈线突破，可考虑跟进")
        
        if patterns['box_breakthrough']['detected']:
            signals.append("检测到箱体突破，可考虑加仓")
        
        if patterns['top_patterns']['detected']:
            signals.append("检测到顶部形态，建议减仓或离场")
        
        if volume_price.get('relation_type') == "量增价涨":
            signals.append("量增价涨，多头力量强劲，可持股待涨")
        
        if volume_price.get('relation_type') == "量增价跌":
            signals.append("量增价跌，恐慌性抛售，建议观望")
        
        if volume_price.get('relation_type') == "量减价涨":
            signals.append("量减价涨，上涨动力不足，注意风险")
        
        return signals
    
    def comprehensive_analysis(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        df = self._prepare_dataframe(data)
        
        if len(df) < 2:
            self.logger.warning(f"数据长度不足，无法进行技术分析: {len(df)} < 2")
            return {
                'ma': {},
                'macd': {'dif': [], 'dea': [], 'macd': [], 'signals': [], 'description': '数据长度不足'},
                'rsi': {'rsi': [], 'description': '数据长度不足'},
                'kdj': {'k': [], 'd': [], 'j': [], 'description': '数据长度不足'},
                'patterns': {},
                'volume_price': {},
                'main_force': {},
                'current_price': None,
                'price_change': 0,
                'volume_change': 0
            }
        
        ma_data = self.calculate_ma(df)
        macd_data = self.calculate_macd(df)
        rsi_data = self.calculate_rsi(df)
        kdj_data = self.calculate_kdj(df)
        patterns = self.detect_patterns(df)
        volume_price = self.analyze_volume_price_relation(df)
        main_force = self.analyze_main_force_behavior(df)
        
        try:
            current_price = df['close'].iloc[-1]
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100
            volume_change = (df['volume'].iloc[-1] - df['volume'].iloc[-2]) / df['volume'].iloc[-2] * 100
        except (IndexError, KeyError, ZeroDivisionError) as e:
            self.logger.warning(f"计算价格/成交量变化失败: {str(e)}")
            current_price = df['close'].iloc[-1] if len(df) > 0 else None
            price_change = 0
            volume_change = 0
        
        analysis_result = {
            'ma': ma_data,
            'macd': macd_data,
            'rsi': rsi_data,
            'kdj': kdj_data,
            'patterns': patterns,
            'volume_price': volume_price,
            'main_force': main_force,
            'current_price': current_price,
            'price_change': price_change,
            'volume_change': volume_change
        }
        
        return analysis_result
