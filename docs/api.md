# Google ADK Chat API 文档

## 概述

本文档描述了Google ADK本地Web大模型交互平台的所有API接口。API基于RESTful设计原则，支持JSON格式的数据交换。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **时间格式**: ISO 8601 (UTC)

## 认证

当前版本暂不需要认证，但建议在生产环境中添加适当的认证机制。

## 响应格式

### 成功响应

```json
{
    "success": true,
    "data": {
        // 具体数据
    },
    "metadata": {
        "timestamp": "2024-01-01T12:00:00Z",
        "version": "1.0.0"
    }
}
```

### 错误响应

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": "详细错误信息"
    },
    "metadata": {
        "timestamp": "2024-01-01T12:00:00Z",
        "request_id": "req_123456"
    }
}
```

## 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 系统接口

### 健康检查

检查系统运行状态。

**请求**
```
GET /api/health
```

**响应**
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "uptime": 3600,
        "llm_status": "connected",
        "tools_loaded": 5
    }
}
```

**字段说明**
- `status`: 系统状态 (healthy/degraded/unhealthy)
- `uptime`: 运行时间（秒）
- `llm_status`: LLM连接状态
- `tools_loaded`: 已加载的工具数量

### 获取配置信息

获取当前系统配置（脱敏后）。

**请求**
```
GET /api/config
```

**响应**
```json
{
    "success": true,
    "data": {
        "llm_model": "gpt-3.5-turbo",
        "llm_base_url": "https://api.openai.com/v1",
        "web_host": "localhost",
        "web_port": 8000,
        "debug_mode": true,
        "version": "1.0.0"
    }
}
```

---

## 聊天接口

### 发送聊天消息

发送消息到大模型并获取回复。

**请求**
```
POST /api/chat
Content-Type: application/json

{
    "message": "你好，世界！",
    "include_history": true,
    "system_message": "你是一个友好的助手"
}
```

**参数说明**
- `message` (required): 用户消息内容
- `include_history` (optional): 是否包含历史对话，默认true
- `system_message` (optional): 系统提示词

**响应**
```json
{
    "success": true,
    "data": {
        "content": "你好！我是AI助手，有什么可以帮助您的吗？",
        "model": "gpt-3.5-turbo",
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "total_tokens": 40
        },
        "response_time": 1.234,
        "message_id": "msg_123456"
    }
}
```

### 流式聊天

通过WebSocket建立流式聊天连接。

**连接**
```
WebSocket: ws://localhost:8000/api/chat/stream
```

**发送消息**
```json
{
    "message": "请介绍一下人工智能",
    "include_history": true,
    "system_message": "你是一个AI专家"
}
```

**接收消息**
```json
{
    "type": "chunk",
    "content": "人工智能是",
    "message_id": "msg_123456"
}
```

**完成消息**
```json
{
    "type": "complete",
    "content": "完整回复内容",
    "usage": {
        "prompt_tokens": 20,
        "completion_tokens": 150,
        "total_tokens": 170
    },
    "message_id": "msg_123456"
}
```

**错误消息**
```json
{
    "type": "error",
    "error": "连接超时",
    "code": "TIMEOUT_ERROR"
}
```

### 清空聊天历史

清空当前会话的聊天历史。

**请求**
```
POST /api/chat/clear
```

**响应**
```json
{
    "success": true,
    "data": {
        "message": "聊天历史已清空",
        "cleared_messages": 15
    }
}
```

### 获取对话摘要

获取当前会话的对话摘要信息。

**请求**
```
GET /api/chat/summary
```

**响应**
```json
{
    "success": true,
    "data": {
        "message_count": 10,
        "total_tokens": 1500,
        "duration": 3600,
        "first_message_time": "2024-01-01T12:00:00Z",
        "last_message_time": "2024-01-01T13:00:00Z",
        "topics": ["AI", "编程", "技术"]
    }
}
```

---

## 工具接口

### 获取工具列表

获取所有可用的MCP工具列表。

**请求**
```
GET /api/tools
```

**响应**
```json
{
    "success": true,
    "data": {
        "tools": [
            {
                "name": "echo",
                "description": "回声工具，返回输入的文本",
                "version": "1.0.0",
                "type": "function",
                "parameters": [
                    {
                        "name": "text",
                        "type": "string",
                        "description": "要回声的文本",
                        "required": true
                    },
                    {
                        "name": "repeat",
                        "type": "integer",
                        "description": "重复次数",
                        "required": false,
                        "default": 1
                    }
                ]
            }
        ],
        "count": 1
    }
}
```

### 获取工具信息

获取特定工具的详细信息。

**请求**
```
GET /api/tools/{tool_name}
```

**路径参数**
- `tool_name`: 工具名称

**响应**
```json
{
    "success": true,
    "data": {
        "name": "calculator",
        "description": "基础数学计算工具",
        "version": "1.0.0",
        "type": "function",
        "parameters": [
            {
                "name": "expression",
                "type": "string",
                "description": "数学表达式",
                "required": true,
                "examples": ["2+3", "10*5", "100/4"]
            }
        ],
        "examples": [
            {
                "input": {"expression": "2+3"},
                "output": {"result": 5}
            }
        ]
    }
}
```

### 执行工具

执行指定的MCP工具。

**请求**
```
POST /api/tools/{tool_name}/execute
Content-Type: application/json

{
    "parameters": {
        "text": "Hello World",
        "repeat": 3
    }
}
```

**路径参数**
- `tool_name`: 工具名称

**请求体参数**
- `parameters`: 工具执行参数

**响应**
```json
{
    "success": true,
    "data": {
        "success": true,
        "data": "[1] Hello World\n[2] Hello World\n[3] Hello World",
        "metadata": {
            "execution_time": 0.001,
            "tool_version": "1.0.0"
        }
    }
}
```

**工具执行失败**
```json
{
    "success": true,
    "data": {
        "success": false,
        "error": "参数验证失败：repeat必须大于0",
        "metadata": {
            "error_code": "VALIDATION_ERROR",
            "tool_version": "1.0.0"
        }
    }
}
```

---

## 页面路由

### 主页

**请求**
```
GET /
```

返回主页面HTML。

### 错误页面

**404页面**
```
GET /404
```

**500页面**
```
GET /500
```

---

## WebSocket事件

### 连接事件

**客户端连接**
```json
{
    "type": "connected",
    "data": {
        "session_id": "session_123456",
        "server_time": "2024-01-01T12:00:00Z"
    }
}
```

**客户端断开**
```json
{
    "type": "disconnected",
    "data": {
        "reason": "client_closed",
        "duration": 3600
    }
}
```

### 聊天事件

**开始处理**
```json
{
    "type": "processing",
    "data": {
        "message_id": "msg_123456",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

**内容块**
```json
{
    "type": "chunk",
    "data": {
        "content": "这是一个",
        "message_id": "msg_123456"
    }
}
```

**处理完成**
```json
{
    "type": "complete",
    "data": {
        "message_id": "msg_123456",
        "total_content": "完整的回复内容",
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 100,
            "total_tokens": 120
        },
        "response_time": 2.5
    }
}
```

**处理错误**
```json
{
    "type": "error",
    "data": {
        "message_id": "msg_123456",
        "error_code": "MODEL_ERROR",
        "error_message": "模型请求失败",
        "details": "连接超时"
    }
}
```

---

## 错误代码

### 系统错误

| 错误代码 | 说明 |
|----------|------|
| SYSTEM_ERROR | 系统内部错误 |
| CONFIG_ERROR | 配置错误 |
| STARTUP_ERROR | 启动失败 |

### LLM错误

| 错误代码 | 说明 |
|----------|------|
| LLM_CONNECTION_ERROR | LLM连接失败 |
| LLM_AUTH_ERROR | LLM认证失败 |
| LLM_QUOTA_ERROR | LLM配额不足 |
| LLM_TIMEOUT_ERROR | LLM请求超时 |
| LLM_INVALID_MODEL | 无效的模型名称 |

### 工具错误

| 错误代码 | 说明 |
|----------|------|
| TOOL_NOT_FOUND | 工具未找到 |
| TOOL_EXECUTION_ERROR | 工具执行失败 |
| TOOL_PARAMETER_ERROR | 工具参数错误 |
| TOOL_TIMEOUT_ERROR | 工具执行超时 |

### 验证错误

| 错误代码 | 说明 |
|----------|------|
| VALIDATION_ERROR | 参数验证失败 |
| MISSING_PARAMETER | 缺少必需参数 |
| INVALID_FORMAT | 无效的数据格式 |
| OUT_OF_RANGE | 参数超出范围 |

---

## 示例代码

### Python客户端

```python
import requests
import json

class ADKChatClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def send_message(self, message, include_history=True):
        """发送聊天消息"""
        url = f"{self.base_url}/api/chat"
        data = {
            "message": message,
            "include_history": include_history
        }
        
        response = requests.post(url, json=data)
        return response.json()
    
    def get_tools(self):
        """获取工具列表"""
        url = f"{self.base_url}/api/tools"
        response = requests.get(url)
        return response.json()
    
    def execute_tool(self, tool_name, parameters):
        """执行工具"""
        url = f"{self.base_url}/api/tools/{tool_name}/execute"
        data = {"parameters": parameters}
        
        response = requests.post(url, json=data)
        return response.json()

# 使用示例
client = ADKChatClient()

# 发送消息
result = client.send_message("你好")
print(result["data"]["content"])

# 获取工具
tools = client.get_tools()
print(f"可用工具: {tools['data']['count']}")

# 执行工具
calc_result = client.execute_tool("calculator", {"expression": "2+3"})
print(f"计算结果: {calc_result['data']['data']}")
```

### JavaScript客户端

```javascript
class ADKChatClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async sendMessage(message, includeHistory = true) {
        const response = await fetch(`${this.baseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                include_history: includeHistory
            })
        });
        
        return await response.json();
    }
    
    async getTools() {
        const response = await fetch(`${this.baseUrl}/api/tools`);
        return await response.json();
    }
    
    async executeTool(toolName, parameters) {
        const response = await fetch(`${this.baseUrl}/api/tools/${toolName}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ parameters })
        });
        
        return await response.json();
    }
    
    connectWebSocket() {
        const ws = new WebSocket(`ws://localhost:8000/api/chat/stream`);
        
        ws.onopen = () => {
            console.log('WebSocket连接已建立');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('接收到消息:', data);
        };
        
        return ws;
    }
}

// 使用示例
const client = new ADKChatClient();

// 发送消息
client.sendMessage('你好').then(result => {
    console.log(result.data.content);
});

// WebSocket示例
const ws = client.connectWebSocket();
ws.onopen = () => {
    ws.send(JSON.stringify({
        message: '请介绍一下AI',
        include_history: true
    }));
};
```

---

## 性能优化建议

1. **缓存**: 对频繁请求的数据进行缓存
2. **压缩**: 启用gzip压缩减少传输大小
3. **连接池**: 复用HTTP连接提高性能
4. **限流**: 实现请求限流防止过载
5. **监控**: 添加性能监控和告警

## 安全注意事项

1. **输入验证**: 严格验证所有输入参数
2. **权限控制**: 实现适当的访问控制
3. **日志审计**: 记录所有API调用
4. **HTTPS**: 生产环境使用HTTPS
5. **API密钥**: 添加API密钥认证机制

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础聊天功能
- MCP工具系统
- WebSocket流式支持 