import os
from binance.client import Client
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

class EmergencyManager:
    def __init__(self):
        load_dotenv()
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.volatility_threshold = 5.0  # 5% 波动率阈值
        self.volume_surge_threshold = 3.0  # 3倍交易量突增阈值
        self.price_change_threshold = 3.0  # 3% 价格变化阈值
        self.liquidation_threshold = -15.0  # -15% 未实现盈亏阈值
        
    def check_emergency(self):
        """检查是否存在紧急情况"""
        try:
            # 获取市场数据
            market_data = self._get_market_data()
            if market_data is None:
                return False
                
            # 检查各种紧急情况
            volatility_emergency = self._check_volatility(market_data)
            volume_emergency = self._check_volume_surge(market_data)
            price_emergency = self._check_price_change(market_data)
            position_emergency = self._check_position_risk()
            
            # 如果任何一个检查返回True，就触发紧急情况
            is_emergency = any([
                volatility_emergency,
                volume_emergency,
                price_emergency,
                position_emergency
            ])
            
            if is_emergency:
                self._log_emergency(locals())
                
            return is_emergency
            
        except Exception as e:
            print(f"Error checking emergency: {e}")
            return False
            
    def _get_market_data(self):
        """获取市场数据"""
        try:
            # 获取最近100根1分钟K线
            klines = self.client.futures_klines(
                symbol=self.trading_pair,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=100
            )
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 转换数据类型
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return None
            
    def _check_volatility(self, df):
        """检查波动率"""
        try:
            # 计算最近20分钟的波动率
            recent_data = df.tail(20)
            returns = np.log(recent_data['close'] / recent_data['close'].shift(1))
            volatility = returns.std() * np.sqrt(20) * 100  # 年化并转换为百分比
            
            return volatility > self.volatility_threshold
            
        except Exception as e:
            print(f"Error checking volatility: {e}")
            return False
            
    def _check_volume_surge(self, df):
        """检查交易量突增"""
        try:
            # 计算最近5分钟的平均交易量
            recent_volume = df.tail(5)['volume'].mean()
            # 计算前15分钟的平均交易量
            previous_volume = df.iloc[-20:-5]['volume'].mean()
            
            # 计算交易量增长倍数
            volume_multiplier = recent_volume / previous_volume if previous_volume > 0 else 0
            
            return volume_multiplier > self.volume_surge_threshold
            
        except Exception as e:
            print(f"Error checking volume surge: {e}")
            return False
            
    def _check_price_change(self, df):
        """检查价格剧烈变化"""
        try:
            # 计算最近5分钟的价格变化百分比
            recent_price_change = (
                (df['close'].iloc[-1] - df['close'].iloc[-5]) /
                df['close'].iloc[-5] * 100
            )
            
            return abs(recent_price_change) > self.price_change_threshold
            
        except Exception as e:
            print(f"Error checking price change: {e}")
            return False
            
    def _check_position_risk(self):
        """检查持仓风险"""
        try:
            # 获取当前持仓信息
            position = self.client.futures_position_information(symbol=self.trading_pair)[0]
            
            # 计算未实现盈亏百分比
            entry_price = float(position['entryPrice'])
            position_size = float(position['positionAmt'])
            unrealized_pnl = float(position['unRealizedProfit'])
            
            if entry_price == 0 or position_size == 0:
                return False
                
            # 计算未实现盈亏百分比
            pnl_percentage = (unrealized_pnl / (abs(position_size) * entry_price)) * 100
            
            return pnl_percentage < self.liquidation_threshold
            
        except Exception as e:
            print(f"Error checking position risk: {e}")
            return False
            
    def _log_emergency(self, data):
        """记录紧急情况"""
        try:
            timestamp = datetime.now()
            emergency_data = {
                'timestamp': timestamp,
                'trading_pair': self.trading_pair,
                'volatility_emergency': data.get('volatility_emergency'),
                'volume_emergency': data.get('volume_emergency'),
                'price_emergency': data.get('price_emergency'),
                'position_emergency': data.get('position_emergency')
            }
            
            # 这里可以添加日志记录逻辑，比如写入文件或数据库
            print(f"Emergency detected at {timestamp}:")
            for key, value in emergency_data.items():
                if key != 'timestamp':
                    print(f"- {key}: {value}")
                    
        except Exception as e:
            print(f"Error logging emergency: {e}") 