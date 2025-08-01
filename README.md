# 文档转换调度系统 (Document Scheduler)

基于 FastAPI 和 MinerU 2.0 的智能文档转换调度系统，支持 Office 文档转 PDF 和 PDF 转 Markdown 的异步任务处理。

## 📊 测试验证结果

✅ **已完成全面测试验证**
- 测试文件：9个不同格式文档（Word、Excel、PowerPoint、PDF）
- 转换成功率：**100%**
- 系统稳定性：无崩溃、无异常
- 转换质量：文本准确、格式保持、中文支持完善

详细测试报告：[批量转换测试总结](docs/batch_conversion_test_summary.md)

## 🌟 功能特性

- 🔄 **多格式转换**: 支持Office文档(Word/Excel/PowerPoint)转PDF，PDF转Markdown
- 🤖 **AI驱动**: 集成MinerU 2.0 Python API，提供高质量PDF到Markdown转换
- 🚀 **GPU加速**: 支持CUDA GPU加速，显著提升转换速度和质量
- 📋 **任务调度**: 异步任务处理，支持优先级队列和并发控制
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
4. **batch_office_to_pdf**: 批量Office转PDF
5. **batch_pdf_to_markdown**: 批量PDF转Markdown
6. **batch_office_to_markdown**: 批量Office转Markdown (推荐)

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

## 📋 使用示例

### 创建转换任务

#### Office转PDF
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_pdf",
    "input_path": "/workspace/test/document.docx",
    "output_path": "/workspace/output/document.pdf",
    "priority": "normal"
  }'
```

#### PDF转Markdown
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "pdf_to_markdown",
    "input_path": "/workspace/test/document.pdf",
    "output_path": "/workspace/output/document.md",
    "priority": "normal",
    "params": {"force_reprocess": true}
  }'
```

#### 批量Office转Markdown (推荐)
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "batch_office_to_markdown",
    "input_path": "/workspace/test",
    "output_path": "/workspace/output/markdown",
    "priority": "normal",
    "params": {"recursive": false, "force_reprocess": true}
  }'
```

### 查看任务状态
```bash
# 查看特定任务状态
curl http://localhost:8000/api/tasks/1

# 查看队列统计
curl http://localhost:8000/api/stats

# 查看所有任务
curl http://localhost:8000/api/tasks
```

## API接口

### 核心接口
- `POST /api/tasks` - 创建转换任务
- `GET /api/tasks/{task_id}` - 查看任务状态
- `GET /api/tasks` - 列出所有任务
- `GET /api/stats` - 查看队列统计
- `GET /health` - 健康检查

### 便捷接口
- `GET /api/shortcuts/office-to-pdf` - 直接创建Office转PDF任务
- `GET /api/shortcuts/pdf-to-markdown` - 直接创建PDF转Markdown任务
- `GET /api/shortcuts/office-to-markdown` - 直接创建Office转Markdown任务
- `GET /api/shortcuts/batch-office-to-pdf` - 批量Office转PDF
- `GET /api/shortcuts/batch-pdf-to-markdown` - 批量PDF转Markdown
- `GET /api/shortcuts/batch-office-to-markdown` - 批量Office转Markdown (推荐)

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