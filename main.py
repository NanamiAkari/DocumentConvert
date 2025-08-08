#!/usr/bin/env python3
"""
文档转换调度系统主应用
复刻MediaConvert的应用架构，支持企业级文档转换服务
"""

import asyncio
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.unified_document_api import router as document_router, initialize_task_processor
from processors.enhanced_task_processor import EnhancedTaskProcessor
from utils.logging_utils import setup_application_logging, configure_logging

# 设置应用日志
setup_application_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "/app/log_files")
)

logger = configure_logging(name=__name__)

# 全局任务处理器
task_processor: EnhancedTaskProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global task_processor
    
    # 启动时初始化
    logger.info("Starting Document Conversion Service...")
    
    try:
        # 初始化任务处理器
        database_type = os.getenv("DATABASE_TYPE", "sqlite")
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./document_tasks.db")
        
        logger.info(f"Initializing task processor - DB: {database_type}")
        
        # 初始化API中的任务处理器
        initialize_task_processor(database_type, database_url)
        
        # 获取任务处理器实例
        from api.unified_document_api import task_processor as api_processor
        task_processor = api_processor
        
        # 启动任务处理器
        await task_processor.start()
        
        logger.info("Document Conversion Service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    
    # 关闭时清理
    logger.info("Shutting down Document Conversion Service...")
    
    try:
        if task_processor:
            await task_processor.stop()
        logger.info("Document Conversion Service stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="文档转换调度系统",
    description="企业级文档转换服务，支持Office、PDF等多种格式转换",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(document_router, prefix="/api", tags=["文档转换"])


@app.get("/", summary="根路径", description="服务基本信息")
async def root():
    """根路径处理"""
    return {
        "service": "Document Conversion Service",
        "version": "1.0.0",
        "description": "企业级文档转换调度系统",
        "features": [
            "Office文档转PDF",
            "PDF转Markdown",
            "Office文档直接转Markdown",
            "批量文档处理",
            "S3云存储集成",
            "智能任务调度",
            "完整日志记录"
        ],
        "api_docs": "/docs",
        "health_check": "/api/health"
    }


@app.get("/health", summary="健康检查", description="服务健康状态检查")
async def health_check():
    """健康检查端点"""
    try:
        global task_processor
        
        if not task_processor:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Task processor not initialized"
                }
            )
        
        stats = task_processor.get_stats()
        
        return {
            "status": "healthy",
            "message": "Document Conversion Service is running",
            "timestamp": "2025-08-07T12:00:00Z",
            "processor_status": {
                "running": stats["is_running"],
                "total_tasks": stats["total_tasks"],
                "active_tasks": stats["active_tasks"],
                "completed_tasks": stats["completed_tasks"],
                "failed_tasks": stats["failed_tasks"]
            },
            "queue_status": stats["queue_sizes"],
            "workspace_status": stats["workspace_stats"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": f"Service error: {str(e)}"
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


def setup_signal_handlers():
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info(f"Starting server on {host}:{port} with {workers} workers")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        reload=False  # 生产环境关闭热重载
    )
