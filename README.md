# 多代理LLM加密货币自动交易系统

这是一个完全基于多个大型语言模型(LLM)协作的加密货币自动化交易系统，专为币安合约交易设计。系统由多个专业AI代理组成，负责市场分析、策略生成、风险评估和决策执行。

## 主要特点

- **多代理协作决策**：多个专业LLM代理协同工作，模拟真实交易团队
- **市场分析AI**：专注于识别市场趋势、支撑阻力位和价格模式
- **策略生成AI**：提出具体交易策略，包括入场价、止损止盈
- **风险管理AI**：评估交易风险，提供风险控制建议
- **应急管理AI**：监控市场异常波动，执行紧急操作
- **最终决策AI**：综合前述分析，做出最终交易决定

## 系统架构

系统由以下主要组件构成：

1. **LLMAgentManager**: 语言模型代理管理器
   - 管理多个LLM代理之间的协作
   - 收集并整合各代理的意见
   - 记录决策过程和对话历史

2. **多个专业AI代理**:
   - 市场分析师：分析市场趋势和状况
   - 交易策略师：提出具体交易策略
   - 风险管理专家：评估策略风险
   - 应急管理者：监控紧急情况
   - 最终决策者：做出交易决定

3. **PositionManager**: 仓位管理模块
   - 执行交易操作
   - 管理持仓
   - 设置止损止盈

4. **PromptManager**: 提示词管理器
   - 生成专业提示词
   - 准备市场数据上下文
   - 动态调整分析深度

## 工作流程

1. **市场分析阶段**:
   - 获取K线数据
   - 根据市场波动性动态决定分析深度
   - 市场分析AI产生专业的市场分析报告

2. **策略生成阶段**:
   - 基于市场分析提出交易策略
   - 指定入场价格、止损止盈位置
   - 建议仓位大小和风险评级

3. **风险评估阶段**:
   - 评估策略风险
   - 提出风险控制建议
   - 决定是否执行或调整策略

4. **最终决策阶段**:
   - 综合所有前述分析
   - 做出最终交易决定
   - 生成JSON格式的交易指令

5. **执行阶段**:
   - 执行交易决策
   - 设置止损止盈
   - 记录交易日志

6. **应急监控阶段**:
   - 实时监控市场异常
   - 评估持仓风险
   - 必要时执行紧急操作

## 安装要求

- Python 3.8+
- OpenAI API密钥（支持GPT-4）
- 币安API密钥和密钥

## 安装步骤

1. 克隆仓库：
```bash
git clone <repository_url>
cd llm-crypto-trader
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

# 交易配置
TRADING_PAIR=BTCUSDT  # 交易对
LEVERAGE=5  # 杠杆倍数
POSITION_SIZE=0.01  # 每次开仓数量
MAX_POSITION=0.05  # 最大持仓量

# AI模型配置
STRATEGY_UPDATE_INTERVAL=15  # 策略更新间隔（分钟）
EMERGENCY_CHECK_INTERVAL=5  # 应急检查间隔（分钟）

# 自定义LLM API设置（可选）
LLM_API_BASE_URL=https://your-custom-endpoint.com/v1  # 自定义API基础URL
LLM_API_KEY=your_api_key_here  # 自定义API密钥
LLM_ORG_ID=your_org_id_here    # 自定义组织ID（可选）

# 代理模型设置（可选）
ANALYST_MODEL=claude-3-opus-20240229    # 市场分析师模型
TRADER_MODEL=claude-3-opus-20240229     # 交易决策者模型
RISK_MODEL=claude-3-sonnet-20240229     # 风险管理者模型
```

## 使用自定义语言模型API

本系统支持使用OpenAI API格式的自定义语言模型端点，这使您能够：

1. **使用Claude模型**：通过兼容OpenAI API的代理服务
2. **使用自托管模型**：指向本地或自托管的语言模型API
3. **使用其他云服务提供商**：如Azure OpenAI或其他提供兼容API的服务

### 配置方法

1. **通过环境变量配置**：
   - 在`.env`文件中设置`LLM_API_BASE_URL`、`LLM_API_KEY`和可选的`LLM_ORG_ID`
   - 系统启动时会自动加载这些配置

2. **通过代码配置**：
   ```python
   from main import LLMTrader
   
   trader = LLMTrader()
   # 设置自定义API URL
   trader.set_custom_api_url(
       base_url="https://your-custom-endpoint.com/v1",
       api_key="your_api_key_here",
       org_id="your_org_id_here"  # 可选
   )
   # 启动交易系统
   trader.start()
   ```

3. **指定不同角色使用的模型**：
   - 在`.env`文件中设置特定角色使用的模型名称
   - 例如：`ANALYST_MODEL=claude-3-opus-20240229`
   - 支持的角色模型设置包括：`ANALYST_MODEL`, `TRADER_MODEL`, `RISK_MODEL`, `EMERGENCY_MODEL`, `DEBATE_MODEL`, `VALIDATOR_MODEL`, `HISTORIAN_MODEL`

### 常见自定义API端点示例

#### Claude模型（通过代理服务）
```
LLM_API_BASE_URL=https://your-claude-proxy.com/v1
LLM_API_KEY=your_api_key_here
ANALYST_MODEL=claude-3-opus-20240229
TRADER_MODEL=claude-3-opus-20240229
```

#### Azure OpenAI服务
```
LLM_API_BASE_URL=https://{your-resource-name}.openai.azure.com/openai/deployments/{deployment-id}
LLM_API_KEY=your_azure_api_key
```

#### 本地托管模型
```
LLM_API_BASE_URL=http://localhost:8000/v1
ANALYST_MODEL=your-local-model-name
```

## 使用方法

1. 启动交易机器人：
```bash
python main.py
```

2. 监控输出：
   - 程序会打印每个阶段的分析结果和决策
   - 在logs目录下查看详细的决策记录

## 自定义与扩展

可以通过以下方式自定义系统：

1. **调整提示词**：
   - 修改`prompt_manager.py`中的提示词模板
   - 调整不同角色的专业性和风格

2. **添加新代理**：
   - 在`llm_agent_manager.py`中添加新的专业代理
   - 加入新的分析维度和决策因素

3. **使用不同模型**：
   - 为不同代理指定不同的OpenAI模型
   - 根据需要调整模型参数

## 风险提示

- 本系统涉及加密货币合约交易，具有高风险
- 建议先在测试网进行测试
- 实盘交易时请谨慎设置交易参数
- 定期检查系统运行状态和持仓情况

## 系统优势

1. **集体智慧**：多个专业AI代理协作，避免单点决策偏见
2. **专业分工**：每个代理专注于特定领域，提高决策质量
3. **风险意识**：独立的风险评估和应急管理机制
4. **透明决策**：完整记录每个步骤的分析和决策过程
5. **灵活性强**：轻松调整提示词和角色定位，适应不同交易风格

## 许可证

MIT License 