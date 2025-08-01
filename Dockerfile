# 基于MinerU基础镜像构建文档转换调度系统
FROM docker.cnb.cool/aiedulab/library/mineru:latest

# 设置工作目录
WORKDIR /workspace

# 设置环境变量
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

# 复制项目文件
COPY api/ /workspace/api/
COPY processors/ /workspace/processors/
COPY services/ /workspace/services/
COPY docs/ /workspace/docs/
COPY start.py /workspace/
COPY __init__.py /workspace/

# 创建必要的目录
RUN mkdir -p /workspace/output \
    && mkdir -p /workspace/task_workspace \
    && mkdir -p /workspace/temp \
    && mkdir -p /workspace/test

# 安装必要的Python包（基础镜像已有大部分依赖）
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    aiofiles==23.2.1 \
    python-multipart==0.0.6 \
    python-dotenv==1.0.0 \
    aiohttp

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "/workspace/start.py"]

# 添加标签
LABEL maintainer="AI Education Lab"
LABEL description="Document Conversion Scheduler with MinerU 2.0"
LABEL version="1.0.0"
LABEL project="mineru-api"
