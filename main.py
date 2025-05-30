#!/usr/bin/env python3
"""
Google ADK 本地Web大模型交互平台 - 主入口文件

启动Web服务器，初始化应用配置和日志系统。
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from loguru import logger
from src.core.config import load_settings, validate_config
from src.core.logger import setup_logger
from src.web.app import create_app


def main():
    """主函数"""
    try:
        # 加载配置
        logger.info("正在启动 Google ADK Chat 应用...")
        settings = load_settings()
        
        # 设置日志系统
        setup_logger(settings)
        logger.info("日志系统初始化完成")
        
        # 验证配置
        if not validate_config(settings):
            logger.error("配置验证失败，应用启动中止")
            sys.exit(1)
        
        # 创建FastAPI应用
        app = create_app(settings)
        
        # 显示启动信息
        logger.info(f"启动Web服务器: {settings.web_host}:{settings.web_port}")
        logger.info("访问地址:")
        logger.info(f"  主页: http://{settings.web_host}:{settings.web_port}")
        if settings.debug_mode:
            logger.info(f"  API文档: http://{settings.web_host}:{settings.web_port}/docs")
            logger.info(f"  ReDoc: http://{settings.web_host}:{settings.web_port}/redoc")
        
        # 配置uvicorn - 修复reload模式警告
        if settings.debug_mode:
            # 开发模式：使用应用工厂函数字符串以支持reload
            uvicorn.run(
                "src.web.app:create_app_for_reload",
                host=settings.web_host,
                port=settings.web_port,
                log_level="info",
                reload=True,
                reload_dirs=[str(project_root / "src")],
                access_log=True
            )
        else:
            # 生产模式：直接使用应用实例
            uvicorn.run(
                app,
                host=settings.web_host,
                port=settings.web_port,
                log_level="warning",
                access_log=False
            )
        
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭应用...")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)
    finally:
        logger.info("应用已关闭")


if __name__ == "__main__":
    main() 