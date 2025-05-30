# MCP工具开发指南

## 概述

本指南将帮助开发者创建自定义的MCP（Model Context Protocol）工具，以扩展Google ADK本地Web大模型交互平台的功能。

## MCP工具架构

### 核心组件

1. **MCPTool基类** - 所有工具的抽象基类
2. **ToolParameter** - 工具参数定义
3. **ToolResult** - 工具执行结果
4. **MCPToolRegistry** - 工具注册表

### 工具类型

- **FUNCTION** - 函数型工具（默认）
- **SERVICE** - 服务型工具
- **UTILITY** - 实用工具

## 创建自定义工具

### 1. 基础工具结构

```python
from src.mcp_tools.base import MCPTool, ToolResult, ToolParameter

class MyTool(MCPTool):
    @property
    def name(self) -> str:
        """工具名称，必须唯一"""
        return "my_tool"
    
    @property
    def description(self) -> str:
        """工具描述，用于用户界面"""
        return "我的自定义工具"
    
    @property
    def version(self) -> str:
        """工具版本"""
        return "1.0.0"
    
    async def execute(self, **kwargs) -> ToolResult:
        """工具执行逻辑"""
        # 实现工具功能
        return ToolResult.success_result("执行成功")
```

### 2. 参数定义

工具参数可以通过两种方式定义：

#### 方式一：自动参数提取（推荐）

```python
async def execute(self, text: str, count: int = 1, format: str = "json") -> ToolResult:
    """
    参数会自动从方法签名中提取：
    - text: 必需参数（str类型）
    - count: 可选参数（int类型，默认值1）
    - format: 可选参数（str类型，默认值"json"）
    """
    pass
```

#### 方式二：手动参数定义

```python
@property
def parameters(self) -> List[ToolParameter]:
    return [
        ToolParameter(
            name="text",
            type=str,
            description="输入文本",
            required=True
        ),
        ToolParameter(
            name="count",
            type=int,
            description="重复次数",
            required=False,
            default=1
        )
    ]
```

### 3. 返回结果

使用`ToolResult`类返回执行结果：

```python
# 成功结果
return ToolResult.success_result(
    data={"message": "执行成功", "value": 42},
    metadata={"execution_time": 0.123}
)

# 错误结果
return ToolResult.error_result(
    error="执行失败：文件不存在",
    metadata={"error_code": 404}
)
```

## 完整示例

### 文本处理工具

```python
import re
from typing import List
from src.mcp_tools.base import MCPTool, ToolResult, ToolType

class TextProcessorTool(MCPTool):
    @property
    def name(self) -> str:
        return "text_processor"
    
    @property
    def description(self) -> str:
        return "文本处理工具，支持大小写转换、单词统计等功能"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.UTILITY
    
    async def execute(
        self, 
        text: str, 
        operation: str = "lowercase",
        include_stats: bool = False
    ) -> ToolResult:
        """
        文本处理工具
        
        Args:
            text: 要处理的文本
            operation: 操作类型 (lowercase, uppercase, title, count_words, clean)
            include_stats: 是否包含统计信息
        """
        try:
            # 执行操作
            if operation == "lowercase":
                result = text.lower()
            elif operation == "uppercase":
                result = text.upper()
            elif operation == "title":
                result = text.title()
            elif operation == "count_words":
                words = re.findall(r'\b\w+\b', text)
                result = len(words)
            elif operation == "clean":
                result = re.sub(r'[^\w\s]', '', text)
            else:
                return ToolResult.error_result(f"不支持的操作: {operation}")
            
            # 准备返回数据
            data = {
                "original": text,
                "result": result,
                "operation": operation
            }
            
            # 添加统计信息
            if include_stats:
                data["stats"] = {
                    "character_count": len(text),
                    "word_count": len(re.findall(r'\b\w+\b', text)),
                    "line_count": text.count('\n') + 1
                }
            
            return ToolResult.success_result(data)
            
        except Exception as e:
            return ToolResult.error_result(f"文本处理失败: {str(e)}")
```

### HTTP请求工具

```python
import httpx
import asyncio
from src.mcp_tools.base import MCPTool, ToolResult, ToolType

class HttpRequestTool(MCPTool):
    @property
    def name(self) -> str:
        return "http_request"
    
    @property
    def description(self) -> str:
        return "HTTP请求工具，支持GET、POST等方法"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.SERVICE
    
    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: dict = None,
        data: dict = None,
        timeout: int = 30
    ) -> ToolResult:
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法 (GET, POST, PUT, DELETE)
            headers: 请求头
            data: 请求体数据
            timeout: 超时时间（秒）
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers or {},
                    json=data,
                    timeout=timeout
                )
                
                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "method": method.upper()
                }
                
                # 尝试解析JSON响应
                try:
                    result["json"] = response.json()
                except:
                    result["text"] = response.text
                
                return ToolResult.success_result(
                    data=result,
                    metadata={
                        "response_time": response.elapsed.total_seconds(),
                        "content_type": response.headers.get("content-type")
                    }
                )
                
        except Exception as e:
            return ToolResult.error_result(f"HTTP请求失败: {str(e)}")
```

## 工具注册

### 方式一：在工具文件中直接注册

```python
# 在工具定义文件末尾
from src.mcp_tools.base import tool_registry

# 注册工具
tool_registry.register(TextProcessorTool())
tool_registry.register(HttpRequestTool())
```

### 方式二：在启动时批量注册

```python
# 在main.py或app.py中
from src.mcp_tools.base import tool_registry
from my_tools import MyTool1, MyTool2

def register_custom_tools():
    """注册自定义工具"""
    tools = [
        MyTool1(),
        MyTool2(),
    ]
    
    for tool in tools:
        tool_registry.register(tool)
```

## 最佳实践

### 1. 错误处理

```python
async def execute(self, **kwargs) -> ToolResult:
    try:
        # 验证参数
        if not kwargs.get("required_param"):
            return ToolResult.error_result("缺少必需参数: required_param")
        
        # 执行业务逻辑
        result = await self._do_work(kwargs)
        
        return ToolResult.success_result(result)
        
    except ValidationError as e:
        return ToolResult.error_result(f"参数验证失败: {e}")
    except Exception as e:
        # 记录详细错误信息
        logger.exception(f"工具执行失败 - {self.name}")
        return ToolResult.error_result(f"内部错误: {type(e).__name__}")
```

### 2. 日志记录

```python
from src.core.logger import get_logger

class MyTool(MCPTool):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(f"tool.{self.name}")
    
    async def execute(self, **kwargs) -> ToolResult:
        self.logger.info(f"开始执行工具: {self.name}")
        self.logger.debug(f"参数: {kwargs}")
        
        try:
            result = await self._process(kwargs)
            self.logger.info(f"工具执行成功: {self.name}")
            return ToolResult.success_result(result)
        except Exception as e:
            self.logger.error(f"工具执行失败: {self.name} - {e}")
            return ToolResult.error_result(str(e))
```

### 3. 参数验证

```python
def validate_parameters(self, **kwargs) -> Dict[str, Any]:
    """自定义参数验证"""
    validated = super().validate_parameters(**kwargs)
    
    # 自定义验证逻辑
    if validated.get("count", 0) < 1:
        raise ValueError("count参数必须大于0")
    
    if validated.get("format") not in ["json", "xml", "text"]:
        raise ValueError("format参数必须是 json、xml 或 text")
    
    return validated
```

### 4. 异步处理

```python
import asyncio
from typing import List

async def execute(self, urls: List[str]) -> ToolResult:
    """并发处理多个URL"""
    try:
        # 创建并发任务
        tasks = [self._fetch_url(url) for url in urls]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successes = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({"url": urls[i], "error": str(result)})
            else:
                successes.append(result)
        
        return ToolResult.success_result({
            "successes": successes,
            "errors": errors,
            "total": len(urls),
            "success_count": len(successes)
        })
        
    except Exception as e:
        return ToolResult.error_result(f"批量处理失败: {e}")
```

## 工具测试

### 单元测试示例

```python
import pytest
from my_tools import TextProcessorTool

class TestTextProcessorTool:
    @pytest.fixture
    def tool(self):
        return TextProcessorTool()
    
    @pytest.mark.asyncio
    async def test_lowercase_operation(self, tool):
        result = await tool.execute(text="HELLO WORLD", operation="lowercase")
        
        assert result.success is True
        assert result.data["result"] == "hello world"
        assert result.data["operation"] == "lowercase"
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self, tool):
        result = await tool.execute(text="test", operation="invalid")
        
        assert result.success is False
        assert "不支持的操作" in result.error
    
    @pytest.mark.asyncio
    async def test_with_stats(self, tool):
        result = await tool.execute(
            text="Hello World", 
            operation="lowercase",
            include_stats=True
        )
        
        assert result.success is True
        assert "stats" in result.data
        assert result.data["stats"]["word_count"] == 2
```

## 部署和分发

### 1. 打包工具

```python
# setup.py for custom tools package
from setuptools import setup, find_packages

setup(
    name="my-mcp-tools",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "httpx",
        "pillow",
        # 其他依赖
    ],
    python_requires=">=3.8",
)
```

### 2. 动态加载

```python
import importlib
import pkgutil

def load_tools_from_package(package_name: str):
    """从包中动态加载工具"""
    try:
        package = importlib.import_module(package_name)
        
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package_name}.{module_name}")
            
            # 查找MCPTool子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, MCPTool) and 
                    attr != MCPTool):
                    
                    tool_registry.register(attr())
                    
    except Exception as e:
        logger.error(f"加载工具包失败: {package_name} - {e}")
```

## 故障排除

### 常见问题

1. **工具注册失败**
   - 检查工具名称是否唯一
   - 确保正确继承MCPTool基类
   - 验证所有必需属性已实现

2. **参数验证错误**
   - 检查参数类型注解
   - 确保默认值正确设置
   - 验证必需参数标记

3. **执行超时**
   - 为长时间运行的操作添加超时控制
   - 考虑使用异步操作
   - 实现进度报告机制

### 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger("tool").setLevel(logging.DEBUG)

# 使用装饰器记录执行时间
from src.core.logger import log_execution

class MyTool(MCPTool):
    @log_execution
    async def execute(self, **kwargs) -> ToolResult:
        # 工具逻辑
        pass
```

## 示例工具仓库

查看 `src/mcp_tools/examples.py` 获取更多示例：

- EchoTool - 简单的回声工具
- CalculatorTool - 数学计算工具
- FileInfoTool - 文件信息查询
- TimestampTool - 时间戳处理
- SystemInfoTool - 系统信息获取

通过学习这些示例，您可以快速掌握MCP工具开发的最佳实践。 