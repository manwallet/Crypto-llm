# AI-Powered Crypto Trading Bot

这是一个基于多个AI模块的加密货币自动化交易系统，专门用于币安合约交易。系统包含新闻分析、技术分析、机器学习预测和风险管理等多个模块。

## 主要特点

- **新闻分析**: 使用GPT-4分析加密货币相关新闻的情绪影响
- **技术分析**: 结合多个技术指标（MACD、RSI、随机指标、布林带）
- **机器学习预测**: 使用LSTM模型预测价格走势
- **风险管理**: 实时监控市场异常波动和持仓风险
- **自动交易**: 根据综合分析自动执行交易订单
- **应急处理**: 在极端市场条件下自动平仓保护资金

## 系统架构

系统由以下主要模块组成：

1. **NewsAnalyzer**: 新闻分析模块
   - 实时获取加密货币新闻
   - 使用GPT-4分析新闻情绪
   - 生成市场情绪信号

2. **StrategyManager**: 策略管理模块
   - 技术指标分析
   - LSTM价格预测
   - 信号综合决策

3. **TradeExecutor**: 交易执行模块
   - 订单管理
   - 仓位控制
   - 止盈止损设置

4. **EmergencyManager**: 应急管理模块
   - 市场异常监控
   - 风险预警
   - 紧急平仓处理

5. **PositionManager**: 仓位管理模块
   - 持仓跟踪
   - 风险评估
   - 仓位调整

## 安装要求

- Python 3.8+
- 币安API密钥
- OpenAI API密钥
- NewsAPI密钥

## 安装步骤

1. 克隆仓库：
```bash
git clone <repository_url>
cd crypto-trading-bot
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
   - 复制`.env.example`为`.env`
   - 填写必要的API密钥和配置参数

## 配置说明

在`.env`文件中配置以下参数：

```
# API配置
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
OPENAI_API_KEY=your_openai_api_key
NEWS_API_KEY=your_newsapi_key

# 交易配置
TRADING_PAIR=BTCUSDT  # 交易对
LEVERAGE=5  # 杠杆倍数
POSITION_SIZE=0.01  # 每次开仓数量
MAX_POSITION=0.05  # 最大持仓量
STOP_LOSS_PERCENTAGE=2  # 止损百分比
TAKE_PROFIT_PERCENTAGE=4  # 止盈百分比

# AI模型配置
NEWS_CHECK_INTERVAL=30  # 新闻检查间隔（分钟）
STRATEGY_UPDATE_INTERVAL=15  # 策略更新间隔（分钟）
EMERGENCY_CHECK_INTERVAL=5  # 应急检查间隔（分钟）
```

## 使用方法

1. 启动交易机器人：
```bash
python main.py
```

2. 监控输出：
   - 程序会打印交易信号、执行情况和风险警告
   - 检查日志文件了解详细信息

## 风险提示

- 本系统涉及加密货币合约交易，具有高风险
- 建议先在测试网进行测试
- 实盘交易时请谨慎设置交易参数
- 定期检查系统运行状态和持仓情况

## 注意事项

1. API安全：
   - 确保API密钥安全存储
   - 建议只授予必要的API权限
   - 定期更换API密钥

2. 风险控制：
   - 合理设置杠杆倍数
   - 谨慎配置持仓限额
   - 设置合适的止损参数

3. 系统维护：
   - 定期检查日志
   - 监控系统性能
   - 及时更新依赖包

## 贡献指南

欢迎提交问题和改进建议：

1. Fork本仓库
2. 创建特性分支
3. 提交变更
4. 发起Pull Request

## 许可证

MIT License 