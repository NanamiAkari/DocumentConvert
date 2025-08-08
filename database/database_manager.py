#!/usr/bin/env python3
"""
数据库管理器
参考MediaConvert的DatabaseManager设计，支持MySQL和SQLite
"""

import asyncio
import datetime as dt
import traceback
from typing import Optional, List, Dict, Union
from sqlalchemy import select, and_, func, case, inspect, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from contextlib import asynccontextmanager

from database.models import Base, DocumentTask, TaskStatus, TaskPriority, QueryTasksFilter, TaskStatistics
from utils.logging_utils import configure_logging

# 配置日志记录器
logger = configure_logging(name=__name__)


class DatabaseManager:
    """
    文档转换任务数据库管理器
    支持MySQL和SQLite数据库，提供任务的增删查改操作
    """

    def __init__(self,
                 database_type: str,
                 database_url: str,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 reconnect_interval: int = 5) -> None:
        """
        初始化数据库管理器
        
        Args:
            database_type: 数据库类型 ("sqlite" 或 "mysql")
            database_url: 数据库连接URL
            loop: 异步事件循环
            reconnect_interval: 重连间隔(秒)
        """
        self.database_type: str = database_type.lower()
        self.database_url: str = database_url
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_running_loop()
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self.reconnect_interval: int = reconnect_interval
        self._is_connected: bool = False
        self._max_retries: int = 5

    async def initialize(self) -> None:
        """初始化数据库引擎和会话工厂，自动创建缺失的表"""
        await self._connect()

    async def _connect(self) -> None:
        """连接数据库并初始化引擎和会话工厂"""
        retries = 0
        while retries < self._max_retries:
            try:
                logger.info(f"Connecting to {self.database_type} database...")
                
                # 根据数据库类型配置引擎参数
                engine_kwargs = {
                    "echo": False,  # 生产环境关闭SQL日志
                    "pool_pre_ping": True,
                    "pool_recycle": 3600,
                }
                
                if self.database_type == "mysql":
                    engine_kwargs.update({
                        "pool_size": 10,
                        "max_overflow": 20,
                        "pool_timeout": 30,
                    })
                elif self.database_type == "sqlite":
                    engine_kwargs.update({
                        "connect_args": {"check_same_thread": False}
                    })
                
                # 创建异步引擎
                self._engine = create_async_engine(self.database_url, **engine_kwargs)
                
                # 创建会话工厂
                self._session_factory = sessionmaker(
                    bind=self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                
                # 测试连接
                async with self._engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                
                self._is_connected = True
                logger.info(f"Successfully connected to {self.database_type} database")
                return
                
            except Exception as e:
                retries += 1
                logger.error(f"Database connection attempt {retries} failed: {e}")
                if retries < self._max_retries:
                    logger.info(f"Retrying in {self.reconnect_interval} seconds...")
                    await asyncio.sleep(self.reconnect_interval)
                else:
                    logger.error("Max retries reached. Database connection failed.")
                    raise

    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话的上下文管理器"""
        if not self._is_connected or not self._session_factory:
            await self._connect()
        
        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()

    async def create_task(self, task: DocumentTask) -> DocumentTask:
        """创建新任务"""
        try:
            async with self.get_session() as session:
                session.add(task)
                await session.commit()
                await session.refresh(task)
                logger.info(f"Created task {task.id} in database")
                return task
        except Exception as e:
            logger.error(f"Failed to create task {task.id}: {e}")
            raise

    async def get_task(self, task_id: str) -> Optional[DocumentTask]:
        """根据ID获取任务"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(DocumentTask).where(DocumentTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    logger.debug(f"Retrieved task {task_id} from database")
                return task
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    async def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务信息"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(DocumentTask).where(DocumentTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    logger.warning(f"Task {task_id} not found for update")
                    return False
                
                # 更新字段
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # 自动更新updated_at
                task.updated_at = dt.datetime.now()
                
                await session.commit()
                logger.debug(f"Updated task {task_id} in database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False

    async def update_task_status(self, task_id: str, status: TaskStatus, 
                               error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        update_data = {"status": status}
        
        if status == TaskStatus.processing:
            update_data["started_at"] = dt.datetime.now()
        elif status in [TaskStatus.completed, TaskStatus.failed]:
            update_data["completed_at"] = dt.datetime.now()
            
        if error_message:
            update_data["error_message"] = error_message
            
        return await self.update_task(task_id, **update_data)

    async def update_callback_status(self, task_id: str, status_code: int, 
                                   message: Optional[str] = None) -> bool:
        """更新回调状态"""
        return await self.update_task(
            task_id,
            callback_status_code=status_code,
            callback_message=message,
            callback_time=dt.datetime.now()
        )

    async def query_tasks(self, filter_params: QueryTasksFilter) -> List[DocumentTask]:
        """查询任务列表"""
        try:
            async with self.get_session() as session:
                query = select(DocumentTask)
                
                # 构建查询条件
                conditions = []
                
                if filter_params.status:
                    conditions.append(DocumentTask.status == filter_params.status)
                if filter_params.priority:
                    conditions.append(DocumentTask.priority == filter_params.priority)
                if filter_params.task_type:
                    conditions.append(DocumentTask.task_type == filter_params.task_type)
                if filter_params.platform:
                    conditions.append(DocumentTask.platform == filter_params.platform)
                if filter_params.created_after:
                    conditions.append(DocumentTask.created_at >= filter_params.created_after)
                if filter_params.created_before:
                    conditions.append(DocumentTask.created_at <= filter_params.created_before)
                if filter_params.has_result is not None:
                    if filter_params.has_result:
                        conditions.append(DocumentTask.result.isnot(None))
                    else:
                        conditions.append(DocumentTask.result.is_(None))
                if filter_params.has_error is not None:
                    if filter_params.has_error:
                        conditions.append(DocumentTask.error_message.isnot(None))
                    else:
                        conditions.append(DocumentTask.error_message.is_(None))
                
                if conditions:
                    query = query.where(and_(*conditions))
                
                # 排序和分页
                query = query.order_by(desc(DocumentTask.created_at))
                query = query.offset(filter_params.offset).limit(filter_params.limit)
                
                result = await session.execute(query)
                tasks = result.scalars().all()
                
                logger.debug(f"Queried {len(tasks)} tasks from database")
                return list(tasks)
                
        except Exception as e:
            logger.error(f"Failed to query tasks: {e}")
            return []

    async def get_tasks_by_status(self, status: str) -> List[DocumentTask]:
        """根据状态获取任务列表"""
        try:
            async with self.get_session() as session:
                query = select(DocumentTask).where(DocumentTask.status == status)
                result = await session.execute(query)
                tasks = result.scalars().all()
                return list(tasks)

        except Exception as e:
            logger.error(f"Failed to get tasks by status {status}: {e}")
            return []

    async def get_task_statistics(self) -> TaskStatistics:
        """获取任务统计信息"""
        try:
            async with self.get_session() as session:
                # 统计各状态任务数量
                status_counts = await session.execute(
                    select(
                        DocumentTask.status,
                        func.count(DocumentTask.id).label('count')
                    ).group_by(DocumentTask.status)
                )
                
                status_dict = {status.value: 0 for status in TaskStatus}
                for row in status_counts:
                    status_dict[row.status.value] = row.count
                
                total_tasks = sum(status_dict.values())
                completed_tasks = status_dict[TaskStatus.completed.value]
                success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                # 计算平均处理时间
                avg_time_result = await session.execute(
                    select(func.avg(DocumentTask.task_processing_time))
                    .where(DocumentTask.task_processing_time.isnot(None))
                )
                avg_processing_time = avg_time_result.scalar()
                
                return TaskStatistics(
                    total_tasks=total_tasks,
                    pending_tasks=status_dict[TaskStatus.pending.value],
                    processing_tasks=status_dict[TaskStatus.processing.value],
                    completed_tasks=completed_tasks,
                    failed_tasks=status_dict[TaskStatus.failed.value],
                    success_rate=round(success_rate, 2),
                    avg_processing_time=round(avg_processing_time, 2) if avg_processing_time else None
                )
                
        except Exception as e:
            logger.error(f"Failed to get task statistics: {e}")
            return TaskStatistics(
                total_tasks=0, pending_tasks=0, processing_tasks=0,
                completed_tasks=0, failed_tasks=0, success_rate=0.0
            )

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(DocumentTask).where(DocumentTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    logger.warning(f"Task {task_id} not found for deletion")
                    return False
                
                await session.delete(task)
                await session.commit()
                logger.info(f"Deleted task {task_id} from database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False

    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """清理旧任务"""
        try:
            cutoff_date = dt.datetime.now() - dt.timedelta(days=days)
            
            async with self.get_session() as session:
                result = await session.execute(
                    select(DocumentTask).where(
                        and_(
                            DocumentTask.created_at < cutoff_date,
                            DocumentTask.status.in_([TaskStatus.completed, TaskStatus.failed])
                        )
                    )
                )
                old_tasks = result.scalars().all()
                
                count = 0
                for task in old_tasks:
                    await session.delete(task)
                    count += 1
                
                await session.commit()
                logger.info(f"Cleaned up {count} old tasks")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")
            return 0

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._is_connected = False
            logger.info("Database connection closed")
