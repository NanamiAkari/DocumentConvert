# MinerU GPU Base Image

基于NVIDIA CUDA的MinerU GPU基础镜像，集成WebIDE支持，自动下载最新模型。

## 镜像信息

- **镜像名称**: `docker.cnb.cool/aiedulab/library/mineru:latest`
- **基础镜像**: `nvidia/cuda:11.8.0-devel-ubuntu22.04`
- **MinerU版本**: 2.1.9+
- **PyTorch版本**: 2.7.1+cu118
- **WebIDE**: VSCode Server 4.96.2
- **Python版本**: 3.11
- **镜像大小**: 22.7GB

## 功能特性

### 🚀 GPU加速
- NVIDIA CUDA 11.8支持
- PyTorch 2.7.1 GPU加速
- MinerU GPU模式配置
- 自动GPU内存管理

### 🌐 WebIDE集成
- VSCode Server在线编辑器
- Python开发环境
- Git集成和扩展
- 代码补全和调试

### 📦 自动模型下载
- 使用官方 `mineru-models-download` 工具
- 通过ModelScope自动下载最新模型
- 支持pipeline模式的完整模型集
- 构建时自动下载，无需手动准备

### 🛠️ 开发工具
- Python 3.11
- LibreOffice
- 中文字体支持
- 常用开发工具

## 快速开始

### 1. 构建镜像

```bash
# 模型将在构建过程中自动下载，无需预先准备
cd .ide
./build.sh
```

### 2. 推送镜像

```bash
./push.sh
```

### 3. 使用镜像

#### 基本使用
```bash
# 拉取镜像
docker pull docker.cnb.cool/aiedulab/library/mineru:latest

# 运行容器
docker run --rm --gpus all -it docker.cnb.cool/aiedulab/library/mineru:latest
```

#### WebIDE模式
```bash
# 启动WebIDE
docker run --rm --gpus all -p 8080:8080 \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  code-server --bind-addr 0.0.0.0:8080 --auth none /workspace

# 访问: http://localhost:8080
```

#### 开发环境
```bash
# 使用docker-compose启动完整开发环境
docker-compose up -d

# 访问WebIDE: http://localhost:8080
# 访问API: http://localhost:8000
```

## 使用示例

### PDF转Markdown
```bash
# 命令行方式
docker run --rm --gpus all \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  mineru -p /workspace/input.pdf -o /workspace/output

# Python API方式
docker run --rm --gpus all \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  python3 -c "
from mineru.api import pdf_to_markdown
result = pdf_to_markdown('/workspace/input.pdf', '/workspace/output.md')
print('转换完成:', result)
"
```

### 开发调试
```bash
# 进入容器进行开发
docker run --rm --gpus all -it \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  /bin/bash

# 在容器内
cd /workspace
python3 your_script.py
```

## 配置说明

### 环境变量
- `MINERU_MODEL_SOURCE=modelscope` - 模型源
- `CUDA_VISIBLE_DEVICES=0` - GPU设备
- `PYTHONUNBUFFERED=1` - Python输出缓冲

### 目录结构
```
/root/.cache/modelscope/     # 自动下载的模型文件
/opt/mineru_venv/           # Python虚拟环境
/workspace/                 # 工作目录
```

### 模型配置
MinerU 2.0+ 版本使用自动配置，模型通过 `mineru-models-download` 命令下载：
```bash
# 模型下载命令（构建时自动执行）
mineru-models-download -s modelscope -m pipeline
```

支持的模型包括：
- Layout模型：doclayout_yolo(2501)
- Formula模型：unimernet(2501)
- OCR模型：PaddleOCR
- Table模型：RapidTable
- Reading Order模型：layoutreader

## 系统要求

### 硬件要求
- NVIDIA GPU (显存 >= 8GB)
- 内存 >= 16GB
- 存储空间 >= 20GB

### 软件要求
- Docker >= 20.10
- NVIDIA Docker Runtime
- CUDA驱动 >= 11.8

## 故障排除

### GPU不可用
```bash
# 检查NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# 检查GPU支持
docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest \
  python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### 模型加载失败
```bash
# 检查模型文件
docker run --rm docker.cnb.cool/aiedulab/library/mineru:latest \
  ls -la /root/.cache/modelscope/

# 重新下载模型
docker run --rm docker.cnb.cool/aiedulab/library/mineru:latest \
  mineru-models-download -s modelscope -m pipeline

# 测试mineru命令
docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest \
  mineru --help
```

### WebIDE无法访问
```bash
# 检查端口映射
docker ps

# 检查防火墙
curl http://localhost:8080
```

## 开发指南

### 扩展镜像
```dockerfile
FROM docker.cnb.cool/aiedulab/library/mineru:latest

# 安装额外依赖
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip install your-package"

# 复制应用代码
COPY . /workspace/

# 设置工作目录
WORKDIR /workspace
```

### 自定义配置
```bash
# 使用自定义配置文件
docker run --rm --gpus all \
  -v $(pwd)/custom-config.json:/root/.mineru/config.json \
  docker.cnb.cool/aiedulab/library/mineru:latest
```

## 更新日志

- **v2.0.0**: 重大更新，升级到MinerU 2.1.9+
  - 升级CUDA到12.1，Python到3.11
  - 使用官方模型下载工具自动下载最新模型
  - 支持最新的doclayout_yolo和unimernet模型
  - 简化构建流程，无需预先准备模型文件
- **v1.0.0**: 初始版本，集成MinerU 2.1.9和WebIDE
  - 支持GPU加速PDF转换
  - 预装完整模型文件
  - WebIDE开发环境

## 支持

如遇问题，请提供：
1. 系统环境信息
2. GPU型号和驱动版本
3. 错误日志
4. 复现步骤
