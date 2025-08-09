# Document Conversion Service

基于MinerU的智能文档转换服务，支持PDF、Office文档的高质量转换，具备完整的S3集成和异步处理能力。

## 🚀 功能特性

- **🔄 PDF转Markdown**: 使用MinerU 2.0进行高质量PDF解析，支持表格、图片、公式识别
- **📄 Office转PDF**: 支持Word、Excel、PowerPoint转PDF，保持格式完整性
- **⚡ 批量处理**: 支持多文件批量转换，异步队列处理
- **☁️ S3集成**: 自动从S3/MinIO下载和上传文件，支持多bucket
- **📊 进度跟踪**: 实时任务状态和进度监控，支持重试机制
- **🔧 灵活配置**: 支持多种数据库、存储后端和部署方式

## 🛠 技术栈

- **后端**: FastAPI + Python 3.9
- **PDF处理**: MinerU 2.0 (支持GPU加速)
- **Office处理**: LibreOffice
- **存储**: S3/MinIO
- **数据库**: SQLite/PostgreSQL
- **容器**: Docker

## 📦 Docker部署 (推荐)

### 快速启动

```bash
# 拉取镜像
docker pull docker.cnb.cool/l8ai/document/documentconvert:latest

# 创建数据目录
mkdir -p ./data/{database,logs,workspace}

# 运行容器
docker run -d \
  --name document-converter \
  -p 33081:8000 \
  --gpus all \
  -v /raid5/data/document-convert/database:/app/database \
  -v /raid5/data/document-convert/logs:/app/log_files \
  -v /raid5/data/document-convert/workspace:/app/task_workspace \
  -e S3_ENDPOINT=http://your-minio-server:9000 \
  -e S3_ACCESS_KEY=your-access-key \
  -e S3_SECRET_KEY=your-secret-key \
  -e S3_REGION=us-east-1 \
  -e DATABASE_TYPE=sqlite \
  -e LOG_LEVEL=INFO \
  -e MAX_CONCURRENT_TASKS=3 \
  docker.cnb.cool/l8ai/document/documentconvert:latest
```

### 使用docker-compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'
services:
  document-converter:
    image: docker.cnb.cool/l8ai/document/documentconvert:latest
    container_name: document-converter
    ports:
      - "8000:8000"
    volumes:
      - ./data/database:/app/database
      - ./data/logs:/app/log_files
      - ./data/workspace:/app/task_workspace
    environment:
      - S3_ENDPOINT=http://your-minio-server:9000
      - S3_ACCESS_KEY=your-access-key
      - S3_SECRET_KEY=your-secret-key
      - S3_REGION=us-east-1
      - DATABASE_TYPE=sqlite
      - LOG_LEVEL=INFO
      - MAX_CONCURRENT_TASKS=3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

启动服务：
```bash
docker-compose up -d
```

## 🔧 环境配置

### 必需的环境变量

| 变量名 | 描述 | 默认值 | 示例 |
|--------|------|--------|------|
| `S3_ENDPOINT` | S3/MinIO服务地址 | - | `http://minio:9000` |
| `S3_ACCESS_KEY` | S3访问密钥 | - | `minioadmin` |
| `S3_SECRET_KEY` | S3密钥 | - | `minioadmin` |
| `S3_REGION` | S3区域 | `us-east-1` | `us-east-1` |

### 可选的环境变量

| 变量名 | 描述 | 默认值 | 示例 |
|--------|------|--------|------|
| `DATABASE_TYPE` | 数据库类型 | `sqlite` | `sqlite`/`postgresql` |
| `DATABASE_URL` | 数据库连接URL | `sqlite:///./database/document_conversion.db` | - |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`/`INFO`/`WARNING` |
| `MAX_CONCURRENT_TASKS` | 最大并发任务数 | `3` | `1-10` |

## 📚 API文档

服务启动后，访问 `http://localhost:8000/docs` 查看完整的API文档。

### 核心API接口

#### 1. 创建转换任务

**PDF转Markdown**
```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=ai-file" \
  -F "file_path=test/document.pdf" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**Office转PDF**
```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "bucket_name=documents" \
  -F "file_path=reports/document.docx" \
  -F "platform=your-platform" \
  -F "priority=normal"
```

**响应示例**:
```json
{
  "task_id": 123,
  "message": "Document conversion task 123 created successfully",
  "status": "pending"
}
```

#### 2. 查询任务状态

```bash
curl "http://localhost:8000/api/tasks/123"
```

**响应示例**:
```json
{
  "id": 123,
  "task_type": "pdf_to_markdown",
  "status": "completed",
  "priority": "high",
  "input_path": "/app/task_workspace/task_123/input/document.pdf",
  "output_path": "/app/task_workspace/task_123/output/document.md",
  "output_url": "s3://ai-file/test/document/markdown/document.md",
  "s3_urls": [
    "s3://ai-file/test/document/markdown/document.md",
    "s3://ai-file/test/document/markdown/document.json",
    "s3://ai-file/test/document/markdown/images/image1.jpg"
  ],
  "file_size_bytes": 1048576,
  "created_at": "2025-08-09T10:00:00",
  "completed_at": "2025-08-09T10:02:30",
  "task_processing_time": 150.5,
  "result": {
    "success": true,
    "conversion_type": "pdf_to_markdown",
    "upload_result": {
      "success": true,
      "total_files": 5,
      "total_size": 2097152
    }
  }
}
```

#### 3. 任务列表查询

```bash
# 查询所有任务
curl "http://localhost:8000/api/tasks"

# 按状态过滤
curl "http://localhost:8000/api/tasks?status=completed&limit=10"
```

#### 4. 重试失败任务

```bash
curl -X POST "http://localhost:8000/api/tasks/123/retry"
```

#### 5. 修改任务类型

```bash
curl -X PUT "http://localhost:8000/api/tasks/123/task-type" \
  -H "Content-Type: application/json" \
  -d '{"new_task_type": "pdf_to_markdown"}'
```

### 支持的任务类型

| 任务类型 | 描述 | 输入格式 | 输出格式 |
|----------|------|----------|----------|
| `pdf_to_markdown` | PDF转Markdown | `.pdf` | `.md` + `.json` + 图片 |
| `office_to_pdf` | Office转PDF | `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx` | `.pdf` |
| `office_to_markdown` | Office转Markdown | Office文档 | `.md` + 图片 |

### 优先级设置

| 优先级 | 描述 | 处理顺序 |
|--------|------|----------|
| `high` | 高优先级 | 优先处理 |
| `normal` | 普通优先级 | 正常处理 |
| `low` | 低优先级 | 最后处理 |

## 📁 S3路径规则

系统遵循以下S3路径规则：

### 输入文件路径
```
s3://{bucket_name}/{file_path}
```

### 输出文件路径
```
s3://ai-file/{original_bucket}/{file_name_without_ext}/{conversion_type}/{output_files}
```

### 示例
```
输入: s3://documents/reports/annual_report.pdf
输出: s3://ai-file/documents/annual_report/markdown/
      ├── annual_report.md
      ├── annual_report.json
      └── images/
          ├── chart1.jpg
          └── table1.jpg
```

## 🔍 监控和日志

### 日志文件位置
- **应用日志**: `/app/log_files/app.log`
- **任务日志**: `/app/log_files/task_{task_id}.log`

### 健康检查
```bash
curl "http://localhost:8000/health"
```

### 服务状态
```bash
curl "http://localhost:8000/api/status"
```

## � 本地开发

### 环境要求
- Python 3.9+
- CUDA 11.8+ (GPU加速)
- LibreOffice
- Git

### 安装步骤

1. **克隆仓库**
```bash
git clone https://cnb.cool/l8ai/document/DocumentConvert.git
cd DocumentConvert
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，配置S3等参数
```

5. **启动服务**
```bash
python main.py
```

## 🔧 故障排除

### 常见问题

1. **GPU内存不足**
   - 减少 `MAX_CONCURRENT_TASKS` 值
   - 使用 `nvidia-smi` 监控GPU使用情况

2. **S3连接失败**
   - 检查 `S3_ENDPOINT` 是否正确
   - 验证 `S3_ACCESS_KEY` 和 `S3_SECRET_KEY`

3. **LibreOffice转换失败**
   - 确保LibreOffice已正确安装
   - 检查文件格式是否支持

4. **任务处理缓慢**
   - 增加 `MAX_CONCURRENT_TASKS` 值
   - 检查GPU资源使用情况

### 日志分析
```bash
# 查看应用日志
docker logs document-converter

# 查看特定任务日志
docker exec document-converter cat /app/log_files/task_123.log
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请联系技术支持或提交Issue。