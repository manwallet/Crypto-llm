import os
from binance.client import Client
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import openai
from .prompt_manager import PromptManager

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
        self.prompt_manager = PromptManager()
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        
    def check_emergency(self):
        """检查是否存在紧急情况"""
        try:
            # 获取市场数据
            market_data = self._get_market_data()
            if market_data is None:
                return False
                
            # 获取市场上下文
            market_context = self.prompt_manager.prepare_market_context(market_data)
            
            # 获取持仓信息
            position_info = self._get_position_info()
            
            # 使用GPT评估风险
            risk_score = self._assess_risk(position_info, market_context)
            
            # 检查各种紧急情况
            volatility_emergency = self._check_volatility(market_data)
            volume_emergency = self._check_volume_surge(market_data)
            price_emergency = self._check_price_change(market_data)
            position_emergency = self._check_position_risk()
            
            # 如果任何一个检查返回True，或风险评分过高，就触发紧急情况
            is_emergency = any([
                volatility_emergency,
                volume_emergency,
                price_emergency,
                position_emergency,
                risk_score > 0.8  # 风险评分阈值
            ])
            
            if is_emergency:
                self._log_emergency({
                    'volatility_emergency': volatility_emergency,
                    'volume_emergency': volume_emergency,
                    'price_emergency': price_emergency,
                    'position_emergency': position_emergency,
                    'risk_score': risk_score
                })
                
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
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return None
            
    def _get_position_info(self):
        """获取持仓信息"""
        try:
            position = self.client.futures_position_information(symbol=self.trading_pair)[0]
            return {
                'size': float(position['positionAmt']),
                'entry_price': float(position['entryPrice']),
                'mark_price': float(position['markPrice']),
                'unrealized_pnl': float(position['unRealizedProfit']),
                'leverage': float(position['leverage']),
                'liquidation_price': float(position['liquidationPrice'])
            }
        except Exception as e:
            print(f"Error getting position information: {e}")
            return None
            
    def _assess_risk(self, position_info, market_context):
        """使用GPT评估风险"""
        try:
            if position_info is None:
                return 0
                
            # 获取风险评估提示词
            prompt = self.prompt_manager.get_risk_assessment_prompt(
                position_data=position_info,
                market_conditions=market_context
            )
            
            # 调用GPT API
            response = self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a risk management specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # 解析响应
            risk_score = float(response.choices[0].message.content.strip())
            return risk_score
            
        except Exception as e:
            print(f"Error assessing risk: {e}")
            return 0
            
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
            position = self._get_position_info()
            if position is None or position['size'] == 0:
                return False
                
            # 计算未实现盈亏百分比
            entry_value = abs(position['size'] * position['entry_price'])
            if entry_value == 0:
                return False
                
            pnl_percentage = (position['unrealized_pnl'] / entry_value) * 100
            
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
                'position_emergency': data.get('position_emergency'),
                'risk_score': data.get('risk_score', 0)
            }
            
            # 这里可以添加日志记录逻辑，比如写入文件或数据库
            print(f"Emergency detected at {timestamp}:")
            for key, value in emergency_data.items():
                if key != 'timestamp':
                    print(f"- {key}: {value}")
                    
        except Exception as e:
            print(f"Error logging emergency: {e}") 