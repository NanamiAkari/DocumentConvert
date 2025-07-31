#!/bin/bash

# Document Scheduler with MinerU 2.0 Build Script
# 文档转换调度系统构建脚本

set -e

echo "=== Document Scheduler with MinerU 2.0 Build Script ==="
echo "文档转换调度系统构建脚本"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查NVIDIA Docker是否安装
if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "⚠️  NVIDIA Docker支持未检测到，将使用CPU模式"
    echo "如需GPU加速，请安装nvidia-docker2"
    GPU_SUPPORT=false
else
    echo "✅ NVIDIA Docker支持已检测到"
    GPU_SUPPORT=true
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p test output logs

# 检查测试文件
if [ ! "$(ls -A test/)" ]; then
    echo "⚠️  test目录为空，请添加测试文件"
    echo "支持的文件格式: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX"
fi

# 构建Docker镜像
echo "🔨 构建Docker镜像..."
docker build -t document-scheduler:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi

# 显示镜像信息
echo "📊 镜像信息:"
docker images document-scheduler:latest

echo ""
echo "🚀 构建完成！"
echo ""
echo "启动服务:"
if [ "$GPU_SUPPORT" = true ]; then
    echo "  GPU模式: docker-compose up -d"
else
    echo "  CPU模式: docker-compose up -d"
    echo "  注意: CPU模式下MinerU转换速度较慢"
fi
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo ""
echo "API文档: http://localhost:8000/docs"
echo "健康检查: http://localhost:8000/health"
echo ""
echo "测试转换:"
echo "  curl -X POST http://localhost:8000/api/tasks \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"task_type\":\"pdf_to_markdown\",\"input_path\":\"/app/test/your-file.pdf\",\"output_path\":\"/app/output/result.md\"}'"
