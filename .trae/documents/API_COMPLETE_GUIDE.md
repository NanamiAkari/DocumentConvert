# 文档转换服务API完整指南

本文档提供文档转换服务的完整使用指南，包括服务启动、API使用示例、详细的curl命令、响应格式和实际使用场景。

## 🌐 API基础信息

- **基础URL**: `http://localhost:8000` (本地部署) 或 `http://your-server:33081` (生产环境)
- **API版本**: v2.0
- **文档地址**: `http://localhost:8000/docs` (Swagger UI)
- **内容类型**: `application/json` 或 `multipart/form-data`

## 🚀 服务启动完整流程

### 1. 启动MinIO服务
```bash
docker compose up -d minio
```
**效果**：启动MinIO服务作为S3存储后端，提供文件存储和管理功能。服务将在端口9000（API）和9001（控制台）上运行。

### 2. 创建数据目录
```bash
mkdir -p ./data/{database,logs,workspace,temp,minio}
```
**效果**：创建项目运行所需的数据目录结构，包括数据库文件、日志文件、工作空间、临时文件和MinIO数据存储目录。

### 3. 创建存储桶
```bash
docker exec minio mc mb minio/ai-file
```
**效果**：在MinIO中创建名为"ai-file"的存储桶，用于存放转换后的文档文件。

### 4. 安装Python依赖
```bash
pip install -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt
```
**效果**：使用腾讯云镜像源安装项目所需的Python依赖包，包括FastAPI、aiosqlite、sqlalchemy等核心组件。

### 5. 启动文档转换服务
```bash
python main.py
```
**效果**：启动文档转换服务，服务将在http://localhost:8000上运行，提供REST API接口用于文档转换任务的创建和管理。

### 6. 验证服务状态
```bash
curl -f http://localhost:8000/health
```
**效果**：检查服务健康状态，确认所有组件正常运行，返回服务状态信息。

## 🔍 服务健康检查

检查服务是否正常运行，获取系统状态信息。

```bash
curl -s http://localhost:8000/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "message": "Document Conversion Service is running",
  "timestamp": "2025-08-09T12:00:00Z",
  "processor_status": {
    "running": true,
    "total_tasks": 25,
    "active_tasks": 0,
    "completed_tasks": 23,
    "failed_tasks": 2
  },
  "queue_status": {
    "fetch_queue": 25,
    "task_processing_queue": 0,
    "high_priority_queue": 0,
    "normal_priority_queue": 0,
    "low_priority_queue": 0,
    "update_queue": 0,
    "cleanup_queue": 0,
    "callback_queue": 0
  },
  "workspace_status": {
    "base_workspace_dir": "/app/task_workspace",
    "temp_files_dir": "/app/temp_files",
    "active_task_workspaces": 25,
    "temp_files_count": 0,
    "total_workspace_size": 64200518,
    "temp_files_size": 0
  }
}
```

**状态说明**:
- `status`: `healthy` 表示服务正常，`unhealthy` 表示服务异常
- `processor_status`: 任务处理器状态和统计信息
- `queue_status`: 各个队列的任务数量
- `workspace_status`: 工作空间使用情况

## 📄 任务创建API

### 2.1 PDF转Markdown任务

将PDF文件转换为Markdown格式，同时提取图片和结构化数据。

```bash
curl -X POST "http://localhost:33081/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=gaojiaqi" \
  -F "file_path=Gemini for Google Workspace 提示指南 101（Gemini 工作区提示指南 101）.pdf" \
  -F "priority=high"
```

**参数说明**:
- `task_type`: 固定值 `pdf_to_markdown`
- `bucket_name`: S3存储桶名称 (例如: `documents`, `ai-file`, `reports`)
- `file_path`: 文件在S3中的路径 (例如: `reports/annual_report.pdf`)
- `platform`: 平台标识，用于任务分类 (例如: `web-app`, `api-client`)
- `priority`: 任务优先级 (`high`, `normal`, `low`)

**响应示例**:
```json
{
  "task_id": 26,
  "message": "Document conversion task 26 created successfully",
  "status": "pending"
}
```

**输出文件**:
- `annual_report.md`: 主要的Markdown文件
- `annual_report.json`: 文档结构化数据
- `images/`: 提取的图片文件夹

### 2.2 Office转PDF任务

将Office文档(Word/Excel/PowerPoint)转换为PDF格式。

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "bucket_name=documents" \
  -F "file_path=presentations/quarterly_review.pptx" \
  -F "platform=your-platform" \
  -F "priority=normal"
```

**支持的文件格式**:
- Word: `.doc`, `.docx`
- Excel: `.xls`, `.xlsx`
- PowerPoint: `.ppt`, `.pptx`

**响应示例**:
```json
{
  "task_id": 27,
  "message": "Document conversion task 27 created successfully",
  "status": "pending"
}
```

### 2.3 Office转Markdown任务 (两步转换)

将Office文档先转换为PDF，再转换为Markdown，适用于复杂格式的文档。

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_markdown" \
  -F "bucket_name=documents" \
  -F "file_path=reports/financial_report.xlsx" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**处理流程**:
1. Office文档 → PDF (使用LibreOffice)
2. PDF → Markdown (使用MinerU)

**输出文件**:
- `financial_report.md`: Markdown文件
- `financial_report.json`: 结构化数据
- `images/`: 图片和图表

## 🔍 任务查询和状态监控API

### 3.1 查询特定任务详情

根据任务ID获取任务的完整状态信息，包括输入输出路径、处理时间、S3 URLs等。

```bash
curl -s "http://localhost:8000/api/tasks/26"
```

**响应示例 - 已完成的PDF转Markdown任务**:
```json
{
  "id": 26,
  "task_type": "pdf_to_markdown",
  "status": "completed",
  "priority": "high",
  "bucket_name": "documents",
  "file_path": "reports/annual_report.pdf",
  "platform": "your-platform",
  "input_path": "/app/task_workspace/task_26/input/annual_report.pdf",
  "output_path": "/app/task_workspace/task_26/output/annual_report.md",
  "output_url": "s3://ai-file/documents/annual_report/markdown/annual_report.md",
  "s3_urls": [
    "s3://ai-file/documents/annual_report/markdown/annual_report.md",
    "s3://ai-file/documents/annual_report/markdown/annual_report.json",
    "s3://ai-file/documents/annual_report/markdown/images/chart1.jpg",
    "s3://ai-file/documents/annual_report/markdown/images/table1.jpg",
    "s3://ai-file/documents/annual_report/markdown/images/diagram1.jpg"
  ],
  "created_at": "2025-08-09T19:38:35Z",
  "updated_at": "2025-08-09T19:41:02Z",
  "processing_time": 147.5,
  "file_size": 1048576,
  "error_message": null
}
```

### 3.2 查询所有任务列表

获取所有任务的列表，包括任务ID、状态、类型、创建时间等信息，支持分页和过滤功能。

```bash
curl "http://localhost:8000/api/tasks"
```

### 3.3 按状态过滤任务

查询指定状态的任务，可选状态包括：pending（等待中）、processing（处理中）、completed（已完成）、failed（失败）。

```bash
curl "http://localhost:8000/api/tasks?status=completed&limit=10"
```

### 3.4 按任务类型过滤

查询指定类型的任务，可按转换类型进行筛选，便于分类管理。

```bash
curl "http://localhost:8000/api/tasks?task_type=pdf_to_markdown&limit=5"
```

### 3.5 获取任务统计

获取系统任务统计信息，包括总任务数、各状态任务数量、处理器运行状态等系统概览数据。

```bash
curl "http://localhost:8000/api/statistics"
```

## 📊 S3路径规则说明

### 输入文件路径
输入文件支持两种路径格式：
1. **S3路径**: `s3://bucket-name/path/to/file.pdf`
2. **相对路径**: `path/to/file.pdf` (需要指定bucket_name参数)

### 输出文件路径规则
输出文件统一存储到ai-file存储桶，路径格式为：
```
s3://ai-file/{original_bucket}/{file_name_without_ext}/{conversion_type}/{output_files}
```

**路径示例**:
- 输入: `s3://documents/reports/annual_report.pdf`
- 输出: `s3://ai-file/documents/annual_report/pdf_to_markdown/annual_report.md`

**特殊情况处理**:
- 如果输入文件已在ai-file存储桶中，避免路径重复
- 支持中文文件名和路径
- 自动处理文件名中的特殊字符

## 🔧 支持的转换类型

- `pdf_to_markdown`：PDF转Markdown
- `office_to_pdf`：Office文档转PDF
- `office_to_markdown`：Office文档转Markdown（两步转换）

## 📋 任务状态说明

- **pending**: 任务已创建，等待处理
- **processing**: 任务正在处理中
- **completed**: 任务处理完成
- **failed**: 任务处理失败

## 🔍 过滤参数说明

- **status**: 按状态过滤 (pending, processing, completed, failed)
- **priority**: 按优先级过滤 (high, normal, low)
- **task_type**: 按任务类型过滤 (pdf_to_markdown, office_to_pdf, office_to_markdown)
- **platform**: 按平台过滤
- **limit**: 返回结果数量限制 (默认20)
- **offset**: 分页偏移量 (默认0)

## 🌐 服务访问地址

- **API服务**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health
- **MinIO控制台**：http://localhost:9001（用户名/密码：minioadmin/minioadmin）

## 🧪 功能测试示例

### 测试PDF转Markdown
```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "input_path=/workspace/test/人人皆可vibe编程.pdf" \
  -F "output_path=/workspace/output/人人皆可vibe编程.md" \
  -F "platform=test" \
  -F "priority=high"
```
**效果**：将PDF文件转换为Markdown格式，自动提取文本、图片和结构化内容，生成高质量的Markdown文件和相关资源。

### 测试Office转PDF
```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "input_path=/workspace/test/智涌君.docx" \
  -F "output_path=/workspace/output/智涌君.pdf" \
  -F "platform=test" \
  -F "priority=high"
```
**效果**：将Word文档转换为PDF格式，保持原有格式和布局完整性。

### 测试Office转Markdown
```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_markdown" \
  -F "input_path=/workspace/test/AI通识课程建设方案.pptx" \
  -F "output_path=/workspace/output/AI通识课程建设方案.md" \
  -F "platform=test" \
  -F "priority=high"
```
**效果**：将PowerPoint演示文稿转换为Markdown格式，提取幻灯片内容和图片资源。

### 查看转换结果
```bash
ls -la /workspace/output/
```
**效果**：查看所有转换完成的文件，包括Markdown文件、PDF文件、JSON结构文件和提取的图片资源。

## ⚠️ 常见问题排查

### 端口冲突
如果遇到端口8000被占用的问题，可以使用以下命令清理：
```bash
lsof -ti:8000 | xargs kill -9
```

### 存储桶不存在
如果遇到"NoSuchBucket"错误，确保已创建ai-file存储桶：
```bash
docker exec minio mc mb minio/ai-file
```

### 依赖安装问题
如果依赖安装失败，确保使用国内镜像源：
```bash
pip install -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt
```

### GPU内存不足
如果遇到GPU内存不足错误，可以：
1. 减少并发任务数量
2. 使用CPU模式运行
3. 清理GPU缓存

### 文件权限问题
确保工作目录有正确的读写权限：
```bash
chmod -R 755 /app/task_workspace
chown -R $(whoami) /app/task_workspace
```

## 📝 注意事项

1. 确保Docker服务正常运行
2. 确保有足够的磁盘空间用于文件转换
3. 大文件转换可能需要较长时间，请耐心等待
4. 转换过程中请勿关闭服务
5. 建议定期清理output目录中的临时文件
6. 生产环境建议使用外部S3存储服务
7. 建议配置适当的日志轮转策略
8. 定期监控系统资源使用情况

---

服务现已完全就绪，支持多种文档格式的智能转换，具备完整的S3集成和异步处理能力。本指南涵盖了从服务启动到API使用的完整流程，为用户提供了详尽的操作参考。