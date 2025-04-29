import os
from datetime import datetime

class PromptManager:
    @staticmethod
    def get_news_analysis_prompt(news_text, base_currency):
        """获取新闻分析提示词"""
        return f"""You are a professional cryptocurrency market analyst.
        Your task is to analyze the sentiment and potential market impact of recent news.
        
        Focus on:
        1. Market sentiment (bullish/bearish)
        2. Potential price impact
        3. Timeframe of the impact
        4. Reliability of the news sources
        
        News about {base_currency}:
        {news_text}
        
        Rate the overall market sentiment on a scale from -1 (extremely bearish) to 1 (extremely bullish).
        Consider only short-term price movements (next 24 hours).
        
        Provide only the numerical score without any explanation."""

    @staticmethod
    def get_chart_analysis_prompt(chart_data, timeframe="15m"):
        """获取图表分析提示词"""
        return f"""You are an expert technical analyst for cryptocurrency markets.
        Analyze the following price chart data and provide a trading signal.
        
        Timeframe: {timeframe}
        
        Consider these factors:
        1. Trend direction and strength
        2. Support/resistance levels
        3. Volume patterns
        4. Price action patterns
        5. Market structure
        
        Chart data summary:
        {chart_data}
        
        Provide a trading signal as one of:
        1 (strong buy)
        0.5 (weak buy)
        0 (neutral)
        -0.5 (weak sell)
        -1 (strong sell)
        
        Return only the numerical signal."""

    @staticmethod
    def get_risk_assessment_prompt(position_data, market_conditions):
        """获取风险评估提示词"""
        return f"""You are a risk management specialist for cryptocurrency trading.
        Analyze the current position and market conditions to assess risk level.
        
        Position details:
        {position_data}
        
        Market conditions:
        {market_conditions}
        
        Consider:
        1. Position size relative to account
        2. Current profit/loss
        3. Market volatility
        4. Distance to liquidation
        5. Overall market trend
        
        Rate the risk level from 0 (safe) to 1 (extreme risk).
        Provide only the numerical risk score."""

    @staticmethod
    def prepare_chart_context(df, lookback_bars=None):
        """准备图表数据上下文"""
        if lookback_bars is None:
            # 让模型自己决定要看多少根K线
            recent_volatility = df['close'].pct_change().std()
            if recent_volatility > 0.02:  # 高波动性
                lookback_bars = 50  # 看更多K线
            elif recent_volatility > 0.01:  # 中等波动性
                lookback_bars = 30
            else:  # 低波动性
                lookback_bars = 20

        # 获取最近的K线数据
        recent_data = df.tail(lookback_bars)
        
        # 计算关键统计数据
        summary = {
            'start_time': recent_data.index[0],
            'end_time': recent_data.index[-1],
            'open': recent_data['open'].iloc[0],
            'close': recent_data['close'].iloc[-1],
            'high': recent_data['high'].max(),
            'low': recent_data['low'].min(),
            'volume': recent_data['volume'].sum(),
            'price_change': (recent_data['close'].iloc[-1] / recent_data['open'].iloc[0] - 1) * 100,
            'volatility': recent_data['close'].pct_change().std() * 100,
            'volume_profile': recent_data['volume'].describe().to_dict()
        }
        
        # 识别关键价格水平
        levels = {
            'recent_highs': recent_data.nlargest(3, 'high')['high'].tolist(),
            'recent_lows': recent_data.nsmallest(3, 'low')['low'].tolist(),
            'volume_weighted_price': (recent_data['close'] * recent_data['volume']).sum() / recent_data['volume'].sum()
        }
        
        return {
            'summary': summary,
            'levels': levels,
            'data_points': len(recent_data),
            'timestamp': datetime.now()
        }

    @staticmethod
    def prepare_news_context(news_articles, max_articles=5):
        """准备新闻数据上下文"""
        # 按重要性和时间排序
        sorted_news = sorted(
            news_articles,
            key=lambda x: (x.get('publishedAt', ''), len(x.get('title', ''))),
            reverse=True
        )[:max_articles]
        
        # 提取关键信息
        processed_news = []
        for article in sorted_news:
            processed_news.append({
                'title': article.get('title', ''),
                'summary': article.get('description', '')[:200],  # 限制长度
                'source': article.get('source', {}).get('name', 'Unknown'),
                'time': article.get('publishedAt', '')
            })
        
        return processed_news

    @staticmethod
    def prepare_market_context(market_data):
        """准备市场数据上下文"""
        return {
            'current_price': market_data['close'].iloc[-1],
            'price_change_1h': (market_data['close'].iloc[-1] / market_data['close'].iloc[-60] - 1) * 100,
            'price_change_24h': (market_data['close'].iloc[-1] / market_data['close'].iloc[-1440] - 1) * 100,
            'volume_change': (market_data['volume'].tail(60).mean() / market_data['volume'].tail(1440).mean() - 1) * 100,
            'volatility_1h': market_data['close'].tail(60).pct_change().std() * 100,
            'volatility_24h': market_data['close'].tail(1440).pct_change().std() * 100
        } 