#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM连接测试脚本

此脚本测试与语言模型API的连接并验证模型间通信功能是否正常。
它对系统中使用的每个AI代理角色执行简单测试，以确保API配置正确。
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# 确保能够导入主模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.llm_agent_manager import LLMAgentManager

class LLMConnectionTester:
    """测试LLM API连接和多代理通信的类"""
    
    def __init__(self):
        """初始化测试器"""
        # 加载环境变量
        load_dotenv()
        print("加载环境变量完成")
        
        # 初始化LLM代理管理器
        self.llm_agent = LLMAgentManager()
        print("初始化LLM代理管理器完成")
        
    def test_api_connection(self):
        """测试API连接是否正常工作"""
        print("\n=== 测试API连接 ===")
        
        # 获取当前API配置
        config = self.llm_agent.get_api_config()
        print(f"当前API配置:")
        print(f"- 基础URL: {config['base_url'] or '使用默认OpenAI API'}")
        print(f"- 组织ID: {config['org_id'] or '未设置'}")
        print(f"- 模型配置:")
        for role, model in config['models'].items():
            print(f"  - {role}: {model}")
        
        # 简单测试调用
        try:
            response = self.llm_agent.openai.chat.completions.create(
                model=self.llm_agent.analyst_agent,
                messages=[{"role": "user", "content": "简单测试句子，请回复'API连接正常'"}],
                max_tokens=20
            )
            
            content = response.choices[0].message.content
            print(f"\n测试响应: {content}")
            
            if "API连接正常" in content or "连接" in content:
                print("✅ API连接测试成功!")
            else:
                print("⚠️ API响应内容与预期不符，但连接可能正常")
                
        except Exception as e:
            print(f"❌ API连接测试失败: {str(e)}")
            return False
            
        return True
    
    def test_analyst_agent(self):
        """测试市场分析师代理"""
        print("\n=== 测试市场分析师代理 ===")
        
        try:
            prompt = "分析比特币当前市场状况，简要回答不超过50字。"
            
            response = self.llm_agent.openai.chat.completions.create(
                model=self.llm_agent.analyst_agent,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            print(f"分析师响应: {content}")
            print("✅ 市场分析师代理测试成功!")
            
        except Exception as e:
            print(f"❌ 市场分析师代理测试失败: {str(e)}")
            return False
            
        return True
    
    def test_trader_agent(self):
        """测试交易决策者代理"""
        print("\n=== 测试交易决策者代理 ===")
        
        try:
            prompt = """
请基于以下市场分析提出一个简短的交易建议:
"比特币目前价格29500美元，处于盘整阶段，支撑位在28000美元，阻力位在30000美元。"

以JSON格式输出你的决定，格式如下:
{
  "action": "开多/开空/平仓/观望",
  "price": "具体价格或价格区间",
  "quantity": "具体数量或账户百分比",
  "stop_loss": "具体价格",
  "take_profit": "具体价格",
  "confidence": "1-10",
  "reason": "简要决策理由"
}
"""
            
            response = self.llm_agent.openai.chat.completions.create(
                model=self.llm_agent.trader_agent,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            print(f"交易者响应: {content}")
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                if "```json" in content:
                    # 去掉 markdown 格式
                    json_text = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_text = content.split("```")[1].strip()
                else:
                    json_text = content
                    
                decision = json.loads(json_text)
                print("成功解析JSON决策:")
                for key, value in decision.items():
                    print(f"- {key}: {value}")
                    
                print("✅ 交易决策者代理测试成功!")
            except:
                print("⚠️ 无法解析JSON响应，但API调用成功")
            
        except Exception as e:
            print(f"❌ 交易决策者代理测试失败: {str(e)}")
            return False
            
        return True
    
    def test_risk_agent(self):
        """测试风险管理者代理"""
        print("\n=== 测试风险管理者代理 ===")
        
        try:
            prompt = """
评估以下交易策略的风险:
"开多BTC，入场价29500美元，止损28800美元，止盈31000美元，使用账户20%资金。"

回复一个1-10的风险评分和简短解释。
"""
            
            response = self.llm_agent.openai.chat.completions.create(
                model=self.llm_agent.risk_agent,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            print(f"风险管理者响应: {content}")
            print("✅ 风险管理者代理测试成功!")
            
        except Exception as e:
            print(f"❌ 风险管理者代理测试失败: {str(e)}")
            return False
            
        return True
    
    def test_multi_agent_debate(self):
        """测试代理间辩论功能"""
        print("\n=== 测试代理间辩论功能 ===")
        
        try:
            prompt = """
你是加密货币交易辩论的协调者。
交易策略师建议: "开多BTC，入场价29500美元，止损28800美元，止盈31000美元，使用账户20%资金。"
风险管理专家评估: "风险评分7/10。风险较高，建议减少仓位至10%并提高止损位。"

请组织一次简短的虚拟辩论，并提出一个平衡的建议。最多100字。
"""
            
            response = self.llm_agent.openai.chat.completions.create(
                model=self.llm_agent.debate_agent,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            content = response.choices[0].message.content
            print(f"辩论协调者响应: {content}")
            print("✅ 多代理辩论功能测试成功!")
            
        except Exception as e:
            print(f"❌ 多代理辩论功能测试失败: {str(e)}")
            return False
            
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("==================================")
        print("LLM连接和多代理通信测试")
        print("==================================")
        print(f"测试时间: {datetime.now()}")
        
        results = {}
        
        # 运行所有测试
        results["api_connection"] = self.test_api_connection()
        
        # 只有在API连接成功的情况下继续其他测试
        if results["api_connection"]:
            results["analyst_agent"] = self.test_analyst_agent()
            results["trader_agent"] = self.test_trader_agent()
            results["risk_agent"] = self.test_risk_agent()
            results["multi_agent_debate"] = self.test_multi_agent_debate()
        
        # 打印总结
        print("\n==================================")
        print("测试结果摘要")
        print("==================================")
        
        for test, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 所有测试通过! LLM通信功能正常。")
        else:
            print("\n⚠️ 部分测试失败。请检查API配置和网络连接。")
        
        return all_passed

# 直接运行
if __name__ == "__main__":
    tester = LLMConnectionTester()
    tester.run_all_tests() 