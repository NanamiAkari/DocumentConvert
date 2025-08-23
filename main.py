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
    """根路径处理 - 返回HTML欢迎页面"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文档转换服务</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }
            .service-info {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin: 30px 0;
            }
            .feature {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .links {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 30px;
                flex-wrap: wrap;
            }
            .link {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 25px;
                transition: all 0.3s ease;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            .link:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            .status {
                text-align: center;
                margin-top: 20px;
                font-size: 1.1em;
            }
            .status.online {
                color: #4ade80;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 文档转换服务</h1>
            
            <div class="service-info">
                <h2>📋 服务信息</h2>
                <p><strong>版本:</strong> 1.0.0</p>
                <p><strong>描述:</strong> 企业级文档转换调度系统</p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>📄 Office转PDF</h3>
                    <p>支持Word、Excel、PowerPoint转PDF</p>
                </div>
                <div class="feature">
                    <h3>📝 PDF转Markdown</h3>
                    <p>智能提取PDF内容转换为Markdown</p>
                </div>
                <div class="feature">
                    <h3>⚡ 直接转换</h3>
                    <p>Office文档直接转Markdown</p>
                </div>
                <div class="feature">
                    <h3>📦 批量处理</h3>
                    <p>支持大批量文档并行处理</p>
                </div>
                <div class="feature">
                    <h3>☁️ 云存储</h3>
                    <p>S3云存储集成，安全可靠</p>
                </div>
                <div class="feature">
                    <h3>🎯 智能调度</h3>
                    <p>优先级队列，智能任务调度</p>
                </div>
            </div>
            
            <div class="links">
                <a href="/docs" class="link">📚 API文档</a>
                <a href="/api/health" class="link">💚 健康检查</a>
                <a href="/redoc" class="link">📖 ReDoc文档</a>
            </div>
            
            <div class="status online">
                ✅ 服务运行正常
            </div>
        </div>
        
        <script>
             // 检查服务状态
             async function checkServiceStatus() {
                 try {
                     const response = await fetch('/api/health', {
                         method: 'GET',
                         headers: {
                             'Accept': 'application/json',
                             'Content-Type': 'application/json'
                         },
                         cache: 'no-cache'
                     });
                     
                     if (response.ok) {
                         const data = await response.json();
                         const statusEl = document.querySelector('.status');
                         if (data.status === 'healthy') {
                             statusEl.innerHTML = '✅ 服务运行正常<br><small>任务处理器已启动</small>';
                             statusEl.className = 'status online';
                         } else {
                             statusEl.innerHTML = '⚠️ 服务部分异常<br><small>请检查服务状态</small>';
                             statusEl.className = 'status warning';
                         }
                     } else {
                         throw new Error(`HTTP ${response.status}`);
                     }
                 } catch (error) {
                     console.log('健康检查请求失败:', error.message);
                     const statusEl = document.querySelector('.status');
                     statusEl.innerHTML = '✅ 页面加载正常<br><small>服务运行中</small>';
                     statusEl.className = 'status online';
                 }
             }
             
             // 页面加载完成后检查状态
             document.addEventListener('DOMContentLoaded', checkServiceStatus);
         </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


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
