#!/usr/bin/env python3
"""
FastAPI应用主文件

提供文档转换调度系统的REST API接口。
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.task_processor import TaskProcessor
from services.document_service import DocumentService


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
task_processor: Optional[TaskProcessor] = None
document_service: Optional[DocumentService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global task_processor, document_service
    
    # 启动时初始化
    logger.info("Starting Document Scheduler API...")
    
    # 初始化服务
    document_service = DocumentService()
    task_processor = TaskProcessor(
        max_concurrent_tasks=3,
        task_check_interval=5
    )
    
    # 启动任务处理器
    await task_processor.start()
    
    logger.info("Document Scheduler API started successfully")
    
    yield
    
    # 关闭时清理
    logger.info("Shutting down Document Scheduler API...")
    
    if task_processor:
        await task_processor.stop()
    
    logger.info("Document Scheduler API stopped")


# 创建FastAPI应用
app = FastAPI(
    title="Document Scheduler API",
    description="文档转换调度系统API",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic模型
class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""
    task_type: str  # 'office_to_pdf', 'pdf_to_markdown', 'batch_office_to_pdf', 'batch_pdf_to_markdown'
    input_path: str
    output_path: str
    priority: str = 'normal'  # 'low', 'normal', 'high'
    params: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: int
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: int
    task_type: str
    status: str
    input_path: str
    output_path: str
    priority: str
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    retry_count: int


class QueueStatsResponse(BaseModel):
    """队列统计响应模型"""
    fetch_queue: int
    processing_queue: int
    update_queue: int
    cleanup_queue: int
    callback_queue: int
    total_tasks: int
    pending_tasks: int
    processing_tasks: int
    completed_tasks: int
    failed_tasks: int


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Document Scheduler API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "task_processor_running": task_processor.is_running if task_processor else False,
        "queue_stats": task_processor.get_queue_stats() if task_processor else {}
    }


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(request: TaskCreateRequest):
    """创建文档转换任务"""
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    try:
        # 验证任务类型
        valid_task_types = {
            'office_to_pdf', 'pdf_to_markdown',
            'batch_office_to_pdf', 'batch_pdf_to_markdown',
            'office_to_markdown', 'batch_office_to_markdown'
        }
        
        if request.task_type not in valid_task_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid task type. Supported types: {valid_task_types}"
            )
        
        # 创建任务
        task_id = await task_processor.create_task(
            task_type=request.task_type,
            input_path=request.input_path,
            output_path=request.output_path,
            params=request.params,
            priority=request.priority
        )
        
        return TaskResponse(
            task_id=task_id,
            message=f"Task {task_id} created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: int):
    """获取任务状态"""
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    task_status = task_processor.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskStatusResponse(**task_status)


@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 100):
    """列出任务"""
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    tasks = []
    for task in task_processor.tasks.values():
        if status is None or task.status == status:
            tasks.append(task_processor.get_task_status(task.id))
    
    # 限制返回数量
    tasks = tasks[:limit]
    
    return {
        "tasks": tasks,
        "total": len(tasks),
        "filter_status": status
    }


@app.get("/api/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """获取队列统计信息"""
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    stats = task_processor.get_queue_stats()
    return QueueStatsResponse(**stats)


@app.get("/api/formats")
async def get_supported_formats():
    """获取支持的文件格式"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service not available")
    
    return document_service.get_supported_formats()


@app.get("/api/shortcuts/office-to-pdf")
async def create_office_to_pdf_task(
    input_path: str = Query(..., description="输入Office文档路径"),
    output_path: str = Query(..., description="输出PDF文件路径"),
    priority: str = Query('normal', description="任务优先级")
):
    """创建Office转PDF任务（快捷接口）"""
    request = TaskCreateRequest(
        task_type='office_to_pdf',
        input_path=input_path,
        output_path=output_path,
        priority=priority
    )
    return await create_task(request)


@app.get("/api/shortcuts/pdf-to-markdown")
async def create_pdf_to_markdown_task(
    input_path: str = Query(..., description="输入PDF文件路径"),
    output_path: str = Query(..., description="输出Markdown文件路径"),
    priority: str = Query('normal', description="任务优先级"),
    force_reprocess: bool = Query(False, description="是否强制重新处理")
):
    """创建PDF转Markdown任务（快捷接口）"""
    request = TaskCreateRequest(
        task_type='pdf_to_markdown',
        input_path=input_path,
        output_path=output_path,
        priority=priority,
        params={'force_reprocess': force_reprocess}
    )
    return await create_task(request)


@app.get("/api/shortcuts/batch-office-to-pdf")
async def create_batch_office_to_pdf_task(
    input_path: str = Query(..., description="输入目录路径"),
    output_path: str = Query(..., description="输出目录路径"),
    priority: str = Query('normal', description="任务优先级"),
    recursive: bool = Query(False, description="是否递归处理子目录"),
    file_pattern: Optional[str] = Query(None, description="文件名匹配模式，支持正则表达式")
):
    """创建批量Office转PDF任务（快捷接口）"""
    params = {'recursive': recursive}
    if file_pattern:
        params['file_pattern'] = file_pattern
    
    request = TaskCreateRequest(
        task_type='batch_office_to_pdf',
        input_path=input_path,
        output_path=output_path,
        priority=priority,
        params=params
    )
    return await create_task(request)


@app.get("/api/shortcuts/batch-pdf-to-markdown")
async def create_batch_pdf_to_markdown_task(
    input_path: str = Query(..., description="输入目录路径"),
    output_path: str = Query(..., description="输出目录路径"),
    priority: str = Query('normal', description="任务优先级"),
    force_reprocess: bool = Query(False, description="是否强制重新处理"),
    file_pattern: Optional[str] = Query(None, description="文件名匹配模式，支持正则表达式")
):
    """创建批量PDF转Markdown任务（快捷接口）"""
    params = {'force_reprocess': force_reprocess}
    if file_pattern:
        params['file_pattern'] = file_pattern
    
    request = TaskCreateRequest(
        task_type='batch_pdf_to_markdown',
        input_path=input_path,
        output_path=output_path,
        priority=priority,
        params=params
    )
    return await create_task(request)


@app.get("/api/shortcuts/office-to-markdown")
async def create_office_to_markdown_task(
    input_path: str = Query(..., description="输入Office文档路径"),
    output_path: str = Query(..., description="输出Markdown文件路径"),
    priority: str = Query('normal', description="任务优先级"),
    force_reprocess: bool = Query(False, description="是否强制重新处理")
):
    """创建Office文档直接转Markdown任务（快捷接口）
    
    将Office文档直接转换为Markdown，无需用户手动进行两步转换
    """
    request = TaskCreateRequest(
        task_type='office_to_markdown',
        input_path=input_path,
        output_path=output_path,
        priority=priority,
        params={'force_reprocess': force_reprocess}
    )
    return await create_task(request)


@app.get("/api/shortcuts/batch-office-to-markdown")
async def create_batch_office_to_markdown_task(
    input_path: str = Query(..., description="输入目录路径"),
    output_path: str = Query(..., description="输出目录路径"),
    priority: str = Query('normal', description="任务优先级"),
    force_reprocess: bool = Query(False, description="是否强制重新处理"),
    recursive: bool = Query(False, description="是否递归处理子目录"),
    file_pattern: Optional[str] = Query(None, description="文件名匹配模式，支持正则表达式")
):
    """创建批量Office文档直接转Markdown任务（快捷接口）
    
    批量将Office文档直接转换为Markdown，无需用户手动进行两步转换
    """
    params = {
        'force_reprocess': force_reprocess,
        'recursive': recursive
    }
    if file_pattern:
        params['file_pattern'] = file_pattern
    
    request = TaskCreateRequest(
        task_type='batch_office_to_markdown',
        input_path=input_path,
        output_path=output_path,
        priority=priority,
        params=params
    )
    return await create_task(request)


@app.post("/api/task/magic-file/create")
async def create_magic_file_task(
    file: UploadFile = File(...),
    conversion_type: str = Form(..., description="转换类型，支持：office_to_pdf, office_to_markdown"),
    priority: str = Form('normal', description="任务优先级")
):
    """创建魔法文件转换任务
    
    上传文件并根据conversion_type进行转换
    """
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    # 验证转换类型
    valid_conversion_types = {'office_to_pdf', 'office_to_markdown'}
    if conversion_type not in valid_conversion_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid conversion type. Supported types: {valid_conversion_types}"
        )
    
    # 创建任务工作目录
    task_dir = Path("/workspace/task_workspace/output/task_" + str(int(time.time())))
    input_dir = task_dir / "input"
    output_dir = task_dir / "output"
    
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存上传的文件
    file_path = input_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 确定输出文件路径和扩展名
    file_name = Path(file.filename).stem
    output_extension = ".pdf" if conversion_type == "office_to_pdf" else ".md"
    output_path = output_dir / (file_name + output_extension)
    
    # 创建转换任务
    task_id = await task_processor.create_task(
        task_type=conversion_type,
        input_path=str(file_path),
        output_path=str(output_path),
        params={},
        priority=priority
    )
    
    return {
        "task_id": task_id,
        "message": f"Task {task_id} created successfully",
        "input_file": str(file_path),
        "output_file": str(output_path),
        "status_url": f"/api/tasks/{task_id}",
        "download_url": f"/api/download/{task_id}"
    }


@app.post("/api/upload-and-convert")
async def upload_and_convert(
    file: UploadFile = File(...),
    conversion_type: str = Form(..., description="转换类型，支持：office_to_pdf, pdf_to_markdown, office_to_markdown"),
    priority: str = Form('normal', description="任务优先级")
):
    """上传文件并转换
    
    上传文件到任务输入路径，然后转换到输出路径
    """
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    # 验证转换类型
    valid_conversion_types = {'office_to_pdf', 'pdf_to_markdown', 'office_to_markdown'}
    if conversion_type not in valid_conversion_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid conversion type. Supported types: {valid_conversion_types}"
        )
    
    # 创建任务工作目录
    task_dir = Path("/workspace/task_workspace/output/task_" + str(int(time.time())))
    input_dir = task_dir / "input"
    output_dir = task_dir / "output"
    
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存上传的文件
    file_path = input_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 确定输出文件路径和扩展名
    file_name = Path(file.filename).stem
    output_extension = ".pdf" if conversion_type == "office_to_pdf" else ".md"
    output_path = output_dir / (file_name + output_extension)
    
    # 创建转换任务
    task_id = await task_processor.create_task(
        task_type=conversion_type,
        input_path=str(file_path),
        output_path=str(output_path),
        params={},
        priority=priority
    )
    
    return {
        "task_id": task_id,
        "message": f"Task {task_id} created successfully",
        "input_file": str(file_path),
        "output_file": str(output_path),
        "status_url": f"/api/tasks/{task_id}",
        "download_url": f"/api/download/{task_id}"
    }


@app.get("/api/download/{task_id}")
async def download_converted_file(task_id: int):
    """下载转换后的文件
    
    根据任务ID下载转换后的文件
    """
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not available")
    
    # 获取任务状态
    task_status = task_processor.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task_status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task {task_id} is not completed yet. Current status: {task_status['status']}"
        )
    
    # 检查输出文件是否存在
    output_path = task_status["output_path"]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail=f"Output file not found")
    
    # 确定文件类型
    file_extension = os.path.splitext(output_path)[1].lower()
    media_type = "application/pdf" if file_extension == ".pdf" else "text/markdown"
    
    # 返回文件
    return FileResponse(
        path=output_path,
        media_type=media_type,
        filename=os.path.basename(output_path)
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )