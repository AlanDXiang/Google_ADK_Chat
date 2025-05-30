"""
日志系统模块

基于loguru实现的统一日志管理，支持文件输出、控制台输出和不同级别的日志记录。
提供唯一标识符和关键变量值记录，便于排错和定位。
"""

import sys
import os
from loguru import logger
from typing import Optional
from src.core.config import Settings


class LoggerSetup:
    """日志配置类"""
    
    def __init__(self, settings: Settings):
        """
        初始化日志配置
        
        Args:
            settings: 应用配置对象
        """
        self.settings = settings
        self._setup_logger()
    
    def _setup_logger(self):
        """配置日志器"""
        # 移除默认配置
        logger.remove()
        
        # 控制台输出配置 - 增加enqueue参数确保线程安全
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=console_format,
            level=self.settings.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True,  # 启用队列确保线程安全
            catch=True  # 捕获异常
        )
        
        # 文件输出配置
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        # 确保日志目录存在
        log_dir = os.path.dirname(self.settings.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        logger.add(
            self.settings.log_file,
            format=file_format,
            level=self.settings.log_level,
            rotation="10 MB",  # 当文件大小达到10MB时轮转
            retention="7 days",  # 保留7天的日志
            compression="zip",  # 压缩旧日志文件
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
            enqueue=True,  # 启用队列确保线程安全
            catch=True  # 捕获异常
        )
        
        logger.info("日志系统初始化完成")
        logger.info(f"日志级别: {self.settings.log_level}")
        logger.info(f"日志文件: {self.settings.log_file}")


def setup_logger(settings: Settings) -> None:
    """
    设置应用日志系统
    
    Args:
        settings: 应用配置对象
    """
    LoggerSetup(settings)


def get_logger(name: Optional[str] = None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为None
        
    Returns:
        logger: 日志记录器实例
    """
    if name:
        return logger.bind(name=name)
    return logger


def log_function_entry(func_name: str, **kwargs):
    """
    记录函数入口日志
    
    Args:
        func_name: 函数名称
        **kwargs: 函数参数
    """
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"进入函数 {func_name}({params})")


def log_function_exit(func_name: str, result=None, execution_time: Optional[float] = None):
    """
    记录函数出口日志
    
    Args:
        func_name: 函数名称
        result: 函数返回值
        execution_time: 执行时间（秒）
    """
    time_info = f" (耗时: {execution_time:.3f}s)" if execution_time else ""
    result_info = f" -> {result}" if result is not None else ""
    logger.debug(f"退出函数 {func_name}{result_info}{time_info}")


def log_error_with_context(error: Exception, context: dict = None, unique_id: str = None):
    """
    记录带有上下文信息的错误日志
    
    Args:
        error: 异常对象
        context: 上下文信息字典
        unique_id: 唯一标识符
    """
    error_id = unique_id or f"ERR_{id(error)}"
    logger.error(f"错误标识: {error_id}")
    
    if context:
        logger.error(f"上下文信息: {context}")
    
    logger.exception(f"异常详情: {str(error)}")


def log_performance_metrics(operation: str, duration: float, **metrics):
    """
    记录性能指标日志
    
    Args:
        operation: 操作名称
        duration: 持续时间（秒）
        **metrics: 其他性能指标
    """
    metrics_str = ", ".join([f"{k}={v}" for k, v in metrics.items()])
    logger.info(f"性能指标 | 操作: {operation} | 耗时: {duration:.3f}s | {metrics_str}")


# 日志装饰器
def log_execution(func):
    """
    函数执行日志装饰器
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        log_function_entry(func_name, **kwargs)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            log_function_exit(func_name, result, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            log_error_with_context(
                e, 
                context={"function": func_name, "args": str(args), "kwargs": str(kwargs)},
                unique_id=f"FUNC_{func_name}_{int(time.time())}"
            )
            raise
    
    return wrapper 