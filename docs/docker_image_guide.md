# 文档转换调度系统 Docker 镜像使用指南

## 镜像信息

### 基本信息
- **镜像名称**: `document-scheduler`
- **版本**: v1.0.0
- **基础镜像**: Ubuntu 22.04
- **镜像大小**: ~1.12GB
- **架构**: x86_64

### 包含组件
- Python 3.10
- FastAPI + Uvicorn
- LibreOffice (完整版)
- 中文字体支持
- PDF处理工具

### 可用标签
- `document-scheduler:latest` - 最新版本
- `document-scheduler:v1.0.0` - 稳定版本 1.0.0
- `document-scheduler:stable` - 稳定版本别名

## 快速开始

### 1. 基础运行
```bash
# 拉取镜像（如果需要）
docker pull document-scheduler:latest

# 运行容器
docker run -d \
  --name document-scheduler \
  -p 8000:8000 \
  -v /path/to/input:/app/test:ro \
  -v /path/to/output:/app/output \
  document-scheduler:latest
```

### 2. 使用Docker Compose（推荐）
```bash
# 使用专用的compose文件
docker-compose -f docker-compose.document-scheduler.yml up -d

# 查看服务状态
docker-compose -f docker-compose.document-scheduler.yml ps

# 查看日志
docker-compose -f docker-compose.document-scheduler.yml logs -f
```

### 3. 健康检查
```bash
# 检查容器状态
docker ps | grep document-scheduler

# 检查API健康状态
curl http://localhost:8000/health
```

## 使用示例

### 单文件转换
```bash
# 创建转换任务
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_markdown",
    "input_path": "/app/test/document.docx",
    "output_path": "/app/output/document.md",
    "priority": "normal"
  }'

# 查询任务状态
curl "http://localhost:8000/api/tasks/1"
```

### 批量转换
```bash
# 批量转换Office文档
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "batch_office_to_markdown",
    "input_path": "/app/test",
    "output_path": "/app/output/batch",
    "params": {"recursive": false}
  }'
```

## 卷挂载说明

### 必需的卷挂载
```bash
-v /host/input:/app/test:ro      # 输入文件目录（只读）
-v /host/output:/app/output      # 输出文件目录（读写）
```

### 可选的卷挂载
```bash
-v /host/logs:/app/logs          # 日志目录
-v /host/temp:/app/temp          # 临时文件目录
-v /host/config:/app/config:ro   # 配置文件目录
```

### 权限设置
```bash
# 确保输出目录有正确的权限
mkdir -p /host/output
chmod 755 /host/output

# 如果遇到权限问题，可以设置更宽松的权限
chmod 777 /host/output
```

## 环境变量配置

### 常用环境变量
```bash
-e API_HOST=0.0.0.0              # API监听地址
-e API_PORT=8000                 # API端口
-e MAX_CONCURRENT_TASKS=3        # 最大并发任务数
-e LOG_LEVEL=INFO                # 日志级别
-e TASK_CHECK_INTERVAL=5         # 任务检查间隔（秒）
```

### 完整示例
```bash
docker run -d \
  --name document-scheduler \
  -p 8000:8000 \
  -e MAX_CONCURRENT_TASKS=5 \
  -e LOG_LEVEL=DEBUG \
  -v /workspace/test:/app/test:ro \
  -v /workspace/output:/app/output \
  document-scheduler:latest
```

## 性能优化

### 资源限制
```bash
# 限制内存和CPU使用
docker run -d \
  --name document-scheduler \
  --memory=2g \
  --cpus=2 \
  -p 8000:8000 \
  -v /workspace/test:/app/test:ro \
  -v /workspace/output:/app/output \
  document-scheduler:latest
```

### 并发调优
```bash
# 根据服务器性能调整并发数
-e MAX_CONCURRENT_TASKS=5        # 高性能服务器
-e MAX_CONCURRENT_TASKS=2        # 低配置服务器
```

## 故障排除

### 常见问题

1. **容器启动失败**
```bash
# 查看容器日志
docker logs document-scheduler

# 检查端口占用
netstat -tlnp | grep 8000
```

2. **权限错误**
```bash
# 检查挂载目录权限
ls -la /host/output

# 修复权限
sudo chown -R 1000:1000 /host/output
```

3. **转换失败**
```bash
# 查看详细日志
docker logs document-scheduler --tail 50

# 检查输入文件是否存在
docker exec document-scheduler ls -la /app/test
```

### 调试模式
```bash
# 启用调试模式
docker run -d \
  --name document-scheduler-debug \
  -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e DEBUG=true \
  -v /workspace/test:/app/test:ro \
  -v /workspace/output:/app/output \
  document-scheduler:latest
```

## 镜像构建

### 从源码构建
```bash
# 克隆项目
git clone <repository-url>
cd document-scheduler

# 构建镜像
docker build -f Dockerfile.document-scheduler -t document-scheduler:custom .

# 运行自定义镜像
docker run -d --name document-scheduler-custom -p 8000:8000 document-scheduler:custom
```

### 自定义构建参数
```bash
# 使用国内镜像源构建
docker build \
  --build-arg PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple/ \
  -f Dockerfile.document-scheduler \
  -t document-scheduler:custom .
```

## 生产环境部署

### 使用Docker Swarm
```bash
# 初始化Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.document-scheduler.yml document-scheduler
```

### 使用Kubernetes
```yaml
# 创建Deployment和Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-scheduler
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-scheduler
  template:
    metadata:
      labels:
        app: document-scheduler
    spec:
      containers:
      - name: document-scheduler
        image: document-scheduler:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: MAX_CONCURRENT_TASKS
          value: "3"
```

## 镜像推送

### 推送到Docker Hub
```bash
# 登录Docker Hub
docker login

# 标记镜像
docker tag document-scheduler:latest username/document-scheduler:v1.0.0

# 推送镜像
docker push username/document-scheduler:v1.0.0
```

### 推送到私有仓库
```bash
# 标记镜像
docker tag document-scheduler:latest registry.company.com/document-scheduler:v1.0.0

# 推送镜像
docker push registry.company.com/document-scheduler:v1.0.0
```

## 安全建议

1. **使用非root用户**: 镜像已配置为使用appuser用户运行
2. **最小权限原则**: 输入目录挂载为只读
3. **网络隔离**: 使用Docker网络进行服务隔离
4. **定期更新**: 定期更新基础镜像和依赖包
5. **扫描漏洞**: 使用工具扫描镜像安全漏洞

```bash
# 扫描镜像漏洞（如果有工具）
docker scan document-scheduler:latest
```
