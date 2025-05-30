# Google ADK 本地Web大模型交互平台

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Beta-orange.svg)

基于Google ADK的本地化Web界面，支持与大模型对话、灵活的环境配置以及可自定义的MCP工具扩展。

## ✨ 主要特性

- 🌐 **本地Web界面**: 现代化的聊天界面，支持实时对话和流式响应
- 🤖 **多模型支持**: 通过LiteLLM支持100+种大模型API（OpenAI、Anthropic、Google等）
- 🔧 **MCP工具系统**: 可扩展的工具框架，支持自定义功能模块
- ⚙️ **灵活配置**: 通过.env文件和环境变量进行配置，支持热切换
- 📱 **响应式设计**: 适配桌面和移动设备
- 🔄 **实时通信**: 支持WebSocket流式对话
- 📊 **工具管理**: 直观的工具管理界面，支持参数化执行

## 🏗️ 项目架构

```
Google_ADK_Chat/
├── src/                          # 源代码目录
│   ├── core/                     # 核心模块
│   │   ├── config.py            # 配置管理
│   │   ├── logger.py            # 日志系统
│   │   └── llm_client.py        # LLM客户端
│   ├── mcp_tools/               # MCP工具模块
│   │   ├── base.py              # 工具基类
│   │   └── examples.py          # 示例工具
│   └── web/                     # Web服务模块
│       ├── app.py               # FastAPI应用
│       ├── static/              # 静态文件
│       └── templates/           # HTML模板
├── tests/                       # 测试目录
├── docs/                        # 文档目录
├── logs/                        # 日志目录
├── main.py                      # 应用入口
├── requirements.txt             # Python依赖
└── env.example                  # 环境变量示例
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 或 conda

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd Google_ADK_Chat
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # 复制示例配置文件
   cp env.example .env
   
   # 编辑配置文件，设置您的API密钥
   # 重要：请设置 LLM_API_KEY 为您的实际API密钥
   ```

5. **启动应用**
   ```bash
   python main.py
   ```

6. **访问应用**
   
   打开浏览器访问: http://localhost:8000

## ⚙️ 配置说明

### 环境变量配置

在`.env`文件中配置以下参数：

```bash
# 大模型配置 - 必需
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=your_api_key_here

# 可选配置
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
LLM_TIMEOUT=30

# Web服务器配置
WEB_HOST=localhost
WEB_PORT=8000
DEBUG_MODE=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# MCP工具目录
MCP_TOOLS_DIR=src/mcp_tools
```

### 配置优先级

环境变量 > .env文件 > 默认值

### 支持的模型

通过LiteLLM，本项目支持以下模型提供商：

- **OpenAI**: GPT-3.5, GPT-4, GPT-4 Turbo
- **Anthropic**: Claude 2, Claude 3
- **Google**: Gemini Pro, PaLM
- **本地模型**: Ollama, LocalAI
- **其他**: Azure OpenAI, AWS Bedrock等

## 🛠️ MCP工具开发

### 创建自定义工具

1. **继承基类**
   ```python
   from src.mcp_tools.base import MCPTool, ToolResult, ToolParameter
   
   class MyCustomTool(MCPTool):
       @property
       def name(self) -> str:
           return "my_tool"
       
       @property
       def description(self) -> str:
           return "我的自定义工具"
       
       @property
       def version(self) -> str:
           return "1.0.0"
       
       async def execute(self, param1: str, param2: int = 10) -> ToolResult:
           # 工具逻辑
           return ToolResult.success_result({"result": "success"})
   ```

2. **注册工具**
   ```python
   from src.mcp_tools.base import tool_registry
   
   tool_registry.register(MyCustomTool())
   ```

### 内置示例工具

- **echo**: 回声工具，返回输入文本
- **calculator**: 基础计算器
- **file_info**: 获取文件信息
- **timestamp**: 时间戳转换工具
- **system_info**: 系统信息查询

## 🌐 API接口

### 聊天接口

- `POST /api/chat` - 标准聊天
- `WebSocket /api/chat/stream` - 流式聊天
- `POST /api/chat/clear` - 清空历史
- `GET /api/chat/summary` - 获取对话摘要

### 工具接口

- `GET /api/tools` - 列出所有工具
- `GET /api/tools/{tool_name}` - 获取工具信息
- `POST /api/tools/{tool_name}/execute` - 执行工具

### 系统接口

- `GET /api/health` - 健康检查
- `GET /api/config` - 获取配置信息

详细API文档请访问: http://localhost:8000/docs （调试模式下）

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_config.py

# 生成覆盖率报告
pytest --cov=src tests/
```

## 📚 开发指南

### 项目规范

- **代码风格**: 遵循PEP 8，使用Black格式化
- **类型注解**: 必须使用类型注解
- **文档字符串**: 使用Google风格的docstring
- **日志记录**: 使用loguru，包含唯一标识符
- **错误处理**: 详细的异常处理和日志记录

### 代码质量

```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 贡献流程

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 运行测试
5. 提交 Pull Request

## 🚀 部署指南

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### 生产环境配置

```bash
# 生产环境变量
DEBUG_MODE=false
LOG_LEVEL=WARNING
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

## 🔒 安全注意事项

- **API密钥**: 妥善保管API密钥，不要提交到版本控制
- **网络安全**: 生产环境请配置HTTPS
- **访问控制**: 考虑添加认证机制
- **输入验证**: 所有用户输入都经过验证

## 🛠️ 故障排除

### 常见问题

1. **API密钥错误**
   - 检查`.env`文件中的`LLM_API_KEY`设置
   - 确认API密钥有效且有足够余额

2. **端口占用**
   - 修改`WEB_PORT`配置
   - 检查其他程序是否占用端口

3. **模型不支持**
   - 参考LiteLLM文档确认模型名称
   - 检查模型提供商API状态

### 日志查看

```bash
# 查看实时日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log
```

## 📊 性能优化

- **缓存**: 考虑添加Redis缓存
- **并发**: 调整uvicorn工作进程数
- **监控**: 集成APM工具监控性能

## 🤝 社区

- **问题反馈**: 通过GitHub Issues报告问题
- **功能建议**: 欢迎提交Feature Request
- **讨论交流**: 加入社区讨论

## 📝 更新日志

### v1.0.0 (2024-01-01)
- 🎉 首次发布
- ✨ 支持多种大模型
- 🛠️ MCP工具系统
- 🌐 现代化Web界面

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- Google ADK 团队提供的优秀框架
- LiteLLM 项目简化了模型集成
- FastAPI 和现代Web技术栈
- 开源社区的宝贵贡献

---

**🌟 如果这个项目对您有帮助，请考虑给个Star⭐**

**📧 联系我们**: [your-email@example.com] 