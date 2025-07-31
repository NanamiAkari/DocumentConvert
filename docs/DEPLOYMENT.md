# Document Scheduler 部署指南

## 概述

Document Scheduler 是一个基于 MinerU 2.0 的文档转换调度系统，支持 Office 文档和 PDF 文件转换为 Markdown 格式。

## 系统要求

### 硬件要求
- **GPU模式（推荐）**: NVIDIA GPU，显存 >= 8GB
- **CPU模式**: 多核CPU，内存 >= 16GB
- 存储空间: >= 50GB（包含模型文件）

### 软件要求
- Docker >= 20.10
- Docker Compose >= 2.0
- NVIDIA Docker（GPU模式）

## 快速部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd document-scheduler
```

### 2. 构建镜像
```bash
./build.sh
```

### 3. 启动服务
```bash
# GPU模式（推荐）
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 验证部署
```bash
# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

## 配置说明

### 环境变量
- `MINERU_MODEL_SOURCE`: 模型源，默认 `modelscope`
- `CUDA_VISIBLE_DEVICES`: GPU设备，默认 `0`
- `PYTHONUNBUFFERED`: Python输出缓冲，默认 `1`

### 目录映射
- `./test:/app/test:ro` - 输入文件目录（只读）
- `./output:/app/output` - 输出文件目录
- `./logs:/app/logs` - 日志目录
- `model-cache:/root/.cache/modelscope` - 模型缓存

## API 使用

### 创建转换任务
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "pdf_to_markdown",
    "input_path": "/app/test/document.pdf",
    "output_path": "/app/output/document.md",
    "priority": "normal"
  }'
```

### 查询任务状态
```bash
curl http://localhost:8000/api/tasks/{task_id}
```

### 支持的转换类型
- `pdf_to_markdown` - PDF转Markdown（使用MinerU）
- `office_to_markdown` - Office文档转Markdown
- `office_to_pdf` - Office文档转PDF

## 性能优化

### GPU内存管理
系统会自动管理GPU内存，包括：
- 任务前清理GPU缓存
- 任务后释放GPU内存
- 错误处理时的内存清理

### 并发处理
- 默认最大并发任务数: 3
- 可通过环境变量调整
- 支持任务优先级队列

## 故障排除

### 常见问题

1. **GPU内存不足**
   ```bash
   # 检查GPU使用情况
   nvidia-smi
   
   # 重启容器释放内存
   docker-compose restart
   ```

2. **模型下载失败**
   ```bash
   # 检查网络连接
   docker-compose exec document-scheduler ping mirrors.cloud.tencent.com
   
   # 手动下载模型
   docker-compose exec document-scheduler python3 -c "
   from mineru.cli.models_download import download_models
   download_models()
   "
   ```

3. **转换失败**
   ```bash
   # 查看详细日志
   docker-compose logs document-scheduler
   
   # 检查输入文件
   docker-compose exec document-scheduler ls -la /app/test/
   ```

### 日志分析
```bash
# 实时日志
docker-compose logs -f

# 错误日志
docker-compose logs | grep ERROR

# 特定时间段日志
docker-compose logs --since="2024-01-01T00:00:00"
```

## 监控和维护

### 健康检查
系统提供多层健康检查：
- Docker容器健康检查
- API服务健康检查
- 任务处理器状态检查

### 备份和恢复
```bash
# 备份输出文件
tar -czf output-backup-$(date +%Y%m%d).tar.gz output/

# 备份模型缓存
docker run --rm -v model-cache:/data -v $(pwd):/backup alpine \
  tar -czf /backup/model-cache-backup.tar.gz -C /data .
```

### 更新部署
```bash
# 停止服务
docker-compose down

# 更新代码
git pull

# 重新构建
./build.sh

# 启动服务
docker-compose up -d
```

## 安全考虑

### 网络安全
- 默认只绑定本地端口
- 生产环境建议使用反向代理
- 启用HTTPS和认证

### 文件安全
- 输入目录设置为只读
- 定期清理临时文件
- 限制文件大小和类型

## 扩展部署

### 多实例部署
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  document-scheduler:
    # ... 基础配置
    deploy:
      replicas: 3
```

### 负载均衡
```nginx
# nginx.conf
upstream document_scheduler {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://document_scheduler;
    }
}
```

## 支持和反馈

如遇问题，请提供以下信息：
1. 系统环境（OS、Docker版本、GPU型号）
2. 错误日志
3. 输入文件类型和大小
4. 复现步骤

---

更多信息请参考：
- [API文档](http://localhost:8000/docs)
- [MinerU官方文档](https://github.com/opendatalab/MinerU)
- [项目README](../README.md)
