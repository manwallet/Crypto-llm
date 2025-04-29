import os
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import openai
from dotenv import load_dotenv

class NewsAnalyzer:
    def __init__(self):
        load_dotenv()
        self.newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.base_currency = self.trading_pair[:3]  # 获取基础货币（如BTC）
        
    def analyze(self):
        """分析新闻并返回交易信号"""
        # 获取最近30分钟的加密货币新闻
        news = self._fetch_recent_news()
        if not news:
            return None
            
        # 使用GPT分析新闻情绪
        sentiment = self._analyze_sentiment(news)
        
        return {
            'timestamp': datetime.now(),
            'sentiment': sentiment,
            'source': 'news',
            'data': news
        }
        
    def _fetch_recent_news(self):
        """获取最近的相关新闻"""
        try:
            # 设置时间范围为过去30分钟
            to_time = datetime.now()
            from_time = to_time - timedelta(minutes=30)
            
            # 获取与交易对相关的新闻
            response = self.newsapi.get_everything(
                q=f"{self.base_currency} OR Bitcoin OR Cryptocurrency",
                language='en',
                sort_by='publishedAt',
                from_param=from_time.isoformat(),
                to=to_time.isoformat()
            )
            
            if response['status'] == 'ok' and response['articles']:
                return response['articles']
            return None
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return None
            
    def _analyze_sentiment(self, news):
        """使用GPT分析新闻情绪"""
        try:
            # 准备新闻文本
            news_text = "\n".join([
                f"Title: {article['title']}\nDescription: {article['description']}"
                for article in news[:5]  # 只分析最新的5条新闻
            ])
            
            # 创建GPT提示
            prompt = f"""Analyze the sentiment of the following cryptocurrency news regarding {self.base_currency}. 
            Rate the overall market sentiment on a scale from -1 (extremely bearish) to 1 (extremely bullish).
            Consider the impact on short-term price movements.
            
            News:
            {news_text}
            
            Please provide only the numerical sentiment score.
            """
            
            # 调用GPT API
            response = self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cryptocurrency market analyst."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 解析响应
            sentiment_score = float(response.choices[0].message.content.strip())
            return max(min(sentiment_score, 1), -1)  # 确保分数在 -1 到 1 之间
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return 0  # 出错时返回中性分数 