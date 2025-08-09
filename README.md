# 文档转换调度系统 (Document Conversion Service)

基于 FastAPI 和 MinerU 2.0 的智能文档转换调度系统，支持 Office 文档转 PDF、PDF 转 Markdown 的异步任务处理，并自动上传到S3存储。

## 🚀 快速启动

### Docker 部署（推荐）

```bash
# 拉取镜像
docker pull docker.cnb.cool/l8ai/document/fileconvert:latest

# 启动服务（带数据持久化）
docker run -d \
  --name fileconvert \
  --gpus all \
  -p 8000:8000 \
  -v /data/database:/data/database \
  -v /data/logs:/data/logs \
  -v /data/workspace:/data/workspace \
  -v /data/temp:/data/temp \
  docker.cnb.cool/l8ai/document/fileconvert:latest

# 健康检查
curl http://localhost:8000/health
```

### 数据持久化目录说明

| 目录 | 用途 | 说明 |
|------|------|------|
| `/data/database` | 数据库文件 | SQLite数据库文件存储 |
| `/data/logs` | 日志文件 | 应用日志和错误日志 |
| `/data/workspace` | 任务工作空间 | 任务处理临时文件 |
| `/data/temp` | 临时文件 | 文件上传和处理缓存 |

## 🌟 功能特性

- 🔄 **多格式转换**: 支持Office文档(Word/Excel/PowerPoint)转PDF，PDF转Markdown，图片转Markdown
- 🖼️ **图片OCR**: 集成MinerU强大OCR功能，支持PNG/JPG/JPEG图片文档识别
- 🤖 **AI驱动**: 集成MinerU 2.0 Python API，提供高质量PDF到Markdown转换
- 🚀 **GPU加速**: 支持CUDA GPU加速，显著提升转换速度和质量
- 📋 **任务调度**: 异步任务处理，支持优先级队列和并发控制
- 🔄 **智能重试**: 支持单个任务重试、批量重试失败任务、任务类型修改
- 🔍 **状态跟踪**: 实时任务状态查询和进度监控
- 🛠️ **错误处理**: 完善的错误处理、重试机制和GPU内存管理
- 📊 **RESTful API**: 标准的REST API接口，支持Swagger文档
- 🐳 **Docker支持**: 容器化部署，开箱即用
- 🌐 **中文优化**: 针对中文文档优化，支持复杂版面识别

## 🛠️ 技术栈配置

### 核心技术栈
- **Web框架**: FastAPI 0.104.1 + Uvicorn
- **AI引擎**: MinerU 2.1.9 (PDF转Markdown)
- **Office转PDF**: LibreOffice (headless模式)
- **任务调度**: 自研异步任务处理器，支持GPU内存管理
- **数据验证**: Pydantic 2.5.0
- **深度学习**: PyTorch + CUDA 11.8

### 依赖工具
- LibreOffice: `/usr/bin/libreoffice` - 用于Office文档转PDF
- MinerU 2.0+: Python API - 用于PDF转Markdown，支持GPU加速
- Python 3.10+
- NVIDIA GPU (推荐，显存 >= 8GB)

## 系统架构

### 业务流程
```
1. 创建任务 (API) → 2. 任务调度 (TaskProcessor) → 3. 任务执行 (DocumentService)
```

### 核心模块
- `api/main.py`: FastAPI应用入口，提供REST API接口
- `processors/task_processor.py`: 异步任务调度器，管理任务队列和并发执行
- `services/document_service.py`: 文档转换服务，集成LibreOffice和MinerU

### 任务类型
1. **office_to_pdf**: Office文档转PDF (使用LibreOffice)
2. **pdf_to_markdown**: PDF转Markdown (基础转换)
3. **office_to_markdown**: Office文档直接转Markdown (两步转换)
4. **image_to_markdown**: 图片转Markdown (OCR识别) ✨ **新增**
5. **batch_office_to_pdf**: 批量Office转PDF
6. **batch_pdf_to_markdown**: 批量PDF转Markdown
7. **batch_office_to_markdown**: 批量Office转Markdown (推荐)
8. **batch_image_to_markdown**: 批量图片转Markdown ✨ **新增**

## 🔄 任务重试功能 ✨ **新增**

### 重试API
- **单个任务重试**: `POST /api/tasks/{task_id}/retry`
- **批量重试失败任务**: `POST /api/tasks/retry-failed`
- **修改任务类型**: `PUT /api/tasks/{task_id}/task-type`

### 重试功能特性
- 🔄 自动重置任务状态为pending
- 🧹 清除错误信息和重试计数
- 📋 重新放入处理队列
- 🎯 支持类型不匹配任务的修复

## 🚀 快速开始

### 方式一：直接运行

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 启动服务
```bash
# 启动API服务器
python3 start.py

# 或直接运行API模块
python3 api/main.py
```

#### 3. 验证服务
```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

### 方式二：Docker部署（推荐）

#### 1. 构建镜像
```bash
docker build -t docker.cnb.cool/aiedulab/library/mineru/mineru-api:latest .
```

#### 2. 运行容器
```bash
docker run -d \
  --name mineru-api \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/test:/workspace/test \
  -v $(pwd)/output:/workspace/output \
  docker.cnb.cool/aiedulab/library/mineru/mineru-api:latest
```

#### 3. 验证部署
```bash
# 检查容器状态
docker ps

# 查看日志
docker logs mineru-api

# 测试API
curl http://localhost:8000/health
```

## 📋 API 使用指南

### 1. 创建Office转PDF任务

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "input_path=/path/to/document.docx" \
  -F "bucket_name=your-bucket" \
  -F "file_path=documents/document.docx" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**参数说明:**
- `task_type`: 固定值 `office_to_pdf`
- `input_path`: 本地文件路径
- `bucket_name`: S3存储桶名称（任意bucket名称）
- `file_path`: 文件在bucket中的路径
- `platform`: 平台标识（任意值）
- `priority`: 优先级 (`high`, `normal`, `low`)

### 2. 创建PDF转Markdown任务

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "input_path=/path/to/document.pdf" \
  -F "bucket_name=your-bucket" \
  -F "file_path=documents/document.pdf" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**参数说明:**
- `task_type`: 固定值 `pdf_to_markdown`
- 其他参数同上

### 3. 根据bucket+file_path查询任务处理结果

```bash
curl -X GET "http://localhost:8000/api/tasks/search?bucket_name=your-bucket&file_path=documents/document.pdf"
```

**响应示例:**
```json
{
  "tasks": [
    {
      "id": 1,
      "task_type": "pdf_to_markdown",
      "status": "completed",
      "bucket_name": "your-bucket",
      "file_path": "documents/document.pdf",
      "s3_urls": [
        "s3://ai-file/your-bucket/documents/document/markdown/document.md",
        "s3://ai-file/your-bucket/documents/document/markdown/document.json"
      ],
      "output_url": "s3://ai-file/your-bucket/documents/document/markdown/document.md",
      "created_at": "2025-08-09T12:00:00Z",
      "completed_at": "2025-08-09T12:05:00Z"
    }
  ]
}
```

### 4. 获取ai-file的S3路径格式

**路径规则:** `ai-file/{bucket_name}/{文件夹路径}/{文件名(无后缀)}/{类型}/{输出文件}`

**示例:**
- 输入文件: `documents/report.pdf`
- Bucket: `company-docs`
- 任务类型: `pdf_to_markdown`
- 输出路径: `s3://ai-file/company-docs/documents/report/markdown/report.md`

**路径组成:**
- `ai-file`: 固定的S3存储桶前缀
- `{bucket_name}`: 用户指定的bucket名称
- `{文件夹路径}`: 从file_path提取的目录路径
- `{文件名(无后缀)}`: 原始文件名去掉扩展名
- `{类型}`: 根据任务类型确定 (`pdf` 或 `markdown`)
- `{输出文件}`: 转换后的文件名

### 5. 查看任务状态

#### 查看特定任务详情
```bash
curl -X GET "http://localhost:8000/api/tasks/1"
```

**响应示例:**
```json
{
  "id": 1,
  "task_type": "pdf_to_markdown",
  "status": "completed",
  "progress": 100,
  "bucket_name": "your-bucket",
  "file_path": "documents/document.pdf",
  "platform": "your-platform",
  "priority": "high",
  "s3_urls": [
    "s3://ai-file/your-bucket/documents/document/markdown/document.md",
    "s3://ai-file/your-bucket/documents/document/markdown/document.json"
  ],
  "output_url": "s3://ai-file/your-bucket/documents/document/markdown/document.md",
  "task_processing_time": 45.67,
  "created_at": "2025-08-09T12:00:00Z",
  "started_at": "2025-08-09T12:01:00Z",
  "completed_at": "2025-08-09T12:05:00Z",
  "error_message": null
}
```

#### 查看所有任务
```bash
curl -X GET "http://localhost:8000/api/tasks?limit=10&offset=0&status=completed"
```

#### 查看系统统计
```bash
curl -X GET "http://localhost:8000/api/stats"
```

## 📚 API接口文档

### 核心接口

| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| `POST` | `/api/tasks/create` | 创建转换任务 | 支持office_to_pdf和pdf_to_markdown |
| `GET` | `/api/tasks/{task_id}` | 查看任务状态 | 获取任务详细信息和处理结果 |
| `GET` | `/api/tasks` | 列出所有任务 | 支持分页和状态过滤 |
| `GET` | `/api/tasks/search` | 搜索任务 | 根据bucket_name和file_path查询 |
| `GET` | `/api/stats` | 查看系统统计 | 队列状态和任务统计信息 |
| `GET` | `/health` | 健康检查 | 服务状态和组件健康状态 |
| `GET` | `/docs` | API文档 | Swagger交互式文档 |

### 任务类型说明

| 任务类型 | 输入格式 | 输出格式 | S3路径类型 |
|----------|----------|----------|------------|
| `office_to_pdf` | .docx, .xlsx, .pptx | .pdf | `pdf` |
| `pdf_to_markdown` | .pdf | .md, .json | `markdown` |

### S3存储路径规则

**格式:** `s3://ai-file/{bucket_name}/{文件夹路径}/{文件名(无后缀)}/{类型}/{输出文件}`

**示例:**
```
输入: bucket_name=company, file_path=docs/report.pdf
输出: s3://ai-file/company/docs/report/markdown/report.md
```

## ⚙️ 配置说明

### 环境要求
- **Python**: 3.11+ (推荐)
- **LibreOffice**: 用于Office文档转PDF转换
- **MinerU**: 2.1.9+ 用于PDF转Markdown转换
- **CUDA**: 11.8+ (可选，用于GPU加速)
- **内存**: 建议8GB+
- **GPU**: NVIDIA GPU，显存8GB+ (可选但推荐)

### 目录结构
```
/workspace/
├── api/                    # FastAPI接口层
│   ├── __init__.py
│   └── main.py            # API主文件
├── processors/             # 任务处理器
│   ├── __init__.py
│   └── task_processor.py  # 异步任务调度器
├── services/              # 业务服务层
│   ├── __init__.py
│   └── document_service.py # 文档转换服务
├── docs/                  # 项目文档
│   ├── document_conversion_workflow.md
│   └── batch_conversion_test_summary.md
├── test/                  # 测试文件目录
├── output/                # 输出文件目录
├── task_workspace/        # 任务工作空间
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker构建文件
├── .gitignore           # Git忽略文件
└── start.py             # 启动脚本
```

### 支持的文件格式

#### 输入格式
- **Office文档**: .doc, .docx, .xls, .xlsx, .ppt, .pptx
- **OpenDocument**: .odt, .ods, .odp
- **其他**: .rtf
- **PDF文档**: .pdf

#### 输出格式
- **PDF**: 从Office文档转换
- **Markdown**: 从PDF或Office文档转换

## 🔧 开发指南

### 开发规范
1. **文档管理**: 所有文档放在 `/docs` 下，测试脚本放在 `test` 目录下
2. **代码质量**: 代码必须编写注释，遵循现有开发规范
3. **依赖管理**: 使用国内镜像源安装依赖，及时更新requirements.txt
4. **测试验证**: API测试优先使用curl进行接口验证
5. **错误处理**: 任务完成前检查运行日志，修复错误异常
6. **版本控制**: 临时文件及时删除，保持代码目录整洁

### 性能优化建议
- **并发设置**: 根据硬件配置调整`max_concurrent_tasks`参数
- **GPU内存**: 大文件处理时注意GPU内存管理
- **批量处理**: 优先使用批量接口提高处理效率
- **缓存策略**: 对重复文件可考虑添加缓存机制

### 监控和调试
```bash
# 查看任务队列状态
curl http://localhost:8000/api/stats

# 查看特定任务详情
curl http://localhost:8000/api/tasks/{task_id}

# 查看系统健康状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

## 🔍 故障排除

### 常见问题及解决方案

#### 1. LibreOffice转换失败
```bash
# 检查LibreOffice安装
which libreoffice
libreoffice --version

# 测试转换功能
libreoffice --headless --convert-to pdf --outdir /tmp test.docx
```

#### 2. MinerU转换失败
```bash
# 检查MinerU安装
pip show mineru
python -c "import mineru; print(mineru.__version__)"

# 检查GPU支持
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

#### 3. 任务队列阻塞
```bash
# 查看队列状态
curl http://localhost:8000/api/stats

# 重启服务
pkill -f "python.*start.py"
python start.py
```

#### 4. 内存不足
- 减少并发任务数量：修改`max_concurrent_tasks`参数
- 清理GPU内存：重启服务或调用内存清理接口
- 分批处理大文件：使用批量接口分批处理

### 日志分析
```bash
# 查看实时日志
python start.py  # 控制台输出

# Docker环境日志
docker logs mineru-api -f

# 检查错误日志
grep -i error /var/log/mineru-api.log
```

### 性能调优
- **CPU密集型任务**: 增加worker数量
- **GPU内存限制**: 减少batch_size或并发数
- **磁盘I/O瓶颈**: 使用SSD存储，优化临时文件管理

## 📚 相关文档

### 项目文档
- [文档转换任务处理流程](docs/document_conversion_workflow.md)
- [批量转换测试总结报告](docs/batch_conversion_test_summary.md)

### 外部链接
- [MinerU 官方文档](https://github.com/opendatalab/MinerU)
- [LibreOffice 文档](https://www.libreoffice.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📞 支持

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 查看项目文档
- 参考故障排除指南