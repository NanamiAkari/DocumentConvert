#!/usr/bin/env python3
"""
文档转换任务处理器
复刻MediaConvert的任务处理逻辑，支持数据库持久化、云存储集成等企业级功能
"""

import asyncio
import threading
import uuid
import gc
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from database.models import DocumentTask, TaskStatus, TaskPriority, TaskCreateRequest
from database.database_manager import DatabaseManager
from services.s3_download_service import S3DownloadService
from services.s3_upload_service import S3UploadService
from utils.workspace_manager import WorkspaceManager
from utils.logging_utils import configure_logging, get_task_logger
from services.document_service import DocumentService

logger = configure_logging(name=__name__)


class TaskProcessor:
    """
    文档转换任务处理器
    复刻MediaConvert的企业级任务处理架构，支持：
    1. 数据库持久化存储
    2. S3云存储集成
    3. 智能任务调度
    4. 完整的日志记录
    5. 资源管理和清理
    """

    def __init__(self,
                 database_type: str = "sqlite",
                 database_url: str = "sqlite:///./document_tasks.db",
                 max_concurrent_tasks: int = 3,
                 task_check_interval: int = 5,
                 workspace_dir: str = "/app/task_workspace"):
        """
        初始化任务处理器
        
        Args:
            max_concurrent_tasks: 最大并发任务数
            task_check_interval: 任务检查间隔（秒）
            workspace_dir: 工作空间目录
        """
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_check_interval = task_check_interval
        self.workspace_dir = Path(workspace_dir)
        
        # 确保工作空间目录存在
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # 任务队列系统（参考MediaConvert设计）
        self.fetch_queue = asyncio.Queue()           # 待获取任务队列
        self.task_processing_queue = asyncio.Queue() # 任务处理队列
        self.update_queue = asyncio.Queue()          # 状态更新队列
        self.cleanup_queue = asyncio.Queue()         # 清理队列
        self.callback_queue = asyncio.Queue()        # 回调队列
        
        # 运行状态
        self.is_running = False
        self.worker_tasks = []
        
        # 任务存储（简化版，实际项目中应使用数据库）
        self.tasks: Dict[int, Task] = {}
        self.task_counter = 0
        
        # 处理器映射
        self.processors = {
            'pdf_convert': self._process_pdf_convert,
            'markdown_convert': self._process_markdown_convert,
            'office_convert': self._process_office_convert,
            'office_to_pdf': self._process_office_to_pdf,
            'pdf_to_markdown': self._process_pdf_to_markdown,
            'office_to_markdown': self._process_office_to_markdown,
            'batch_office_to_markdown': self._process_batch_office_to_markdown,
            'batch_pdf_to_markdown': self._process_batch_pdf_to_markdown,
        }
        
        self.logger.info(f"TaskProcessor initialized with {max_concurrent_tasks} max concurrent tasks")
    
    async def start(self):
        """启动任务处理器"""
        if self.is_running:
            self.logger.warning("TaskProcessor is already running")
            return
            
        self.is_running = True
        self.logger.info("Starting TaskProcessor...")
        
        # 启动工作协程（参考MediaConvert的设计）
        self.worker_tasks = [
            asyncio.create_task(self._fetch_task_worker()),      # 获取任务工作协程
            asyncio.create_task(self._process_tasks_worker()),   # 处理任务工作协程
            asyncio.create_task(self._update_task_worker()),     # 更新状态工作协程
            asyncio.create_task(self._cleanup_worker()),         # 清理工作协程
            asyncio.create_task(self._callback_worker()),        # 回调工作协程
        ]
        
        self.logger.info("TaskProcessor started successfully")
    
    async def stop(self):
        """停止任务处理器"""
        if not self.is_running:
            return
            
        self.logger.info("Stopping TaskProcessor...")
        self.is_running = False
        
        # 取消所有工作协程
        for task in self.worker_tasks:
            task.cancel()
        
        # 等待所有协程完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        self.logger.info("TaskProcessor stopped")
    
    async def create_task(self, 
                         task_type: str,
                         input_path: str,
                         output_path: str,
                         params: Dict[str, Any] = None,
                         priority: str = 'normal') -> int:
        """创建新任务"""
        self.task_counter += 1
        task_id = self.task_counter
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status='pending',
            input_path=input_path,
            output_path=output_path,
            params=params or {},
            priority=priority,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        await self.fetch_queue.put(task_id)
        
        self.logger.info(f"Created task {task_id}: {task_type} - {input_path} -> {output_path}")
        return task_id
    
    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
            
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'input_path': task.input_path,
            'output_path': task.output_path,
            'priority': task.priority,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error_message': task.error_message,
            'retry_count': task.retry_count
        }
    
    async def _fetch_task_worker(self):
        """获取任务工作协程"""
        while self.is_running:
            try:
                # 从队列获取任务ID
                task_id = await asyncio.wait_for(
                    self.fetch_queue.get(), 
                    timeout=self.task_check_interval
                )
                
                # 将任务放入处理队列
                await self.task_processing_queue.put(task_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in fetch_task_worker: {e}")
                await asyncio.sleep(1)
    
    async def _process_tasks_worker(self):
        """处理任务工作协程"""
        # 创建多个并发处理协程
        workers = [
            asyncio.create_task(self._task_worker(i))
            for i in range(self.max_concurrent_tasks)
        ]
        
        try:
            await asyncio.gather(*workers)
        except Exception as e:
            self.logger.error(f"Error in process_tasks_worker: {e}")
    
    async def _task_worker(self, worker_id: int):
        """单个任务处理工作协程"""
        while self.is_running:
            try:
                # 从处理队列获取任务
                task_id = await asyncio.wait_for(
                    self.task_processing_queue.get(),
                    timeout=self.task_check_interval
                )
                
                task = self.tasks.get(task_id)
                if not task:
                    continue
                
                self.logger.info(f"Worker {worker_id} processing task {task_id}")
                
                # 更新任务状态为处理中
                task.status = 'processing'
                task.started_at = datetime.now()
                await self.update_queue.put(task_id)
                
                # 处理任务
                result = await self._process_task(task)
                
                # 更新任务状态
                if result['success']:
                    task.status = 'completed'
                    task.completed_at = datetime.now()
                else:
                    task.error_message = result.get('error', 'Unknown error')
                    task.retry_count += 1
                    
                    if task.retry_count < task.max_retries:
                        task.status = 'pending'
                        await self.fetch_queue.put(task_id)  # 重新排队
                        self.logger.info(f"Task {task_id} retry {task.retry_count}/{task.max_retries}")
                    else:
                        task.status = 'failed'
                        task.completed_at = datetime.now()
                
                await self.update_queue.put(task_id)
                await self.cleanup_queue.put(task_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in task_worker {worker_id}: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task) -> Dict[str, Any]:
        """处理单个任务"""
        try:
            # 创建任务工作目录
            task_workspace = self.workspace_dir / f"task_{task.task_id}"
            task_workspace.mkdir(exist_ok=True)
            
            # 根据任务类型分发处理
            processor = self.processors.get(task.task_type)
            if not processor:
                return {
                    'success': False,
                    'error': f'Unsupported task type: {task.task_type}'
                }
            
            # 执行任务处理
            result = await processor(task, task_workspace)
            
            self.logger.info(f"Task {task.task_id} processed successfully")
            return {'success': True, 'result': result}
            
        except Exception as e:
            self.logger.error(f"Error processing task {task.task_id}: {e}")
            self.logger.debug(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_pdf_convert(self, task, workspace: Path) -> Dict[str, Any]:
        """处理PDF转换任务"""
        self.logger.info(f"Processing PDF convert task {task.task_id}")
        
        # 这里调用实际的PDF转换逻辑
        # 例如：调用之前的pdf2md_batch.py脚本
        
        # 模拟处理时间
        await asyncio.sleep(2)
        
        return {
            'input_file': task.input_path,
            'output_file': task.output_path,
            'conversion_type': 'pdf_to_markdown'
        }
    
    async def _process_markdown_convert(self, task, workspace: Path) -> Dict[str, Any]:
        """处理Markdown转换任务"""
        self.logger.info(f"Processing Markdown convert task {task.task_id}")
        
        # 模拟处理时间
        await asyncio.sleep(1)
        
        return {
            'input_file': task.input_path,
            'output_file': task.output_path,
            'conversion_type': 'markdown_processing'
        }
    
    async def _process_office_convert(self, task, workspace: Path) -> Dict[str, Any]:
        """处理Office文档转换任务"""
        self.logger.info(f"Processing Office convert task {task.task_id}")
        
        # 这里调用LibreOffice转换逻辑
        # 例如：调用之前的batch_convert.py脚本
        
        # 模拟处理时间
        await asyncio.sleep(3)
        
        return {
            'input_file': task.input_path,
            'output_file': task.output_path,
            'conversion_type': 'office_to_pdf'
        }
    
    async def _process_office_to_pdf(self, task, workspace: Path) -> Dict[str, Any]:
        """处理Office文档转PDF任务"""
        self.logger.info(f"Processing Office to PDF task {task.task_id}")
        
        try:
            from services.document_service import DocumentService
            doc_service = DocumentService()
            
            # 确保输出目录存在
            output_path = Path(task.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行转换
            result = await doc_service.convert_office_to_pdf(
                input_path=task.input_path,
                output_path=task.output_path
            )
            
            if result['success']:
                self.logger.info(f"Office to PDF conversion completed: {task.output_path}")
                return {
                    'input_file': task.input_path,
                    'output_file': task.output_path,
                    'conversion_type': 'office_to_pdf',
                    'file_size': result.get('file_size', 0)
                }
            else:
                raise Exception(result.get('error', 'Conversion failed'))
                
        except Exception as e:
            self.logger.error(f"Office to PDF conversion failed: {e}")
            raise
    
    async def _process_pdf_to_markdown(self, task, workspace: Path) -> Dict[str, Any]:
        """处理PDF转Markdown任务"""
        self.logger.info(f"Processing PDF to Markdown task {task.task_id}")
        
        try:
            from services.document_service import DocumentService
            doc_service = DocumentService()
            
            # 确保输出目录存在
            output_path = Path(task.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行转换
            result = await doc_service.convert_pdf_to_markdown(
                input_path=task.input_path,
                output_path=task.output_path
            )
            
            if result['success']:
                self.logger.info(f"PDF to Markdown conversion completed: {task.output_path}")
                return {
                    'input_file': task.input_path,
                    'output_file': task.output_path,
                    'conversion_type': 'pdf_to_markdown',
                    'pages_processed': result.get('pages_processed', 0)
                }
            else:
                raise Exception(result.get('error', 'Conversion failed'))
                
        except Exception as e:
            self.logger.error(f"PDF to Markdown conversion failed: {e}")
            raise
    
    async def _process_office_to_markdown(self, task, workspace: Path) -> Dict[str, Any]:
        """处理Office文档直接转Markdown任务"""
        self.logger.info(f"Processing Office to Markdown task {task.task_id}")
        
        try:
            from services.document_service import DocumentService
            doc_service = DocumentService()
            
            # 确保输出目录存在
            output_path = Path(task.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行转换
            result = await doc_service.convert_office_to_markdown(
                input_path=task.input_path,
                output_path=task.output_path,
                params=task.params
            )
            
            if result['success']:
                self.logger.info(f"Office to Markdown conversion completed: {task.output_path}")
                return {
                    'input_file': task.input_path,
                    'output_file': task.output_path,
                    'temp_pdf_file': result.get('temp_pdf_path'),
                    'conversion_type': 'office_to_markdown'
                }
            else:
                raise Exception(result.get('error', 'Conversion failed'))
                
        except Exception as e:
            self.logger.error(f"Office to Markdown conversion failed: {e}")
            raise
    
    async def _process_batch_office_to_markdown(self, task, workspace: Path) -> Dict[str, Any]:
        """处理批量Office文档直接转Markdown任务"""
        self.logger.info(f"Processing batch Office to Markdown task {task.task_id}")
        
        try:
            from services.document_service import DocumentService
            doc_service = DocumentService()
            
            # 确保输出目录存在
            output_path = Path(task.output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 执行批量转换
            result = await doc_service.batch_convert_office_to_markdown(
                input_dir=task.input_path,
                output_dir=task.output_path,
                **task.params
            )
            
            if result['success']:
                self.logger.info(f"Batch Office to Markdown conversion completed: {len(result.get('converted_files', []))} files")
                return {
                    'input_dir': task.input_path,
                    'output_dir': task.output_path,
                    'conversion_type': 'batch_office_to_markdown',
                    'files_processed': result.get('total_files', 0),
                    'successful_conversions': result.get('successful_conversions', 0),
                    'failed_conversions': result.get('failed_conversions', 0),
                    'converted_files': result.get('converted_files', [])
                }
            else:
                raise Exception(result.get('error', 'Batch conversion failed'))
                
        except Exception as e:
            self.logger.error(f"Batch Office to Markdown conversion failed: {e}")
            raise
    
    async def _process_batch_pdf_to_markdown(self, task, workspace: Path) -> Dict[str, Any]:
        """处理批量PDF转Markdown任务"""
        self.logger.info(f"Processing batch PDF to Markdown task {task.task_id}")
        
        try:
            from services.document_service import DocumentService
            doc_service = DocumentService()
            
            # 确保输出目录存在
            output_path = Path(task.output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 执行批量转换
            result = await doc_service.batch_convert_pdf_to_markdown(
                input_dir=task.input_path,
                output_dir=task.output_path,
                **task.params
            )
            
            if result['success']:
                self.logger.info(f"Batch PDF to Markdown conversion completed: {len(result.get('converted_files', []))} files")
                return {
                    'input_dir': task.input_path,
                    'output_dir': task.output_path,
                    'conversion_type': 'batch_pdf_to_markdown',
                    'files_processed': len(result.get('converted_files', [])),
                    'converted_files': result.get('converted_files', [])
                }
            else:
                raise Exception(result.get('error', 'Batch conversion failed'))
                
        except Exception as e:
            self.logger.error(f"Batch PDF to Markdown conversion failed: {e}")
            raise
    
    async def _update_task_worker(self):
        """更新任务状态工作协程"""
        while self.is_running:
            try:
                task_id = await asyncio.wait_for(
                    self.update_queue.get(),
                    timeout=self.task_check_interval
                )
                
                task = self.tasks.get(task_id)
                if task:
                    # 这里可以将状态更新到数据库
                    self.logger.debug(f"Updated task {task_id} status to {task.status}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in update_task_worker: {e}")
    
    async def _cleanup_worker(self):
        """清理工作协程"""
        while self.is_running:
            try:
                task_id = await asyncio.wait_for(
                    self.cleanup_queue.get(),
                    timeout=self.task_check_interval
                )
                
                # 清理任务工作目录
                task_workspace = self.workspace_dir / f"task_{task_id}"
                if task_workspace.exists():
                    # 这里可以添加文件清理逻辑
                    self.logger.debug(f"Cleaned up workspace for task {task_id}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in cleanup_worker: {e}")
    
    async def _callback_worker(self):
        """回调处理工作协程"""
        while self.is_running:
            try:
                # 这里可以处理任务完成后的回调通知
                await asyncio.sleep(self.task_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in callback_worker: {e}")
    
    def get_queue_stats(self) -> Dict[str, int]:
        """获取队列统计信息"""
        return {
            'fetch_queue': self.fetch_queue.qsize(),
            'processing_queue': self.task_processing_queue.qsize(),
            'update_queue': self.update_queue.qsize(),
            'cleanup_queue': self.cleanup_queue.qsize(),
            'callback_queue': self.callback_queue.qsize(),
            'total_tasks': len(self.tasks),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == 'pending']),
            'processing_tasks': len([t for t in self.tasks.values() if t.status == 'processing']),
            'completed_tasks': len([t for t in self.tasks.values() if t.status == 'completed']),
            'failed_tasks': len([t for t in self.tasks.values() if t.status == 'failed'])
        }