import os
import time
import schedule
import threading
import json
from datetime import datetime
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *

from modules.llm_agent_manager import LLMAgentManager
from modules.position_manager import PositionManager
from modules.prompt_manager import PromptManager

class LLMTrader:
    def __init__(self):
        load_dotenv()
        
        # 初始化币安客户端
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        
        # 初始化模块
        self.llm_agent = LLMAgentManager()
        self.position_manager = PositionManager()
        self.prompt_manager = PromptManager()
        
        # 获取配置
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.strategy_interval = int(os.getenv('STRATEGY_UPDATE_INTERVAL', 15))
        self.emergency_interval = int(os.getenv('EMERGENCY_CHECK_INTERVAL', 5))
        self.leverage = int(os.getenv('LEVERAGE', '5'))
        
        # 设置杠杆
        self.client.futures_change_leverage(
            symbol=self.trading_pair,
            leverage=self.leverage
        )
        
        # 日志目录
        self.log_dir = 'logs'
        os.makedirs(self.log_dir, exist_ok=True)
        
    def start(self):
        print(f"AI语言模型交易系统启动于 {datetime.now()}")
        print(f"交易对: {self.trading_pair}, 杠杆: {self.leverage}倍")
        
        # 设置定时任务
        schedule.every(self.strategy_interval).minutes.do(self.strategy_update_job)
        schedule.every(self.emergency_interval).minutes.do(self.emergency_check_job)
        
        # 启动定时任务线程
        threading.Thread(target=self.run_schedule, daemon=True).start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在关闭交易系统...")
    
    def run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def get_market_data(self):
        """获取市场数据"""
        try:
            # 获取最近500根K线数据
            klines = self.client.futures_klines(
                symbol=self.trading_pair,
                interval=Client.KLINE_INTERVAL_15MINUTE,
                limit=500
            )
            
            # 转换为DataFrame
            import pandas as pd
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
            print(f"获取市场数据时出错: {e}")
            return None
    
    def strategy_update_job(self):
        """策略更新任务"""
        try:
            print(f"\n===== 策略更新任务开始: {datetime.now()} =====")
            
            # 获取市场数据
            market_data = self.get_market_data()
            if market_data is None:
                print("无法获取市场数据，跳过本次策略更新")
                return
                
            # 获取当前持仓
            position_info = self.position_manager.get_position_info()
            
            # 多代理协作分析与决策过程
            # 1. 市场分析
            print("1. 市场分析中...")
            analysis_result = self.llm_agent.analyze_market(market_data)
            
            # 2. 提出交易策略
            print("2. 生成交易策略中...")
            strategy_result = self.llm_agent.suggest_strategy(analysis_result, position_info)
            
            # 3. 评估风险
            print("3. 风险评估中...")
            risk_result = self.llm_agent.evaluate_risk(strategy_result, position_info)
            
            # 4. 最终决策
            print("4. 制定最终决策中...")
            decision_result = self.llm_agent.make_final_decision(
                risk_result, 
                analysis_result["market_data"], 
                position_info
            )
            
            # 5. 执行交易
            print("5. 执行交易决策...")
            self.execute_decision(decision_result["decision"])
            
            # 记录决策过程
            self.log_decision_process(
                analysis_result, 
                strategy_result, 
                risk_result, 
                decision_result
            )
            
            print(f"===== 策略更新任务完成: {datetime.now()} =====\n")
            
        except Exception as e:
            print(f"策略更新任务出错: {e}")
    
    def emergency_check_job(self):
        """应急检查任务"""
        try:
            # 获取市场数据
            market_data = self.get_market_data()
            if market_data is None:
                return
                
            # 获取当前持仓
            position_info = self.position_manager.get_position_info()
            if position_info is None or position_info['size'] == 0:
                return  # 无持仓，无需紧急检查
                
            # 应急评估
            emergency_result = self.llm_agent.check_emergency(market_data, position_info)
            
            if emergency_result.get("is_emergency", False):
                print(f"\n===== 紧急情况检测: {datetime.now()} =====")
                print(f"紧急原因: {emergency_result.get('reason')}")
                print(f"建议操作: {emergency_result.get('action')}")
                print(f"紧急程度: {emergency_result.get('urgency')}/10")
                
                # 记录紧急情况
                self.log_emergency(emergency_result)
                
                # 执行紧急操作
                if emergency_result.get('action') == "平仓":
                    print("执行紧急平仓...")
                    self.position_manager.close_all_positions()
                elif emergency_result.get('action') == "调整止损":
                    # 这里可以实现调整止损的逻辑
                    print("紧急调整止损位...")
                
                print(f"===== 紧急操作完成: {datetime.now()} =====\n")
                
        except Exception as e:
            print(f"应急检查任务出错: {e}")
    
    def execute_decision(self, decision):
        """执行交易决策"""
        try:
            action = decision.get("action", "观望")
            price = decision.get("price", "market")
            quantity = decision.get("quantity", "0")
            stop_loss = decision.get("stop_loss", "0")
            take_profit = decision.get("take_profit", "0")
            confidence = decision.get("confidence", "0")
            reason = decision.get("reason", "无理由")
            
            print(f"交易决策:")
            print(f"- 操作: {action}")
            print(f"- 价格: {price}")
            print(f"- 数量: {quantity}")
            print(f"- 止损: {stop_loss}")
            print(f"- 止盈: {take_profit}")
            print(f"- 置信度: {confidence}/10")
            print(f"- 理由: {reason}")
            
            # 检查是否需要执行交易
            if action == "观望":
                print("决定观望，不执行交易")
                return
                
            # 处理数量
            try:
                if isinstance(quantity, str) and "%" in quantity:
                    # 处理百分比
                    percent = float(quantity.replace("%", "")) / 100
                    # 这里需要根据账户余额计算具体数量
                    account_info = self.client.futures_account()
                    balance = float(account_info['totalWalletBalance'])
                    # 计算数量，假设是USDT本位合约
                    current_price = float(self.client.futures_symbol_ticker(symbol=self.trading_pair)['price'])
                    quantity = (balance * percent * self.leverage) / current_price
                    # 四舍五入到适当的精度
                    quantity = self._adjust_quantity_precision(quantity)
                else:
                    quantity = float(quantity)
                    quantity = self._adjust_quantity_precision(quantity)
            except:
                print(f"无法处理数量: {quantity}，默认使用最小数量")
                quantity = self._get_min_quantity()
            
            # 执行交易
            if action == "开多":
                self._open_long_position(price, quantity, stop_loss, take_profit)
            elif action == "开空":
                self._open_short_position(price, quantity, stop_loss, take_profit)
            elif action == "平仓":
                self.position_manager.close_all_positions()
                
        except Exception as e:
            print(f"执行交易决策时出错: {e}")
    
    def _adjust_quantity_precision(self, quantity):
        """调整数量精度"""
        try:
            exchange_info = self.client.futures_exchange_info()
            symbol_info = next(item for item in exchange_info['symbols'] if item['symbol'] == self.trading_pair)
            quantity_precision = symbol_info['quantityPrecision']
            return round(quantity, quantity_precision)
        except:
            return round(quantity, 4)  # 默认精度
            
    def _get_min_quantity(self):
        """获取最小下单数量"""
        try:
            exchange_info = self.client.futures_exchange_info()
            symbol_info = next(item for item in exchange_info['symbols'] if item['symbol'] == self.trading_pair)
            filters = symbol_info['filters']
            lot_size_filter = next(filter for filter in filters if filter['filterType'] == 'LOT_SIZE')
            return float(lot_size_filter['minQty'])
        except:
            return 0.001  # 默认最小数量
    
    def _open_long_position(self, price, quantity, stop_loss, take_profit):
        """开多仓"""
        try:
            # 获取当前价格
            current_price = float(self.client.futures_symbol_ticker(symbol=self.trading_pair)['price'])
            
            # 判断是否市价单
            if price == "market" or isinstance(price, str) and ("市价" in price or "现价" in price):
                # 市价开多
                order = self.client.futures_create_order(
                    symbol=self.trading_pair,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )
                print(f"市价开多成功: {quantity} {self.trading_pair}")
                entry_price = current_price  # 大约的入场价
            else:
                # 限价开多
                try:
                    price = float(price)
                except:
                    print(f"无法处理价格: {price}，使用当前市价")
                    price = current_price
                
                order = self.client.futures_create_order(
                    symbol=self.trading_pair,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    price=price
                )
                print(f"限价开多成功: {quantity} {self.trading_pair} @ {price}")
                entry_price = price
            
            # 设置止损
            try:
                stop_loss = float(stop_loss)
                if stop_loss > 0:
                    self.client.futures_create_order(
                        symbol=self.trading_pair,
                        side=SIDE_SELL,
                        type=ORDER_TYPE_STOP_MARKET,
                        stopPrice=stop_loss,
                        closePosition=True,
                        workingType='MARK_PRICE'
                    )
                    print(f"已设置止损: {stop_loss}")
            except:
                print(f"无法设置止损: {stop_loss}")
            
            # 设置止盈
            try:
                take_profit = float(take_profit)
                if take_profit > 0:
                    self.client.futures_create_order(
                        symbol=self.trading_pair,
                        side=SIDE_SELL,
                        type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                        stopPrice=take_profit,
                        closePosition=True,
                        workingType='MARK_PRICE'
                    )
                    print(f"已设置止盈: {take_profit}")
            except:
                print(f"无法设置止盈: {take_profit}")
                
        except Exception as e:
            print(f"开多仓时出错: {e}")
    
    def _open_short_position(self, price, quantity, stop_loss, take_profit):
        """开空仓"""
        try:
            # 获取当前价格
            current_price = float(self.client.futures_symbol_ticker(symbol=self.trading_pair)['price'])
            
            # 判断是否市价单
            if price == "market" or isinstance(price, str) and ("市价" in price or "现价" in price):
                # 市价开空
                order = self.client.futures_create_order(
                    symbol=self.trading_pair,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )
                print(f"市价开空成功: {quantity} {self.trading_pair}")
                entry_price = current_price  # 大约的入场价
            else:
                # 限价开空
                try:
                    price = float(price)
                except:
                    print(f"无法处理价格: {price}，使用当前市价")
                    price = current_price
                
                order = self.client.futures_create_order(
                    symbol=self.trading_pair,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    price=price
                )
                print(f"限价开空成功: {quantity} {self.trading_pair} @ {price}")
                entry_price = price
            
            # 设置止损
            try:
                stop_loss = float(stop_loss)
                if stop_loss > 0:
                    self.client.futures_create_order(
                        symbol=self.trading_pair,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_STOP_MARKET,
                        stopPrice=stop_loss,
                        closePosition=True,
                        workingType='MARK_PRICE'
                    )
                    print(f"已设置止损: {stop_loss}")
            except:
                print(f"无法设置止损: {stop_loss}")
            
            # 设置止盈
            try:
                take_profit = float(take_profit)
                if take_profit > 0:
                    self.client.futures_create_order(
                        symbol=self.trading_pair,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                        stopPrice=take_profit,
                        closePosition=True,
                        workingType='MARK_PRICE'
                    )
                    print(f"已设置止盈: {take_profit}")
            except:
                print(f"无法设置止盈: {take_profit}")
                
        except Exception as e:
            print(f"开空仓时出错: {e}")
    
    def log_decision_process(self, analysis_result, strategy_result, risk_result, decision_result):
        """记录决策过程"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"{self.log_dir}/decision_{timestamp}.json"
            
            log_data = {
                "timestamp": str(datetime.now()),
                "trading_pair": self.trading_pair,
                "market_data": {
                    "current_price": analysis_result["market_data"]["current_price"],
                    "price_change_24h": analysis_result["market_data"]["price_change_24h"],
                    "volatility_24h": analysis_result["market_data"]["volatility_24h"]
                },
                "analysis": analysis_result["analysis"],
                "strategy": strategy_result["strategy"],
                "risk_assessment": risk_result["risk_assessment"],
                "final_decision": decision_result["decision"]
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"记录决策过程时出错: {e}")
    
    def log_emergency(self, emergency_result):
        """记录紧急情况"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"{self.log_dir}/emergency_{timestamp}.json"
            
            log_data = {
                "timestamp": str(datetime.now()),
                "trading_pair": self.trading_pair,
                "is_emergency": emergency_result.get("is_emergency"),
                "reason": emergency_result.get("reason"),
                "action": emergency_result.get("action"),
                "urgency": emergency_result.get("urgency")
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"记录紧急情况时出错: {e}")

if __name__ == "__main__":
    trader = LLMTrader()
    trader.start() 