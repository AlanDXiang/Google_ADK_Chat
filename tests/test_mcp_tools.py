"""
MCP工具模块测试

测试工具基类、工具注册表和示例工具的功能。
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.mcp_tools.base import (
    MCPTool, ToolResult, ToolParameter, ToolType, MCPToolRegistry
)
from src.mcp_tools.examples import (
    EchoTool, CalculatorTool, FileInfoTool, TimestampTool, SystemInfoTool
)


class TestToolResult:
    """工具结果测试"""
    
    def test_success_result(self):
        """测试成功结果创建"""
        result = ToolResult.success_result("test data", {"key": "value"})
        
        assert result.success is True
        assert result.data == "test data"
        assert result.error is None
        assert result.metadata == {"key": "value"}
    
    def test_error_result(self):
        """测试错误结果创建"""
        result = ToolResult.error_result("test error", {"context": "test"})
        
        assert result.success is False
        assert result.data is None
        assert result.error == "test error"
        assert result.metadata == {"context": "test"}


class TestToolParameter:
    """工具参数测试"""
    
    def test_required_parameter(self):
        """测试必需参数"""
        param = ToolParameter(
            name="test_param",
            type=str,
            description="Test parameter",
            required=True
        )
        
        assert param.name == "test_param"
        assert param.type == str
        assert param.description == "Test parameter"
        assert param.required is True
        assert param.default is None
    
    def test_optional_parameter_with_default(self):
        """测试有默认值的可选参数"""
        param = ToolParameter(
            name="optional_param",
            type=int,
            description="Optional parameter",
            required=False,
            default=10
        )
        
        assert param.required is False
        assert param.default == 10
    
    def test_optional_parameter_without_default_raises_error(self):
        """测试无默认值的可选参数应该抛出错误"""
        with pytest.raises(ValueError):
            ToolParameter(
                name="invalid_param",
                type=str,
                description="Invalid parameter",
                required=False  # 没有提供default值
            )


class MockTool(MCPTool):
    """测试用的模拟工具"""
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "Mock tool for testing"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def execute(self, text: str, count: int = 1) -> ToolResult:
        return ToolResult.success_result(f"Processed: {text} x {count}")


class InvalidTool:
    """无效的工具类，用于测试验证"""
    pass


class TestMCPTool:
    """MCP工具基类测试"""
    
    def test_tool_initialization(self):
        """测试工具初始化"""
        tool = MockTool()
        
        assert tool.name == "mock_tool"
        assert tool.description == "Mock tool for testing"
        assert tool.version == "1.0.0"
        assert tool.tool_type == ToolType.FUNCTION
    
    def test_tool_metadata(self):
        """测试工具元数据"""
        tool = MockTool()
        metadata = tool.metadata
        
        assert metadata["name"] == "mock_tool"
        assert metadata["description"] == "Mock tool for testing"
        assert metadata["version"] == "1.0.0"
        assert metadata["type"] == "function"
        assert "parameters" in metadata
    
    def test_parameter_extraction(self):
        """测试参数自动提取"""
        tool = MockTool()
        params = tool.parameters
        
        assert len(params) == 2
        
        # 检查text参数
        text_param = params[0]
        assert text_param.name == "text"
        assert text_param.type == str
        assert text_param.required is True
        
        # 检查count参数
        count_param = params[1]
        assert count_param.name == "count"
        assert count_param.type == int
        assert count_param.required is False
        assert count_param.default == 1
    
    def test_parameter_validation_success(self):
        """测试参数验证成功"""
        tool = MockTool()
        
        # 测试所有参数都提供
        validated = tool.validate_parameters(text="hello", count=3)
        assert validated == {"text": "hello", "count": 3}
        
        # 测试只提供必需参数
        validated = tool.validate_parameters(text="hello")
        assert validated == {"text": "hello", "count": 1}
    
    def test_parameter_validation_missing_required(self):
        """测试缺少必需参数"""
        tool = MockTool()
        
        with pytest.raises(ValueError, match="缺少必需参数: text"):
            tool.validate_parameters(count=5)
    
    def test_parameter_validation_type_conversion(self):
        """测试参数类型转换"""
        tool = MockTool()
        
        # 测试字符串到整数的转换
        validated = tool.validate_parameters(text="hello", count="5")
        assert validated == {"text": "hello", "count": 5}
    
    def test_parameter_validation_type_error(self):
        """测试参数类型错误"""
        tool = MockTool()
        
        with pytest.raises(ValueError, match="参数 count 类型错误"):
            tool.validate_parameters(text="hello", count="invalid")
    
    @pytest.mark.asyncio
    async def test_execute_method(self):
        """测试工具执行方法"""
        tool = MockTool()
        
        result = await tool.execute(text="test", count=2)
        
        assert result.success is True
        assert result.data == "Processed: test x 2"
    
    def test_execute_sync(self):
        """测试同步执行方法"""
        tool = MockTool()
        
        result = tool.execute_sync(text="test", count=2)
        
        assert result.success is True
        assert result.data == "Processed: test x 2"
    
    def test_string_representation(self):
        """测试字符串表示"""
        tool = MockTool()
        
        assert str(tool) == "mock_tool v1.0.0 - Mock tool for testing"
        assert repr(tool) == "MCPTool(name='mock_tool', version='1.0.0')"


class TestMCPToolRegistry:
    """MCP工具注册表测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.registry = MCPToolRegistry()
    
    def test_register_tool(self):
        """测试工具注册"""
        tool = MockTool()
        
        self.registry.register(tool)
        
        assert "mock_tool" in self.registry.list_tools()
        assert self.registry.get_tool("mock_tool") is tool
    
    def test_register_invalid_tool(self):
        """测试注册无效工具"""
        invalid_tool = InvalidTool()
        
        with pytest.raises(TypeError, match="只能注册MCPTool类型的工具"):
            self.registry.register(invalid_tool)
    
    def test_register_duplicate_tool(self):
        """测试注册重复工具"""
        tool1 = MockTool()
        tool2 = MockTool()
        
        with patch('src.mcp_tools.base.logger') as mock_logger:
            self.registry.register(tool1)
            self.registry.register(tool2)  # 应该覆盖第一个
            
            assert self.registry.get_tool("mock_tool") is tool2
            mock_logger.warning.assert_called()
    
    def test_unregister_tool(self):
        """测试工具注销"""
        tool = MockTool()
        
        self.registry.register(tool)
        self.registry.unregister("mock_tool")
        
        assert "mock_tool" not in self.registry.list_tools()
        assert self.registry.get_tool("mock_tool") is None
    
    def test_unregister_nonexistent_tool(self):
        """测试注销不存在的工具"""
        with patch('src.mcp_tools.base.logger') as mock_logger:
            self.registry.unregister("nonexistent_tool")
            
            mock_logger.warning.assert_called()
    
    def test_get_all_tools(self):
        """测试获取所有工具"""
        tool1 = MockTool()
        tool2 = EchoTool()
        
        self.registry.register(tool1)
        self.registry.register(tool2)
        
        all_tools = self.registry.get_all_tools()
        
        assert len(all_tools) == 2
        assert "mock_tool" in all_tools
        assert "echo" in all_tools
    
    def test_get_tool_metadata(self):
        """测试获取工具元数据"""
        tool = MockTool()
        self.registry.register(tool)
        
        metadata = self.registry.get_tool_metadata("mock_tool")
        
        assert metadata is not None
        assert metadata["name"] == "mock_tool"
        assert metadata["version"] == "1.0.0"
    
    def test_get_all_metadata(self):
        """测试获取所有工具元数据"""
        tool1 = MockTool()
        tool2 = EchoTool()
        
        self.registry.register(tool1)
        self.registry.register(tool2)
        
        all_metadata = self.registry.get_all_metadata()
        
        assert len(all_metadata) == 2
        assert "mock_tool" in all_metadata
        assert "echo" in all_metadata


class TestExampleTools:
    """示例工具测试"""
    
    @pytest.mark.asyncio
    async def test_echo_tool(self):
        """测试回声工具"""
        tool = EchoTool()
        
        # 测试基本回声
        result = await tool.execute(text="hello", repeat=1)
        assert result.success is True
        assert result.data == "[1] hello"
        
        # 测试多次重复
        result = await tool.execute(text="world", repeat=3)
        assert result.success is True
        assert "[1] world" in result.data
        assert "[2] world" in result.data
        assert "[3] world" in result.data
        
        # 测试无效重复次数
        result = await tool.execute(text="test", repeat=0)
        assert result.success is False
        assert "重复次数必须大于0" in result.error
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self):
        """测试计算器工具"""
        tool = CalculatorTool()
        
        # 测试基本运算
        result = await tool.execute(expression="2 + 3")
        assert result.success is True
        assert result.data == 5
        
        # 测试复杂表达式
        result = await tool.execute(expression="2 * 3 + 4")
        assert result.success is True
        assert result.data == 10
        
        # 测试除零错误
        result = await tool.execute(expression="1 / 0")
        assert result.success is False
        assert "除零错误" in result.error
        
        # 测试无效字符
        result = await tool.execute(expression="import os")
        assert result.success is False
        assert "不允许的字符" in result.error
    
    @pytest.mark.asyncio
    async def test_system_info_tool(self):
        """测试系统信息工具"""
        tool = SystemInfoTool()
        
        result = await tool.execute()
        
        assert result.success is True
        assert isinstance(result.data, dict)
        assert "system" in result.data
        assert "python_version" in result.data
        assert "current_working_directory" in result.data
    
    @pytest.mark.asyncio
    async def test_timestamp_tool(self):
        """测试时间戳工具"""
        tool = TimestampTool()
        
        # 测试获取当前时间
        result = await tool.execute(action="now")
        assert result.success is True
        assert "timestamp" in result.data
        assert "iso_format" in result.data
        
        # 测试时间戳转换
        result = await tool.execute(action="convert", value="1640995200")
        assert result.success is True
        assert "formatted" in result.data
        
        # 测试无效操作
        result = await tool.execute(action="invalid")
        assert result.success is False
        assert "不支持的操作" in result.error
    
    @pytest.mark.asyncio
    async def test_file_info_tool(self):
        """测试文件信息工具"""
        tool = FileInfoTool()
        
        # 测试不存在的文件
        result = await tool.execute(file_path="nonexistent_file.txt")
        assert result.success is False
        assert "文件不存在" in result.error
        
        # 测试存在的文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_file = f.name
        
        try:
            result = await tool.execute(file_path=temp_file)
            assert result.success is True
            assert "path" in result.data
            assert "size" in result.data
            assert "is_file" in result.data
        finally:
            import os
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__]) 