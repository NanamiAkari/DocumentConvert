#!/bin/bash

# MinerU GPU Base Image Build Script
# 构建MinerU GPU基础镜像脚本

set -e

echo "=== MinerU GPU Base Image Build Script ==="
echo "构建MinerU GPU基础镜像"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查NVIDIA Docker是否可用
if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "⚠️  NVIDIA Docker支持未检测到"
    echo "如需GPU加速，请安装nvidia-docker2"
    echo "继续构建CPU版本..."
fi

# 检查模型文件是否存在
MODEL_PATH="/root/.cache/modelscope"
if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ 模型文件不存在: $MODEL_PATH"
    echo "请先下载MinerU模型文件"
    echo ""
    echo "下载方法:"
    echo "1. 使用MinerU命令: mineru-models-download"
    echo "2. 使用Python脚本:"
    echo "   python3 -c 'from mineru.cli.models_download import download_models; download_models()'"
    echo "3. 手动下载到指定目录"
    echo ""
    exit 1
fi

echo "✅ 模型文件检查通过: $MODEL_PATH"

# 显示模型文件大小和内容
MODEL_SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | cut -f1 || echo "未知")
echo "📦 模型文件大小: $MODEL_SIZE"

# 检查关键模型目录
echo "🔍 检查模型目录结构:"
if [ -d "$MODEL_PATH/opendatalab" ]; then
    echo "  ✅ opendatalab目录存在"
    if [ -d "$MODEL_PATH/opendatalab/PDF-Extract-Kit" ]; then
        echo "  ✅ PDF-Extract-Kit目录存在"
    else
        echo "  ⚠️  PDF-Extract-Kit目录不存在"
    fi
else
    echo "  ⚠️  opendatalab目录不存在"
fi

# 构建Docker镜像
echo "🔨 开始构建MinerU GPU基础镜像..."
echo "镜像名称: docker.cnb.cool/aiedulab/library/mineru:latest"

# 切换到.ide目录
cd "$(dirname "$0")"

# 构建镜像
docker build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    -t docker.cnb.cool/aiedulab/library/mineru:latest \
    -f Dockerfile \
    /

if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi

# 显示镜像信息
echo "📊 镜像信息:"
docker images docker.cnb.cool/aiedulab/library/mineru:latest

# 测试镜像
echo "🧪 测试镜像..."
docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest python3 -c "
import torch
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA version:', torch.version.cuda)
    print('GPU count:', torch.cuda.device_count())

try:
    from mineru.api import pdf_to_markdown
    print('MinerU API: OK')
except Exception as e:
    print('MinerU API Error:', e)

import os
if os.path.exists('/root/mineru.json'):
    print('MinerU config: OK')
else:
    print('MinerU config: Missing')
"

echo ""
echo "🚀 构建完成！"
echo ""
echo "推送镜像到仓库:"
echo "  docker push docker.cnb.cool/aiedulab/library/mineru:latest"
echo ""
echo "使用镜像:"
echo "  docker run --rm --gpus all -it docker.cnb.cool/aiedulab/library/mineru:latest"
echo ""
echo "启动WebIDE:"
echo "  docker run --rm --gpus all -p 8080:8080 docker.cnb.cool/aiedulab/library/mineru:latest code-server --bind-addr 0.0.0.0:8080 --auth none"
echo ""
echo "测试MinerU:"
echo "  docker run --rm --gpus all -v \$(pwd):/workspace docker.cnb.cool/aiedulab/library/mineru:latest mineru -p /workspace/test.pdf -o /workspace/output"
