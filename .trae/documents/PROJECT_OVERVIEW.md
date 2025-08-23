# 文档转换服务项目概览

本文档提供文档转换服务的完整项目概览，包括系统架构、核心组件、部署指南、环境配置和开发说明。

## 📋 项目简介

文档转换服务是一个基于FastAPI的高性能异步文档处理系统，支持PDF、Office文档等多种格式的智能转换。系统采用队列驱动的架构设计，具备高并发处理能力、智能优先级调度和完整的S3存储集成。

### 核心特性
- 🚀 **高性能异步处理**：基于asyncio的非阻塞任务处理
- 📊 **智能优先级调度**：支持高、中、低三级优先级队列
- 🔄 **多格式转换支持**：PDF↔Markdown、Office→PDF、Office→Markdown
- 💾 **完整S3集成**：支持MinIO和AWS S3存储
- 🔍 **实时监控**：提供详细的任务状态和系统健康检查
- 🛡️ **容错机制**：自动重试、错误恢复和资源清理

## 🏗️ 系统架构

### 整体架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   API Client    │    │  Mobile App     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     FastAPI Server       │
                    │   (Port: 8000/33081)     │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    Task Processor         │
                    │  (Async Queue System)     │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────┴────────┐    ┌──────────┴──────────┐    ┌────────┴────────┐
│   SQLite DB    │    │     MinIO S3        │    │  File System    │
│  (Task Queue)  │    │   (File Storage)    │    │  (Workspace)    │
└────────────────┘    └─────────────────────┘    └─────────────────┘
```

### 核心组件架构

#### 1. API层 (FastAPI)
- **路由管理**：任务创建、查询、状态监控
- **请求验证**：参数校验、文件类型检查
- **响应格式化**：统一的JSON响应格式
- **错误处理**：全局异常捕获和处理

#### 2. 任务处理层 (Task Processor)
- **队列管理器**：多优先级队列调度
- **任务执行器**：异步任务处理引擎
- **资源管理器**：工作空间和临时文件管理
- **状态跟踪器**：实时任务状态更新

#### 3. 存储层 (Storage Layer)
- **数据库**：SQLite任务队列和状态存储
- **文件存储**：MinIO S3兼容存储
- **工作空间**：本地临时文件处理区域

## 🔄 队列系统架构

### 队列层次结构
```
┌─────────────────────────────────────────────────────────────┐
│                    Task Queue System                        │
├─────────────────────────────────────────────────────────────┤
│  Fetch Queue (文件下载)                                      │
│  ├── High Priority Queue                                    │
│  ├── Normal Priority Queue                                  │
│  └── Low Priority Queue                                     │
├─────────────────────────────────────────────────────────────┤
│  Processing Queue (文档转换)                                 │
│  ├── High Priority Queue                                    │
│  ├── Normal Priority Queue                                  │
│  └── Low Priority Queue                                     │
├─────────────────────────────────────────────────────────────┤
│  Update Queue (状态更新)                                     │
├─────────────────────────────────────────────────────────────┤
│  Cleanup Queue (资源清理)                                    │
├─────────────────────────────────────────────────────────────┤
│  Callback Queue (回调通知)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 队列处理流程
1. **任务创建** → Fetch Queue (按优先级分配)
2. **文件下载** → Processing Queue (转换处理)
3. **文档转换** → Update Queue (状态更新)
4. **结果上传** → Cleanup Queue (资源清理)
5. **任务完成** → Callback Queue (通知回调)

## 🚀 部署指南

### 环境要求
- **操作系统**：Linux/macOS/Windows
- **Python版本**：3.8+
- **Docker版本**：20.10+
- **内存要求**：最小4GB，推荐8GB+
- **磁盘空间**：最小10GB，推荐50GB+

### 快速部署步骤

#### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd document-conversion-service

# 创建数据目录
mkdir -p ./data/{database,logs,workspace,temp,minio}

# 设置权限
chmod -R 755 ./data
```

#### 2. 启动MinIO存储服务
```bash
# 启动MinIO容器
docker compose up -d minio

# 等待服务启动
sleep 10

# 创建存储桶
docker exec minio mc mb minio/ai-file

# 验证存储桶创建
docker exec minio mc ls minio/
```

#### 3. 安装Python依赖
```bash
# 使用国内镜像源安装依赖
pip install -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt

# 验证关键依赖
python -c "import fastapi, aiosqlite, sqlalchemy; print('Dependencies OK')"
```

#### 4. 启动文档转换服务
```bash
# 启动主服务
python main.py

# 或使用uvicorn启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. 验证部署
```bash
# 健康检查
curl -f http://localhost:8000/health

# API文档访问
open http://localhost:8000/docs

# MinIO控制台访问
open http://localhost:9001
```

### 生产环境部署

#### Docker Compose部署
```yaml
version: '3.8'
services:
  document-service:
    build: .
    ports:
      - "33081:8000"
    environment:
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    volumes:
      - ./data:/app/data
    depends_on:
      - minio

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - ./data/minio:/data
    command: server /data --console-address ":9001"
```

#### Kubernetes部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-conversion-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-service
  template:
    metadata:
      labels:
        app: document-service
    spec:
      containers:
      - name: document-service
        image: document-conversion-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: MINIO_ENDPOINT
          value: "minio-service:9000"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## ⚙️ 环境配置

### 环境变量配置
```bash
# 服务配置
export HOST=0.0.0.0
export PORT=8000
export DEBUG=false

# MinIO S3配置
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
export MINIO_SECURE=false
export DEFAULT_BUCKET=ai-file

# 数据库配置
export DATABASE_URL=sqlite:///./data/database/tasks.db
export DATABASE_POOL_SIZE=20

# 任务处理配置
export MAX_CONCURRENT_TASKS=5
export TASK_TIMEOUT=3600
export RETRY_ATTEMPTS=3
export RETRY_DELAY=60

# 工作空间配置
export WORKSPACE_DIR=./data/workspace
export TEMP_DIR=./data/temp
export MAX_WORKSPACE_SIZE=10GB
export CLEANUP_INTERVAL=3600

# 日志配置
export LOG_LEVEL=INFO
export LOG_FILE=./data/logs/service.log
export LOG_ROTATION=daily
export LOG_RETENTION=30
```

### 配置文件示例 (config.yaml)
```yaml
server:
  host: 0.0.0.0
  port: 8000
  debug: false
  workers: 4

storage:
  minio:
    endpoint: localhost:9000
    access_key: minioadmin
    secret_key: minioadmin
    secure: false
    default_bucket: ai-file

database:
  url: sqlite:///./data/database/tasks.db
  pool_size: 20
  echo: false

processing:
  max_concurrent_tasks: 5
  task_timeout: 3600
  retry_attempts: 3
  retry_delay: 60
  queue_check_interval: 5

workspace:
  base_dir: ./data/workspace
  temp_dir: ./data/temp
  max_size: 10737418240  # 10GB
  cleanup_interval: 3600

logging:
  level: INFO
  file: ./data/logs/service.log
  rotation: daily
  retention: 30
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## 🔧 开发指南

### 项目结构
```
document-conversion-service/
├── main.py                 # 应用入口
├── app/
│   ├── __init__.py
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   ├── tasks.py       # 任务相关API
│   │   └── health.py      # 健康检查API
│   ├── core/              # 核心组件
│   │   ├── __init__.py
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   └── storage.py     # S3存储管理
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   └── task.py        # 任务模型
│   ├── services/          # 业务服务
│   │   ├── __init__.py
│   │   ├── task_processor.py  # 任务处理器
│   │   ├── queue_manager.py   # 队列管理器
│   │   └── converter.py       # 文档转换器
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── file_utils.py  # 文件操作工具
│       └── logger.py      # 日志工具
├── data/                  # 数据目录
│   ├── database/          # 数据库文件
│   ├── logs/              # 日志文件
│   ├── workspace/         # 工作空间
│   ├── temp/              # 临时文件
│   └── minio/             # MinIO数据
├── tests/                 # 测试文件
├── docs/                  # 文档目录
├── docker-compose.yml     # Docker编排文件
├── Dockerfile            # Docker镜像构建文件
├── requirements.txt      # Python依赖
└── README.md            # 项目说明
```

### 开发环境设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 安装pre-commit钩子
pre-commit install

# 运行测试
pytest tests/

# 代码格式化
black app/
flake8 app/

# 类型检查
mypy app/
```

### API开发规范
```python
# 路由定义示例
from fastapi import APIRouter, HTTPException, Depends
from app.models.task import TaskCreate, TaskResponse
from app.services.task_processor import TaskProcessor

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("/create", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    processor: TaskProcessor = Depends(get_task_processor)
):
    """创建新的文档转换任务"""
    try:
        task = await processor.create_task(task_data)
        return TaskResponse.from_orm(task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 📊 性能优化

### 系统性能指标
- **并发处理能力**：支持最多50个并发任务
- **文件处理速度**：PDF转换平均2-5秒/页
- **内存使用**：单任务平均占用200-500MB
- **存储效率**：支持文件压缩和增量备份

### 优化建议

#### 1. 硬件优化
- **CPU**：推荐8核心以上，支持多任务并行处理
- **内存**：推荐16GB以上，支持大文件处理
- **存储**：推荐SSD，提升文件I/O性能
- **网络**：推荐千兆网络，加速文件传输

#### 2. 软件优化
```python
# 异步处理优化
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.semaphore = asyncio.Semaphore(5)  # 限制并发数
    
    async def process_task(self, task):
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, self._sync_process, task
            )
```

#### 3. 缓存策略
```python
# Redis缓存配置
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key, expire_time, json.dumps(result)
            )
            return result
        return wrapper
    return decorator
```

## 🔍 监控和运维

### 系统监控
```python
# Prometheus指标收集
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
task_counter = Counter('tasks_total', 'Total tasks processed', ['status', 'type'])
processing_time = Histogram('task_processing_seconds', 'Task processing time')
active_tasks = Gauge('active_tasks', 'Number of active tasks')

# 使用示例
task_counter.labels(status='completed', type='pdf_to_markdown').inc()
with processing_time.time():
    await process_document()
active_tasks.set(len(active_task_list))
```

### 日志管理
```python
# 结构化日志配置
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# 使用示例
logger.info(
    "Task processing started",
    task_id=task.id,
    task_type=task.task_type,
    file_size=task.file_size
)
```

### 健康检查
```python
# 详细健康检查实现
from fastapi import APIRouter
from app.core.database import get_db_status
from app.core.storage import get_storage_status

@router.get("/health")
async def health_check():
    """系统健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": await get_db_status(),
            "storage": await get_storage_status(),
            "processor": await get_processor_status(),
            "queues": await get_queue_status()
        }
    }
    
    # 检查组件状态
    unhealthy_components = [
        name for name, status in health_status["components"].items()
        if status.get("status") != "healthy"
    ]
    
    if unhealthy_components:
        health_status["status"] = "unhealthy"
        health_status["unhealthy_components"] = unhealthy_components
    
    return health_status
```

## 🔒 安全配置

### API安全
```python
# JWT认证配置
from fastapi_users.authentication import JWTAuthentication

jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=3600,
    tokenUrl="auth/jwt/login",
)

# 权限控制
from fastapi import Depends
from app.auth import get_current_user, require_permissions

@router.post("/tasks/create")
async def create_task(
    task_data: TaskCreate,
    user = Depends(get_current_user),
    _: None = Depends(require_permissions(["task:create"]))
):
    """创建任务（需要认证和权限）"""
    pass
```

### 数据安全
```python
# 敏感数据加密
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# 使用示例
encryption = DataEncryption(ENCRYPTION_KEY)
encrypted_path = encryption.encrypt(file_path)
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. 服务启动失败
```bash
# 检查端口占用
lsof -ti:8000 | xargs kill -9

# 检查依赖安装
pip check

# 检查配置文件
python -c "from app.core.config import settings; print(settings)"
```

#### 2. 任务处理失败
```bash
# 查看任务日志
tail -f ./data/logs/service.log | grep "task_id:123"

# 检查工作空间权限
ls -la ./data/workspace/
chmod -R 755 ./data/workspace/

# 清理僵尸任务
curl -X POST "http://localhost:8000/api/tasks/cleanup"
```

#### 3. 存储连接问题
```bash
# 检查MinIO服务状态
docker ps | grep minio

# 测试S3连接
docker exec minio mc ls minio/

# 重新创建存储桶
docker exec minio mc rb minio/ai-file --force
docker exec minio mc mb minio/ai-file
```

#### 4. 内存不足问题
```bash
# 监控内存使用
free -h
ps aux --sort=-%mem | head -10

# 清理临时文件
find ./data/temp -type f -mtime +1 -delete

# 重启服务释放内存
sudo systemctl restart document-conversion-service
```

## 📈 扩展和集成

### 水平扩展
```yaml
# Kubernetes水平扩展配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: document-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: document-conversion-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 第三方集成
```python
# Webhook回调集成
import httpx

class WebhookNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient()
    
    async def notify_task_completion(self, task):
        payload = {
            "event": "task.completed",
            "task_id": task.id,
            "status": task.status,
            "output_url": task.output_url,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
```

---

## 📞 技术支持

如需技术支持或有任何问题，请通过以下方式联系：

- **文档更新**：请查看最新版本的技术文档
- **问题反馈**：请提供详细的错误日志和环境信息
- **功能建议**：欢迎提出改进建议和新功能需求

---

本项目概览文档涵盖了文档转换服务的完整技术架构、部署指南、开发规范和运维要求，为开发者和运维人员提供了全面的参考资料。