import os
from binance.client import Client
from binance.enums import *
from datetime import datetime
from dotenv import load_dotenv

class PositionManager:
    def __init__(self):
        load_dotenv()
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        
    def get_position_info(self):
        """获取当前持仓信息"""
        try:
            position = self.client.futures_position_information(symbol=self.trading_pair)[0]
            return {
                'symbol': position['symbol'],
                'size': float(position['positionAmt']),
                'entry_price': float(position['entryPrice']),
                'mark_price': float(position['markPrice']),
                'unrealized_pnl': float(position['unRealizedProfit']),
                'liquidation_price': float(position['liquidationPrice']),
                'leverage': float(position['leverage']),
                'margin_type': position['marginType']
            }
        except Exception as e:
            print(f"Error getting position information: {e}")
            return None
            
    def close_all_positions(self):
        """关闭所有持仓"""
        try:
            # 获取当前持仓
            position = self.get_position_info()
            if position is None or position['size'] == 0:
                return True
                
            # 取消所有未完成的订单
            self.client.futures_cancel_all_open_orders(symbol=self.trading_pair)
            
            # 市价平仓
            side = SIDE_SELL if position['size'] > 0 else SIDE_BUY
            quantity = abs(position['size'])
            
            order = self.client.futures_create_order(
                symbol=self.trading_pair,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            print(f"Closed position: {quantity} {self.trading_pair} at market price")
            return True
            
        except Exception as e:
            print(f"Error closing positions: {e}")
            return False
            
    def get_position_risk(self):
        """获取持仓风险指标"""
        try:
            position = self.get_position_info()
            if position is None or position['size'] == 0:
                return {
                    'risk_level': 'none',
                    'pnl_percentage': 0,
                    'liquidation_distance': 0
                }
                
            # 计算未实现盈亏百分比
            entry_value = abs(position['size'] * position['entry_price'])
            pnl_percentage = (position['unrealized_pnl'] / entry_value) * 100 if entry_value > 0 else 0
            
            # 计算到清算价格的距离（百分比）
            current_price = float(position['mark_price'])
            liquidation_price = float(position['liquidation_price'])
            if liquidation_price > 0:
                liquidation_distance = abs((current_price - liquidation_price) / current_price * 100)
            else:
                liquidation_distance = 100
                
            # 确定风险等级
            risk_level = self._calculate_risk_level(pnl_percentage, liquidation_distance)
            
            return {
                'risk_level': risk_level,
                'pnl_percentage': pnl_percentage,
                'liquidation_distance': liquidation_distance
            }
            
        except Exception as e:
            print(f"Error calculating position risk: {e}")
            return None
            
    def _calculate_risk_level(self, pnl_percentage, liquidation_distance):
        """计算风险等级"""
        if liquidation_distance <= 5:  # 距离清算价格小于5%
            return 'extreme'
        elif liquidation_distance <= 10:  # 距离清算价格小于10%
            return 'high'
        elif pnl_percentage < -10:  # 未实现亏损超过10%
            return 'medium'
        elif pnl_percentage < -5:  # 未实现亏损超过5%
            return 'low'
        else:
            return 'safe'
            
    def get_position_summary(self):
        """获取持仓摘要"""
        try:
            position = self.get_position_info()
            if position is None:
                return None
                
            risk_info = self.get_position_risk()
            
            return {
                'timestamp': datetime.now(),
                'symbol': position['symbol'],
                'position_size': position['size'],
                'entry_price': position['entry_price'],
                'current_price': position['mark_price'],
                'unrealized_pnl': position['unrealized_pnl'],
                'pnl_percentage': risk_info['pnl_percentage'] if risk_info else 0,
                'liquidation_price': position['liquidation_price'],
                'liquidation_distance': risk_info['liquidation_distance'] if risk_info else 0,
                'risk_level': risk_info['risk_level'] if risk_info else 'unknown',
                'leverage': position['leverage'],
                'margin_type': position['margin_type']
            }
            
        except Exception as e:
            print(f"Error getting position summary: {e}")
            return None 