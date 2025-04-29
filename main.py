import os
import time
import schedule
import threading
from datetime import datetime
from dotenv import load_dotenv

from modules.news_analyzer import NewsAnalyzer
from modules.strategy_manager import StrategyManager
from modules.trade_executor import TradeExecutor
from modules.emergency_manager import EmergencyManager
from modules.position_manager import PositionManager

class TradingBot:
    def __init__(self):
        load_dotenv()
        
        # 初始化各个模块
        self.news_analyzer = NewsAnalyzer()
        self.strategy_manager = StrategyManager()
        self.trade_executor = TradeExecutor()
        self.emergency_manager = EmergencyManager()
        self.position_manager = PositionManager()
        
        # 获取配置
        self.news_interval = int(os.getenv('NEWS_CHECK_INTERVAL', 30))
        self.strategy_interval = int(os.getenv('STRATEGY_UPDATE_INTERVAL', 15))
        self.emergency_interval = int(os.getenv('EMERGENCY_CHECK_INTERVAL', 5))
        
    def start(self):
        print(f"Trading bot started at {datetime.now()}")
        
        # 设置定时任务
        schedule.every(self.news_interval).minutes.do(self.news_analysis_job)
        schedule.every(self.strategy_interval).minutes.do(self.strategy_update_job)
        schedule.every(self.emergency_interval).minutes.do(self.emergency_check_job)
        
        # 启动定时任务线程
        threading.Thread(target=self.run_schedule, daemon=True).start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down the trading bot...")
    
    def run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def news_analysis_job(self):
        """新闻分析任务"""
        try:
            news_signal = self.news_analyzer.analyze()
            if news_signal:
                self.strategy_manager.update_strategy(news_signal)
        except Exception as e:
            print(f"Error in news analysis: {e}")
    
    def strategy_update_job(self):
        """策略更新任务"""
        try:
            strategy_signal = self.strategy_manager.generate_signal()
            if strategy_signal:
                self.trade_executor.execute_trade(strategy_signal)
        except Exception as e:
            print(f"Error in strategy update: {e}")
    
    def emergency_check_job(self):
        """应急检查任务"""
        try:
            if self.emergency_manager.check_emergency():
                self.position_manager.close_all_positions()
        except Exception as e:
            print(f"Error in emergency check: {e}")

if __name__ == "__main__":
    bot = TradingBot()
    bot.start() 