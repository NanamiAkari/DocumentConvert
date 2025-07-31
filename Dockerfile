# Document Scheduler with MinerU 2.0
FROM ubuntu:22.04

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV MINERU_MODEL_SOURCE=modelscope

# Update the package list and install necessary packages
RUN apt-get update && \
    apt-get install -y \
        software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.10 \
        python3.10-venv \
        python3.10-dev \
        python3-pip \
        wget \
        git \
        curl \
        vim \
        unzip \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libxrender1 \
        libxext6 \
        libsm6 \
        libxrandr2 \
        libfontconfig1 \
        libxss1 \
        libreoffice \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        ttf-mscorefonts-installer \
        fontconfig \
        poppler-utils \
        && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Create a virtual environment for MinerU
RUN python3 -m venv /opt/mineru_venv

# Activate virtual environment and install MinerU
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip3 install --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple/ && \
    pip3 install 'mineru[core]==2.1.9' -i https://mirrors.cloud.tencent.com/pypi/simple/"

# Download MinerU models during build
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    export MINERU_MODEL_SOURCE=modelscope && \
    python3 -c 'from mineru.cli.models_download import download_models; download_models()' || echo 'Model download failed, will retry at runtime'"

# Create working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY api/ ./api/
COPY services/ ./services/
COPY processors/ ./processors/
COPY start.py .
COPY __init__.py .

# Install application dependencies in the virtual environment
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip3 install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple/"

# Create task workspace directory
RUN mkdir -p /app/task_workspace/output

# Add virtual environment to PATH
ENV PATH="/opt/mineru_venv/bin:$PATH"

# Expose port for API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set the entry point to activate the virtual environment and start the API
ENTRYPOINT ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && python3 start.py"]

# Default command (can be overridden)
CMD []
