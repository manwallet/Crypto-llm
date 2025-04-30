import numpy as np
import pandas as pd
from datetime import datetime

class MarketClassifier:
    """市场环境分类器，用于识别当前市场状态"""
    
    def __init__(self):
        # 趋势识别参数
        self.trend_lookback_short = 5  # 短期趋势周期
        self.trend_lookback_medium = 20  # 中期趋势周期
        self.trend_lookback_long = 50  # 长期趋势周期
        self.trend_threshold = 0.03  # 3%价格变化作为趋势阈值
        
        # 波动性识别参数
        self.volatility_lookback = 20  # 波动性计算周期
        self.high_volatility_threshold = 0.04  # 高波动性阈值
        self.low_volatility_threshold = 0.015  # 低波动性阈值
        
        # 市场状态记忆
        self.last_classification = None
        self.last_update_time = None
    
    def classify_market(self, market_data):
        """对市场进行分类"""
        if market_data is None or len(market_data) < self.trend_lookback_long:
            return {
                "trend": "unknown",
                "volatility": "unknown",
                "momentum": "unknown",
                "support_resistance": [],
                "critical_levels": []
            }
        
        # 准备数据
        close_prices = market_data['close']
        high_prices = market_data['high']
        low_prices = market_data['low']
        
        # 趋势识别
        trend = self._identify_trend(close_prices)
        
        # 波动性识别
        volatility = self._identify_volatility(close_prices)
        
        # 动量识别
        momentum = self._identify_momentum(close_prices)
        
        # 支撑阻力位识别
        support_resistance = self._identify_support_resistance(high_prices, low_prices, close_prices)
        
        # 关键价格水平
        critical_levels = self._identify_critical_levels(close_prices, high_prices, low_prices)
        
        # 更新状态
        self.last_classification = {
            "trend": trend,
            "volatility": volatility,
            "momentum": momentum,
            "support_resistance": support_resistance,
            "critical_levels": critical_levels,
            "timestamp": datetime.now()
        }
        
        return self.last_classification
    
    def _identify_trend(self, prices):
        """识别市场趋势"""
        # 计算不同周期的变化率
        short_change = (prices.iloc[-1] / prices.iloc[-self.trend_lookback_short] - 1)
        medium_change = (prices.iloc[-1] / prices.iloc[-self.trend_lookback_medium] - 1)
        long_change = (prices.iloc[-1] / prices.iloc[-self.trend_lookback_long] - 1)
        
        # 根据变化率判断趋势
        if short_change > self.trend_threshold and medium_change > 0:
            return "uptrend"
        elif short_change < -self.trend_threshold and medium_change < 0:
            return "downtrend"
        elif abs(medium_change) < self.trend_threshold / 2:
            return "sideways"
        elif short_change > 0 and medium_change > 0 and long_change > 0:
            return "strong_uptrend"
        elif short_change < 0 and medium_change < 0 and long_change < 0:
            return "strong_downtrend"
        elif short_change > 0 and medium_change < 0:
            return "pullback"
        elif short_change < 0 and medium_change > 0:
            return "correction"
        else:
            return "mixed"
    
    def _identify_volatility(self, prices):
        """识别市场波动性"""
        returns = prices.pct_change().dropna()
        volatility = returns.tail(self.volatility_lookback).std() * np.sqrt(365)
        
        if volatility > self.high_volatility_threshold:
            return "high"
        elif volatility < self.low_volatility_threshold:
            return "low"
        else:
            return "medium"
    
    def _identify_momentum(self, prices):
        """识别市场动量"""
        # 使用RSI概念识别动量
        delta = prices.diff().dropna()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(window=14).mean().iloc[-1]
        avg_loss = loss.rolling(window=14).mean().iloc[-1]
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi > 70:
            return "overbought"
        elif rsi < 30:
            return "oversold"
        elif rsi > 60:
            return "strong"
        elif rsi < 40:
            return "weak"
        else:
            return "neutral"
    
    def _identify_support_resistance(self, high_prices, low_prices, close_prices, n_levels=3):
        """识别主要支撑和阻力位"""
        support_levels = []
        resistance_levels = []
        
        # 使用过去100个周期的价格
        lookback = min(100, len(close_prices))
        
        # 查找低点作为支撑位
        for i in range(2, lookback-2):
            if low_prices.iloc[-i] < low_prices.iloc[-i-1] and low_prices.iloc[-i] < low_prices.iloc[-i-2] and \
               low_prices.iloc[-i] < low_prices.iloc[-i+1] and low_prices.iloc[-i] < low_prices.iloc[-i+2]:
                support_levels.append(low_prices.iloc[-i])
        
        # 查找高点作为阻力位
        for i in range(2, lookback-2):
            if high_prices.iloc[-i] > high_prices.iloc[-i-1] and high_prices.iloc[-i] > high_prices.iloc[-i-2] and \
               high_prices.iloc[-i] > high_prices.iloc[-i+1] and high_prices.iloc[-i] > high_prices.iloc[-i+2]:
                resistance_levels.append(high_prices.iloc[-i])
        
        # 合并相近的水平
        support_levels = self._merge_close_levels(support_levels)
        resistance_levels = self._merge_close_levels(resistance_levels)
        
        # 选择最接近当前价格的几个水平
        current_price = close_prices.iloc[-1]
        
        support_levels = sorted([(abs(level - current_price), level) for level in support_levels if level < current_price])
        resistance_levels = sorted([(abs(level - current_price), level) for level in resistance_levels if level > current_price])
        
        important_supports = [level for _, level in support_levels[:n_levels]] if support_levels else []
        important_resistances = [level for _, level in resistance_levels[:n_levels]] if resistance_levels else []
        
        return {
            "support": important_supports,
            "resistance": important_resistances
        }
    
    def _merge_close_levels(self, levels, threshold_pct=0.005):
        """合并相近的价格水平"""
        if not levels:
            return []
            
        levels = sorted(levels)
        merged_levels = []
        current_group = [levels[0]]
        
        for level in levels[1:]:
            # 如果当前水平与组内平均值相差不超过阈值，则加入组
            group_avg = sum(current_group) / len(current_group)
            if abs(level - group_avg) / group_avg < threshold_pct:
                current_group.append(level)
            else:
                # 否则，结束当前组并开始新组
                merged_levels.append(sum(current_group) / len(current_group))
                current_group = [level]
        
        # 添加最后一组
        if current_group:
            merged_levels.append(sum(current_group) / len(current_group))
        
        return merged_levels
    
    def _identify_critical_levels(self, close_prices, high_prices, low_prices):
        """识别关键价格水平"""
        # 当前价格
        current_price = close_prices.iloc[-1]
        
        # 历史高点和低点
        all_time_high = high_prices.max()
        all_time_low = low_prices.min()
        
        # 心理整数关口
        price_magnitude = 10 ** (len(str(int(current_price))) - 1)
        nearest_round_number = round(current_price / price_magnitude) * price_magnitude
        
        # 最近的成交量加权平均价
        vwap = (close_prices * market_data.get('volume', 1)).sum() / close_prices.sum()
        
        # 移动平均线
        ma20 = close_prices.rolling(window=20).mean().iloc[-1]
        ma50 = close_prices.rolling(window=50).mean().iloc[-1]
        ma200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else None
        
        critical_levels = [
            {"type": "current_price", "value": current_price},
            {"type": "all_time_high", "value": all_time_high},
            {"type": "all_time_low", "value": all_time_low},
            {"type": "psychological_level", "value": nearest_round_number},
            {"type": "vwap", "value": vwap},
            {"type": "ma20", "value": ma20},
            {"type": "ma50", "value": ma50}
        ]
        
        if ma200 is not None:
            critical_levels.append({"type": "ma200", "value": ma200})
        
        return critical_levels 