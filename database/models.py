#!/usr/bin/env python3
"""
文档转换任务数据库模型
参考MediaConvert的设计，实现完整的任务状态持久化
"""

import datetime as dt
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, JSON, Enum as SQLEnum, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, ConfigDict, field_validator

# 定义Base类
Base = declarative_base()


class TaskStatus(str, Enum):
    """任务状态枚举"""
    pending = "pending"           # 等待处理
    processing = "processing"     # 正在处理
    completed = "completed"       # 处理完成
    failed = "failed"            # 处理失败
    cancelled = "cancelled"       # 已取消


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    low = "low"                  # 低优先级
    normal = "normal"            # 普通优先级
    high = "high"                # 高优先级


class DocumentTask(Base):
    """文档转换任务模型"""
    __tablename__ = "document_tasks"

    # 基本信息
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.pending, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.normal, nullable=False)
    
    # 文件信息
    input_path = Column(Text, nullable=True)          # 本地输入路径
    output_path = Column(Text, nullable=True)         # 本地输出路径
    file_url = Column(Text, nullable=True)            # 原始文件URL
    bucket_name = Column(String(255), nullable=True)  # S3存储桶名称
    file_path = Column(Text, nullable=True)           # 文件在bucket中的路径
    file_name = Column(String(255), nullable=True)    # 文件名称
    file_size_bytes = Column(Integer, nullable=True)  # 文件大小
    
    # 输出信息
    output_url = Column(String(500), nullable=True)   # 输出文件URL
    s3_urls = Column(JSON, nullable=True)             # S3访问地址列表
    
    # 处理参数
    params = Column(JSON, nullable=True)              # 任务参数
    decode_options = Column(JSON, nullable=True)      # 解码选项
    
    # 时间信息
    created_at = Column(DateTime, default=dt.datetime.now, nullable=False)
    updated_at = Column(DateTime, onupdate=dt.datetime.now, nullable=True)
    started_at = Column(DateTime, nullable=True)      # 开始处理时间
    completed_at = Column(DateTime, nullable=True)    # 完成时间
    task_processing_time = Column(Float, nullable=True)  # 处理耗时(秒)
    
    # 处理结果
    result = Column(JSON, nullable=True)              # 处理结果
    error_message = Column(Text, nullable=True)       # 错误信息
    pages_processed = Column(Integer, nullable=True)  # 处理的页数
    conversion_quality = Column(String(20), nullable=True)  # 转换质量
    
    # 重试机制
    retry_count = Column(Integer, default=0, nullable=False)
    max_retry_count = Column(Integer, default=3, nullable=False)
    last_retry_at = Column(DateTime, nullable=True)
    
    # 回调信息
    callback_url = Column(String(500), nullable=True)
    callback_status_code = Column(Integer, nullable=True)
    callback_message = Column(String(512), nullable=True)
    callback_time = Column(DateTime, nullable=True)
    
    # 平台信息
    platform = Column(String(50), nullable=True)     # 平台标识
    engine_name = Column(String(50), nullable=True)  # 引擎名称
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'status': self.status.value if hasattr(self.status, 'value') else str(self.status),
            'priority': self.priority.value if hasattr(self.priority, 'value') else str(self.priority),
            'input_path': self.input_path,
            'output_path': self.output_path,
            'file_url': self.file_url,
            'bucket_name': self.bucket_name,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size_bytes': self.file_size_bytes,
            'output_url': self.output_url,
            's3_urls': self.s3_urls,
            'params': self.params,
            'decode_options': self.decode_options,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'task_processing_time': self.task_processing_time,
            'result': self.result,
            'error_message': self.error_message,
            'pages_processed': self.pages_processed,
            'conversion_quality': self.conversion_quality,
            'retry_count': self.retry_count,
            'max_retry_count': self.max_retry_count,
            'last_retry_at': self.last_retry_at.isoformat() if self.last_retry_at else None,
            'callback_url': self.callback_url,
            'callback_status_code': self.callback_status_code,
            'callback_message': self.callback_message,
            'callback_time': self.callback_time.isoformat() if self.callback_time else None,
            'platform': self.platform,
            'engine_name': self.engine_name
        }


class TaskCreateRequest(BaseModel):
    """任务创建请求模型"""
    # 任务基本信息
    task_type: str = Field(..., description="任务类型")
    priority: TaskPriority = Field(TaskPriority.normal, description="任务优先级")
    
    # 文件输入方式（三选一）
    bucket_name: Optional[str] = Field(None, description="S3存储桶名称")
    file_path: Optional[str] = Field(None, description="文件在bucket中的路径")
    file_url: Optional[str] = Field(None, description="文件HTTP URL")
    input_path: Optional[str] = Field(None, description="本地文件路径")
    
    # 输出配置
    output_path: Optional[str] = Field(None, description="输出文件路径")
    
    # 任务参数
    params: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    
    # 回调配置
    callback_url: Optional[str] = Field(None, description="任务完成回调URL")
    
    # 平台信息
    platform: Optional[str] = Field(None, description="平台标识")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_validator("task_type")
    def validate_task_type(cls, v):
        """验证任务类型"""
        valid_types = {
            'office_to_pdf', 'pdf_to_markdown', 'office_to_markdown',
            'batch_office_to_pdf', 'batch_pdf_to_markdown', 'batch_office_to_markdown',
            'image_to_markdown', 'batch_image_to_markdown'
        }
        if v not in valid_types:
            raise ValueError(f"Invalid task type. Supported types: {valid_types}")
        return v


class QueryTasksFilter(BaseModel):
    """任务查询过滤器"""
    status: Optional[TaskStatus] = Field(None, description="任务状态过滤")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级过滤")
    task_type: Optional[str] = Field(None, description="任务类型过滤")
    platform: Optional[str] = Field(None, description="平台过滤")
    created_after: Optional[dt.datetime] = Field(None, description="创建时间起始")
    created_before: Optional[dt.datetime] = Field(None, description="创建时间结束")
    has_result: Optional[bool] = Field(None, description="是否有结果")
    has_error: Optional[bool] = Field(None, description="是否有错误")
    limit: int = Field(20, description="每页记录数", ge=1, le=100)
    offset: int = Field(0, description="分页偏移量", ge=0)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_validator("created_after", "created_before", mode="before")
    def parse_datetime(cls, v):
        """解析日期时间"""
        if not v:
            return None
        if isinstance(v, str):
            try:
                return dt.datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid datetime format: {v}")
        return v


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: int = Field(..., description="任务ID (自增整数)")
    message: str = Field(..., description="响应消息")
    status: Optional[str] = Field(None, description="任务状态")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TaskStatistics(BaseModel):
    """任务统计模型"""
    total_tasks: int = Field(..., description="总任务数")
    pending_tasks: int = Field(..., description="等待中任务数")
    processing_tasks: int = Field(..., description="处理中任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    failed_tasks: int = Field(..., description="失败任务数")
    success_rate: float = Field(..., description="成功率")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
