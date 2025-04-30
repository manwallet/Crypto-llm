#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
示例：如何使用自定义API URL配置
此示例展示如何配置交易系统使用Claude或其他通过OpenAI兼容API提供的模型
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import LLMTrader
from dotenv import load_dotenv

# 示例1：通过环境变量配置
def configure_via_env():
    """通过环境变量配置自定义API URL"""
    # 设置环境变量
    os.environ["LLM_API_BASE_URL"] = "https://your-claude-proxy.com/v1"
    os.environ["LLM_API_KEY"] = "your_api_key_here"
    
    # 设置模型名称（对Claude模型）
    os.environ["ANALYST_MODEL"] = "claude-3-opus-20240229"
    os.environ["TRADER_MODEL"] = "claude-3-opus-20240229"
    os.environ["RISK_MODEL"] = "claude-3-sonnet-20240229"
    os.environ["EMERGENCY_MODEL"] = "claude-3-sonnet-20240229"
    os.environ["DEBATE_MODEL"] = "claude-3-sonnet-20240229"
    os.environ["VALIDATOR_MODEL"] = "claude-3-haiku-20240307"
    os.environ["HISTORIAN_MODEL"] = "claude-3-sonnet-20240229"
    
    # 初始化交易系统
    trader = LLMTrader()
    print(f"通过环境变量配置API: {trader.get_api_config()}")
    
    # 正常启动交易系统（此处仅展示，不实际启动）
    # trader.start()
    
    return trader

# 示例2：通过代码直接配置
def configure_programmatically():
    """通过代码直接配置自定义API URL"""
    # 初始化交易系统
    trader = LLMTrader()
    
    # 配置自定义API
    trader.set_custom_api_url(
        base_url="https://your-claude-proxy.com/v1",
        api_key="your_api_key_here"
    )
    
    # 打印配置信息
    print(f"通过代码配置API: {trader.get_api_config()}")
    
    # 正常启动交易系统（此处仅展示，不实际启动）
    # trader.start()
    
    return trader

# 示例3：使用本地模型
def configure_local_model():
    """配置使用本地部署的语言模型"""
    # 初始化交易系统
    trader = LLMTrader()
    
    # 配置连接到本地运行的模型
    trader.set_custom_api_url(
        base_url="http://localhost:8000/v1",
        api_key="not-needed-for-local"  # 本地模型可能不需要API密钥
    )
    
    # 打印配置信息
    print(f"连接到本地模型: {trader.get_api_config()}")
    
    return trader

# 主函数
if __name__ == "__main__":
    # 示例1：通过环境变量配置
    trader1 = configure_via_env()
    
    # 清除环境变量，以免影响后续示例
    for key in ["LLM_API_BASE_URL", "LLM_API_KEY", "LLM_ORG_ID",
                "ANALYST_MODEL", "TRADER_MODEL", "RISK_MODEL", 
                "EMERGENCY_MODEL", "DEBATE_MODEL", "VALIDATOR_MODEL", 
                "HISTORIAN_MODEL"]:
        if key in os.environ:
            del os.environ[key]
    
    # 示例2：通过代码直接配置
    trader2 = configure_programmatically()
    
    # 示例3：使用本地模型
    trader3 = configure_local_model()
    
    print("\n演示完成！\n")
    print("在实际使用中，选择其中一种配置方法，然后调用 trader.start() 启动交易系统。") 