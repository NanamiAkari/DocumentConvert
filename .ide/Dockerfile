# MinerU GPU Base Image with WebIDE Support
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Update the package list and install necessary packages
RUN apt-get update && \
    apt-get install -y \
        software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-distutils \
        python3-pip \
        wget \
        git \
        libgl1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libreoffice \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        ttf-mscorefonts-installer \
        fontconfig \
        libxrender1 \
        unzip \
        lsof \
        curl \
        vim \
        nano \
        openssh-server \
        poppler-utils \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Install VSCode Server and extensions for WebIDE
RUN curl -fsSL https://code-server.dev/install.sh | sh -s -- --version 4.96.2 && \
    code-server --install-extension redhat.vscode-yaml && \
    code-server --install-extension tencent-cloud.coding-copilot && \
    code-server --install-extension waderyan.gitblame && \
    code-server --install-extension mhutchie.git-graph && \
    code-server --install-extension donjayamanne.githistory && \
    code-server --install-extension cloudstudio.live-server && \
    code-server --install-extension cnbcool.cnb-welcome && \
    code-server --install-extension ms-python.python && \
    code-server --install-extension ms-python.pylint

# Set Python 3.11 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Create a virtual environment for MinerU
RUN python3 -m venv /opt/mineru_venv

# Activate virtual environment and install PyTorch with CUDA support
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip3 install --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple && \
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"

# Install MinerU with full dependencies (latest version 2.1.9+)
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip3 install 'mineru[core]>=2.1.9' -i https://mirrors.cloud.tencent.com/pypi/simple && \
    pip3 install modelscope -i https://mirrors.cloud.tencent.com/pypi/simple"

# Download MinerU models using the official model download tool
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    echo 'Downloading MinerU models using modelscope...' && \
    mineru-models-download -s modelscope -m pipeline && \
    echo 'Model download completed'"

# Verify model installation and GPU support
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    python3 -c 'import torch; print(torch.__version__)' && \
    echo 'Checking MinerU installation...' && \
    python3 -c 'import mineru; print(\"MinerU OK\")' && \
    echo 'Checking mineru command...' && \
    mineru --help > /dev/null && \
    echo 'Model verification completed'"

# Set up environment for MinerU
ENV MINERU_MODEL_SOURCE=modelscope

# Add virtual environment activation to bashrc
RUN echo 'source /opt/mineru_venv/bin/activate' >> /root/.bashrc

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory
WORKDIR /workspace

# Expose ports for WebIDE and API services
EXPOSE 8080 8000 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import torch; print('PyTorch available:', True)" || exit 1

# Set the entry point to activate the virtual environment
ENTRYPOINT ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && exec \"$@\"", "--"]

# Default command
CMD ["/bin/bash"]
