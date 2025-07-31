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

# 检查Docker构建环境
echo "🔍 检查Docker构建环境..."
echo "注意: MinerU 2.0+ 版本将在构建过程中自动下载最新模型"
echo "模型将通过 mineru-models-download 命令自动下载到容器内"

# 构建Docker镜像
echo "🔨 开始构建MinerU GPU基础镜像..."
echo "镜像名称: docker.cnb.cool/aiedulab/library/mineru:latest"
echo "MinerU版本: 2.1.9+"
echo "CUDA版本: 11.8"
echo "Python版本: 3.11"

# 切换到.ide目录
cd "$(dirname "$0")"

# 构建镜像
docker build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    -t docker.cnb.cool/aiedulab/library/mineru:latest \
    -f Dockerfile \
    .

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

# 首先尝试GPU测试
if docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest python3 -c "import torch; print('GPU test passed')" 2>/dev/null; then
    echo "✅ GPU支持可用，进行GPU测试"
    docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest python3 -c "
import torch
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA version:', torch.version.cuda)
    print('GPU count:', torch.cuda.device_count())

try:
    import mineru
    print('MinerU import: OK')
except Exception as e:
    print('MinerU import Error:', e)
"
else
    echo "⚠️  GPU不可用，进行CPU测试"
    docker run --rm docker.cnb.cool/aiedulab/library/mineru:latest python3 -c "
import torch
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())

try:
    import mineru
    print('MinerU import: OK')
except Exception as e:
    print('MinerU import Error:', e)

# Test mineru command
import subprocess
try:
    result = subprocess.run(['mineru', '--help'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print('MinerU command: OK')
    else:
        print('MinerU command Error:', result.stderr)
except Exception as e:
    print('MinerU command Error:', e)
"
fi

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
