#!/usr/bin/env python3
"""
增强版文档转换任务处理器
复刻MediaConvert的企业级任务处理架构，支持数据库持久化、云存储集成等功能
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


class EnhancedTaskProcessor:
    """
    增强版文档转换任务处理器
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
        初始化增强版任务处理器
        
        Args:
            database_type: 数据库类型 ("sqlite" 或 "mysql")
            database_url: 数据库连接URL
            max_concurrent_tasks: 最大并发任务数
            task_check_interval: 任务检查间隔(秒)
            workspace_dir: 工作空间目录
        """
        self.database_type = database_type
        self.database_url = database_url
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_check_interval = task_check_interval
        
        # 初始化数据库管理器
        self.db_manager: Optional[DatabaseManager] = None
        
        # 初始化服务组件
        self.s3_download_service = S3DownloadService()
        self.s3_upload_service = S3UploadService()
        self.workspace_manager = WorkspaceManager(workspace_dir)
        self.doc_service = DocumentService()
        
        # 队列系统 - 复刻MediaConvert的多队列设计
        self.fetch_queue = asyncio.Queue()           # 获取任务队列
        self.task_processing_queue = asyncio.Queue() # 任务处理队列
        self.update_queue = asyncio.Queue()          # 状态更新队列
        self.cleanup_queue = asyncio.Queue()         # 清理队列
        self.callback_queue = asyncio.Queue()        # 回调队列
        
        # 优先级队列 - 支持智能调度
        self.high_priority_queue = asyncio.Queue()   # 高优先级队列
        self.normal_priority_queue = asyncio.Queue() # 普通优先级队列
        self.low_priority_queue = asyncio.Queue()    # 低优先级队列
        
        # 运行状态
        self.is_running = False
        self.workers = []
        self.shutdown_event = threading.Event()
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0
        }
        
        logger.info(f"EnhancedTaskProcessor initialized - DB: {database_type}, Max concurrent: {max_concurrent_tasks}")
    
    async def initialize(self):
        """初始化数据库连接和其他资源"""
        try:
            # 初始化数据库管理器
            self.db_manager = DatabaseManager(
                database_type=self.database_type,
                database_url=self.database_url
            )
            await self.db_manager.initialize()
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_task(self, request: TaskCreateRequest) -> str:
        """
        创建新任务
        
        Args:
            request: 任务创建请求
            
        Returns:
            任务ID
        """
        try:
            # 创建任务对象 - 使用数据库自增ID
            task = DocumentTask(
                task_type=request.task_type,
                status=TaskStatus.pending,
                priority=request.priority,
                bucket_name=request.bucket_name,
                file_path=request.file_path,
                file_url=request.file_url,
                input_path=request.input_path,
                output_path=request.output_path,
                params=request.params,
                callback_url=request.callback_url,
                platform=request.platform,
                created_at=datetime.now()
            )
            
            # 保存到数据库 - 数据库会自动分配自增ID
            task = await self.db_manager.create_task(task)
            task_id = task.id  # 获取数据库分配的自增ID

            # 放入获取队列
            await self.fetch_queue.put(task_id)

            # 更新统计
            self.stats["total_tasks"] += 1

            task_logger = get_task_logger(task_id)
            task_logger.log_task_start(request.task_type, f"Input: {request.input_path or request.file_url or f's3://{request.bucket_name}/{request.file_path}'}")

            logger.info(f"Created task {task_id}: {request.task_type}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def start(self):
        """启动任务处理器"""
        if self.is_running:
            logger.warning("TaskProcessor is already running")
            return

        try:
            # 初始化数据库
            await self.initialize()

            # 恢复未完成的任务
            await self._recover_incomplete_tasks()

            self.is_running = True

            # 启动工作协程
            self.workers = [
                asyncio.create_task(self._fetch_task_worker()),
                asyncio.create_task(self._priority_scheduler_worker()),
                asyncio.create_task(self._update_task_worker()),
                asyncio.create_task(self._cleanup_worker()),
                asyncio.create_task(self._callback_worker()),
                asyncio.create_task(self._gc_worker()),
            ]

            # 启动任务处理工作协程
            for i in range(self.max_concurrent_tasks):
                worker = asyncio.create_task(self._task_worker(i))
                self.workers.append(worker)

            logger.info(f"TaskProcessor started with {len(self.workers)} workers")
            
        except Exception as e:
            logger.error(f"Failed to start TaskProcessor: {e}")
            self.is_running = False
            raise

    async def _recover_incomplete_tasks(self):
        """恢复未完成的任务"""
        try:
            logger.info("Recovering incomplete tasks...")

            # 查询processing状态的任务
            from database.models import QueryTasksFilter, TaskStatus
            filter_params = QueryTasksFilter(
                status=TaskStatus.processing,
                limit=100  # 最大限制100个任务
            )

            processing_tasks = await self.db_manager.query_tasks(filter_params)

            if not processing_tasks:
                logger.info("No incomplete tasks to recover")
                return

            logger.info(f"Found {len(processing_tasks)} incomplete tasks to recover")

            # 将任务状态重置为pending
            recovered_count = 0
            for task in processing_tasks:
                try:
                    await self.db_manager.update_task_status(
                        task.id,
                        TaskStatus.pending,
                        error_message="Task recovered after service restart"
                    )
                    recovered_count += 1
                    logger.debug(f"Recovered task {task.id}: {task.task_type}")
                except Exception as e:
                    logger.error(f"Failed to recover task {task.id}: {e}")

            logger.info(f"Successfully recovered {recovered_count} tasks to pending status")

        except Exception as e:
            logger.error(f"Failed to recover incomplete tasks: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def stop(self):
        """停止任务处理器"""
        if not self.is_running:
            return
        
        logger.info("Stopping TaskProcessor...")
        self.is_running = False
        
        # 等待所有工作协程完成
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        # 关闭数据库连接
        if self.db_manager:
            await self.db_manager.close()
        
        logger.info("TaskProcessor stopped")
    
    async def _fetch_task_worker(self):
        """获取任务工作协程"""
        while self.is_running:
            try:
                # 从数据库获取待处理任务
                from database.models import QueryTasksFilter
                filter_params = QueryTasksFilter(
                    status=TaskStatus.pending,
                    limit=self.max_concurrent_tasks
                )
                tasks = await self.db_manager.query_tasks(filter_params)
                
                for task in tasks:
                    # 更新状态为处理中
                    await self.db_manager.update_task_status(task.id, TaskStatus.processing)
                    
                    # 根据优先级分发到不同队列
                    if task.priority == TaskPriority.high:
                        await self.high_priority_queue.put(task.id)
                    elif task.priority == TaskPriority.low:
                        await self.low_priority_queue.put(task.id)
                    else:
                        await self.normal_priority_queue.put(task.id)
                
                # 等待一段时间再次检查
                await asyncio.sleep(self.task_check_interval)
                
            except Exception as e:
                logger.error(f"Error in fetch_task_worker: {e}")
                await asyncio.sleep(self.task_check_interval)
    
    async def _priority_scheduler_worker(self):
        """优先级调度工作协程"""
        while self.is_running:
            try:
                task_id = None
                
                # 按优先级顺序获取任务
                if not self.high_priority_queue.empty():
                    task_id = await self.high_priority_queue.get()
                elif not self.normal_priority_queue.empty():
                    task_id = await self.normal_priority_queue.get()
                elif not self.low_priority_queue.empty():
                    task_id = await self.low_priority_queue.get()
                
                if task_id:
                    await self.task_processing_queue.put(task_id)
                else:
                    await asyncio.sleep(1)  # 没有任务时短暂等待
                    
            except Exception as e:
                logger.error(f"Error in priority_scheduler_worker: {e}")
                await asyncio.sleep(1)
    
    async def _task_worker(self, worker_id: int):
        """任务处理工作协程"""
        logger.info(f"Task worker {worker_id} started")
        
        while self.is_running:
            try:
                # 从处理队列获取任务
                task_id = await asyncio.wait_for(
                    self.task_processing_queue.get(),
                    timeout=self.task_check_interval
                )
                
                # 获取任务详情
                task = await self.db_manager.get_task(task_id)
                if not task:
                    logger.warning(f"Task {task_id} not found")
                    continue
                
                task_logger = get_task_logger(task_id)
                task_logger.info(f"Worker {worker_id} processing task")
                
                # 更新活跃任务统计
                self.stats["active_tasks"] += 1
                
                # 执行任务处理
                start_time = datetime.now()
                result = await self._process_task(task, task_logger)
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                
                # 更新任务结果
                await self._handle_task_result(task, result, processing_time, task_logger)
                
                # 更新统计
                self.stats["active_tasks"] -= 1
                if result['success']:
                    self.stats["completed_tasks"] += 1
                else:
                    self.stats["failed_tasks"] += 1
                
                # 放入后续处理队列
                await self.update_queue.put(task_id)
                await self.cleanup_queue.put(task_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task_worker {worker_id}: {e}")
                if 'task_id' in locals():
                    await self._handle_task_error(task_id, str(e))
                await asyncio.sleep(1)

    async def _process_task(self, task: DocumentTask, task_logger) -> Dict[str, Any]:
        """
        处理单个任务

        Args:
            task: 任务对象
            task_logger: 任务日志记录器

        Returns:
            处理结果字典
        """
        try:
            # 创建任务工作空间
            workspace = self.workspace_manager.create_task_workspace(task.id)
            task_logger.log_task_progress("workspace_created", f"Workspace: {workspace}")

            # 步骤1: 下载文件
            input_file_path = await self._download_input_file(task, task_logger)
            if not input_file_path:
                raise Exception("Failed to download input file")

            # 步骤2: 执行文档转换
            output_file_path = await self._execute_conversion(task, input_file_path, task_logger)
            if not output_file_path:
                raise Exception("Document conversion failed")

            # 步骤3: 上传结果文件
            upload_result = await self._upload_output_file(task, output_file_path, task_logger)
            if not upload_result['success']:
                raise Exception(f"Failed to upload output file: {upload_result.get('error')}")

            return {
                'success': True,
                'input_file': str(input_file_path),
                'output_file': str(output_file_path),
                'upload_result': upload_result,
                'conversion_type': task.task_type
            }

        except Exception as e:
            task_logger.error(f"Task processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    async def _download_input_file(self, task: DocumentTask, task_logger) -> Optional[Path]:
        """下载输入文件"""
        try:
            if task.bucket_name and task.file_path:
                # 从S3下载 - 应用MediaConvert的中文文件名处理方案
                from utils.encoding_utils import EncodingUtils

                # 处理中文文件名编码
                raw_filename = Path(task.file_path).name
                filename = EncodingUtils.decode_url_filename(raw_filename)

                task_logger.debug(f"Raw filename: {raw_filename}")
                task_logger.debug(f"Decoded filename: {filename}")

                local_path = self.workspace_manager.get_downloaded_file_path(task.id, filename)

                task_logger.log_task_progress("downloading_from_s3", f"s3://{task.bucket_name}/{task.file_path}")

                result = await self.s3_download_service.download_file(
                    bucket_name=task.bucket_name,
                    s3_key=task.file_path,
                    local_file_path=str(local_path)
                )

                if result['success']:
                    task_logger.log_s3_operation("download", f"s3://{task.bucket_name}/{task.file_path}", True,
                                                f"Size: {result['file_size']} bytes, Time: {result['download_time']:.2f}s")

                    # 更新任务信息
                    await self.db_manager.update_task(
                        task.id,
                        input_path=str(local_path),
                        file_name=filename,
                        file_size_bytes=result['file_size']
                    )

                    return local_path
                else:
                    task_logger.log_s3_operation("download", f"s3://{task.bucket_name}/{task.file_path}", False, result.get('error'))
                    return None

            elif task.file_url:
                # 从HTTP URL下载
                # TODO: 实现HTTP下载逻辑
                task_logger.error("HTTP URL download not implemented yet")
                return None

            elif task.input_path:
                # 使用本地文件 - 复制到task_workspace的input目录
                input_path = Path(task.input_path)
                if input_path.exists():
                    # 复制文件到task_workspace的input目录
                    filename = input_path.name
                    workspace_input_path = self.workspace_manager.get_downloaded_file_path(task.id, filename)

                    # 确保input目录存在
                    workspace_input_path.parent.mkdir(parents=True, exist_ok=True)

                    # 复制文件
                    import shutil
                    shutil.copy2(str(input_path), str(workspace_input_path))

                    task_logger.log_file_operation("local_file_copy", f"{input_path} -> {workspace_input_path}", True,
                                                 f"Size: {workspace_input_path.stat().st_size} bytes")

                    # 更新任务信息
                    await self.db_manager.update_task(
                        task.id,
                        input_path=str(workspace_input_path),
                        file_name=filename,
                        file_size_bytes=workspace_input_path.stat().st_size
                    )

                    return workspace_input_path
                else:
                    task_logger.log_file_operation("local_file_access", str(input_path), False, "File not found")
                    return None
            else:
                task_logger.error("No valid input source specified")
                return None

        except Exception as e:
            task_logger.error(f"Failed to download input file: {e}")
            return None

    async def _execute_conversion(self, task: DocumentTask, input_file: Path, task_logger) -> Optional[Path]:
        """执行文档转换"""
        try:
            # 准备输出文件路径
            if task.output_path:
                output_file = self.workspace_manager.ensure_output_directory(task.output_path)
            else:
                # 自动生成输出文件名
                if task.task_type == 'office_to_pdf':
                    output_filename = input_file.stem + '.pdf'
                elif task.task_type in ['pdf_to_markdown', 'office_to_markdown', 'image_to_markdown']:
                    output_filename = input_file.stem + '.md'
                else:
                    output_filename = input_file.stem + '_converted' + input_file.suffix

                output_file = self.workspace_manager.get_output_file_path(task.id, output_filename)

            task_logger.log_task_progress("conversion_started", f"Type: {task.task_type}")

            # 根据任务类型执行转换
            if task.task_type == 'office_to_pdf':
                result = await self.doc_service.convert_office_to_pdf(
                    input_path=str(input_file),
                    output_path=str(output_file)
                )
            elif task.task_type == 'pdf_to_markdown':
                result = await self.doc_service.convert_pdf_to_markdown(
                    input_path=str(input_file),
                    output_path=str(output_file),
                    **task.params or {}
                )
            elif task.task_type == 'office_to_markdown':
                result = await self.doc_service.convert_office_to_markdown(
                    input_path=str(input_file),
                    output_path=str(output_file)
                )
            elif task.task_type == 'image_to_markdown':
                result = await self.doc_service.convert_image_to_markdown(
                    input_path=str(input_file),
                    output_path=str(output_file)
                )
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")

            if result['success']:
                task_logger.log_conversion_step(task.task_type, str(input_file), str(output_file), True,
                                              f"Output size: {output_file.stat().st_size if output_file.exists() else 0} bytes")

                # 更新任务信息
                await self.db_manager.update_task(
                    task.id,
                    output_path=str(output_file),
                    result=result
                )

                return output_file
            else:
                task_logger.log_conversion_step(task.task_type, str(input_file), str(output_file), False, result.get('error'))
                return None

        except Exception as e:
            task_logger.error(f"Conversion failed: {e}")
            return None

    async def _upload_output_file(self, task: DocumentTask, output_file: Path, task_logger) -> Dict[str, Any]:
        """上传输出文件到S3（支持完整目录上传）"""
        try:
            # 检查是否是完整的输出目录（包含多个文件）
            output_dir = output_file.parent
            has_multiple_files = len(list(output_dir.iterdir())) > 1
            has_images_dir = (output_dir / "images").exists()
            has_json_file = any(f.suffix == '.json' for f in output_dir.iterdir() if f.is_file())

            # 如果有多个文件（特别是图片目录或JSON文件），使用完整目录上传
            if has_multiple_files and (has_images_dir or has_json_file):
                task_logger.log_task_progress("uploading_to_s3", f"Complete result directory: {output_dir.name}")

                # 解析原始文件路径信息
                original_bucket = None
                original_folder = None
                original_filename = None

                if task.bucket_name and task.file_path:
                    # 特殊处理：如果bucket是ai-file且路径包含pdf/markdown结构，需要解析出原始信息
                    if task.bucket_name == "ai-file" and ("/pdf/" in task.file_path or "/markdown/" in task.file_path):
                        # 解析ai-file路径：{original_bucket}/{original_name}/{type}/{filename}
                        # 例如：test/杭电申报-428定/pdf/杭电申报-428定.pdf
                        path_parts = task.file_path.split('/')
                        logger.info(f"[Task {task.id}] Parsing ai-file path: {task.file_path}, parts: {path_parts}")
                        if len(path_parts) >= 4 and (path_parts[2] == "pdf" or path_parts[2] == "markdown"):
                            original_bucket = path_parts[0]  # 真正的原始bucket: test
                            original_name = path_parts[1]    # 原始文件名(无后缀): 杭电申报-428定
                            # 对于PDF转Markdown，我们需要使用原始的doc文件名作为original_filename
                            if task.task_type == "pdf_to_markdown":
                                original_filename = f"{original_name}.doc"  # 假设原始文件是doc
                            else:
                                original_filename = Path(task.file_path).name  # 保持当前文件名
                            original_folder = ""  # 根目录
                            logger.info(f"[Task {task.id}] Parsed: bucket={original_bucket}, name={original_name}, filename={original_filename}")
                        else:
                            # 如果路径格式不符合预期，使用默认处理
                            original_bucket = task.bucket_name
                            original_filename = Path(task.file_path).name
                            file_path_parts = task.file_path.split('/')
                            if len(file_path_parts) > 1:
                                original_folder = '/'.join(file_path_parts[:-1])
                            else:
                                original_folder = ""
                    else:
                        # 普通处理
                        original_bucket = task.bucket_name
                        original_filename = Path(task.file_path).name
                        # 从file_path提取文件夹路径
                        file_path_parts = task.file_path.split('/')
                        if len(file_path_parts) > 1:
                            original_folder = '/'.join(file_path_parts[:-1])
                        else:
                            original_folder = ""
                elif task.platform and task.input_path:
                    # 后备方案：根据平台设置bucket和folder
                    original_filename = Path(task.input_path).name
                    # 使用bucket_name如果有的话，否则使用platform作为bucket
                    original_bucket = task.bucket_name if task.bucket_name else task.platform
                    # 使用文件所在的目录路径作为folder
                    input_path = Path(task.input_path)
                    if len(input_path.parts) > 1:
                        # 提取相对于某个基础路径的文件夹路径
                        original_folder = str(input_path.parent).replace('/workspace/', '').replace('/workspace', '')
                    else:
                        original_folder = "documents"
                elif task.input_path and not original_filename:
                    # 从本地路径提取文件名（仅当之前没有解析出original_filename时）
                    original_filename = Path(task.input_path).name

                # 上传完整的转换结果
                result = await self.s3_upload_service.upload_complete_conversion_result(
                    output_dir_path=str(output_dir),
                    task_id=task.id,
                    original_filename=original_filename,
                    original_bucket=original_bucket,
                    original_folder=original_folder,
                    task_type=task.task_type
                )

                if result['success']:
                    task_logger.log_s3_operation("upload", result.get('s3_prefix', f"task_{task.id}"), True,
                                                f"Files: {result['total_files']}, Size: {result['total_size']} bytes")

                    # 收集所有上传文件的URL
                    s3_urls = [file_info['s3_url'] for file_info in result.get('uploaded_files', [])]

                    # 更新任务信息
                    await self.db_manager.update_task(
                        task.id,
                        output_url=result.get('s3_url'),  # 主要文件URL
                        s3_urls=s3_urls
                    )
                else:
                    task_logger.log_s3_operation("upload", f"task_{task.id}/complete", False, result.get('error'))

                return result

            else:
                # 单文件上传（原有逻辑）
                task_logger.log_task_progress("uploading_to_s3", f"File: {output_file.name}")

                # 解析原始文件路径信息
                original_bucket = None
                original_folder = None
                if task.bucket_name and task.file_path:
                    original_bucket = task.bucket_name
                    # 从file_path中提取文件夹路径
                    file_path_parts = task.file_path.split('/')
                    if len(file_path_parts) > 1:
                        original_folder = '/'.join(file_path_parts[:-1])  # 除了文件名的所有部分
                elif task.bucket_name and task.file_path:
                    # 使用任务中的bucket_name和file_path
                    original_bucket = task.bucket_name
                    original_filename = Path(task.file_path).name
                    # 从file_path提取文件夹路径
                    file_path_parts = task.file_path.split('/')
                    if len(file_path_parts) > 1:
                        original_folder = '/'.join(file_path_parts[:-1])
                    else:
                        original_folder = ""
                elif task.platform and task.input_path:
                    # 后备方案：根据平台设置bucket和folder
                    # 使用bucket_name如果有的话，否则使用platform作为bucket
                    original_bucket = task.bucket_name if task.bucket_name else task.platform
                    # 使用文件所在的目录路径作为folder
                    input_path = Path(task.input_path)
                    if len(input_path.parts) > 1:
                        # 提取相对于某个基础路径的文件夹路径
                        original_folder = str(input_path.parent).replace('/workspace/', '').replace('/workspace', '')
                    else:
                        original_folder = "documents"

                # 上传到ai-file存储桶，遵循Media-Convert路径规则
                result = await self.s3_upload_service.upload_converted_document(
                    local_path=str(output_file),
                    task_id=task.id,
                    original_filename=output_file.name,
                    original_bucket=original_bucket,
                    original_folder=original_folder,
                    task_type=task.task_type
                )

                if result['success']:
                    task_logger.log_s3_operation("upload", result['s3_url'], True,
                                                f"Size: {result['file_size']} bytes, Time: {result['upload_time']:.2f}s")

                    # 更新任务信息
                    await self.db_manager.update_task(
                        task.id,
                        output_url=result.get('http_url'),
                        s3_urls=[result['s3_url']]
                    )
                else:
                    task_logger.log_s3_operation("upload", f"task_{task.id}/{output_file.name}", False, result.get('error'))

                return result

        except Exception as e:
            task_logger.error(f"Failed to upload output file: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    async def _handle_task_result(self, task: DocumentTask, result: Dict[str, Any], processing_time: float, task_logger):
        """处理任务结果"""
        try:
            if result['success']:
                # 成功处理
                await self.db_manager.update_task(
                    task.id,
                    status=TaskStatus.completed,
                    completed_at=datetime.now(),
                    task_processing_time=processing_time,
                    result=result
                )
                task_logger.log_task_completion(True, processing_time, result.get('upload_result', {}).get('s3_url', ''))
            else:
                # 失败处理
                await self._handle_task_error(task.id, result.get('error', 'Unknown error'))

        except Exception as e:
            logger.error(f"Error handling task result for {task.id}: {e}")

    async def _handle_task_error(self, task_id: str, error_message: str):
        """处理任务错误"""
        try:
            task = await self.db_manager.get_task(task_id)
            if not task:
                return

            task_logger = get_task_logger(task_id)

            # 增加重试次数
            retry_count = task.retry_count + 1

            if retry_count < task.max_retry_count:
                # 重试
                await self.db_manager.update_task(
                    task_id,
                    status=TaskStatus.pending,
                    retry_count=retry_count,
                    last_retry_at=datetime.now(),
                    error_message=error_message
                )

                task_logger.log_error_with_retry(error_message, retry_count, task.max_retry_count)

                # 重新放入获取队列
                await self.fetch_queue.put(task_id)
            else:
                # 标记为最终失败
                await self.db_manager.update_task(
                    task_id,
                    status=TaskStatus.failed,
                    completed_at=datetime.now(),
                    retry_count=retry_count,
                    error_message=error_message
                )

                task_logger.log_error_with_retry(error_message, retry_count, task.max_retry_count)

        except Exception as e:
            logger.error(f"Error handling task error for {task_id}: {e}")

    async def _update_task_worker(self):
        """任务状态更新工作协程"""
        while self.is_running:
            try:
                task_id = await asyncio.wait_for(
                    self.update_queue.get(),
                    timeout=self.task_check_interval
                )

                # 这里可以添加额外的状态更新逻辑
                # 例如发送通知、更新缓存等
                logger.debug(f"Updated task {task_id}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in update_task_worker: {e}")

    async def _cleanup_worker(self):
        """资源清理工作协程 - 只清理临时文件，保留input和output"""
        while self.is_running:
            try:
                task_id = await asyncio.wait_for(
                    self.cleanup_queue.get(),
                    timeout=self.task_check_interval
                )

                # 只清理临时文件，保留input和output目录
                task_workspace = self.workspace_manager.get_task_workspace(task_id)
                if task_workspace.exists():
                    # 清理temp目录中的临时文件
                    temp_dir = task_workspace / "temp"
                    if temp_dir.exists():
                        import shutil
                        for item in temp_dir.iterdir():
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item)
                        logger.debug(f"Cleaned temp files for task {task_id}")

                    # 清理output目录中的临时文件（如temp_mineru_output）
                    output_dir = task_workspace / "output"
                    if output_dir.exists():
                        for item in output_dir.iterdir():
                            if item.is_dir() and "temp" in item.name.lower():
                                shutil.rmtree(item)
                                logger.debug(f"Cleaned temp output dir: {item.name}")

                # 放入回调队列
                await self.callback_queue.put(task_id)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in cleanup_worker: {e}")

    async def _callback_worker(self):
        """回调处理工作协程"""
        while self.is_running:
            try:
                task_id = await asyncio.wait_for(
                    self.callback_queue.get(),
                    timeout=self.task_check_interval
                )

                # 获取任务信息
                task = await self.db_manager.get_task(task_id)
                if task and task.callback_url:
                    # TODO: 实现HTTP回调
                    logger.info(f"Task {task_id} callback URL: {task.callback_url}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in callback_worker: {e}")

    async def _gc_worker(self):
        """垃圾回收工作协程"""
        while self.is_running:
            try:
                # 每30分钟执行一次垃圾回收
                await asyncio.sleep(1800)

                if not self.is_running:
                    break

                # 清理临时文件
                cleaned_files = self.workspace_manager.cleanup_temp_files(max_age_hours=24)
                if cleaned_files > 0:
                    logger.info(f"GC: Cleaned {cleaned_files} temp files")

                # 执行Python垃圾回收
                collected = gc.collect()
                if collected > 0:
                    logger.info(f"GC: Collected {collected} objects")

                # 清理旧任务记录（可选）
                # cleaned_tasks = await self.db_manager.cleanup_old_tasks(days=30)
                # if cleaned_tasks > 0:
                #     logger.info(f"GC: Cleaned {cleaned_tasks} old tasks")

            except Exception as e:
                logger.error(f"Error in gc_worker: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        workspace_stats = self.workspace_manager.get_workspace_stats()

        return {
            **self.stats,
            "is_running": self.is_running,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "queue_sizes": {
                "fetch_queue": self.fetch_queue.qsize(),
                "task_processing_queue": self.task_processing_queue.qsize(),
                "high_priority_queue": self.high_priority_queue.qsize(),
                "normal_priority_queue": self.normal_priority_queue.qsize(),
                "low_priority_queue": self.low_priority_queue.qsize(),
                "update_queue": self.update_queue.qsize(),
                "cleanup_queue": self.cleanup_queue.qsize(),
                "callback_queue": self.callback_queue.qsize()
            },
            "workspace_stats": workspace_stats
        }
