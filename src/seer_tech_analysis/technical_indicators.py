import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .models import StockData, MACDIndicator, RSIIndicator, KDJIndicator, TechnicalIndicator
from .config import settings
from seer.logger import logger


class TechnicalIndicators:
    def __init__(self):
        self.logger = logger
        self.config = settings.indicators
    
    def _prepare_dataframe(self, stock_data_list: List[StockData]) -> pd.DataFrame:
        df = pd.DataFrame([item.model_dump() for item in stock_data_list])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    
    def calculate_ma(self, df: pd.DataFrame, period: int) -> List[float]:
        ma_values = df['close_price'].rolling(window=period).mean().tolist()
        return ma_values
    
    def calculate_macd(self, stock_data_list: List[StockData]) -> Tuple[bool, str, Optional[MACDIndicator]]:
        try:
            df = self._prepare_dataframe(stock_data_list)
            
            close_prices = df['close_price'].values
            
            ema_fast = pd.Series(close_prices).ewm(span=self.config.macd_fast_period, adjust=False).mean()
            ema_slow = pd.Series(close_prices).ewm(span=self.config.macd_slow_period, adjust=False).mean()
            
            dif = ema_fast - ema_slow
            dea = dif.ewm(span=self.config.macd_signal_period, adjust=False).mean()
            macd = (dif - dea) * 2
            
            dif_list = dif.fillna(0).tolist()
            dea_list = dea.fillna(0).tolist()
            macd_list = macd.fillna(0).tolist()
            
            signals = self._generate_macd_signals(dif_list, dea_list, macd_list)
            
            description = self._generate_macd_description(dif_list[-1], dea_list[-1], macd_list[-1])
            
            macd_indicator = MACDIndicator(
                dif=dif_list,
                dea=dea_list,
                macd=macd_list,
                signals=signals,
                description=description
            )
            
            return True, "MACD计算成功", macd_indicator
            
        except Exception as e:
            self.logger.error(f"MACD计算失败: {str(e)}")
            return False, str(e), None
    
    def _generate_macd_signals(self, dif: List[float], dea: List[float], macd: List[float]) -> List[str]:
        signals = []
        
        for i in range(1, len(dif)):
            if dif[i] > dea[i] and dif[i-1] <= dea[i-1]:
                signals.append(f"第{i}天: DIF上穿DEA，金叉信号")
            elif dif[i] < dea[i] and dif[i-1] >= dea[i-1]:
                signals.append(f"第{i}天: DIF下穿DEA，死叉信号")
            
            if macd[i] > 0 and macd[i-1] <= 0:
                signals.append(f"第{i}天: MACD柱状图由负转正，买入信号")
            elif macd[i] < 0 and macd[i-1] >= 0:
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
        
        if abs(macd) > abs(dif - dea) * 2 * 1.5:
            desc_parts.append("MACD柱状图放大，趋势加强")
        elif abs(macd) < abs(dif - dea) * 2 * 0.5:
            desc_parts.append("MACD柱状图缩小，趋势减弱")
        
        return "；".join(desc_parts)
    
    def calculate_rsi(self, stock_data_list: List[StockData]) -> Tuple[bool, str, Optional[RSIIndicator]]:
        try:
            df = self._prepare_dataframe(stock_data_list)
            
            close_prices = df['close_price'].values
            
            def calculate_rsi_series(prices: np.ndarray, period: int) -> np.ndarray:
                delta = np.diff(prices)
                gain = np.where(delta > 0, delta, 0)
                loss = np.where(delta < 0, -delta, 0)
                
                avg_gain = pd.Series(gain).rolling(window=period).mean()
                avg_loss = pd.Series(loss).rolling(window=period).mean()
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
                return rsi.fillna(50).values
        
            rsi6 = calculate_rsi_series(close_prices, 6)
            rsi12 = calculate_rsi_series(close_prices, 12)
            rsi24 = calculate_rsi_series(close_prices, 24)
            
            rsi6_list = rsi6.tolist()
            rsi12_list = rsi12.tolist()
            rsi24_list = rsi24.tolist()
            
            signals = self._generate_rsi_signals(rsi6_list, rsi12_list, rsi24_list)
            
            description = self._generate_rsi_description(rsi6_list[-1], rsi12_list[-1], rsi24_list[-1])
            
            rsi_indicator = RSIIndicator(
                rsi6=rsi6_list,
                rsi12=rsi12_list,
                rsi24=rsi24_list,
                signals=signals,
                description=description
            )
            
            return True, "RSI计算成功", rsi_indicator
            
        except Exception as e:
            self.logger.error(f"RSI计算失败: {str(e)}")
            return False, str(e), None
    
    def _generate_rsi_signals(self, rsi6: List[float], rsi12: List[float], rsi24: List[float]) -> List[str]:
        signals = []
        
        for i in range(1, len(rsi6)):
            if rsi6[i] > self.config.rsi_overbought and rsi6[i-1] <= self.config.rsi_overbought:
                signals.append(f"第{i}天: RSI6突破{self.config.rsi_overbought}，超买信号")
            elif rsi6[i] < self.config.rsi_oversold and rsi6[i-1] >= self.config.rsi_oversold:
                signals.append(f"第{i}天: RSI6跌破{self.config.rsi_oversold}，超卖信号")
            
            if rsi12[i] > self.config.rsi_overbought and rsi12[i-1] <= self.config.rsi_overbought:
                signals.append(f"第{i}天: RSI12突破{self.config.rsi_overbought}，超买信号")
            elif rsi12[i] < self.config.rsi_oversold and rsi12[i-1] >= self.config.rsi_oversold:
                signals.append(f"第{i}天: RSI12跌破{self.config.rsi_oversold}，超卖信号")
            
            if rsi6[i] > rsi12[i] and rsi6[i-1] <= rsi12[i-1]:
                signals.append(f"第{i}天: RSI6上穿RSI12，短期走强")
            elif rsi6[i] < rsi12[i] and rsi6[i-1] >= rsi12[i-1]:
                signals.append(f"第{i}天: RSI6下穿RSI12，短期走弱")
        
        return signals
    
    def _generate_rsi_description(self, rsi6: float, rsi12: float, rsi24: float) -> str:
        desc_parts = []
        
        if rsi6 > self.config.rsi_overbought:
            desc_parts.append(f"RSI6为{rsi6:.2f}，处于超买区域，注意回调风险")
        elif rsi6 < self.config.rsi_oversold:
            desc_parts.append(f"RSI6为{rsi6:.2f}，处于超卖区域，可能反弹")
        else:
            desc_parts.append(f"RSI6为{rsi6:.2f}，处于正常区间")
        
        if rsi6 > rsi12 > rsi24:
            desc_parts.append("短期RSI均高于长期RSI，短期趋势向上")
        elif rsi6 < rsi12 < rsi24:
            desc_parts.append("短期RSI均低于长期RSI，短期趋势向下")
        
        return "；".join(desc_parts)
    
    def calculate_kdj(self, stock_data_list: List[StockData]) -> Tuple[bool, str, Optional[KDJIndicator]]:
        try:
            df = self._prepare_dataframe(stock_data_list)
            
            low_min = df['low_price'].rolling(window=self.config.kdj_period).min()
            high_max = df['high_price'].rolling(window=self.config.kdj_period).max()
            
            rsv = (df['close_price'] - low_min) / (high_max - low_min) * 100
            rsv = rsv.fillna(50)
            
            k_values = pd.Series([50] * len(df))
            d_values = pd.Series([50] * len(df))
            j_values = pd.Series([50] * len(df))
            
            for i in range(1, len(df)):
                k_values.iloc[i] = (2/3) * k_values.iloc[i-1] + (1/3) * rsv.iloc[i]
                d_values.iloc[i] = (2/3) * d_values.iloc[i-1] + (1/3) * k_values.iloc[i]
                j_values.iloc[i] = 3 * k_values.iloc[i] - 2 * d_values.iloc[i]
            
            k_list = k_values.tolist()
            d_list = d_values.tolist()
            j_list = j_values.tolist()
            
            signals = self._generate_kdj_signals(k_list, d_list, j_list)
            
            description = self._generate_kdj_description(k_list[-1], d_list[-1], j_list[-1])
            
            kdj_indicator = KDJIndicator(
                k=k_list,
                d=d_list,
                j=j_list,
                signals=signals,
                description=description
            )
            
            return True, "KDJ计算成功", kdj_indicator
            
        except Exception as e:
            self.logger.error(f"KDJ计算失败: {str(e)}")
            return False, str(e), None
    
    def _generate_kdj_signals(self, k: List[float], d: List[float], j: List[float]) -> List[str]:
        signals = []
        
        for i in range(1, len(k)):
            if k[i] > d[i] and k[i-1] <= d[i-1]:
                signals.append(f"第{i}天: K线上穿D线，金叉信号")
            elif k[i] < d[i] and k[i-1] >= d[i-1]:
                signals.append(f"第{i}天: K线下穿D线，死叉信号")
            
            if k[i] > 80 and k[i-1] <= 80:
                signals.append(f"第{i}天: K线突破80，超买信号")
            elif k[i] < 20 and k[i-1] >= 20:
                signals.append(f"第{i}天: K线跌破20，超卖信号")
            
            if j[i] > 100 and j[i-1] <= 100:
                signals.append(f"第{i}天: J线突破100，严重超买")
            elif j[i] < 0 and j[i-1] >= 0:
                signals.append(f"第{i}天: J线跌破0，严重超卖")
        
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
    
    def calculate_all_indicators(self, stock_data_list: List[StockData]) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            results = {}
            
            success, msg, macd = self.calculate_macd(stock_data_list)
            if success:
                results['macd'] = macd
                self.logger.info("MACD计算成功")
            
            success, msg, rsi = self.calculate_rsi(stock_data_list)
            if success:
                results['rsi'] = rsi
                self.logger.info("RSI计算成功")
            
            success, msg, kdj = self.calculate_kdj(stock_data_list)
            if success:
                results['kdj'] = kdj
                self.logger.info("KDJ计算成功")
            
            ma_indicators = {}
            for period in self.config.ma_periods:
                df = self._prepare_dataframe(stock_data_list)
                ma_values = self.calculate_ma(df, period)
                ma_indicators[f'MA{period}'] = TechnicalIndicator(
                    name=f'MA{period}',
                    values=ma_values,
                    signals=[],
                    description=f'{period}日均线'
                )
            results['ma'] = ma_indicators
            
            return True, "技术指标计算完成", results
            
        except Exception as e:
            self.logger.error(f"技术指标计算失败: {str(e)}")
            return False, str(e), None
