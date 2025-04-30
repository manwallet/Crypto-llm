import os
import json
from datetime import datetime
import openai
from dotenv import load_dotenv
from .prompt_manager import PromptManager
from .market_classifier import MarketClassifier
from .trade_history import TradeHistory

class LLMAgentManager:
    """语言模型代理管理器，协调多个LLM代理进行协作决策"""
    
    def __init__(self):
        load_dotenv()
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # 支持自定义API URL
        self.base_url = os.getenv('OPENAI_API_BASE_URL')
        if self.base_url:
            self.openai.base_url = self.base_url
            
        # 支持自定义组织ID
        self.org_id = os.getenv('OPENAI_ORG_ID')
        if self.org_id:
            self.openai.organization = self.org_id
            
        self.prompt_manager = PromptManager()
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.market_classifier = MarketClassifier()
        self.trade_history = TradeHistory()
        
        # 初始化代理角色和模型
        self.analyst_agent = os.getenv('ANALYST_MODEL', 'gpt-4')  # 市场分析师
        self.trader_agent = os.getenv('TRADER_MODEL', 'gpt-4')  # 交易决策者
        self.risk_agent = os.getenv('RISK_MODEL', 'gpt-4')  # 风险管理者
        self.emergency_agent = os.getenv('EMERGENCY_MODEL', 'gpt-4')  # 应急管理者
        self.debate_agent = os.getenv('DEBATE_MODEL', 'gpt-4')  # 辩论协调者
        self.validator_agent = os.getenv('VALIDATOR_MODEL', 'gpt-4')  # 验证者
        self.historian_agent = os.getenv('HISTORIAN_MODEL', 'gpt-4')  # 历史分析师
        
        # 记录对话历史
        self.conversation_history = []
        
        # 当前交易ID
        self.current_trade_id = None
        
        # 市场状态记忆
        self.market_state = None
    
    def set_custom_api_url(self, base_url=None, api_key=None, org_id=None):
        """设置自定义API URL和相关配置"""
        if base_url:
            self.base_url = base_url
            self.openai.base_url = base_url
            
        if api_key:
            self.openai.api_key = api_key
            
        if org_id:
            self.org_id = org_id
            self.openai.organization = org_id
            
        return {
            "base_url": self.base_url,
            "org_id": self.org_id,
            "api_key_set": self.openai.api_key is not None
        }
        
    def get_api_config(self):
        """获取当前API配置信息"""
        return {
            "base_url": self.base_url,
            "org_id": self.org_id,
            "models": {
                "analyst": self.analyst_agent,
                "trader": self.trader_agent,
                "risk": self.risk_agent,
                "emergency": self.emergency_agent,
                "debate": self.debate_agent,
                "validator": self.validator_agent,
                "historian": self.historian_agent
            }
        }
    
    def analyze_market(self, market_data):
        """市场分析代理，负责分析市场状况"""
        # 对市场进行分类
        self.market_state = self.market_classifier.classify_market(market_data)
        
        # 准备市场数据上下文
        chart_context = self.prompt_manager.prepare_chart_context(market_data)
        market_context = self.prompt_manager.prepare_market_context(market_data)
        
        # 准备历史交易表现数据
        performance_summary = self.trade_history.get_performance_summary()
        
        # 准备多时间框架分析
        timeframes_analysis = self._analyze_multiple_timeframes(market_data)
        
        prompt = f"""你是一位专业的加密货币市场分析师。分析以下市场数据并提供你的见解。

市场数据摘要:
交易对: {self.trading_pair}
时间范围: {chart_context['summary']['start_time']} 到 {chart_context['summary']['end_time']}
当前价格: {market_context['current_price']}
24小时价格变化: {market_context['price_change_24h']:.2f}%
1小时价格变化: {market_context['price_change_1h']:.2f}%
24小时波动率: {market_context['volatility_24h']:.2f}%
交易量变化: {market_context['volume_change']:.2f}%

市场环境分类:
趋势: {self.market_state['trend']}
波动性: {self.market_state['volatility']}
动量: {self.market_state['momentum']}

价格统计:
开盘价: {chart_context['summary']['open']}
最高价: {chart_context['summary']['high']}
最低价: {chart_context['summary']['low']}
收盘价: {chart_context['summary']['close']}
近期高点: {', '.join([str(p) for p in chart_context['levels']['recent_highs']])}
近期低点: {', '.join([str(p) for p in chart_context['levels']['recent_lows']])}
成交量加权价格: {chart_context['levels']['volume_weighted_price']}

支撑阻力位:
支撑位: {', '.join([str(p) for p in self.market_state['support_resistance'].get('support', [])])}
阻力位: {', '.join([str(p) for p in self.market_state['support_resistance'].get('resistance', [])])}

多时间框架分析:
{timeframes_analysis}

历史交易表现:
{performance_summary}

请分析当前市场状况，识别主要趋势、支撑/阻力位、波动模式和任何重要的市场结构。
重点关注短期价格走势的可能性，考虑不同时间范围的市场表现。
同时参考历史交易表现，特别是在类似市场环境下的表现。
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
            "chart_data": chart_context,
            "market_state": self.market_state
        }
    
    def _analyze_multiple_timeframes(self, market_data):
        """分析多个时间框架"""
        # 这里我们模拟从不同时间框架的数据中提取信息
        # 实际实现时，应该从市场数据中提取不同时间框架的数据
        
        # 获取短期趋势（1小时内）
        short_term = market_data.iloc[-12:] if len(market_data) >= 12 else market_data
        short_term_change = (short_term['close'].iloc[-1] / short_term['close'].iloc[0] - 1) * 100
        short_term_trend = "上涨" if short_term_change > 0 else "下跌"
        
        # 获取中期趋势（4小时内）
        medium_term = market_data.iloc[-48:] if len(market_data) >= 48 else market_data
        medium_term_change = (medium_term['close'].iloc[-1] / medium_term['close'].iloc[0] - 1) * 100
        medium_term_trend = "上涨" if medium_term_change > 0 else "下跌"
        
        # 获取长期趋势（1天内）
        long_term = market_data.iloc[-96:] if len(market_data) >= 96 else market_data
        long_term_change = (long_term['close'].iloc[-1] / long_term['close'].iloc[0] - 1) * 100
        long_term_trend = "上涨" if long_term_change > 0 else "下跌"
        
        # 检查趋势一致性
        trends_consistent = (
            (short_term_change > 0 and medium_term_change > 0 and long_term_change > 0) or
            (short_term_change < 0 and medium_term_change < 0 and long_term_change < 0)
        )
        
        return f"""短期趋势(1小时): {short_term_trend} ({short_term_change:.2f}%)
中期趋势(4小时): {medium_term_trend} ({medium_term_change:.2f}%)
长期趋势(1天): {long_term_trend} ({long_term_change:.2f}%)
趋势一致性: {"一致" if trends_consistent else "不一致"}"""
    
    def suggest_strategy(self, analysis_result, position_info=None):
        """交易策略代理，负责提出交易策略"""
        market_analysis = analysis_result["analysis"]
        market_data = analysis_result["market_data"]
        market_state = analysis_result.get("market_state", self.market_state)
        
        # 分析历史策略在当前市场环境下的表现
        historical_performance = self._analyze_historical_performance(market_state)
        
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

市场环境分类:
趋势: {market_state['trend']}
波动性: {market_state['volatility']}
动量: {market_state['momentum']}

历史表现分析:
{historical_performance}

{position_text}

请提出具体的交易策略，包括:
1. 建议的操作(开多/开空/平仓/持仓观望)
2. 进场价格区间
3. 止损位置
4. 止盈位置
5. 建议的仓位大小(占账户的百分比)
6. 此次交易的风险评估(1-10分)
7. 给出你的信心水平(1-10分)

给出你的分析和明确的交易策略建议。同时解释你的建议与历史表现分析的关系。
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
        
        # 验证策略的数值计算
        validated_strategy = self._validate_strategy(strategy, market_data['current_price'])
        
        return {
            "strategy": validated_strategy,
            "original_strategy": strategy,
            "market_data": market_data,
            "market_state": market_state
        }
    
    def _analyze_historical_performance(self, market_state):
        """分析历史策略在当前市场环境下的表现"""
        recent_trades = self.trade_history.get_recent_trades(30)
        
        # 筛选类似市场条件下的交易
        similar_trades = []
        for trade in recent_trades:
            if "data" not in trade or "result" not in trade:
                continue
                
            trade_market_state = trade.get("data", {}).get("market_state", {})
            if not trade_market_state:
                continue
                
            # 判断市场状态相似性
            if (trade_market_state.get("trend") == market_state.get("trend") or
                trade_market_state.get("volatility") == market_state.get("volatility") or
                trade_market_state.get("momentum") == market_state.get("momentum")):
                similar_trades.append(trade)
        
        if not similar_trades:
            return "无足够的历史数据在类似市场条件下进行分析。"
            
        # 分析类似市场条件下的表现
        total_trades = len(similar_trades)
        winning_trades = sum(1 for t in similar_trades if t.get("result", {}).get("profit", 0) > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 分析方向性能
        long_trades = [t for t in similar_trades if "开多" in t.get("data", {}).get("action", "")]
        short_trades = [t for t in similar_trades if "开空" in t.get("data", {}).get("action", "")]
        
        long_win_rate = sum(1 for t in long_trades if t.get("result", {}).get("profit", 0) > 0) / len(long_trades) if long_trades else 0
        short_win_rate = sum(1 for t in short_trades if t.get("result", {}).get("profit", 0) > 0) / len(short_trades) if short_trades else 0
        
        return f"""在类似市场条件下的历史表现:
总交易次数: {total_trades}
总体胜率: {win_rate:.2%}
多头胜率: {long_win_rate:.2%} (共{len(long_trades)}笔)
空头胜率: {short_win_rate:.2%} (共{len(short_trades)}笔)
"""
    
    def _validate_strategy(self, strategy, current_price):
        """验证策略的数值计算"""
        prompt = f"""作为一位数据验证专家，请验证以下交易策略建议中的数值计算是否合理。
特别关注:
1. 止损止盈位置是否合理
2. 风险收益比是否正确计算
3. 仓位大小是否符合风险管理原则
4. 价格区间是否符合逻辑

当前市场价格: {current_price}

交易策略:
{strategy}

如果发现任何计算错误或逻辑问题，请指出并修正。如果一切正确，请返回原始策略内容。
"""
        
        response = self.openai.chat.completions.create(
            model=self.validator_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        validated_strategy = response.choices[0].message.content
        return validated_strategy
    
    def evaluate_risk(self, strategy_result, position_info=None, market_data=None):
        """风险管理代理，负责评估交易风险"""
        strategy = strategy_result["strategy"]
        market_data = strategy_result["market_data"]
        market_state = strategy_result.get("market_state")
        
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

市场环境:
趋势: {market_state['trend']}
波动性: {market_state['volatility']}
动量: {market_state['momentum']}

{position_text}

请评估此交易策略的风险，并提出具体的风险管理建议:
1. 总体风险评分(1-10分)
2. 主要风险因素
3. 如何降低风险(调整仓位/止损/分批建仓等)
4. 是否建议执行此策略(是/否/调整后执行)
5. 如建议调整，请详细说明如何调整
6. 给出风险评估的信心水平(1-10分)

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
            "strategy": strategy,
            "market_state": market_state
        }
    
    def debate_strategy(self, strategy_result, risk_result):
        """代理间辩论，协调不同观点"""
        strategy = strategy_result["strategy"]
        risk_assessment = risk_result["risk_assessment"]
        
        # 判断是否需要辩论，如果风险评估建议不执行或调整，则触发辩论
        if "不建议执行" in risk_assessment or "调整后执行" in risk_assessment:
            debate_prompt = f"""你是加密货币交易辩论的协调者。交易策略师和风险管理专家对以下交易策略有不同意见。
请主持一次辩论，让双方表达观点，然后形成一个折中的建议。

交易策略师的建议:
{strategy}

风险管理专家的评估:
{risk_assessment}

请组织一次虚拟辩论，让双方交换意见。然后提出一个平衡了收益和风险的修改后策略建议。
确保最终建议包含具体的操作、价格、止损止盈位置和仓位大小。
"""
            
            response = self.openai.chat.completions.create(
                model=self.debate_agent,
                messages=[{"role": "user", "content": debate_prompt}],
                temperature=0.4
            )
            
            debate_result = response.choices[0].message.content
            self.conversation_history.append({
                "role": "辩论协调者",
                "content": debate_result,
                "timestamp": datetime.now()
            })
            
            return {
                "debated_strategy": debate_result,
                "original_strategy": strategy,
                "risk_assessment": risk_assessment,
                "was_debated": True
            }
        
        # 如果无需辩论，直接返回原策略
        return {
            "debated_strategy": strategy,
            "original_strategy": strategy,
            "risk_assessment": risk_assessment,
            "was_debated": False
        }
    
    def make_final_decision(self, strategy_result, market_data, position_info=None):
        """最终决策代理，综合所有信息做出交易决策"""
        # 如果已经过辩论，使用辩论后的策略
        if "debated_strategy" in strategy_result:
            strategy = strategy_result["debated_strategy"]
            was_debated = strategy_result.get("was_debated", False)
        else:
            strategy = strategy_result.get("strategy", "")
            risk_assessment = strategy_result.get("risk_assessment", "")
            
            # 先进行辩论
            debate_result = self.debate_strategy({"strategy": strategy}, {"risk_assessment": risk_assessment})
            strategy = debate_result["debated_strategy"]
            was_debated = debate_result["was_debated"]
        
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
            for item in self.conversation_history[-4:]  # 取最近的4条对话
        ])
        
        prompt = f"""你是一位果断的加密货币交易决策者。基于以下信息，做出最终的交易决定。

之前的分析和建议:
{conversation}

市场数据:
交易对: {self.trading_pair}
当前价格: {market_data['current_price']}
24小时价格变化: {market_data['price_change_24h']:.2f}%

{'策略已经过专家辩论和调整。' if was_debated else ''}

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
            
            # 添加市场状态信息
            decision["market_state"] = self.market_state
            
            self.conversation_history.append({
                "role": "最终决策者",
                "content": decision_text,
                "timestamp": datetime.now()
            })
            
            # 记录交易决策
            self.current_trade_id = self.trade_history.add_trade(decision)
            
            return {
                "decision": decision,
                "raw_response": decision_text,
                "trade_id": self.current_trade_id
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
                    "reason": "解析决策时出错",
                    "market_state": self.market_state
                },
                "raw_response": response.choices[0].message.content,
                "trade_id": None
            }
    
    def update_trade_result(self, trade_id, result_data):
        """更新交易结果"""
        if not trade_id:
            return False
        
        return self.trade_history.update_trade_result(trade_id, result_data)
    
    def check_emergency(self, market_data, position_info=None):
        """应急管理代理，检查是否需要紧急干预"""
        if position_info is None or position_info['size'] == 0:
            return {"is_emergency": False, "action": None}
        
        market_context = self.prompt_manager.prepare_market_context(market_data)
        
        # 获取历史表现数据
        performance_metrics = self.trade_history.calculate_performance_metrics()
        
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

历史表现指标:
总交易次数: {performance_metrics.get('total_trades', 0)}
胜率: {performance_metrics.get('win_rate', 0):.2%}
平均利润: {performance_metrics.get('avg_profit', 0):.2f}
最大亏损: {performance_metrics.get('max_loss', 0):.2f}

判断标准:
1. 当前是否接近清算价格
2. 市场是否异常波动
3. 是否出现剧烈不利走势
4. 是否存在其他紧急风险
5. 考虑历史表现，特别是最大亏损情况

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
    
    def analyze_trading_history(self, days=30):
        """分析交易历史，获取经验和改进点"""
        # 获取历史交易数据
        recent_trades = self.trade_history.get_recent_trades(days)
        performance_metrics = self.trade_history.calculate_performance_metrics(days)
        
        if not recent_trades:
            return "没有足够的历史交易记录进行分析。"
        
        # 准备交易历史摘要
        trades_summary = []
        for trade in recent_trades:
            if "data" not in trade or "result" not in trade:
                continue
                
            trade_data = trade["data"]
            result = trade["result"]
            
            trades_summary.append(f"""
交易ID: {trade.get('trade_id')}
时间: {trade.get('timestamp')}
操作: {trade_data.get('action')}
价格: {trade_data.get('price')}
数量: {trade_data.get('quantity')}
止损: {trade_data.get('stop_loss')}
止盈: {trade_data.get('take_profit')}
市场状态: {trade_data.get('market_state', {}).get('trend', 'unknown')}/{trade_data.get('market_state', {}).get('volatility', 'unknown')}
结果: {"盈利" if result.get('profit', 0) > 0 else "亏损"} {result.get('profit', 0)}
""")
        
        # 限制交易摘要长度，避免超过令牌限制
        if len(trades_summary) > 10:
            trades_summary = trades_summary[:5] + ["...省略中间记录..."] + trades_summary[-5:]
        
        trades_text = "\n".join(trades_summary)
        
        # 创建分析提示
        prompt = f"""作为加密货币交易历史分析师，请分析以下过去{days}天的交易记录，找出模式、经验和可能的改进点。

交易记录摘要:
{trades_text}

性能指标:
总交易次数: {performance_metrics.get('total_trades', 0)}
胜率: {performance_metrics.get('win_rate', 0):.2%}
平均利润: {performance_metrics.get('avg_profit', 0):.2f}
最大盈利: {performance_metrics.get('max_profit', 0):.2f}
最大亏损: {performance_metrics.get('max_loss', 0):.2f}
盈亏比: {performance_metrics.get('profit_factor', 0):.2f}

方向表现:
多头胜率: {performance_metrics.get('success_by_direction', {}).get('long', 0):.2%}
空头胜率: {performance_metrics.get('success_by_direction', {}).get('short', 0):.2%}

请分析这些交易记录，找出:
1. 最成功的交易策略和市场条件
2. 导致亏损的主要因素
3. 可能的优化建议
4. 应该加强或避免的市场条件
5. 止损和止盈策略的有效性
6. 整体交易策略的改进建议

请提供详细分析，帮助改进我们的交易决策过程。
"""
        
        response = self.openai.chat.completions.create(
            model=self.historian_agent,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        analysis = response.choices[0].message.content
        return analysis 