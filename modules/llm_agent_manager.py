import os
import json
from datetime import datetime
import openai
from dotenv import load_dotenv
from .prompt_manager import PromptManager

class LLMAgentManager:
    """语言模型代理管理器，协调多个LLM代理进行协作决策"""
    
    def __init__(self):
        load_dotenv()
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        self.prompt_manager = PromptManager()
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        
        # 初始化代理角色
        self.analyst_agent = "gpt-4"  # 市场分析师
        self.trader_agent = "gpt-4"  # 交易决策者
        self.risk_agent = "gpt-4"  # 风险管理者
        self.emergency_agent = "gpt-4"  # 应急管理者
        
        # 记录对话历史
        self.conversation_history = []
        
    def analyze_market(self, market_data):
        """市场分析代理，负责分析市场状况"""
        # 准备市场数据上下文
        chart_context = self.prompt_manager.prepare_chart_context(market_data)
        market_context = self.prompt_manager.prepare_market_context(market_data)
        
        prompt = f"""你是一位专业的加密货币市场分析师。分析以下市场数据并提供你的见解。

市场数据摘要:
交易对: {self.trading_pair}
时间范围: {chart_context['summary']['start_time']} 到 {chart_context['summary']['end_time']}
当前价格: {market_context['current_price']}
24小时价格变化: {market_context['price_change_24h']:.2f}%
1小时价格变化: {market_context['price_change_1h']:.2f}%
24小时波动率: {market_context['volatility_24h']:.2f}%
交易量变化: {market_context['volume_change']:.2f}%

价格统计:
开盘价: {chart_context['summary']['open']}
最高价: {chart_context['summary']['high']}
最低价: {chart_context['summary']['low']}
收盘价: {chart_context['summary']['close']}
近期高点: {', '.join([str(p) for p in chart_context['levels']['recent_highs']])}
近期低点: {', '.join([str(p) for p in chart_context['levels']['recent_lows']])}
成交量加权价格: {chart_context['levels']['volume_weighted_price']}

请分析当前市场状况，识别主要趋势、支撑/阻力位、波动模式和任何重要的市场结构。
重点关注短期价格走势的可能性，考虑不同时间范围的市场表现。
提供你的市场分析，但不要给出具体的交易建议。
"""
        
        response = self.openai.chat.completions.create(
            model=self.analyst_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        analysis = response.choices[0].message.content
        self.conversation_history.append({
            "role": "市场分析师",
            "content": analysis,
            "timestamp": datetime.now()
        })
        
        return {
            "analysis": analysis,
            "market_data": market_context,
            "chart_data": chart_context
        }
    
    def suggest_strategy(self, analysis_result, position_info=None):
        """交易策略代理，负责提出交易策略"""
        market_analysis = analysis_result["analysis"]
        market_data = analysis_result["market_data"]
        
        position_text = "当前无持仓" if position_info is None or position_info['size'] == 0 else f"""
当前持仓:
方向: {'多头' if position_info['size'] > 0 else '空头'}
规模: {abs(position_info['size'])}
入场价: {position_info['entry_price']}
未实现盈亏: {position_info['unrealized_pnl']}
杠杆: {position_info['leverage']}倍
清算价: {position_info['liquidation_price']}
"""
        
        prompt = f"""你是一位经验丰富的加密货币交易策略师。基于以下市场分析和当前持仓情况，提出具体的交易策略。

当前市场分析:
{market_analysis}

市场数据:
交易对: {self.trading_pair}
当前价格: {market_data['current_price']}
24小时价格变化: {market_data['price_change_24h']:.2f}%
24小时波动率: {market_data['volatility_24h']:.2f}%

{position_text}

请提出具体的交易策略，包括:
1. 建议的操作(开多/开空/平仓/持仓观望)
2. 进场价格区间
3. 止损位置
4. 止盈位置
5. 建议的仓位大小(占账户的百分比)
6. 此次交易的风险评估(1-10分)

给出你的分析和明确的交易策略建议。
"""
        
        response = self.openai.chat.completions.create(
            model=self.trader_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        
        strategy = response.choices[0].message.content
        self.conversation_history.append({
            "role": "交易策略师",
            "content": strategy,
            "timestamp": datetime.now()
        })
        
        return {
            "strategy": strategy,
            "market_data": market_data
        }
    
    def evaluate_risk(self, strategy_result, position_info=None, market_data=None):
        """风险管理代理，负责评估交易风险"""
        strategy = strategy_result["strategy"]
        market_data = strategy_result["market_data"]
        
        position_text = "当前无持仓" if position_info is None or position_info['size'] == 0 else f"""
当前持仓:
方向: {'多头' if position_info['size'] > 0 else '空头'}
规模: {abs(position_info['size'])}
入场价: {position_info['entry_price']}
未实现盈亏: {position_info['unrealized_pnl']}
杠杆: {position_info['leverage']}倍
清算价: {position_info['liquidation_price']}
"""
        
        prompt = f"""你是一位谨慎的加密货币风险管理专家。评估以下交易策略的风险，并提供风险管理建议。

交易策略:
{strategy}

市场数据:
交易对: {self.trading_pair}
当前价格: {market_data['current_price']}
24小时价格变化: {market_data['price_change_24h']:.2f}%
24小时波动率: {market_data['volatility_24h']:.2f}%

{position_text}

请评估此交易策略的风险，并提出具体的风险管理建议:
1. 总体风险评分(1-10分)
2. 主要风险因素
3. 如何降低风险(调整仓位/止损/分批建仓等)
4. 是否建议执行此策略(是/否/调整后执行)
5. 如建议调整，请详细说明如何调整

提供全面的风险评估和明确的建议。
"""
        
        response = self.openai.chat.completions.create(
            model=self.risk_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        risk_assessment = response.choices[0].message.content
        self.conversation_history.append({
            "role": "风险管理专家",
            "content": risk_assessment,
            "timestamp": datetime.now()
        })
        
        return {
            "risk_assessment": risk_assessment,
            "strategy": strategy
        }
    
    def make_final_decision(self, risk_result, market_data, position_info=None):
        """最终决策代理，综合所有信息做出交易决策"""
        strategy = risk_result["strategy"]
        risk_assessment = risk_result["risk_assessment"]
        
        position_text = "当前无持仓" if position_info is None or position_info['size'] == 0 else f"""
当前持仓:
方向: {'多头' if position_info['size'] > 0 else '空头'}
规模: {abs(position_info['size'])}
入场价: {position_info['entry_price']}
未实现盈亏: {position_info['unrealized_pnl']}
杠杆: {position_info['leverage']}倍
清算价: {position_info['liquidation_price']}
"""
        
        # 收集之前的对话
        conversation = "\n\n".join([
            f"{item['role']}:\n{item['content']}" 
            for item in self.conversation_history[-3:]  # 取最近的3条对话
        ])
        
        prompt = f"""你是一位果断的加密货币交易决策者。基于以下信息，做出最终的交易决定。

之前的分析和建议:
{conversation}

市场数据:
交易对: {self.trading_pair}
当前价格: {market_data['current_price']}
24小时价格变化: {market_data['price_change_24h']:.2f}%

{position_text}

请做出最终的交易决定:

1. 最终操作: [开多/开空/平仓/持仓观望]
2. 价格: [具体价格或价格区间]
3. 数量: [具体数量或账户百分比]
4. 止损价: [具体价格]
5. 止盈价: [具体价格]
6. 决策的置信度: [1-10分]
7. 最重要的决策理由: [简要说明]

以JSON格式输出你的决定，便于系统直接处理。格式如下:
{{
  "action": "开多/开空/平仓/观望",
  "price": "具体价格或价格区间",
  "quantity": "具体数量或账户百分比",
  "stop_loss": "具体价格",
  "take_profit": "具体价格",
  "confidence": "1-10",
  "reason": "简要决策理由"
}}

仅输出JSON格式的决定，不要添加其他解释。
"""
        
        response = self.openai.chat.completions.create(
            model=self.trader_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        try:
            decision_text = response.choices[0].message.content
            # 提取JSON部分
            if "```json" in decision_text:
                # 去掉 markdown 格式
                json_text = decision_text.split("```json")[1].split("```")[0].strip()
            elif "```" in decision_text:
                json_text = decision_text.split("```")[1].strip()
            else:
                json_text = decision_text
                
            decision = json.loads(json_text)
            
            self.conversation_history.append({
                "role": "最终决策者",
                "content": decision_text,
                "timestamp": datetime.now()
            })
            
            return {
                "decision": decision,
                "raw_response": decision_text
            }
            
        except Exception as e:
            print(f"Error parsing decision JSON: {e}")
            print(f"Raw response: {response.choices[0].message.content}")
            # 返回一个安全的默认决定
            return {
                "decision": {
                    "action": "观望",
                    "price": "market",
                    "quantity": "0",
                    "stop_loss": "0",
                    "take_profit": "0",
                    "confidence": "0",
                    "reason": "解析决策时出错"
                },
                "raw_response": response.choices[0].message.content
            }
    
    def check_emergency(self, market_data, position_info=None):
        """应急管理代理，检查是否需要紧急干预"""
        if position_info is None or position_info['size'] == 0:
            return {"is_emergency": False, "action": None}
        
        market_context = self.prompt_manager.prepare_market_context(market_data)
        
        prompt = f"""你是一位加密货币交易的应急管理专家。评估当前市场和持仓情况，判断是否存在需要紧急干预的情况。

当前持仓:
方向: {'多头' if position_info['size'] > 0 else '空头'}
规模: {abs(position_info['size'])}
入场价: {position_info['entry_price']}
当前价格: {market_context['current_price']}
未实现盈亏: {position_info['unrealized_pnl']}
杠杆: {position_info['leverage']}倍
清算价: {position_info['liquidation_price']}

市场数据:
1小时价格变化: {market_context['price_change_1h']:.2f}%
24小时价格变化: {market_context['price_change_24h']:.2f}%
1小时波动率: {market_context['volatility_1h']:.2f}%
24小时波动率: {market_context['volatility_24h']:.2f}%
成交量变化: {market_context['volume_change']:.2f}%

判断标准:
1. 当前是否接近清算价格
2. 市场是否异常波动
3. 是否出现剧烈不利走势
4. 是否存在其他紧急风险

以JSON格式回答以下问题:
{{
  "is_emergency": true/false,
  "reason": "判断理由",
  "action": "建议的紧急操作(平仓/调整止损/无需操作)",
  "urgency": "紧急程度(1-10)"
}}

只返回JSON格式的回答。
"""
        
        response = self.openai.chat.completions.create(
            model=self.emergency_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        try:
            emergency_text = response.choices[0].message.content
            # 提取JSON部分
            if "```json" in emergency_text:
                json_text = emergency_text.split("```json")[1].split("```")[0].strip()
            elif "```" in emergency_text:
                json_text = emergency_text.split("```")[1].strip()
            else:
                json_text = emergency_text
                
            emergency = json.loads(json_text)
            
            if emergency["is_emergency"]:
                self.conversation_history.append({
                    "role": "应急管理者",
                    "content": emergency_text,
                    "timestamp": datetime.now()
                })
            
            return emergency
            
        except Exception as e:
            print(f"Error parsing emergency JSON: {e}")
            return {"is_emergency": False, "action": None} 