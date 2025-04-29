import os
from binance.client import Client
from binance.enums import *
from datetime import datetime
import math
from dotenv import load_dotenv

class TradeExecutor:
    def __init__(self):
        load_dotenv()
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.leverage = int(os.getenv('LEVERAGE', '5'))
        self.position_size = float(os.getenv('POSITION_SIZE', '0.01'))
        self.max_position = float(os.getenv('MAX_POSITION', '0.05'))
        self.stop_loss_percentage = float(os.getenv('STOP_LOSS_PERCENTAGE', '2'))
        self.take_profit_percentage = float(os.getenv('TAKE_PROFIT_PERCENTAGE', '4'))
        
        # 设置杠杆
        self.client.futures_change_leverage(
            symbol=self.trading_pair,
            leverage=self.leverage
        )
        
    def execute_trade(self, signal):
        """执行交易信号"""
        try:
            # 检查当前持仓
            position = self._get_current_position()
            
            if signal['action'] == 'buy':
                if position['size'] >= self.max_position:
                    print(f"Maximum position size reached: {position['size']}")
                    return
                    
                # 开多仓
                self._open_long_position(signal['confidence'])
                
            elif signal['action'] == 'sell':
                if position['size'] <= -self.max_position:
                    print(f"Maximum position size reached: {position['size']}")
                    return
                    
                # 开空仓
                self._open_short_position(signal['confidence'])
                
        except Exception as e:
            print(f"Error executing trade: {e}")
            
    def _get_current_position(self):
        """获取当前持仓信息"""
        try:
            position = self.client.futures_position_information(symbol=self.trading_pair)[0]
            return {
                'size': float(position['positionAmt']),
                'entry_price': float(position['entryPrice']),
                'unrealized_pnl': float(position['unRealizedProfit']),
                'leverage': float(position['leverage'])
            }
        except Exception as e:
            print(f"Error getting position information: {e}")
            return {'size': 0, 'entry_price': 0, 'unrealized_pnl': 0, 'leverage': self.leverage}
            
    def _calculate_quantity(self, confidence):
        """根据信心度计算下单数量"""
        try:
            # 获取当前价格
            ticker = self.client.futures_symbol_ticker(symbol=self.trading_pair)
            current_price = float(ticker['price'])
            
            # 基础下单数量
            base_quantity = self.position_size
            
            # 根据信心度调整数量（信心度在0-1之间）
            adjusted_quantity = base_quantity * (0.5 + 0.5 * confidence)
            
            # 确保不超过最大持仓
            max_additional = self.max_position - abs(self._get_current_position()['size'])
            quantity = min(adjusted_quantity, max_additional)
            
            # 根据交易对的最小数量规则调整
            info = self.client.futures_exchange_info()
            symbol_info = next(item for item in info['symbols'] if item['symbol'] == self.trading_pair)
            quantity_precision = symbol_info['quantityPrecision']
            
            # 四舍五入到正确的精度
            quantity = round(quantity, quantity_precision)
            
            return quantity
            
        except Exception as e:
            print(f"Error calculating quantity: {e}")
            return self.position_size
            
    def _open_long_position(self, confidence):
        """开多仓"""
        try:
            quantity = self._calculate_quantity(confidence)
            if quantity <= 0:
                return
                
            # 获取当前价格
            ticker = self.client.futures_symbol_ticker(symbol=self.trading_pair)
            current_price = float(ticker['price'])
            
            # 计算止损止盈价格
            stop_loss_price = current_price * (1 - self.stop_loss_percentage / 100)
            take_profit_price = current_price * (1 + self.take_profit_percentage / 100)
            
            # 开仓订单
            main_order = self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # 设置止损
            self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_MARKET,
                stopPrice=stop_loss_price,
                closePosition=True,
                workingType='MARK_PRICE'
            )
            
            # 设置止盈
            self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_SELL,
                type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                stopPrice=take_profit_price,
                closePosition=True,
                workingType='MARK_PRICE'
            )
            
            print(f"Opened long position: {quantity} {self.trading_pair} at {current_price}")
            
        except Exception as e:
            print(f"Error opening long position: {e}")
            
    def _open_short_position(self, confidence):
        """开空仓"""
        try:
            quantity = self._calculate_quantity(confidence)
            if quantity <= 0:
                return
                
            # 获取当前价格
            ticker = self.client.futures_symbol_ticker(symbol=self.trading_pair)
            current_price = float(ticker['price'])
            
            # 计算止损止盈价格
            stop_loss_price = current_price * (1 + self.stop_loss_percentage / 100)
            take_profit_price = current_price * (1 - self.take_profit_percentage / 100)
            
            # 开仓订单
            main_order = self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # 设置止损
            self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_MARKET,
                stopPrice=stop_loss_price,
                closePosition=True,
                workingType='MARK_PRICE'
            )
            
            # 设置止盈
            self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_BUY,
                type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                stopPrice=take_profit_price,
                closePosition=True,
                workingType='MARK_PRICE'
            )
            
            print(f"Opened short position: {quantity} {self.trading_pair} at {current_price}")
            
        except Exception as e:
            print(f"Error opening short position: {e}")
            
    def close_all_positions(self):
        """关闭所有持仓"""
        try:
            position = self._get_current_position()
            if position['size'] == 0:
                return
                
            # 市价平仓
            self.client.futures_create_order(
                symbol=self.trading_pair,
                side=SIDE_SELL if position['size'] > 0 else SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=abs(position['size'])
            )
            
            print(f"Closed all positions for {self.trading_pair}")
            
        except Exception as e:
            print(f"Error closing positions: {e}") 