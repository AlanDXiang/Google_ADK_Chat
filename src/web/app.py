"""
FastAPI Web应用主文件

定义Web应用的路由、中间件和核心功能，
提供与大模型交互的RESTful API接口。
"""

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import json
import time
from datetime import datetime

from loguru import logger
from src.core.config import Settings
from src.core.llm_client import LLMClient, ChatResponse
from src.mcp_tools.base import tool_registry
from src.mcp_tools.examples import register_example_tools


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    include_history: bool = True
    system_message: Optional[str] = None


class ChatStreamRequest(BaseModel):
    """流式聊天请求模型"""
    message: str
    include_history: bool = True
    system_message: Optional[str] = None


class ToolExecuteRequest(BaseModel):
    """工具执行请求模型"""
    tool_name: str
    parameters: Dict[str, Any]


def create_app(settings: Settings) -> FastAPI:
    """
    创建FastAPI应用实例
    
    Args:
        settings: 应用配置
        
    Returns:
        FastAPI: 应用实例
    """
    app = FastAPI(
        title="Google ADK 本地Web大模型交互平台",
        description="基于Google ADK的本地化Web界面，支持与大模型对话和MCP工具扩展",
        version="1.0.0",
        docs_url="/docs" if settings.debug_mode else None,
        redoc_url="/redoc" if settings.debug_mode else None
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug_mode else ["http://localhost", f"http://{settings.web_host}"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 配置静态文件和模板
    app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    templates = Jinja2Templates(directory="src/web/templates")
    
    # 初始化LLM客户端
    llm_client = LLMClient(settings)
    
    # 注册示例MCP工具
    tools_count = register_example_tools()
    logger.info(f"已注册 {tools_count} 个示例MCP工具")
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info("FastAPI应用启动完成")
        
        # 执行LLM客户端健康检查
        if settings.llm_api_key and settings.llm_api_key != "your_api_key_here":
            logger.info("执行LLM客户端健康检查...")
            # 注意：这里暂时注释掉健康检查，避免启动时的API调用
            # is_healthy = llm_client.health_check()
            # logger.info(f"LLM客户端健康状态: {'正常' if is_healthy else '异常'}")
        else:
            logger.warning("LLM API密钥未配置，请检查环境变量或.env文件")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        logger.info("FastAPI应用正在关闭...")
    
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """主页"""
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "Google ADK Chat",
            "debug_mode": settings.debug_mode
        })
    
    @app.get("/api/health")
    async def health_check():
        """健康检查API"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "llm_model": settings.llm_model,
            "tools_count": len(tool_registry.list_tools())
        }
    
    @app.get("/api/config")
    async def get_config():
        """获取配置信息API（隐藏敏感信息）"""
        return {
            "llm_model": settings.llm_model,
            "llm_base_url": settings.llm_base_url,
            "debug_mode": settings.debug_mode,
            "tools_directory": settings.mcp_tools_dir,
            "api_key_configured": bool(settings.llm_api_key and settings.llm_api_key != "your_api_key_here")
        }
    
    @app.post("/api/chat")
    async def chat_completion(request: ChatRequest) -> Dict[str, Any]:
        """聊天补全API"""
        try:
            logger.info(f"收到聊天请求 | 消息长度: {len(request.message)}")
            
            response = await llm_client.chat_completion(
                user_message=request.message,
                include_history=request.include_history,
                system_message=request.system_message
            )
            
            return {
                "success": True,
                "data": {
                    "content": response.content,
                    "model": response.model,
                    "response_time": response.response_time,
                    "timestamp": response.timestamp,
                    "usage": response.usage
                }
            }
        
        except Exception as e:
            logger.error(f"聊天请求处理失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.websocket("/api/chat/stream")
    async def chat_stream(websocket: WebSocket):
        """流式聊天WebSocket端点"""
        await websocket.accept()
        logger.info("WebSocket连接已建立")
        
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                logger.info(f"收到WebSocket聊天请求 | 消息长度: {len(request_data.get('message', ''))}")
                
                # 发送开始标记
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # 流式生成响应
                async for chunk in llm_client.stream_chat_completion(
                    user_message=request_data["message"],
                    include_history=request_data.get("include_history", True),
                    system_message=request_data.get("system_message")
                ):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk
                    }))
                
                # 发送结束标记
                await websocket.send_text(json.dumps({
                    "type": "end",
                    "timestamp": datetime.now().isoformat()
                }))
        
        except WebSocketDisconnect:
            logger.info("WebSocket连接已断开")
        except Exception as e:
            logger.error(f"WebSocket错误: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    @app.post("/api/chat/clear")
    async def clear_chat_history():
        """清空聊天历史API"""
        llm_client.clear_history()
        logger.info("聊天历史已清空")
        return {"success": True, "message": "聊天历史已清空"}
    
    @app.get("/api/chat/summary")
    async def get_chat_summary():
        """获取聊天摘要API"""
        summary = llm_client.get_conversation_summary()
        return {"success": True, "data": summary}
    
    @app.get("/api/tools")
    async def list_tools():
        """列出所有MCP工具API"""
        tools_metadata = tool_registry.get_all_metadata()
        return {
            "success": True,
            "data": {
                "tools": tools_metadata,
                "count": len(tools_metadata)
            }
        }
    
    @app.get("/api/tools/{tool_name}")
    async def get_tool_info(tool_name: str):
        """获取特定工具信息API"""
        metadata = tool_registry.get_tool_metadata(tool_name)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        return {"success": True, "data": metadata}
    
    @app.post("/api/tools/{tool_name}/execute")
    async def execute_tool(tool_name: str, request: ToolExecuteRequest):
        """执行MCP工具API"""
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        try:
            logger.info(f"执行MCP工具: {tool_name}")
            result = await tool.execute(**request.parameters)
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata
            }
        
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "metadata": {"tool_name": tool_name, "timestamp": datetime.now().isoformat()}
            }
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        """404错误处理"""
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "API端点不存在", "path": request.url.path}
            )
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        """500错误处理"""
        logger.error(f"内部服务器错误: {exc}")
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "内部服务器错误", "details": str(exc)}
            )
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
    
    return app


def create_app_for_reload():
    """
    为uvicorn reload模式创建应用的工厂函数
    
    这个函数在reload模式下被调用，需要重新加载配置
    """
    from src.core.config import load_settings
    from src.core.logger import setup_logger
    
    settings = load_settings()
    # 确保在reload模式下日志系统正确初始化
    setup_logger(settings)
    return create_app(settings) 