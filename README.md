# Document Conversion Service

🚀 **企业级智能文档转换服务** - 基于MinerU 2.0的高性能文档处理平台，支持PDF、Office文档的智能转换，具备完整的云存储集成、异步处理和监控能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## 🌟 核心特性

### 📄 智能文档转换
- **🔄 PDF转Markdown**: 基于MinerU 2.0的AI驱动解析，精确识别表格、图片、公式和复杂布局
- **📊 Office转PDF**: 支持Word、Excel、PowerPoint等格式，保持原始格式和样式
- **🔗 Office转Markdown**: 直接将Office文档转换为Markdown，支持图片提取
- **🎯 高精度识别**: 支持多语言文档、复杂表格、数学公式和图表

### ⚡ 高性能处理
- **🚀 GPU加速**: 支持CUDA加速，显著提升处理速度
- **📦 批量处理**: 异步队列系统，支持大规模文档批量转换
- **🔄 智能重试**: 自动错误恢复和重试机制
- **⚖️ 负载均衡**: 可配置并发任务数，优化资源利用

### ☁️ 企业级集成
- **🗄️ S3/MinIO集成**: 无缝对接云存储，支持多bucket管理
- **📊 实时监控**: 完整的任务状态跟踪和性能监控
- **🔐 安全可靠**: 支持访问控制和数据加密
- **📈 可扩展**: 支持水平扩展和微服务架构

### 🎨 用户友好界面
- **🌐 Web界面**: 现代化Gradio界面，支持拖拽上传
- **📚 API文档**: 完整的RESTful API和自动生成文档
- **📱 响应式设计**: 支持桌面和移动设备访问
- **🔍 实时预览**: 转换进度实时显示和结果预览

## 🛠 技术架构

### 核心技术栈
| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **Web框架** | FastAPI | 0.104+ | 高性能异步API框架 |
| **AI引擎** | MinerU | 2.0+ | 智能文档解析引擎 |
| **Web界面** | Gradio | 4.44+ | 交互式Web界面 |
| **文档处理** | LibreOffice | 7.0+ | Office文档转换 |
| **数据库** | SQLite/PostgreSQL | - | 支持多种数据库 |
| **存储** | S3/MinIO | - | 分布式对象存储 |
| **容器** | Docker | 20.0+ | 容器化部署 |
| **运行时** | Python | 3.9+ | 异步编程支持 |

### 依赖库详情
```python
# 核心依赖
fastapi>=0.104.0          # Web框架
uvicorn[standard]>=0.24.0 # ASGI服务器
gradio>=4.44.0           # Web界面
magic-pdf[full]>=0.7.0   # MinerU PDF处理
sqlalchemy>=2.0.0        # ORM框架
aiosqlite>=0.19.0        # 异步SQLite
boto3>=1.34.0            # AWS S3客户端
httpx>=0.25.0            # 异步HTTP客户端
psutil>=5.9.0            # 系统监控
```

### 系统架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web界面       │    │   API服务       │    │   任务处理器     │
│  (Gradio)       │◄──►│  (FastAPI)      │◄──►│  (AsyncQueue)   │
│  Port: 7860     │    │  Port: 8001     │    │  (Background)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   存储层        │
                    │ ┌─────────────┐ │
                    │ │   数据库    │ │
                    │ │ (SQLite)    │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │   文件存储  │ │
                    │ │ (S3/MinIO)  │ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

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
  -p 8001:8001 \
  -p 7860:7860 \
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
      - "8001:8001"
      - "7860:7860"
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
| `DATABASE_URL` | 数据库连接URL | `sqlite:///./database/document_conversion.db` | `postgresql://user:pass@host:5432/db` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `MAX_CONCURRENT_TASKS` | 最大并发任务数 | `3` | `1-10` (根据GPU内存调整) |
| `TASK_TIMEOUT` | 任务超时时间(秒) | `3600` | `1800-7200` |
| `RETRY_MAX_ATTEMPTS` | 最大重试次数 | `3` | `1-5` |
| `WORKSPACE_PATH` | 工作目录路径 | `/app/task_workspace` | 绝对路径 |
| `ENABLE_GPU` | 启用GPU加速 | `true` | `true`/`false` |
| `GRADIO_SERVER_NAME` | Gradio服务地址 | `0.0.0.0` | IP地址 |
| `GRADIO_SERVER_PORT` | Gradio服务端口 | `7860` | 端口号 |

### 高级配置

#### GPU配置
```bash
# 检查GPU可用性
nvidia-smi

# 设置GPU内存限制
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

#### 性能调优
```bash
# 根据系统资源调整并发数
# 4GB GPU内存: MAX_CONCURRENT_TASKS=1
# 8GB GPU内存: MAX_CONCURRENT_TASKS=2
# 16GB+ GPU内存: MAX_CONCURRENT_TASKS=3-5
export MAX_CONCURRENT_TASKS=3

# 调整任务超时时间
export TASK_TIMEOUT=3600  # 1小时
```

## 🎨 Web界面访问

服务启动后，可以通过以下方式访问：

- **API文档**: `http://localhost:8001/docs` - FastAPI自动生成的API文档
- **Gradio界面**: `http://localhost:7860` - 用户友好的Web界面，支持文件上传和转换

### Gradio界面功能

1. **文件上传**: 支持拖拽上传PDF和Office文档
2. **转换类型选择**: 
   - PDF → Markdown
   - Office → PDF  
   - Office → Markdown
3. **任务优先级**: 可选择normal或high优先级
4. **实时状态**: 显示转换进度和状态
5. **结果下载**: 转换完成后直接下载结果文件

## 📚 API文档

服务启动后，访问 `http://localhost:8001/docs` 查看完整的API文档。

### 核心API接口

#### 1. 创建转换任务

**PDF转Markdown**
```bash
curl -X POST "http://localhost:8001/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=ai-file" \
  -F "file_path=test/document.pdf" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**Office转PDF**
```bash
curl -X POST "http://localhost:8001/api/tasks/create" \
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
curl "http://localhost:8001/api/tasks/123"
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
curl "http://localhost:8001/api/tasks"

# 按状态过滤
curl "http://localhost:8001/api/tasks?status=completed&limit=10"
```

#### 4. 重试失败任务

```bash
curl -X POST "http://localhost:8001/api/tasks/123/retry"
```

#### 5. 修改任务类型

```bash
curl -X PUT "http://localhost:8001/api/tasks/123/task-type" \
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
curl "http://localhost:8001/health"
```

### 服务状态
```bash
curl "http://localhost:8001/api/status"
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

启动API服务：
```bash
python main.py
# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info
```

启动Gradio Web界面（新终端）：
```bash
python gradio_app.py
```

启动MinIO存储服务（新终端）：
```bash
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin minio server ./minio-data --address ":9003" --console-address ":9004"
```

### 本地开发访问地址

- **API服务**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **Gradio界面**: http://localhost:7860
- **MinIO控制台**: http://localhost:9004

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 🚨 GPU相关问题

**问题**: GPU内存不足 (CUDA out of memory)
```bash
# 解决方案
# 1. 减少并发任务数
export MAX_CONCURRENT_TASKS=1

# 2. 监控GPU使用情况
nvidia-smi -l 1

# 3. 清理GPU缓存
docker exec document-converter python -c "import torch; torch.cuda.empty_cache()"
```

**问题**: GPU不可用
```bash
# 检查GPU驱动
nvidia-smi

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# 禁用GPU加速
export ENABLE_GPU=false
```

#### 2. 🔗 网络连接问题

**问题**: S3连接失败
```bash
# 诊断步骤
# 1. 测试网络连通性
curl -I http://your-minio-server:9000

# 2. 验证凭据
aws s3 ls --endpoint-url=http://your-minio-server:9000

# 3. 检查防火墙设置
telnet your-minio-server 9000
```

**问题**: API服务无响应
```bash
# 检查服务状态
curl -f http://localhost:8001/health || echo "API服务异常"

# 检查端口占用
netstat -tlnp | grep :8001

# 重启服务
docker restart document-converter
```

#### 3. 📄 文档处理问题

**问题**: LibreOffice转换失败
```bash
# 检查LibreOffice安装
docker exec document-converter libreoffice --version

# 测试转换功能
docker exec document-converter libreoffice --headless --convert-to pdf test.docx

# 检查文件权限
ls -la /app/task_workspace/
```

**问题**: PDF解析失败
```bash
# 检查文件完整性
file document.pdf

# 验证PDF可读性
pdfinfo document.pdf

# 检查MinerU版本
pip show magic-pdf
```

#### 4. 💾 存储问题

**问题**: 磁盘空间不足
```bash
# 检查磁盘使用情况
df -h

# 清理临时文件
docker exec document-converter find /app/task_workspace -name "*.tmp" -delete

# 清理旧任务文件
docker exec document-converter find /app/task_workspace -mtime +7 -type d -exec rm -rf {} +
```

### 🔍 诊断工具

#### 系统健康检查脚本
```bash
#!/bin/bash
# health_check.sh

echo "=== 系统健康检查 ==="

# 检查服务状态
echo "1. 检查API服务..."
curl -s http://localhost:8001/health | jq . || echo "❌ API服务异常"

# 检查GPU状态
echo "2. 检查GPU状态..."
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits || echo "❌ GPU不可用"

# 检查存储空间
echo "3. 检查存储空间..."
df -h | grep -E "(/$|/app)"

# 检查内存使用
echo "4. 检查内存使用..."
free -h

# 检查任务队列
echo "5. 检查任务队列..."
curl -s http://localhost:8001/api/tasks?status=pending | jq '.[] | length' || echo "无法获取任务信息"

echo "=== 检查完成 ==="
```

#### 性能监控脚本
```bash
#!/bin/bash
# monitor.sh

while true; do
    echo "$(date): CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}'), \
    GPU=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)%, \
    Memory=$(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    sleep 30
done
```

### 📊 日志分析

#### 查看实时日志
```bash
# API服务日志
docker logs -f document-converter

# 特定任务日志
docker exec document-converter tail -f /app/log_files/task_123.log

# 错误日志过滤
docker logs document-converter 2>&1 | grep -i error
```

#### 日志级别配置
```bash
# 开启调试模式
export LOG_LEVEL=DEBUG
docker restart document-converter

# 查看详细错误信息
docker exec document-converter python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# 你的测试代码
"
```

### 🆘 紧急恢复

#### 服务重启
```bash
# 优雅重启
docker restart document-converter

# 强制重启
docker kill document-converter
docker start document-converter

# 完全重建
docker-compose down
docker-compose up -d
```

#### 数据恢复
```bash
# 备份数据库
docker exec document-converter sqlite3 /app/database/document_conversion.db ".backup /app/database/backup.db"

# 恢复数据库
docker exec document-converter sqlite3 /app/database/document_conversion.db ".restore /app/database/backup.db"
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下指南：

### 🔧 开发环境设置

1. **Fork项目**
```bash
git clone https://github.com/your-username/DocumentConvert.git
cd DocumentConvert
```

2. **创建开发分支**
```bash
git checkout -b feature/your-feature-name
```

3. **安装开发依赖**
```bash
pip install -r requirements-dev.txt
pre-commit install
```

### 📝 代码规范

- **代码风格**: 遵循PEP 8规范
- **类型注解**: 使用Python类型提示
- **文档字符串**: 使用Google风格的docstring
- **测试覆盖**: 新功能需要包含单元测试

### 🧪 测试指南

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=app tests/
```

### 📋 提交规范

使用[Conventional Commits](https://www.conventionalcommits.org/)格式：

```
feat: 添加新的PDF解析功能
fix: 修复S3上传错误
docs: 更新API文档
test: 添加单元测试
refactor: 重构任务处理逻辑
```

### 🔍 Pull Request流程

1. 确保所有测试通过
2. 更新相关文档
3. 添加变更日志条目
4. 提交PR并描述变更内容
5. 等待代码审查

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

```
MIT License

Copyright (c) 2024 Document Conversion Service

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMplied, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🌟 致谢

感谢以下开源项目的支持：

- [MinerU](https://github.com/opendatalab/MinerU) - 智能PDF解析引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [Gradio](https://gradio.app/) - 机器学习Web界面
- [LibreOffice](https://www.libreoffice.org/) - 开源办公套件

## 📞 支持与联系

### 🐛 问题报告

如果您遇到问题，请通过以下方式报告：

1. **GitHub Issues**: [提交Issue](https://github.com/your-repo/DocumentConvert/issues)
2. **邮件支持**: support@documentconvert.com
3. **技术文档**: 查看 [完整文档](/.trae/documents/)

### 💬 社区交流

- **讨论区**: [GitHub Discussions](https://github.com/your-repo/DocumentConvert/discussions)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)
- **路线图**: [项目路线图](https://github.com/your-repo/DocumentConvert/projects)

### 🚀 商业支持

如需企业级支持、定制开发或技术咨询，请联系：

- **商务邮箱**: business@documentconvert.com
- **技术咨询**: consulting@documentconvert.com

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！ ⭐**

[🏠 首页](https://github.com/your-repo/DocumentConvert) • 
[📚 文档](/.trae/documents/) • 
[🐛 报告问题](https://github.com/your-repo/DocumentConvert/issues) • 
[💡 功能请求](https://github.com/your-repo/DocumentConvert/issues/new?template=feature_request.md)

</div>