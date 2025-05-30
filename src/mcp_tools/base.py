"""
MCP工具基类模块

定义MCP工具的标准接口和基础功能，
为自定义工具提供统一的规范和框架。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import inspect
from loguru import logger


class ToolType(Enum):
    """工具类型枚举"""
    FUNCTION = "function"  # 函数型工具
    SERVICE = "service"    # 服务型工具
    UTILITY = "utility"    # 实用工具


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: type
    description: str
    required: bool = True
    default: Any = None
    
    def __post_init__(self):
        if not self.required and self.default is None:
            raise ValueError(f"可选参数 {self.name} 必须提供默认值")


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_result(cls, data: Any, metadata: Optional[Dict[str, Any]] = None):
        """创建成功结果"""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None):
        """创建错误结果"""
        return cls(success=False, error=error, metadata=metadata)


class MCPTool(ABC):
    """MCP工具基类"""
    
    def __init__(self):
        self._validate_implementation()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """工具版本"""
        pass
    
    @property
    def tool_type(self) -> ToolType:
        """工具类型，默认为函数型"""
        return ToolType.FUNCTION
    
    @property
    def parameters(self) -> List[ToolParameter]:
        """工具参数定义，默认从execute方法自动推断"""
        return self._extract_parameters()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """工具元数据"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": self.tool_type.value,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type.__name__,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default
                }
                for param in self.parameters
            ]
        }
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具功能
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    def execute_sync(self, **kwargs) -> ToolResult:
        """
        同步执行工具功能
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        import asyncio
        return asyncio.run(self.execute(**kwargs))
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """
        验证参数
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            Dict[str, Any]: 验证后的参数
            
        Raises:
            ValueError: 参数验证失败
        """
        validated = {}
        
        for param in self.parameters:
            if param.name in kwargs:
                # 参数存在，验证类型
                value = kwargs[param.name]
                if not isinstance(value, param.type):
                    try:
                        # 尝试类型转换
                        value = param.type(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"参数 {param.name} 类型错误，期望 {param.type.__name__}")
                validated[param.name] = value
            elif param.required:
                # 必需参数缺失
                raise ValueError(f"缺少必需参数: {param.name}")
            else:
                # 使用默认值
                validated[param.name] = param.default
        
        return validated
    
    def _validate_implementation(self):
        """验证工具实现是否正确"""
        # 验证必需属性
        if not hasattr(self, 'name') or not self.name:
            raise NotImplementedError("工具必须实现name属性")
        
        if not hasattr(self, 'description') or not self.description:
            raise NotImplementedError("工具必须实现description属性")
        
        if not hasattr(self, 'version') or not self.version:
            raise NotImplementedError("工具必须实现version属性")
        
        # 验证execute方法
        if not hasattr(self, 'execute'):
            raise NotImplementedError("工具必须实现execute方法")
        
        logger.debug(f"MCP工具 {self.name} 验证通过")
    
    def _extract_parameters(self) -> List[ToolParameter]:
        """从execute方法自动提取参数定义"""
        parameters = []
        
        try:
            sig = inspect.signature(self.execute)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 获取参数类型
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                
                # 判断是否必需
                required = param.default == inspect.Parameter.empty
                
                # 获取默认值
                default = None if required else param.default
                
                # 创建参数定义（描述需要子类覆盖parameters属性来提供）
                tool_param = ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"参数 {param_name}",  # 默认描述
                    required=required,
                    default=default
                )
                
                parameters.append(tool_param)
        
        except Exception as e:
            logger.warning(f"无法自动提取参数定义: {e}")
        
        return parameters
    
    def __str__(self) -> str:
        return f"{self.name} v{self.version} - {self.description}"
    
    def __repr__(self) -> str:
        return f"MCPTool(name='{self.name}', version='{self.version}')"


class MCPToolRegistry:
    """MCP工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        logger.info("MCP工具注册表初始化完成")
    
    def register(self, tool: MCPTool):
        """
        注册工具
        
        Args:
            tool: MCP工具实例
        """
        if not isinstance(tool, MCPTool):
            raise TypeError("只能注册MCPTool类型的工具")
        
        if tool.name in self._tools:
            logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
        
        self._tools[tool.name] = tool
        logger.info(f"注册MCP工具: {tool}")
    
    def unregister(self, tool_name: str):
        """
        注销工具
        
        Args:
            tool_name: 工具名称
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"注销MCP工具: {tool_name}")
        else:
            logger.warning(f"工具 {tool_name} 不存在")
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[MCPTool]: 工具实例
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    def get_all_tools(self) -> Dict[str, MCPTool]:
        """
        获取所有工具
        
        Returns:
            Dict[str, MCPTool]: 工具字典
        """
        return self._tools.copy()
    
    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具元数据
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具元数据
        """
        tool = self.get_tool(tool_name)
        return tool.metadata if tool else None
    
    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有工具的元数据
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有工具元数据
        """
        return {name: tool.metadata for name, tool in self._tools.items()}


# 全局工具注册表实例
tool_registry = MCPToolRegistry() 