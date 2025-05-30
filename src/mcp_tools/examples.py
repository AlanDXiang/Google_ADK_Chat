"""
示例MCP工具

提供一些基本的示例工具，演示如何创建自定义MCP工具。
开发者可以参考这些示例来创建自己的工具。
"""

import asyncio
import time
import os
import json
from typing import Dict, Any, List
from datetime import datetime

from .base import MCPTool, ToolResult, ToolParameter, ToolType


class EchoTool(MCPTool):
    """回声工具示例 - 简单地返回输入的文本"""
    
    @property
    def name(self) -> str:
        return "echo"
    
    @property
    def description(self) -> str:
        return "回声工具，返回输入的文本内容"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type=str,
                description="要回声的文本内容",
                required=True
            ),
            ToolParameter(
                name="repeat",
                type=int,
                description="重复次数",
                required=False,
                default=1
            )
        ]
    
    async def execute(self, text: str, repeat: int = 1) -> ToolResult:
        try:
            validated_params = self.validate_parameters(text=text, repeat=repeat)
            
            if validated_params["repeat"] < 1:
                return ToolResult.error_result("重复次数必须大于0")
            
            result = []
            for i in range(validated_params["repeat"]):
                result.append(f"[{i+1}] {validated_params['text']}")
            
            return ToolResult.success_result(
                data="\n".join(result),
                metadata={
                    "original_text": text,
                    "repeat_count": repeat,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            return ToolResult.error_result(f"执行回声工具失败: {str(e)}")


class CalculatorTool(MCPTool):
    """计算器工具示例 - 执行基本的数学运算"""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "基础计算器，支持加减乘除运算"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type=str,
                description="要计算的数学表达式，如 '2 + 3 * 4'",
                required=True
            )
        ]
    
    async def execute(self, expression: str) -> ToolResult:
        try:
            validated_params = self.validate_parameters(expression=expression)
            expr = validated_params["expression"].strip()
            
            # 安全的数学表达式评估（仅允许基本运算）
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expr):
                return ToolResult.error_result("表达式包含不允许的字符")
            
            # 使用eval进行计算（在生产环境中应该使用更安全的解析器）
            result = eval(expr)
            
            return ToolResult.success_result(
                data=result,
                metadata={
                    "expression": expr,
                    "result_type": type(result).__name__,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except ZeroDivisionError:
            return ToolResult.error_result("除零错误")
        except SyntaxError:
            return ToolResult.error_result("表达式语法错误")
        except Exception as e:
            return ToolResult.error_result(f"计算失败: {str(e)}")


class FileInfoTool(MCPTool):
    """文件信息工具示例 - 获取文件的基本信息"""
    
    @property
    def name(self) -> str:
        return "file_info"
    
    @property
    def description(self) -> str:
        return "获取文件的基本信息，如大小、创建时间等"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.UTILITY
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type=str,
                description="文件路径",
                required=True
            )
        ]
    
    async def execute(self, file_path: str) -> ToolResult:
        try:
            validated_params = self.validate_parameters(file_path=file_path)
            path = validated_params["file_path"]
            
            if not os.path.exists(path):
                return ToolResult.error_result(f"文件不存在: {path}")
            
            stat = os.stat(path)
            
            file_info = {
                "path": os.path.abspath(path),
                "name": os.path.basename(path),
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": os.path.isfile(path),
                "is_directory": os.path.isdir(path),
                "readable": os.access(path, os.R_OK),
                "writable": os.access(path, os.W_OK),
                "executable": os.access(path, os.X_OK)
            }
            
            return ToolResult.success_result(
                data=file_info,
                metadata={
                    "operation": "file_info",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except PermissionError:
            return ToolResult.error_result("没有权限访问该文件")
        except Exception as e:
            return ToolResult.error_result(f"获取文件信息失败: {str(e)}")


class TimestampTool(MCPTool):
    """时间戳工具示例 - 时间相关的实用功能"""
    
    @property
    def name(self) -> str:
        return "timestamp"
    
    @property
    def description(self) -> str:
        return "时间戳工具，支持时间格式转换和计算"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.UTILITY
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type=str,
                description="操作类型: 'now', 'convert', 'parse'",
                required=True
            ),
            ToolParameter(
                name="value",
                type=str,
                description="时间值（用于convert和parse操作）",
                required=False,
                default=""
            ),
            ToolParameter(
                name="format",
                type=str,
                description="时间格式",
                required=False,
                default="%Y-%m-%d %H:%M:%S"
            )
        ]
    
    async def execute(self, action: str, value: str = "", format: str = "%Y-%m-%d %H:%M:%S") -> ToolResult:
        try:
            validated_params = self.validate_parameters(action=action, value=value, format=format)
            
            action = validated_params["action"].lower()
            value = validated_params["value"]
            fmt = validated_params["format"]
            
            if action == "now":
                # 返回当前时间信息
                now = datetime.now()
                result = {
                    "timestamp": now.timestamp(),
                    "iso_format": now.isoformat(),
                    "formatted": now.strftime(fmt),
                    "unix_timestamp": int(now.timestamp())
                }
            
            elif action == "convert":
                # 将时间戳转换为格式化时间
                if not value:
                    return ToolResult.error_result("convert操作需要提供时间戳值")
                
                timestamp = float(value)
                dt = datetime.fromtimestamp(timestamp)
                result = {
                    "timestamp": timestamp,
                    "iso_format": dt.isoformat(),
                    "formatted": dt.strftime(fmt),
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second
                }
            
            elif action == "parse":
                # 将格式化时间解析为时间戳
                if not value:
                    return ToolResult.error_result("parse操作需要提供时间字符串")
                
                dt = datetime.strptime(value, fmt)
                result = {
                    "input_string": value,
                    "timestamp": dt.timestamp(),
                    "iso_format": dt.isoformat(),
                    "unix_timestamp": int(dt.timestamp())
                }
            
            else:
                return ToolResult.error_result(f"不支持的操作: {action}")
            
            return ToolResult.success_result(
                data=result,
                metadata={
                    "action": action,
                    "format_used": fmt,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except ValueError as e:
            return ToolResult.error_result(f"时间格式错误: {str(e)}")
        except Exception as e:
            return ToolResult.error_result(f"时间戳工具执行失败: {str(e)}")


class SystemInfoTool(MCPTool):
    """系统信息工具示例 - 获取系统基本信息"""
    
    @property
    def name(self) -> str:
        return "system_info"
    
    @property
    def description(self) -> str:
        return "获取系统基本信息，如操作系统、Python版本等"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.UTILITY
    
    async def execute(self) -> ToolResult:
        try:
            import platform
            import sys
            
            system_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "python_version_info": {
                    "major": sys.version_info.major,
                    "minor": sys.version_info.minor,
                    "micro": sys.version_info.micro
                },
                "current_working_directory": os.getcwd(),
                "environment_variables_count": len(os.environ)
            }
            
            return ToolResult.success_result(
                data=system_info,
                metadata={
                    "collection_time": datetime.now().isoformat(),
                    "tool_version": self.version
                }
            )
        
        except Exception as e:
            return ToolResult.error_result(f"获取系统信息失败: {str(e)}")


# 注册示例工具的便捷函数
def register_example_tools():
    """注册所有示例工具到全局注册表"""
    from .base import tool_registry
    
    example_tools = [
        EchoTool(),
        CalculatorTool(),
        FileInfoTool(),
        TimestampTool(),
        SystemInfoTool()
    ]
    
    for tool in example_tools:
        tool_registry.register(tool)
    
    return len(example_tools) 