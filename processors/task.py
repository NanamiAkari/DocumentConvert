#!/usr/bin/env python3
"""
任务模型定义
"""

from datetime import datetime
from typing import Dict, Any, Optional


class Task:
    """任务模型类"""
    
    def __init__(self,
                 task_id: int,
                 task_type: str,
                 status: str,
                 input_path: str,
                 output_path: str,
                 params: Dict[str, Any] = None,
                 priority: str = 'normal',
                 created_at: Optional[datetime] = None,
                 max_retries: int = 3):
        """
        初始化任务
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            status: 任务状态
            input_path: 输入路径
            output_path: 输出路径
            params: 任务参数
            priority: 优先级
            created_at: 创建时间
            max_retries: 最大重试次数
        """
        self.task_id = task_id
        self.task_type = task_type
        self.status = status
        self.input_path = input_path
        self.output_path = output_path
        self.params = params or {}
        self.priority = priority
        self.created_at = created_at or datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.retry_count: int = 0
        self.max_retries = max_retries
    
    def __repr__(self):
        return f"Task(id={self.task_id}, type={self.task_type}, status={self.status})"
