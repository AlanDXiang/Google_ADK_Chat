"""
配置管理模块

负责从.env文件和环境变量中加载配置，确保环境变量优先级。
支持配置校验和默认值设置。
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv
from loguru import logger


class Settings(BaseSettings):
    """应用配置类"""
    
    # 大模型配置
    llm_base_url: str = Field(default="https://api.openai.com/v1", description="LLM API基础URL", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-3.5-turbo", description="LLM模型名称", alias="LLM_MODEL")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API密钥", alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM温度参数", alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, gt=0, description="LLM最大令牌数", alias="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=30, gt=0, description="LLM请求超时时间(秒)", alias="LLM_TIMEOUT")
    
    # Web服务器配置
    web_host: str = Field(default="localhost", description="Web服务器主机", alias="WEB_HOST")
    web_port: int = Field(default=8000, ge=1, le=65535, description="Web服务器端口", alias="WEB_PORT")
    debug_mode: bool = Field(default=False, description="调试模式", alias="DEBUG_MODE")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", description="日志文件路径", alias="LOG_FILE")
    
    # MCP工具配置
    mcp_tools_dir: str = Field(default="src/mcp_tools", description="MCP工具目录", alias="MCP_TOOLS_DIR")
    
    @validator('llm_api_key')
    def validate_api_key(cls, v):
        """验证API密钥"""
        if not v or v == "your_api_key_here":
            logger.warning("LLM API密钥未配置或使用默认值，请在.env文件或环境变量中设置LLM_API_KEY")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是以下之一: {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings() -> Settings:
    """
    加载应用配置
    
    优先级: 环境变量 > .env文件 > 默认值
    
    Returns:
        Settings: 配置对象
    """
    # 加载.env文件
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        load_dotenv(env_file_path)
        logger.info(f"已加载.env文件: {env_file_path}")
    else:
        logger.warning(f".env文件不存在: {env_file_path}")
    
    # 创建配置对象
    try:
        settings = Settings()
        logger.info("配置加载成功")
        
        # 记录关键配置信息（隐藏敏感信息）
        logger.info(f"LLM模型: {settings.llm_model}")
        logger.info(f"LLM基础URL: {settings.llm_base_url}")
        logger.info(f"Web服务器: {settings.web_host}:{settings.web_port}")
        logger.info(f"调试模式: {settings.debug_mode}")
        logger.info(f"MCP工具目录: {settings.mcp_tools_dir}")
        
        return settings
        
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        raise


def validate_config(settings: Settings) -> bool:
    """
    验证配置完整性
    
    Args:
        settings: 配置对象
        
    Returns:
        bool: 验证是否通过
    """
    validation_errors = []
    
    # 验证API密钥
    if not settings.llm_api_key or settings.llm_api_key == "your_api_key_here":
        validation_errors.append("LLM_API_KEY未正确配置")
    
    # 验证MCP工具目录
    if not os.path.exists(settings.mcp_tools_dir):
        logger.warning(f"MCP工具目录不存在，将创建: {settings.mcp_tools_dir}")
        try:
            os.makedirs(settings.mcp_tools_dir, exist_ok=True)
        except Exception as e:
            validation_errors.append(f"无法创建MCP工具目录: {e}")
    
    # 验证日志目录
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        logger.warning(f"日志目录不存在，将创建: {log_dir}")
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            validation_errors.append(f"无法创建日志目录: {e}")
    
    if validation_errors:
        for error in validation_errors:
            logger.error(f"配置验证失败: {error}")
        return False
    
    logger.info("配置验证通过")
    return True


# 全局配置实例
settings = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global settings
    if settings is None:
        settings = load_settings()
    return settings 