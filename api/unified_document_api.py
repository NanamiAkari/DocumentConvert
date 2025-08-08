#!/usr/bin/env python3
"""
统一文档转换API
复刻MediaConvert的统一任务创建接口，支持多种输入方式和任务类型
"""

from typing import Optional, Union
from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from database.models import TaskCreateRequest, TaskResponse, DocumentTask, QueryTasksFilter, TaskStatistics
from processors.enhanced_task_processor import EnhancedTaskProcessor
from utils.logging_utils import configure_logging

router = APIRouter()
logger = configure_logging(name=__name__)

# 全局任务处理器实例
task_processor: Optional[EnhancedTaskProcessor] = None


async def get_task_processor() -> EnhancedTaskProcessor:
    """获取任务处理器实例"""
    global task_processor
    if task_processor is None:
        raise HTTPException(status_code=503, detail="Task processor not initialized")
    return task_processor


def initialize_task_processor(database_type: str = "sqlite", 
                            database_url: str = "sqlite:///./document_tasks.db"):
    """初始化任务处理器"""
    global task_processor
    task_processor = EnhancedTaskProcessor(
        database_type=database_type,
        database_url=database_url
    )


@router.get("/health", summary="健康检查", description="检查文档转换API服务状态")
async def health_check():
    """
    健康检查端点
    
    Returns:
        dict: 服务状态信息
    """
    try:
        processor = await get_task_processor()
        stats = processor.get_stats()
        
        return {
            "status": "healthy",
            "message": "Document Conversion API is running",
            "processor_running": stats["is_running"],
            "total_tasks": stats["total_tasks"],
            "active_tasks": stats["active_tasks"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Service error: {str(e)}"
        }


@router.post(
    "/tasks/create",
    response_model=TaskResponse,
    summary="统一文档转换任务创建接口",
    description="支持多种任务类型和输入方式的统一创建接口，复刻MediaConvert的设计"
)
async def create_document_task(
    request: Request,
    
    # === 文件输入方式（三选一） ===
    bucket_name: Optional[str] = Form(None, description="S3存储桶名称"),
    file_path: Optional[str] = Form(None, description="文件在bucket中的路径"),
    file_upload: Optional[UploadFile] = File(None, description="本地文件上传"),
    file_url: Optional[str] = Form(None, description="文件HTTP URL"),
    input_path: Optional[str] = Form(None, description="本地文件路径"),
    
    # === 任务基本参数 ===
    task_type: str = Form(..., description="任务类型：office_to_pdf, pdf_to_markdown, office_to_markdown"),
    priority: str = Form("normal", description="任务优先级：low, normal, high"),
    callback_url: Optional[str] = Form(None, description="任务完成回调URL"),
    platform: Optional[str] = Form("gaojiaqi", description="平台标识，用于分类管理"),
    
    # === 输出配置 ===
    output_path: Optional[str] = Form(None, description="输出文件路径"),
    
    # === 转换参数 ===
    params: Optional[str] = Form(None, description="转换参数JSON字符串"),
    
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
) -> TaskResponse:
    """
    # 统一文档转换任务创建接口
    
    ## 功能说明
    
    这是一个统一的文档转换任务创建接口，支持多种任务类型和输入方式，复刻MediaConvert的设计。
    
    ## 支持的任务类型

    - **office_to_pdf**: Office文档转PDF
    - **pdf_to_markdown**: PDF转Markdown
    - **office_to_markdown**: Office文档直接转Markdown
    - **image_to_markdown**: 图片转Markdown（OCR识别）
    - **batch_office_to_pdf**: 批量Office转PDF
    - **batch_pdf_to_markdown**: 批量PDF转Markdown
    - **batch_office_to_markdown**: 批量Office转Markdown
    - **batch_image_to_markdown**: 批量图片转Markdown

    ## 任务重试功能

    ### 单个任务重试
    ```bash
    curl -X POST "http://localhost:8000/api/tasks/{task_id}/retry"
    ```

    ### 批量重试失败任务
    ```bash
    curl -X POST "http://localhost:8000/api/tasks/retry-failed"
    ```

    重试功能会：
    - 重置任务状态为pending
    - 清除错误信息
    - 重新放入处理队列
    - 重置重试计数器
    
    ## 输入方式
    
    支持三种输入方式（三选一）：
    
    1. **S3存储**: 提供 `bucket_name` 和 `file_path`
    2. **HTTP URL**: 提供 `file_url`
    3. **本地文件**: 提供 `input_path` 或上传 `file_upload`
    
    ## 输出配置
    
    - 转换结果自动上传到 `ai-file` 存储桶
    - 支持自定义输出路径
    - 自动生成访问URL
    
    ## 示例
    
    ### S3输入示例
    ```bash
    curl -X POST "http://localhost:8000/api/tasks/create" \
         -F "task_type=pdf_to_markdown" \
         -F "bucket_name=ai-file" \
         -F "file_path=2024本科生学生手册.pdf" \
         -F "platform=gaojiaqi" \
         -F "priority=normal"
    ```
    
    ### 本地文件上传示例
    ```bash
    curl -X POST "http://localhost:8000/api/tasks/create" \
         -F "task_type=office_to_pdf" \
         -F "file_upload=@document.docx" \
         -F "platform=gaojiaqi"
    ```
    """
    try:
        # 验证输入方式
        input_count = sum([
            bool(bucket_name and file_path),
            bool(file_url),
            bool(input_path),
            bool(file_upload)
        ])
        
        if input_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Must provide one input method: (bucket_name + file_path), file_url, input_path, or file_upload"
            )
        
        if input_count > 1:
            raise HTTPException(
                status_code=400,
                detail="Only one input method allowed"
            )
        
        # 处理文件上传
        if file_upload:
            # TODO: 实现文件上传逻辑
            raise HTTPException(status_code=501, detail="File upload not implemented yet")
        
        # 解析参数
        task_params = {}
        if params:
            import json
            try:
                task_params = json.loads(params)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid params JSON")
        
        # 验证优先级
        if priority not in ["low", "normal", "high"]:
            raise HTTPException(status_code=400, detail="Invalid priority. Must be: low, normal, high")
        
        # 应用MediaConvert的中文文件名处理方案
        if file_path:
            from utils.encoding_utils import EncodingUtils
            original_file_path = file_path
            file_path = EncodingUtils.fix_file_path_encoding(file_path)
            if file_path != original_file_path:
                logger.info(f"Fixed file_path encoding: {original_file_path} -> {file_path}")

        # 创建任务请求
        task_request = TaskCreateRequest(
            task_type=task_type,
            priority=priority,
            bucket_name=bucket_name,
            file_path=file_path,
            file_url=file_url,
            input_path=input_path,
            output_path=output_path,
            params=task_params,
            callback_url=callback_url,
            platform=platform
        )
        
        # 创建任务
        task_id = await processor.create_task(task_request)
        
        logger.info(f"Created document conversion task {task_id} for platform {platform}")
        
        return TaskResponse(
            task_id=task_id,
            message=f"Document conversion task {task_id} created successfully",
            status="pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create document task: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/tasks/{task_id}/task-type", summary="修改任务类型")
async def update_task_type(
    task_id: int,
    new_task_type: str = Form(..., description="新的任务类型"),
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
):
    """修改任务的类型，适用于类型不匹配的失败任务"""
    try:
        # 验证任务类型
        valid_types = [
            "office_to_pdf", "pdf_to_markdown", "office_to_markdown", "image_to_markdown",
            "batch_office_to_pdf", "batch_pdf_to_markdown", "batch_office_to_markdown", "batch_image_to_markdown"
        ]

        if new_task_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task type. Supported types: {', '.join(valid_types)}"
            )

        # 获取任务
        task = await processor.db_manager.get_task(str(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 只允许修改失败的任务
        if task.status not in ["failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Can only modify failed tasks. Current status: {task.status}"
            )

        # 更新任务类型
        success = await processor.db_manager.update_task(
            str(task_id),
            task_type=new_task_type
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update task type")

        logger.info(f"Task {task_id} type updated from {task.task_type} to {new_task_type}")

        return {
            "message": f"Task {task_id} type updated successfully",
            "task_id": task_id,
            "old_task_type": task.task_type,
            "new_task_type": new_task_type,
            "status": "ready_for_retry"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task type for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks/{task_id}", summary="获取任务详情")
async def get_task(
    task_id: str,
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
):
    """获取指定任务的详细信息"""
    try:
        task = await processor.db_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tasks", summary="查询任务列表")
async def query_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
):
    """查询任务列表"""
    try:
        filter_params = QueryTasksFilter(
            status=status,
            priority=priority,
            task_type=task_type,
            platform=platform,
            limit=limit,
            offset=offset
        )
        
        tasks = await processor.db_manager.query_tasks(filter_params)
        
        return {
            "tasks": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to query tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/statistics", summary="获取任务统计")
async def get_statistics(
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
):
    """获取任务统计信息"""
    try:
        # 获取数据库统计
        db_stats = await processor.db_manager.get_task_statistics()
        
        # 获取处理器统计
        processor_stats = processor.get_stats()
        
        return {
            "database_statistics": db_stats.dict(),
            "processor_statistics": processor_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tasks/{task_id}/retry", summary="重试任务")
async def retry_task(
    task_id: str,
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
):
    """手动重试失败的任务"""
    try:
        task = await processor.db_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status not in ["failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Only failed or cancelled tasks can be retried")
        
        # 重置任务状态
        await processor.db_manager.update_task(
            task_id,
            status="pending",
            retry_count=0,
            error_message=None
        )
        
        # 重新放入队列
        await processor.fetch_queue.put(task_id)
        
        logger.info(f"Task {task_id} queued for retry")
        
        return {"message": f"Task {task_id} queued for retry"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tasks/retry-failed", summary="批量重试失败的任务")
async def retry_failed_tasks(
    processor: EnhancedTaskProcessor = Depends(get_task_processor)
):
    """批量重试所有失败的任务"""
    try:
        # 获取所有失败的任务
        failed_tasks = await processor.db_manager.get_tasks_by_status("failed")

        if not failed_tasks:
            return {"message": "No failed tasks found", "retried_count": 0}

        retried_tasks = []

        for task in failed_tasks:
            try:
                # 重置任务状态
                await processor.db_manager.update_task(
                    task.id,
                    status="pending",
                    retry_count=0,
                    error_message=None
                )

                # 重新放入队列
                await processor.fetch_queue.put(task.id)
                retried_tasks.append(task.id)

                logger.info(f"Task {task.id} queued for retry")

            except Exception as e:
                logger.error(f"Failed to retry task {task.id}: {e}")
                continue

        return {
            "message": f"Successfully queued {len(retried_tasks)} failed tasks for retry",
            "retried_count": len(retried_tasks),
            "retried_task_ids": retried_tasks,
            "total_failed_tasks": len(failed_tasks)
        }

    except Exception as e:
        logger.error(f"Failed to retry failed tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
