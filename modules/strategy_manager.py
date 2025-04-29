import os
import numpy as np
import pandas as pd
from binance.client import Client
from datetime import datetime, timedelta
import talib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from dotenv import load_dotenv
from .prompt_manager import PromptManager
import openai

class StrategyManager:
    def __init__(self):
        load_dotenv()
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.model = self._build_lstm_model()
        self.scaler = MinMaxScaler()
        self.prompt_manager = PromptManager()
        
    def update_strategy(self, news_signal):
        """根据新闻信号更新策略"""
        self.latest_news_sentiment = news_signal['sentiment']
        
    def generate_signal(self):
        """生成交易信号"""
        # 获取市场数据
        klines = self._get_market_data()
        if klines is None:
            return None
            
        # 准备图表上下文
        chart_context = self.prompt_manager.prepare_chart_context(klines)
        
        # 计算技术指标
        tech_signals = self._calculate_technical_indicators(klines)
        
        # 使用LSTM预测
        lstm_prediction = self._make_lstm_prediction(klines)
        
        # 获取市场上下文
        market_context = self.prompt_manager.prepare_market_context(klines)
        
        # 使用GPT分析图表
        chart_signal = self._analyze_chart(chart_context)
        
        # 综合分析所有信号
        final_signal = self._combine_signals(tech_signals, lstm_prediction, chart_signal)
        
        return final_signal
        
    def _get_market_data(self):
        """获取市场数据"""
        try:
            # 获取最近500根K线数据
            klines = self.client.futures_klines(
                symbol=self.trading_pair,
                interval=Client.KLINE_INTERVAL_15MINUTE,
                limit=500
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
            print(f"Error fetching market data: {e}")
            return None
            
    def _analyze_chart(self, chart_context):
        """使用GPT分析图表"""
        try:
            # 获取图表分析提示词
            prompt = self.prompt_manager.get_chart_analysis_prompt(
                chart_data=chart_context,
                timeframe="15m"
            )
            
            # 调用GPT API
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert technical analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # 解析响应
            signal = float(response.choices[0].message.content.strip())
            return signal
            
        except Exception as e:
            print(f"Error analyzing chart: {e}")
            return 0
            
    def _calculate_technical_indicators(self, df):
        """计算技术指标"""
        try:
            close_prices = df['close'].values
            high_prices = df['high'].values
            low_prices = df['low'].values
            
            # 计算各种技术指标
            macd, macd_signal, _ = talib.MACD(close_prices)
            rsi = talib.RSI(close_prices)
            slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices)
            
            # 布林带
            upper, middle, lower = talib.BBANDS(close_prices)
            
            # 计算信号
            macd_signal = 1 if macd[-1] > macd_signal[-1] else -1
            rsi_signal = 1 if rsi[-1] < 30 else -1 if rsi[-1] > 70 else 0
            stoch_signal = 1 if slowk[-1] < 20 else -1 if slowk[-1] > 80 else 0
            bb_signal = 1 if close_prices[-1] < lower[-1] else -1 if close_prices[-1] > upper[-1] else 0
            
            return {
                'macd': macd_signal,
                'rsi': rsi_signal,
                'stoch': stoch_signal,
                'bb': bb_signal
            }
            
        except Exception as e:
            print(f"Error calculating technical indicators: {e}")
            return None
            
    def _make_lstm_prediction(self, df):
        """使用LSTM模型进行预测"""
        try:
            # 准备数据
            data = df[['open', 'high', 'low', 'close', 'volume']].values
            scaled_data = self.scaler.fit_transform(data)
            
            # 创建预测用的数据窗口
            X_pred = []
            for i in range(len(scaled_data) - 60):
                X_pred.append(scaled_data[i:(i + 60)])
            X_pred = np.array(X_pred)
            
            # 进行预测
            pred = self.model.predict(X_pred[-1:], verbose=0)
            pred = self.scaler.inverse_transform(np.concatenate([X_pred[-1, -1, :-1], pred], axis=1))
            
            # 计算预测信号
            current_price = df['close'].iloc[-1]
            predicted_price = pred[0, -1]
            
            return 1 if predicted_price > current_price else -1
            
        except Exception as e:
            print(f"Error making LSTM prediction: {e}")
            return 0
            
    def _combine_signals(self, tech_signals, lstm_signal, chart_signal):
        """综合所有信号"""
        if tech_signals is None:
            return None
            
        # 计算技术指标的综合得分
        tech_score = sum([
            tech_signals['macd'] * 0.3,
            tech_signals['rsi'] * 0.2,
            tech_signals['stoch'] * 0.2,
            tech_signals['bb'] * 0.3
        ])
        
        # 综合所有信号
        final_score = (
            tech_score * 0.3 +  # 技术指标权重
            getattr(self, 'latest_news_sentiment', 0) * 0.2 +  # 新闻情绪权重
            lstm_signal * 0.2 +  # LSTM预测权重
            chart_signal * 0.3  # GPT图表分析权重
        )
        
        # 生成交易信号
        if abs(final_score) < 0.2:  # 信号不够强烈
            return None
            
        return {
            'timestamp': datetime.now(),
            'action': 'buy' if final_score > 0 else 'sell',
            'confidence': abs(final_score),
            'source': 'strategy',
            'score_details': {
                'technical': tech_score,
                'news': getattr(self, 'latest_news_sentiment', 0),
                'lstm': lstm_signal,
                'chart': chart_signal
            }
        }
        
    def _build_lstm_model(self):
        """构建LSTM模型"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(60, 5)),
            LSTM(50, return_sequences=False),
            Dense(25),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model 