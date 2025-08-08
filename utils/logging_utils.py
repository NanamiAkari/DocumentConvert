#!/usr/bin/env python3
"""
日志记录工具
复刻MediaConvert的日志记录逻辑，提供统一的日志配置和格式
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def configure_logging(name: str = __name__, 
                     level: str = "INFO",
                     log_file: Optional[str] = None,
                     max_bytes: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径，如果为None则使用默认路径
        max_bytes: 日志文件最大大小
        backup_count: 备份文件数量
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 创建日志格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file is None:
        # 使用默认日志文件路径，与MediaConvert保持一致
        log_dir = Path("/app/log_files")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
    
    try:
        # 使用RotatingFileHandler进行日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        # 如果文件处理器创建失败，只使用控制台输出
        logger.warning(f"Failed to create file handler: {e}")
    
    # 防止日志重复
    logger.propagate = False
    
    return logger


class TaskLogger:
    """任务专用日志记录器"""
    
    def __init__(self, task_id: int, logger: Optional[logging.Logger] = None):
        """
        初始化任务日志记录器
        
        Args:
            task_id: 任务ID
            logger: 基础日志记录器，如果为None则创建新的
        """
        self.task_id = str(task_id)  # 转换为字符串用于日志显示
        self.logger = logger or configure_logging(f"task_{task_id}")
    
    def _format_message(self, message: str) -> str:
        """格式化消息，添加任务ID前缀"""
        return f"[Task {self.task_id}] {message}"
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(self._format_message(message), **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(self._format_message(message), **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(self._format_message(message), **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(self._format_message(message), **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(self._format_message(message), **kwargs)
    
    def log_task_start(self, task_type: str, input_info: str):
        """记录任务开始"""
        self.info(f"Task started - Type: {task_type}, Input: {input_info}")
    
    def log_task_progress(self, step: str, details: str = ""):
        """记录任务进度"""
        message = f"Task progress - Step: {step}"
        if details:
            message += f", Details: {details}"
        self.info(message)
    
    def log_task_completion(self, success: bool, processing_time: float, output_info: str = ""):
        """记录任务完成"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Task completed - Status: {status}, Time: {processing_time:.2f}s"
        if output_info:
            message += f", Output: {output_info}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, details: str = ""):
        """记录文件操作"""
        status = "SUCCESS" if success else "FAILED"
        message = f"File operation - {operation}: {file_path} - Status: {status}"
        if details:
            message += f", Details: {details}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_s3_operation(self, operation: str, s3_path: str, success: bool, details: str = ""):
        """记录S3操作"""
        status = "SUCCESS" if success else "FAILED"
        message = f"S3 operation - {operation}: {s3_path} - Status: {status}"
        if details:
            message += f", Details: {details}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_conversion_step(self, step: str, input_file: str, output_file: str, success: bool, details: str = ""):
        """记录转换步骤"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Conversion step - {step}: {input_file} -> {output_file} - Status: {status}"
        if details:
            message += f", Details: {details}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_error_with_retry(self, error: str, retry_count: int, max_retries: int):
        """记录错误和重试信息"""
        self.error(f"Task failed (attempt {retry_count}/{max_retries}): {error}")
        if retry_count < max_retries:
            self.info(f"Will retry task (attempt {retry_count + 1}/{max_retries})")
        else:
            self.error(f"Task failed permanently after {max_retries} attempts")


def setup_application_logging(log_level: str = "INFO", log_dir: str = "/app/log_files"):
    """
    设置应用程序级别的日志配置
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
    """
    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 如果已经配置过，清除现有处理器
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # 创建格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = Path(log_dir) / "app.log"
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        print(f"Logging configured - Level: {log_level}, File: {log_file}")
        
    except Exception as e:
        print(f"Failed to create file handler: {e}")
    
    # 设置第三方库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_task_logger(task_id: int) -> TaskLogger:
    """
    获取任务专用日志记录器
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务日志记录器
    """
    return TaskLogger(task_id)
