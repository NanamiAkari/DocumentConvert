# 文档转换调度系统项目结构

## 📁 项目目录结构

```
document-scheduler/
├── 📄 核心应用文件
│   ├── start.py                    # 应用启动入口
│   ├── __init__.py                 # Python包初始化
│   └── requirements.txt            # 基础Python依赖
│
├── 🌐 API接口层
│   └── api/
│       ├── __init__.py
│       └── main.py                 # FastAPI应用主文件
│
├── ⚙️ 业务逻辑层
│   ├── processors/
│   │   ├── __init__.py
│   │   └── task_processor.py       # 异步任务处理器
│   └── services/
│       ├── __init__.py
│       └── document_service.py     # 文档转换服务
│
├── 🐳 Docker部署文件
│   ├── Dockerfile                  # 原始Dockerfile
│   ├── Dockerfile.document-scheduler # 通用版本Dockerfile
│   ├── Dockerfile.cpu              # CPU优化版本
│   ├── Dockerfile.gpu              # GPU加速版本
│   ├── .dockerignore               # Docker构建忽略文件
│   ├── docker-compose.yml          # 原始Docker Compose
│   ├── docker-compose.document-scheduler.yml # 通用版本
│   ├── docker-compose.cpu.yml      # CPU版本配置
│   ├── docker-compose.gpu.yml      # GPU版本配置
│   └── .env.example                # 环境变量模板
│
├── 🛠️ 部署工具
│   ├── deploy.sh                   # 智能部署脚本
│   └── export_image.sh             # 镜像导出工具
│
├── ⚙️ 配置文件
│   ├── mineru.json                 # 默认MinerU配置
│   ├── mineru-cpu.json             # CPU版本配置
│   ├── mineru-gpu.json             # GPU版本配置
│   ├── requirements-cpu.txt        # CPU版本依赖
│   └── requirements-gpu.txt        # GPU版本依赖
│
├── 📖 文档目录
│   └── docs/
│       ├── README.md               # 项目说明
│       ├── api_interface.md        # API接口文档
│       ├── deployment.md           # 部署指南
│       ├── docker_image_guide.md   # Docker镜像使用指南
│       ├── docker_deployment_summary.md # Docker部署总结
│       ├── gpu_cpu_comparison.md   # GPU/CPU版本对比
│       ├── final_deployment_summary.md # 最终部署总结
│       ├── project_summary.md      # 项目技术总结
│       ├── office_to_markdown.md   # 功能说明
│       └── mineru_official_api_integration.md # MinerU集成文档
│
├── 🧪 测试文件
│   └── test/
│       ├── 测试文档文件 (*.doc, *.docx, *.xlsx, *.pptx, *.pdf)
│       ├── mineru_api_test.py       # MinerU API测试
│       ├── mineru_python_api_test.py # MinerU Python API测试
│       ├── mineru_official_service.py # MinerU官方服务测试
│       └── test_pdf_conversion.py   # PDF转换测试
│
├── 🎨 前端预览 (可选)
│   └── preview_frontend/
│       ├── index.html              # 简单的Web界面
│       └── server.py               # 前端服务器
│
├── 📁 运行时目录
│   ├── logs/                       # 日志目录
│   └── temp/                       # 临时文件目录
│
└── 📄 项目文件
    └── PROJECT_STRUCTURE.md        # 本文件
```

## 🔧 核心组件说明

### 应用层 (Application Layer)
- **start.py**: 应用启动入口，支持API服务器和演示模式
- **api/main.py**: FastAPI应用，提供RESTful API接口

### 业务层 (Business Layer)
- **processors/task_processor.py**: 异步任务调度器，管理转换任务队列
- **services/document_service.py**: 文档转换服务，集成LibreOffice和MinerU

### 部署层 (Deployment Layer)
- **Docker镜像**: 三个版本（通用、CPU优化、GPU加速）
- **Docker Compose**: 对应的容器编排配置
- **部署脚本**: 智能部署和管理工具

## 📊 文件统计

### 代码文件
- Python源码: 6个文件
- 配置文件: 8个文件
- Docker文件: 8个文件
- 脚本文件: 2个文件

### 文档文件
- 技术文档: 9个文件
- 项目说明: 1个文件
- 总计文档: 10个文件

### 测试文件
- 测试脚本: 4个文件
- 测试文档: 8个文件 (多种格式)

## 🚀 部署版本

### 1. 通用版本 (document-scheduler:latest)
- **文件**: Dockerfile.document-scheduler
- **大小**: 1.12GB
- **特点**: 稳定可靠，生产验证

### 2. CPU优化版本 (document-scheduler:cpu)
- **文件**: Dockerfile.cpu
- **大小**: 1.74GB
- **特点**: CPU优化，无GPU依赖

### 3. GPU加速版本 (document-scheduler:gpu)
- **文件**: Dockerfile.gpu
- **大小**: 预计6-8GB
- **特点**: GPU加速，高性能处理

## 📖 文档体系

### 用户文档
1. **README.md** - 项目概览和快速开始
2. **deployment.md** - 详细部署指南
3. **docker_image_guide.md** - Docker使用指南

### 技术文档
1. **api_interface.md** - 完整API文档
2. **project_summary.md** - 技术架构总结
3. **gpu_cpu_comparison.md** - 版本对比分析

### 部署文档
1. **docker_deployment_summary.md** - Docker部署总结
2. **final_deployment_summary.md** - 最终部署总结

## 🛠️ 开发工具

### 部署工具
- **deploy.sh**: 智能部署脚本，支持版本选择
- **export_image.sh**: 镜像导出和打包工具

### 配置管理
- **.env.example**: 环境变量模板
- **mineru-*.json**: 不同版本的MinerU配置

## 🧪 测试覆盖

### 功能测试
- API接口测试
- 文档转换测试
- 批量处理测试

### 集成测试
- MinerU集成测试
- Docker容器测试
- 部署脚本测试

## 📈 项目特点

### 架构设计
- **分层架构**: 清晰的API、业务、服务分层
- **异步处理**: 基于asyncio的高并发处理
- **模块化**: 松耦合的组件设计

### 部署灵活性
- **多版本支持**: GPU/CPU/通用三个版本
- **智能部署**: 自动检测和版本选择
- **容器化**: 完整的Docker化部署

### 文档完善
- **全面覆盖**: 从技术到使用的完整文档
- **多层次**: 概览、详细、参考三个层次
- **实用性**: 包含示例和最佳实践

## 🎯 使用指南

### 快速开始
```bash
# 自动选择最佳版本启动
./deploy.sh start auto

# 检查服务状态
./deploy.sh health
```

### 开发模式
```bash
# 本地开发
python start.py

# 或启动演示
python start.py demo
```

### 生产部署
```bash
# 检查GPU支持
./deploy.sh gpu-check

# 启动对应版本
./deploy.sh start gpu  # 或 cpu
```

这个项目结构提供了完整的企业级文档转换解决方案，从开发到部署的全流程支持。
