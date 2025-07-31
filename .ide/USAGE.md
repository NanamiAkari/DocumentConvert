# MinerU GPU Base Image 使用指南

## 快速开始

### 1. 构建镜像

确保您已经下载了MinerU模型文件到 `/root/.cache/modelscope` 目录：

```bash
# 进入.ide目录
cd .ide

# 运行构建脚本
./build.sh
```

### 2. 测试镜像

```bash
# 运行测试脚本验证镜像功能
./test.sh
```

### 3. 推送镜像

```bash
# 推送到仓库
./push.sh
```

## 使用场景

### 场景1: WebIDE开发环境

启动完整的Web开发环境：

```bash
# 方式1: 直接运行
docker run --rm --gpus all -p 8080:8080 \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  code-server --bind-addr 0.0.0.0:8080 --auth none /workspace

# 方式2: 使用docker-compose
cd .ide
docker-compose up -d mineru-webide

# 访问: http://localhost:8080
```

### 场景2: PDF批量转换

```bash
# 创建输入输出目录
mkdir -p input output

# 复制PDF文件到input目录
cp your-files.pdf input/

# 批量转换
docker run --rm --gpus all \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  bash -c "
    for pdf in /input/*.pdf; do
      filename=\$(basename \"\$pdf\" .pdf)
      echo \"转换: \$filename\"
      mineru -p \"\$pdf\" -o \"/output/\$filename.md\"
    done
  "
```

### 场景3: API服务部署

```bash
# 启动API服务
docker run -d --gpus all -p 8000:8000 \
  --name mineru-api \
  -v $(pwd)/data:/data \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  python3 -c "
import uvicorn
from fastapi import FastAPI
from mineru.api import pdf_to_markdown

app = FastAPI()

@app.post('/convert')
async def convert_pdf(input_path: str, output_path: str):
    try:
        result = pdf_to_markdown(input_path, output_path)
        return {'success': True, 'result': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get('/health')
async def health():
    return {'status': 'healthy'}

uvicorn.run(app, host='0.0.0.0', port=8000)
"

# 测试API
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"input_path": "/data/test.pdf", "output_path": "/data/test.md"}'
```

### 场景4: 交互式开发

```bash
# 进入容器进行交互式开发
docker run --rm --gpus all -it \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  /bin/bash

# 在容器内
cd /workspace
python3

# Python交互式环境
>>> from mineru.api import pdf_to_markdown
>>> result = pdf_to_markdown('input.pdf', 'output.md')
>>> print(result)
```

## 高级配置

### 自定义MinerU配置

```bash
# 创建自定义配置文件
cat > custom-mineru.json << EOF
{
  "model": {
    "layout": {
      "model_path": "/root/.cache/modelscope/opendatalab/PDF-Extract-Kit/models/Layout/LayoutLMv3",
      "device": "cuda",
      "batch_size": 16
    },
    "formula": {
      "model_path": "/root/.cache/modelscope/opendatalab/PDF-Extract-Kit/models/Formula/UniMERNet",
      "device": "cuda"
    },
    "table": {
      "model_path": "/root/.cache/modelscope/opendatalab/PDF-Extract-Kit/models/Table/StructEqTable",
      "device": "cuda"
    },
    "ocr": {
      "model_path": "/root/.cache/modelscope/opendatalab/PDF-Extract-Kit/models/OCR/PaddleOCR",
      "device": "cuda"
    }
  },
  "device_mode": "cuda"
}
EOF

# 使用自定义配置
docker run --rm --gpus all \
  -v $(pwd)/custom-mineru.json:/root/mineru.json \
  -v $(pwd):/workspace \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  mineru -p /workspace/input.pdf -o /workspace/output.md
```

### 多GPU支持

```bash
# 使用多个GPU
docker run --rm --gpus all \
  -e CUDA_VISIBLE_DEVICES=0,1 \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  python3 -c "
import torch
print(f'Available GPUs: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
"
```

### 内存优化

```bash
# 限制GPU内存使用
docker run --rm --gpus all \
  --memory=16g \
  --shm-size=8g \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  python3 -c "
import torch
torch.cuda.set_per_process_memory_fraction(0.8)  # 使用80%的GPU内存
# 您的代码
"
```

## 开发扩展

### 基于此镜像开发新应用

```dockerfile
# Dockerfile
FROM docker.cnb.cool/aiedulab/library/mineru:latest

# 安装额外依赖
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip install fastapi uvicorn sqlalchemy"

# 复制应用代码
COPY app/ /app/
COPY requirements.txt /app/

# 安装应用依赖
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    cd /app && pip install -r requirements.txt"

# 设置工作目录
WORKDIR /app

# 启动应用
CMD ["python3", "main.py"]
```

### 集成到现有项目

```yaml
# docker-compose.yml
version: '3.8'
services:
  mineru-service:
    image: docker.cnb.cool/aiedulab/library/mineru:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./data:/data
    environment:
      - MINERU_CONFIG_PATH=/data/mineru.json
    command: python3 /data/your_service.py
```

## 性能优化

### 批处理优化

```python
# batch_convert.py
import os
from pathlib import Path
from mineru.api import pdf_to_markdown
import torch

def batch_convert(input_dir, output_dir, batch_size=4):
    """批量转换PDF文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    pdf_files = list(input_path.glob("*.pdf"))
    
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i+batch_size]
        
        for pdf_file in batch:
            output_file = output_path / f"{pdf_file.stem}.md"
            try:
                result = pdf_to_markdown(str(pdf_file), str(output_file))
                print(f"✅ {pdf_file.name} -> {output_file.name}")
            except Exception as e:
                print(f"❌ {pdf_file.name}: {e}")
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

if __name__ == "__main__":
    batch_convert("/input", "/output")
```

### 监控和日志

```bash
# 启动带监控的容器
docker run -d --gpus all \
  --name mineru-monitor \
  -v $(pwd)/logs:/logs \
  docker.cnb.cool/aiedulab/library/mineru:latest \
  bash -c "
    # 启动GPU监控
    nvidia-smi dmon -s pucvmet -d 10 > /logs/gpu_monitor.log &
    
    # 启动您的应用
    python3 your_app.py 2>&1 | tee /logs/app.log
  "

# 查看日志
docker logs -f mineru-monitor
tail -f logs/gpu_monitor.log
```

## 故障排除

### 常见问题

1. **GPU内存不足**
```bash
# 检查GPU使用情况
docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest nvidia-smi

# 清理GPU内存
docker run --rm --gpus all docker.cnb.cool/aiedulab/library/mineru:latest \
  python3 -c "import torch; torch.cuda.empty_cache(); print('GPU memory cleared')"
```

2. **模型加载失败**
```bash
# 检查模型文件
docker run --rm docker.cnb.cool/aiedulab/library/mineru:latest \
  find /root/.cache/modelscope -name "*.bin" -o -name "*.pth" | head -10
```

3. **WebIDE无法访问**
```bash
# 检查端口占用
netstat -tulpn | grep 8080

# 检查容器状态
docker ps | grep mineru
```

## 最佳实践

1. **资源管理**: 合理分配GPU内存，避免OOM
2. **批处理**: 对大量文件使用批处理模式
3. **监控**: 监控GPU使用率和内存占用
4. **缓存**: 合理使用模型缓存，避免重复加载
5. **日志**: 记录详细的转换日志便于调试

## 支持

如需帮助，请提供：
- 系统环境信息
- GPU型号和驱动版本
- 错误日志和堆栈跟踪
- 输入文件信息
- 复现步骤
