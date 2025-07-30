# MinerU CPU Mode Dockerfile
FROM ubuntu:22.04

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV PYTHONUNBUFFERED=1

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
    pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip3 install uv -i https://mirrors.aliyun.com/pypi/simple/ && \
    uv pip install 'mineru[core]' -i https://mirrors.aliyun.com/pypi/simple/"

# Create default configuration for CPU mode
COPY mineru.json /root/mineru.json

# Create working directory
WORKDIR /app

# Add virtual environment to PATH
ENV PATH="/opt/mineru_venv/bin:$PATH"

# Expose port for API
EXPOSE 8000

# Set the entry point to activate the virtual environment
ENTRYPOINT ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && exec \"$@\"", "--"]

# Default command
CMD ["bash"]
