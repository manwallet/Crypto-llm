import os
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import openai
from dotenv import load_dotenv
from .prompt_manager import PromptManager

class NewsAnalyzer:
    def __init__(self):
        load_dotenv()
        self.newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.base_currency = self.trading_pair[:3]  # 获取基础货币（如BTC）
        self.prompt_manager = PromptManager()
        
    def analyze(self):
        """分析新闻并返回交易信号"""
        # 获取最近新闻
        news = self._fetch_recent_news()
        if not news:
            return None
            
        # 准备新闻上下文
        processed_news = self.prompt_manager.prepare_news_context(news)
        
        # 使用GPT分析新闻情绪
        sentiment = self._analyze_sentiment(processed_news)
        
        return {
            'timestamp': datetime.now(),
            'sentiment': sentiment,
            'source': 'news',
            'data': processed_news
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
            
    def _analyze_sentiment(self, processed_news):
        """使用GPT分析新闻情绪"""
        try:
            # 准备新闻文本
            news_text = "\n\n".join([
                f"Source: {article['source']}\n"
                f"Time: {article['time']}\n"
                f"Title: {article['title']}\n"
                f"Summary: {article['summary']}"
                for article in processed_news
            ])
            
            # 获取分析提示词
            prompt = self.prompt_manager.get_news_analysis_prompt(news_text, self.base_currency)
            
            # 调用GPT API
            response = self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cryptocurrency market analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # 降低温度以获得更一致的输出
            )
            
            # 解析响应
            sentiment_score = float(response.choices[0].message.content.strip())
            return max(min(sentiment_score, 1), -1)  # 确保分数在 -1 到 1 之间
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return 0  # 出错时返回中性分数 