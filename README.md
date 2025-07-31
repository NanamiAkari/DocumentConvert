# 文档转换调度系统

基于 FastAPI 的文档转换调度系统，支持 Office 文档转 PDF 和 PDF 转 Markdown 的异步任务处理。

## 技术栈配置

### 核心技术栈
- **Web框架**: FastAPI 0.104.1 + Uvicorn
- **Office转PDF**: LibreOffice (headless模式)
- **PDF转Markdown**: MinerU 2.0+ (magic-pdf命令)
- **任务调度**: 自研异步任务处理器
- **数据验证**: Pydantic 2.5.0

### 依赖工具
- LibreOffice: `/usr/bin/libreoffice` - 用于Office文档转PDF
- MinerU 2.0+: `magic-pdf` 命令 - 用于PDF转Markdown
- Python 3.10+

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

## 快速开始

### 1. 启动服务
```bash
# 启动API服务器
python3 api/main.py

# 或使用start.py
python3 start.py
```

### 2. 创建转换任务

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

### 3. 查看任务状态
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

## 配置说明

### 环境要求
- Python 3.10+
- LibreOffice (用于Office文档转换)
- MinerU 2.0+ (用于PDF转Markdown)

### 目录结构
```
/workspace/
├── api/                 # API接口层
├── processors/          # 任务处理器
├── services/           # 业务服务层
├── test/               # 测试文件和脚本
├── output/             # 输出目录
├── requirements.txt    # Python依赖
└── start.py           # 启动脚本
```

## 开发规范

1. 所有文档放在 `/docs` 下，测试脚本放在 `test` 目录下
2. 代码必须编写注释，遵循现有开发规范
3. 使用国内镜像源安装依赖
4. API测试优先使用curl进行接口验证
5. 任务完成前检查运行日志，修复错误异常

## 故障排除

### 常见问题
1. **LibreOffice转换失败**: 检查LibreOffice是否正确安装
2. **MinerU转换失败**: 确认MinerU 2.0+版本和magic-pdf命令可用
3. **任务卡住**: 查看API服务器日志，检查任务处理器状态

### 日志查看
```bash
# 查看API服务器日志
tail -f /var/log/document-scheduler.log

# 或直接查看控制台输出
python3 api/main.py
```

## 相关链接
- [MinerU 官方文档](https://github.com/opendatalab/MinerU)
- [LibreOffice 文档](https://www.libreoffice.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)