"""
大语言模型客户端模块

基于LiteLLM实现与各种大模型API的统一交互接口，
支持多种模型提供商，提供重试机制和错误处理。
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import time
from dataclasses import dataclass
from loguru import logger

try:
    import litellm
    from litellm import completion, acompletion
except ImportError:
    logger.error("LiteLLM未安装，请运行: pip install litellm")
    raise

from src.core.config import Settings
from src.core.logger import log_execution, log_error_with_context, log_performance_metrics


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    """聊天响应数据类"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self, settings: Settings):
        """
        初始化LLM客户端
        
        Args:
            settings: 应用配置对象
        """
        self.settings = settings
        self._setup_litellm()
        
        # 会话历史
        self.conversation_history: List[ChatMessage] = []
        
        logger.info(f"LLM客户端初始化完成 | 模型: {settings.llm_model}")
    
    def _setup_litellm(self):
        """配置LiteLLM"""
        # 设置API密钥
        if self.settings.llm_api_key:
            # 根据模型类型设置相应的API密钥
            if "gpt" in self.settings.llm_model.lower():
                litellm.openai_key = self.settings.llm_api_key
            elif "claude" in self.settings.llm_model.lower():
                litellm.anthropic_key = self.settings.llm_api_key
            elif "gemini" in self.settings.llm_model.lower():
                litellm.google_key = self.settings.llm_api_key
            # 可以根据需要添加更多模型类型
        
        # 设置基础URL（如果是自定义部署）
        if self.settings.llm_base_url != "https://api.openai.com/v1":
            litellm.api_base = self.settings.llm_base_url
        
        # 设置超时
        litellm.request_timeout = self.settings.llm_timeout
        
        logger.info("LiteLLM配置完成")
    
    @log_execution
    def add_message(self, role: str, content: str) -> ChatMessage:
        """
        添加消息到会话历史
        
        Args:
            role: 消息角色
            content: 消息内容
            
        Returns:
            ChatMessage: 消息对象
        """
        message = ChatMessage(role=role, content=content)
        self.conversation_history.append(message)
        
        # 限制历史长度，避免内存过大
        max_history = 50
        if len(self.conversation_history) > max_history:
            # 保留系统消息和最近的对话
            system_messages = [msg for msg in self.conversation_history if msg.role == "system"]
            recent_messages = self.conversation_history[-(max_history - len(system_messages)):]
            self.conversation_history = system_messages + recent_messages
        
        logger.debug(f"添加消息 | 角色: {role} | 内容长度: {len(content)}")
        return message
    
    @log_execution
    async def chat_completion(
        self, 
        user_message: str, 
        include_history: bool = True,
        system_message: Optional[str] = None
    ) -> ChatResponse:
        """
        执行聊天补全
        
        Args:
            user_message: 用户消息
            include_history: 是否包含历史对话
            system_message: 系统消息
            
        Returns:
            ChatResponse: 响应对象
        """
        start_time = time.time()
        
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统消息
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # 添加历史消息
            if include_history:
                messages.extend([msg.to_dict() for msg in self.conversation_history])
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 记录用户消息
            self.add_message("user", user_message)
            
            logger.info(f"发送聊天请求 | 消息数: {len(messages)} | 模型: {self.settings.llm_model}")
            
            # 调用LiteLLM
            response = await acompletion(
                model=self.settings.llm_model,
                messages=messages,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                timeout=self.settings.llm_timeout
            )
            
            # 处理响应
            assistant_message = response.choices[0].message.content
            response_time = time.time() - start_time
            
            # 记录助手消息
            self.add_message("assistant", assistant_message)
            
            # 创建响应对象
            chat_response = ChatResponse(
                content=assistant_message,
                model=response.model,
                usage=response.usage.dict() if hasattr(response, 'usage') and response.usage else None,
                response_time=response_time
            )
            
            # 记录性能指标
            log_performance_metrics(
                "chat_completion",
                response_time,
                model=self.settings.llm_model,
                message_count=len(messages),
                response_length=len(assistant_message),
                tokens_used=chat_response.usage.get('total_tokens', 0) if chat_response.usage else 0
            )
            
            logger.info(f"聊天完成 | 响应长度: {len(assistant_message)} | 耗时: {response_time:.3f}s")
            
            return chat_response
            
        except Exception as e:
            response_time = time.time() - start_time
            log_error_with_context(
                e,
                context={
                    "model": self.settings.llm_model,
                    "user_message_length": len(user_message),
                    "message_count": len(messages) if 'messages' in locals() else 0,
                    "response_time": response_time
                },
                unique_id=f"LLM_CHAT_{int(time.time())}"
            )
            raise
    
    @log_execution
    def chat_completion_sync(
        self, 
        user_message: str, 
        include_history: bool = True,
        system_message: Optional[str] = None
    ) -> ChatResponse:
        """
        同步版本的聊天补全
        
        Args:
            user_message: 用户消息
            include_history: 是否包含历史对话
            system_message: 系统消息
            
        Returns:
            ChatResponse: 响应对象
        """
        return asyncio.run(self.chat_completion(user_message, include_history, system_message))
    
    @log_execution
    async def stream_chat_completion(
        self, 
        user_message: str, 
        include_history: bool = True,
        system_message: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天补全
        
        Args:
            user_message: 用户消息
            include_history: 是否包含历史对话
            system_message: 系统消息
            
        Yields:
            str: 响应片段
        """
        start_time = time.time()
        
        try:
            # 构建消息列表
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            if include_history:
                messages.extend([msg.to_dict() for msg in self.conversation_history])
            
            messages.append({"role": "user", "content": user_message})
            
            # 记录用户消息
            self.add_message("user", user_message)
            
            logger.info(f"发送流式聊天请求 | 消息数: {len(messages)} | 模型: {self.settings.llm_model}")
            
            # 调用LiteLLM流式API
            response_stream = await acompletion(
                model=self.settings.llm_model,
                messages=messages,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                timeout=self.settings.llm_timeout,
                stream=True
            )
            
            full_response = ""
            async for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # 记录完整响应
            self.add_message("assistant", full_response)
            
            response_time = time.time() - start_time
            log_performance_metrics(
                "stream_chat_completion",
                response_time,
                model=self.settings.llm_model,
                message_count=len(messages),
                response_length=len(full_response)
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            log_error_with_context(
                e,
                context={
                    "model": self.settings.llm_model,
                    "user_message_length": len(user_message),
                    "stream": True,
                    "response_time": response_time
                },
                unique_id=f"LLM_STREAM_{int(time.time())}"
            )
            raise
    
    def clear_history(self):
        """清空会话历史"""
        self.conversation_history.clear()
        logger.info("会话历史已清空")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "message_count": len(self.conversation_history),
            "user_messages": len([msg for msg in self.conversation_history if msg.role == "user"]),
            "assistant_messages": len([msg for msg in self.conversation_history if msg.role == "assistant"]),
            "total_characters": sum(len(msg.content) for msg in self.conversation_history)
        }
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 客户端是否健康
        """
        try:
            # 发送简单的测试消息
            test_message = "Hello"
            response = self.chat_completion_sync(test_message, include_history=False)
            
            if response and response.content:
                logger.info("LLM客户端健康检查通过")
                return True
            else:
                logger.warning("LLM客户端健康检查失败：无响应内容")
                return False
                
        except Exception as e:
            logger.error(f"LLM客户端健康检查失败: {e}")
            return False 