# 文档转换调度系统部署指南

## 部署方式

### 1. Docker Compose 部署（推荐）

#### 基础部署
```bash
# 克隆项目
git clone <repository-url>
cd document-scheduler

# 复制环境变量配置
cp .env.example .env

# 编辑配置文件（可选）
vim .env

# 启动服务
docker-compose -f docker-compose.document-scheduler.yml up -d

# 查看服务状态
docker-compose -f docker-compose.document-scheduler.yml ps

# 查看日志
docker-compose -f docker-compose.document-scheduler.yml logs -f
```

#### 带Redis缓存的部署
```bash
# 启动包含Redis的服务
docker-compose -f docker-compose.document-scheduler.yml --profile with-redis up -d
```

#### 带数据库的完整部署
```bash
# 启动包含PostgreSQL的完整服务
docker-compose -f docker-compose.document-scheduler.yml --profile with-database up -d
```

### 2. 本地开发部署

#### 环境准备
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装LibreOffice
# Ubuntu/Debian:
sudo apt-get install libreoffice

# CentOS/RHEL:
sudo yum install libreoffice

# macOS:
brew install --cask libreoffice
```

#### 启动服务
```bash
# 直接启动API服务
python start.py

# 或者启动演示任务
python start.py demo
```

### 3. 生产环境部署

#### 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间用于大文件处理
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

#### 使用systemd服务
```ini
# /etc/systemd/system/document-scheduler.service
[Unit]
Description=Document Scheduler API
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/document-scheduler
Environment=PATH=/opt/document-scheduler/venv/bin
ExecStart=/opt/document-scheduler/venv/bin/python start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable document-scheduler
sudo systemctl start document-scheduler
sudo systemctl status document-scheduler
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| API_HOST | 0.0.0.0 | API服务监听地址 |
| API_PORT | 8000 | API服务端口 |
| MAX_CONCURRENT_TASKS | 3 | 最大并发任务数 |
| TASK_CHECK_INTERVAL | 5 | 任务检查间隔（秒） |
| LIBREOFFICE_PATH | /usr/bin/libreoffice | LibreOffice路径 |

### 性能调优

#### 并发任务数调整
```bash
# 根据服务器性能调整并发数
export MAX_CONCURRENT_TASKS=5
```

#### 内存优化
```bash
# 设置Python内存限制
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2
```

#### 磁盘空间管理
```bash
# 定期清理临时文件
find /workspace/temp -type f -mtime +1 -delete
```

## 监控和日志

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查队列统计
curl http://localhost:8000/api/stats
```

### 日志管理
```bash
# 查看实时日志
docker-compose -f docker-compose.document-scheduler.yml logs -f document-scheduler

# 查看错误日志
docker-compose -f docker-compose.document-scheduler.yml logs document-scheduler | grep ERROR
```

### 性能监控
```bash
# 监控容器资源使用
docker stats document-scheduler

# 监控磁盘使用
df -h /workspace/output
```

## 故障排除

### 常见问题

1. **LibreOffice转换失败**
   - 检查LibreOffice是否正确安装
   - 确认文件权限正确
   - 检查磁盘空间是否充足

2. **任务队列阻塞**
   - 重启服务：`docker-compose restart document-scheduler`
   - 检查并发任务数设置
   - 查看系统资源使用情况

3. **文件转换超时**
   - 增加转换超时时间
   - 检查文件大小是否超限
   - 优化服务器性能

### 调试模式
```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=DEBUG

# 重启服务
docker-compose -f docker-compose.document-scheduler.yml restart
```

## 备份和恢复

### 数据备份
```bash
# 备份输出文件
tar -czf backup-$(date +%Y%m%d).tar.gz /workspace/output

# 备份数据库（如果使用）
docker exec document-scheduler-postgres pg_dump -U scheduler document_scheduler > backup.sql
```

### 数据恢复
```bash
# 恢复输出文件
tar -xzf backup-20250731.tar.gz -C /

# 恢复数据库
docker exec -i document-scheduler-postgres psql -U scheduler document_scheduler < backup.sql
```

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
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - document-scheduler
```

### 集群部署
使用Docker Swarm或Kubernetes进行集群部署，支持高可用和负载均衡。

## 安全建议

1. **网络安全**
   - 使用HTTPS
   - 配置防火墙
   - 限制API访问

2. **文件安全**
   - 验证上传文件类型
   - 限制文件大小
   - 定期清理临时文件

3. **访问控制**
   - 配置API密钥
   - 实施IP白名单
   - 监控异常访问
