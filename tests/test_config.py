"""
配置模块测试

测试配置加载、验证和环境变量处理功能。
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from src.core.config import Settings, load_settings, validate_config


class TestSettings:
    """设置类测试"""
    
    def test_default_values(self):
        """测试默认值设置"""
        settings = Settings()
        
        assert settings.llm_base_url == "https://api.openai.com/v1"
        assert settings.llm_model == "gpt-3.5-turbo"
        assert settings.llm_temperature == 0.7
        assert settings.llm_max_tokens == 2048
        assert settings.llm_timeout == 30
        assert settings.web_host == "localhost"
        assert settings.web_port == 8000
        assert settings.debug_mode is False
        assert settings.log_level == "INFO"
        assert settings.log_file == "logs/app.log"
        assert settings.mcp_tools_dir == "src/mcp_tools"
    
    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {
            'LLM_MODEL': 'gpt-4',
            'LLM_TEMPERATURE': '0.5',
            'WEB_PORT': '9000',
            'DEBUG_MODE': 'true'
        }):
            settings = Settings()
            
            assert settings.llm_model == "gpt-4"
            assert settings.llm_temperature == 0.5
            assert settings.web_port == 9000
            assert settings.debug_mode is True
    
    def test_api_key_validation(self):
        """测试API密钥验证"""
        # 测试默认API密钥警告
        with patch('src.core.config.logger') as mock_logger:
            settings = Settings(llm_api_key="your_api_key_here")
            mock_logger.warning.assert_called_once()
        
        # 测试空API密钥警告
        with patch('src.core.config.logger') as mock_logger:
            settings = Settings(llm_api_key="")
            mock_logger.warning.assert_called_once()
        
        # 测试有效API密钥
        with patch('src.core.config.logger') as mock_logger:
            settings = Settings(llm_api_key="sk-valid-key")
            mock_logger.warning.assert_not_called()
    
    def test_log_level_validation(self):
        """测试日志级别验证"""
        # 测试有效日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            settings = Settings(log_level=level)
            assert settings.log_level == level.upper()
        
        # 测试无效日志级别
        with pytest.raises(ValueError):
            Settings(log_level="INVALID")
    
    def test_port_validation(self):
        """测试端口号验证"""
        # 测试有效端口
        settings = Settings(web_port=8080)
        assert settings.web_port == 8080
        
        # 测试无效端口（太小）
        with pytest.raises(ValueError):
            Settings(web_port=0)
        
        # 测试无效端口（太大）
        with pytest.raises(ValueError):
            Settings(web_port=70000)
    
    def test_temperature_validation(self):
        """测试温度参数验证"""
        # 测试有效温度
        settings = Settings(llm_temperature=0.8)
        assert settings.llm_temperature == 0.8
        
        # 测试无效温度（太小）
        with pytest.raises(ValueError):
            Settings(llm_temperature=-0.1)
        
        # 测试无效温度（太大）
        with pytest.raises(ValueError):
            Settings(llm_temperature=2.1)


class TestLoadSettings:
    """设置加载测试"""
    
    def test_load_without_env_file(self):
        """测试无.env文件时的加载"""
        with patch('src.core.config.os.path.exists', return_value=False):
            with patch('src.core.config.logger') as mock_logger:
                settings = load_settings()
                
                assert isinstance(settings, Settings)
                mock_logger.warning.assert_called()
    
    def test_load_with_env_file(self):
        """测试有.env文件时的加载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("LLM_MODEL=gpt-4\n")
            f.write("WEB_PORT=9000\n")
            env_file = f.name
        
        try:
            with patch('src.core.config.load_dotenv') as mock_load_dotenv:
                with patch('src.core.config.os.path.exists', return_value=True):
                    with patch('src.core.config.logger') as mock_logger:
                        settings = load_settings()
                        
                        assert isinstance(settings, Settings)
                        mock_load_dotenv.assert_called_once()
                        mock_logger.info.assert_called()
        finally:
            os.unlink(env_file)
    
    def test_load_settings_exception(self):
        """测试设置加载异常"""
        with patch('src.core.config.Settings', side_effect=Exception("Test error")):
            with patch('src.core.config.logger') as mock_logger:
                with pytest.raises(Exception):
                    load_settings()
                
                mock_logger.error.assert_called()


class TestValidateConfig:
    """配置验证测试"""
    
    def test_validate_with_valid_config(self):
        """测试有效配置验证"""
        settings = Settings(
            llm_api_key="sk-valid-key",
            mcp_tools_dir="tests/temp_tools",
            log_file="tests/temp_logs/test.log"
        )
        
        with patch('src.core.config.os.path.exists', return_value=True):
            with patch('src.core.config.logger') as mock_logger:
                result = validate_config(settings)
                
                assert result is True
                mock_logger.info.assert_called_with("配置验证通过")
    
    def test_validate_with_invalid_api_key(self):
        """测试无效API密钥验证"""
        settings = Settings(llm_api_key="your_api_key_here")
        
        with patch('src.core.config.os.path.exists', return_value=True):
            with patch('src.core.config.logger') as mock_logger:
                result = validate_config(settings)
                
                assert result is False
                mock_logger.error.assert_called()
    
    def test_validate_create_missing_directories(self):
        """测试创建缺失目录"""
        settings = Settings(
            llm_api_key="sk-valid-key",
            mcp_tools_dir="tests/nonexistent_tools",
            log_file="tests/nonexistent_logs/test.log"
        )
        
        with patch('src.core.config.os.path.exists', return_value=False):
            with patch('src.core.config.os.makedirs') as mock_makedirs:
                with patch('src.core.config.logger') as mock_logger:
                    result = validate_config(settings)
                    
                    assert result is True
                    assert mock_makedirs.call_count == 2  # tools dir + log dir
    
    def test_validate_directory_creation_failure(self):
        """测试目录创建失败"""
        settings = Settings(
            llm_api_key="sk-valid-key",
            mcp_tools_dir="tests/nonexistent_tools"
        )
        
        with patch('src.core.config.os.path.exists', return_value=False):
            with patch('src.core.config.os.makedirs', side_effect=OSError("Permission denied")):
                with patch('src.core.config.logger') as mock_logger:
                    result = validate_config(settings)
                    
                    assert result is False
                    mock_logger.error.assert_called()


class TestGetSettings:
    """全局设置获取测试"""
    
    def test_get_settings_singleton(self):
        """测试设置单例模式"""
        from src.core.config import get_settings
        
        # 重置全局设置
        import src.core.config
        src.core.config.settings = None
        
        # 第一次调用
        settings1 = get_settings()
        
        # 第二次调用应该返回同一个实例
        settings2 = get_settings()
        
        assert settings1 is settings2


if __name__ == "__main__":
    pytest.main([__file__]) 