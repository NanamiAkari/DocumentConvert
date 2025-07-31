#!/bin/bash

# MinerU GPU Base Image Push Script
# 推送MinerU GPU基础镜像脚本

set -e

echo "=== MinerU GPU Base Image Push Script ==="
echo "推送MinerU GPU基础镜像到仓库"

# 镜像名称
IMAGE_NAME="docker.cnb.cool/aiedulab/library/mineru:latest"

# 检查镜像是否存在
if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$IMAGE_NAME"; then
    echo "❌ 镜像不存在: $IMAGE_NAME"
    echo "请先运行构建脚本: ./build.sh"
    exit 1
fi

echo "✅ 镜像检查通过: $IMAGE_NAME"

# 显示镜像信息
echo "📊 镜像信息:"
docker images "$IMAGE_NAME"

# 获取镜像大小
IMAGE_SIZE=$(docker images --format "table {{.Size}}" "$IMAGE_NAME" | tail -n 1)
echo "📦 镜像大小: $IMAGE_SIZE"

# 推送镜像
echo "🚀 开始推送镜像到仓库..."
echo "目标仓库: docker.cnb.cool/aiedulab/library/mineru:latest"

# 推送镜像
docker push "$IMAGE_NAME"

if [ $? -eq 0 ]; then
    echo "✅ 镜像推送成功"
else
    echo "❌ 镜像推送失败"
    exit 1
fi

echo ""
echo "🎉 推送完成！"
echo ""
echo "镜像地址: $IMAGE_NAME"
echo ""
echo "使用方法:"
echo "  # 拉取镜像"
echo "  docker pull $IMAGE_NAME"
echo ""
echo "  # 运行容器"
echo "  docker run --rm --gpus all -it $IMAGE_NAME"
echo ""
echo "  # 启动WebIDE"
echo "  docker run --rm --gpus all -p 8080:8080 $IMAGE_NAME code-server --bind-addr 0.0.0.0:8080 --auth none"
echo ""
echo "  # 测试MinerU"
echo "  docker run --rm --gpus all -v \$(pwd):/workspace $IMAGE_NAME mineru -p /workspace/test.pdf -o /workspace/output"
