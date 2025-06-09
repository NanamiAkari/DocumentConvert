# Use the official Ubuntu base image
FROM ubuntu:22.04

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8

# Update the package list and install necessary packages
RUN apt-get update && \
    apt-get install -y \
        software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.10 \
        python3.10-venv \
        python3.10-distutils \
        python3-pip \
        wget \
        git \
        libgl1 \
        libreoffice \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        ttf-mscorefonts-installer \
        fontconfig \
        libglib2.0-0 \
        libxrender1 \
        libsm6 \
        libxext6 \
        unzip \
        lsof \
        curl \
        vim \
        nano \
        openssh-server \
        libglib2.0-0 \
        poppler-utils \
        && rm -rf /var/lib/apt/lists/*

# VSC
RUN curl -fsSL https://code-server.dev/install.sh | sh -s -- --version 4.96.2 &&\
        code-server --install-extension redhat.vscode-yaml &&\
        code-server --install-extension tencent-cloud.coding-copilot &&\
        code-server --install-extension waderyan.gitblame &&\
        code-server --install-extension mhutchie.git-graph &&\
        code-server --install-extension donjayamanne.githistory &&\
        code-server --install-extension cloudstudio.live-server &&\
        code-server --install-extension cnbcool.cnb-welcome
    

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Create a virtual environment for MinerU
RUN python3 -m venv /opt/mineru_venv

# Copy the configuration file template and install magic-pdf latest
RUN /bin/bash -c "wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/magic-pdf.template.json && \
    cp magic-pdf.template.json /root/magic-pdf.json && \
    source /opt/mineru_venv/bin/activate && \
    pip3 install --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple && \
    pip3 install -U magic-pdf[full] -i https://mirrors.cloud.tencent.com/pypi/simple"

# Download models and update the configuration file
RUN /bin/bash -c "pip3 install modelscope -i https://mirrors.cloud.tencent.com/pypi/simple && \
    wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models.py -O download_models.py && \
    python3 download_models.py && \
    sed -i 's|cpu|cuda|g' /root/magic-pdf.json"

RUN echo 'source /opt/mineru_venv/bin/activate' >> /root/.bashrc

# Set the entry point to activate the virtual environment and run the command line tool
ENTRYPOINT ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && exec \"$@\"", "--"]
