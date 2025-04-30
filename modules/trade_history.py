import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class TradeHistory:
    def __init__(self, history_dir="logs"):
        self.history_dir = history_dir
        self.trades_file = f"{history_dir}/trade_history.json"
        self.trades = self._load_history()
        
    def _load_history(self):
        """加载交易历史记录"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"加载交易历史时出错: {e}")
            return []
    
    def save_history(self):
        """保存交易历史记录"""
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                json.dump(self.trades, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存交易历史时出错: {e}")
    
    def add_trade(self, trade_data):
        """添加新的交易记录"""
        trade = {
            "timestamp": str(datetime.now()),
            "trade_id": len(self.trades) + 1,
            "data": trade_data
        }
        self.trades.append(trade)
        self.save_history()
        return trade["trade_id"]
    
    def update_trade_result(self, trade_id, result_data):
        """更新交易结果"""
        for trade in self.trades:
            if trade.get("trade_id") == trade_id:
                trade["result"] = result_data
                trade["updated_at"] = str(datetime.now())
                self.save_history()
                return True
        return False
    
    def get_recent_trades(self, days=7):
        """获取最近一段时间的交易记录"""
        recent_trades = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for trade in self.trades:
            try:
                trade_date = datetime.fromisoformat(trade["timestamp"])
                if trade_date >= cutoff_date:
                    recent_trades.append(trade)
            except:
                continue
                
        return recent_trades
    
    def calculate_performance_metrics(self, days=30):
        """计算交易表现指标"""
        recent_trades = self.get_recent_trades(days)
        if not recent_trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "max_profit": 0,
                "max_loss": 0,
                "profit_factor": 0,
                "success_by_direction": {"long": 0, "short": 0}
            }
            
        # 初始化计数器
        total_trades = len(recent_trades)
        winning_trades = 0
        total_profit = 0
        total_loss = 0
        profits = []
        long_wins = 0
        long_total = 0
        short_wins = 0
        short_total = 0
        
        # 分析交易
        for trade in recent_trades:
            if "result" not in trade:
                continue
                
            result = trade["result"]
            profit = result.get("profit", 0)
            profits.append(profit)
            
            if profit > 0:
                winning_trades += 1
                total_profit += profit
            else:
                total_loss += abs(profit)
            
            # 按方向分析
            direction = trade["data"].get("action", "")
            if "多" in direction or direction == "开多":
                long_total += 1
                if profit > 0:
                    long_wins += 1
            elif "空" in direction or direction == "开空":
                short_total += 1
                if profit > 0:
                    short_wins += 1
        
        # 计算指标
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_profit = sum(profits) / len(profits) if profits else 0
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        long_win_rate = long_wins / long_total if long_total > 0 else 0
        short_win_rate = short_wins / short_total if short_total > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "profit_factor": profit_factor,
            "success_by_direction": {
                "long": long_win_rate,
                "short": short_win_rate
            }
        }
    
    def analyze_market_conditions(self, recent_trades=None):
        """分析不同市场条件下的表现"""
        if recent_trades is None:
            recent_trades = self.get_recent_trades(30)
            
        if not recent_trades:
            return {"trend": {}, "volatility": {}}
            
        # 按照市场条件分类
        trend_markets = {"uptrend": [], "downtrend": [], "sideways": []}
        volatility_markets = {"high": [], "medium": [], "low": []}
        
        for trade in recent_trades:
            if "data" not in trade or "result" not in trade:
                continue
                
            # 获取市场条件标签
            market_conditions = trade.get("data", {}).get("market_conditions", {})
            trend = market_conditions.get("trend", "unknown")
            volatility = market_conditions.get("volatility", "unknown")
            
            # 添加到对应类别
            profit = trade["result"].get("profit", 0)
            if trend in trend_markets:
                trend_markets[trend].append(profit)
            
            if volatility in volatility_markets:
                volatility_markets[volatility].append(profit)
        
        # 计算每种市场条件下的表现
        trend_performance = {}
        for trend, profits in trend_markets.items():
            if profits:
                win_rate = sum(1 for p in profits if p > 0) / len(profits)
                avg_profit = sum(profits) / len(profits)
                trend_performance[trend] = {
                    "trades": len(profits),
                    "win_rate": win_rate,
                    "avg_profit": avg_profit
                }
        
        volatility_performance = {}
        for vol, profits in volatility_markets.items():
            if profits:
                win_rate = sum(1 for p in profits if p > 0) / len(profits)
                avg_profit = sum(profits) / len(profits)
                volatility_performance[vol] = {
                    "trades": len(profits),
                    "win_rate": win_rate,
                    "avg_profit": avg_profit
                }
        
        return {
            "trend": trend_performance,
            "volatility": volatility_performance
        }
    
    def get_performance_summary(self):
        """获取性能总结文本"""
        metrics = self.calculate_performance_metrics()
        market_analysis = self.analyze_market_conditions()
        
        summary = f"""交易表现摘要（最近30天）:
总交易次数: {metrics['total_trades']}
胜率: {metrics['win_rate']:.2%}
平均利润: {metrics['avg_profit']:.2f}
最大盈利: {metrics['max_profit']:.2f}
最大亏损: {metrics['max_loss']:.2f}
盈亏比: {metrics['profit_factor']:.2f}

方向表现:
多头胜率: {metrics['success_by_direction']['long']:.2%}
空头胜率: {metrics['success_by_direction']['short']:.2%}

不同市场条件下的表现:
"""
        
        # 添加趋势市场表现
        if market_analysis["trend"]:
            summary += "趋势市场:\n"
            for trend, data in market_analysis["trend"].items():
                if data["trades"] > 0:
                    summary += f"- {trend}: 胜率 {data['win_rate']:.2%}, 平均利润 {data['avg_profit']:.2f} ({data['trades']}笔交易)\n"
        
        # 添加波动性市场表现
        if market_analysis["volatility"]:
            summary += "\n波动性市场:\n"
            for vol, data in market_analysis["volatility"].items():
                if data["trades"] > 0:
                    summary += f"- {vol}: 胜率 {data['win_rate']:.2%}, 平均利润 {data['avg_profit']:.2f} ({data['trades']}笔交易)\n"
        
        return summary 