# 基于MinerU基础镜像构建文档转换调度系统
FROM docker.cnb.cool/aiedulab/library/mineru:latest

# 设置工作目录
WORKDIR /workspace

# 设置环境变量
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/mineru_venv/bin:$PATH"

# 复制项目文件
COPY api/ /workspace/api/
COPY processors/ /workspace/processors/
COPY services/ /workspace/services/
COPY database/ /workspace/database/
COPY utils/ /workspace/utils/
COPY docs/ /workspace/docs/
COPY main.py /workspace/
COPY start.py /workspace/
COPY __init__.py /workspace/
COPY requirements.txt /workspace/

# 创建必要的目录和数据持久化目录
RUN mkdir -p /workspace/output \
    && mkdir -p /workspace/task_workspace \
    && mkdir -p /workspace/temp \
    && mkdir -p /workspace/test \
    && mkdir -p /data/database \
    && mkdir -p /data/logs \
    && mkdir -p /data/workspace \
    && mkdir -p /data/temp

# 激活虚拟环境并安装必要的Python包
RUN /opt/mineru_venv/bin/pip install --no-cache-dir -r /workspace/requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

# 创建.env文件
RUN echo "# S3/MinIO配置" > /workspace/.env && \
    echo "# S3/MinIO Configuration" >> /workspace/.env && \
    echo "" >> /workspace/.env && \
    echo "# 下载服务配置（用于从S3/MinIO下载文件）" >> /workspace/.env && \
    echo "# Download service configuration (for downloading files from S3/MinIO)" >> /workspace/.env && \
    echo "AWS_ACCESS_KEY_ID=test" >> /workspace/.env && \
    echo "AWS_SECRET_ACCESS_KEY=Ab123456" >> /workspace/.env && \
    echo "S3_ENDPOINT_URL=http://shenben.club:9000" >> /workspace/.env && \
    echo "AWS_REGION=us-east-1" >> /workspace/.env && \
    echo "S3_ENABLED=true" >> /workspace/.env && \
    echo "" >> /workspace/.env && \
    echo "# 上传服务配置（用于将文件上传到S3/MinIO）" >> /workspace/.env && \
    echo "# Upload service configuration (for uploading files to S3/MinIO)" >> /workspace/.env && \
    echo "UPLOAD_S3_ACCESS_KEY_ID=test" >> /workspace/.env && \
    echo "UPLOAD_S3_SECRET_ACCESS_KEY=Ab123456" >> /workspace/.env && \
    echo "UPLOAD_S3_ENDPOINT_URL=http://shenben.club:9000" >> /workspace/.env && \
    echo "UPLOAD_S3_BUCKET=ai-file" >> /workspace/.env

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 声明数据卷
VOLUME ["/data/database", "/data/logs", "/data/workspace", "/data/temp"]

# 设置启动命令
CMD ["/opt/mineru_venv/bin/python", "/workspace/main.py"]

# 添加标签
LABEL maintainer="AI Education Lab"
LABEL description="Document Conversion Scheduler with MinerU 2.0"
LABEL version="1.0.0"
LABEL project="mineru-api"
