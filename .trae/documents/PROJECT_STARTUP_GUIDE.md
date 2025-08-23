# PROJECT\_STARTUP\_GUIDE

本指南基于当前代码库实际实现，给出项目运行所需的服务清单、端口号，以及本地与容器两种启动方式的完整步骤与命令（含执行顺序）。

## 一、服务清单与端口

必需/可选服务及其端口如下：

* 文档转换 API（FastAPI + Uvicorn）

  * 端口：8000/TCP（固定，支持通过环境变量 PORT 自定义，默认 8000）

  * 作用：对外提供统一的任务创建、查询、统计与健康检查接口

  * 代码入口：main.py（引入 api/unified\_document\_api.py 路由）

* S3 兼容对象存储（可选，生产可接入外部 S3，开发可使用 MinIO）

  * MinIO 服务（本地开发可用）：

    * API 端口：9000/TCP

    * 控制台端口：9001/TCP

  * 作用：任务输入文件下载与输出文件上传所需的对象存储

* 数据库（默认内置 SQLite，无需独立服务；可选使用 MySQL）

  * SQLite：默认使用本地文件（无需端口）

  * 可选 MySQL：3306/TCP（如采用 MySQL，请配置异步驱动 DSN）

* 本地二进制/库依赖（无端口，仅作为本机依赖）

  * LibreOffice（office\_to\_pdf）

  * MinerU（pdf\_to\_markdown；容器镜像已内置，本地开发需自行安装）

备注：健康检查接口同时提供 /api/health 与 /health 两个路径。

## 二、环境准备

* Python 3.9+

* 可选 GPU（MinerU 可用 CPU，GPU 仅加速）

* 建议在中国大陆环境下使用腾讯云 PyPI 镜像加速

复制环境变量模板并按需调整：

```bash
cp .env.example .env
# 按需修改：S3_ENDPOINT/S3_ACCESS_KEY/S3_SECRET_KEY、DATABASE_TYPE/DATABASE_URL、PORT/HOST 等
```

关键环境变量说明（节选）：

* S3\_ENDPOINT（如本机 MinIO 则为 <http://localhost:9000）>

* DATABASE\_TYPE（默认 sqlite，可改 mysql）

* DATABASE\_URL（默认 sqlite，本地 SQLite 示例：sqlite+aiosqlite:///./document\_tasks.db）

* PORT（默认 8000）

## 三、启动方式 A：Docker Compose（推荐一键启动）

说明：仓库已提供 docker-compose.yml。包含：

* document-converter（对外暴露 8000:8000）

* 可选 minio（对外暴露 9000:9000、9001:9001）

注意：compose 文件中的 healthcheck 指向 /health，代码同时提供 /health 与 /api/health，均可用。

1）启动可选 MinIO（如需本地 S3）

```bash
docker compose up -d minio
```

默认账号/密码：minioadmin/minioadmin（由 compose 环境变量设置）

2）启动文档转换 API 服务

```bash
docker compose up -d document-converter
```

3）健康检查（确认服务正常）

```bash
curl "http://localhost:8000/health"
# 或
curl "http://localhost:8000/api/health"
```

4）快速功能验证（举例：创建任务）

```bash
# PDF 转 Markdown（S3 输入示例）
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=documents" \
  -F "file_path=reports/annual_report.pdf" \
  -F "platform=demo" \
  -F "priority=normal"

# Office 转 PDF（本地上传示例）
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "file_upload=@/absolute/path/to/file.docx" \
  -F "platform=demo" \
  -F "priority=high"
```

5）查询任务

```bash
# 列表
curl "http://localhost:8000/api/tasks?limit=10"

# 统计
curl "http://localhost:8000/api/statistics"
```

## 四、启动方式 B：本地 Python 运行

1）创建虚拟环境并安装依赖（使用腾讯云镜像）

```bash
python -m venv venv
source venv/bin/activate
pip install -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt
```

2）本地依赖（如需 Office->PDF 或 PDF->Markdown）

* LibreOffice（Linux 示例）

```bash
sudo apt-get update && sudo apt-get install -y libreoffice
```

* MinerU（容器镜像已内置；若本地执行 pdf\_to\_markdown，需要安装 MinerU）

```bash
pip install -i https://mirrors.cloud.tencent.com/pypi/simple "mineru[core]==2.1.9"
```

3）环境变量

```bash
cp .env.example .env
# 本地 MinIO 场景：
# S3_ENDPOINT=http://localhost:9000
# S3_ACCESS_KEY=minioadmin
# S3_SECRET_KEY=minioadmin
# 如使用 SQLite：DATABASE_TYPE=sqlite
# DATABASE_URL=sqlite+aiosqlite:///./document_tasks.db
```

4）启动 API（二选一）

```bash
# 方式一：直接运行主程序（读取 .env，默认端口 8000）
python main.py

# 方式二：使用 Uvicorn 显式启动
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info

# 方式三：使用提供的启动脚本（将日志输出到 /workspace/service_output.log）
python start_service.py
```

5）健康检查与验证

```bash
# 健康检查
curl "http://localhost:8000/health"
# 或
curl "http://localhost:8000/api/health"

# 创建任务（同上 Docker 示例）
# …（略）
```

## 五、可选依赖：本地快速启动 MinIO 与 MySQL（无需修改代码）

* MinIO（独立命令行启动）

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -v $(pwd)/data/minio:/data \
  minio/minio server /data --console-address ":9001"
```

* MySQL 8.0（如需将 DATABASE\_TYPE 切换为 mysql）

```bash
docker run -d --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=document_tasks \
  mysql:8.0

# 数据库连接串（示例，需与 .env 对应）
# DATABASE_TYPE=mysql
# DATABASE_URL=mysql+aiomysql://root:your_root_password@localhost:3306/document_tasks
```

## 六、执行顺序（总览）

* Docker 方式：

  1. 可选：启动 MinIO → docker compose up -d minio
  2. 启动文档转换 API → docker compose up -d document-converter
  3. 健康检查 → curl <http://localhost:8000/health（或> /api/health）
  4. 创建与查询任务（curl 示例见上）

* 本地 Python 方式：

  1. 创建虚拟环境并安装依赖
  2. 安装本地依赖（LibreOffice / MinerU，按需）
  3. 准备 .env（S3 / DB / 端口等）
  4. 启动 API（python main.py 或 uvicorn）
  5. 健康检查与功能验证

## 七、常见问题

* 健康检查 404：请使用 /health 或 /api/health

* S3 连接失败：检查 S3\_ENDPOINT/ACCESS\_KEY/SECRET\_KEY；本地 MinIO 用 <http://localhost:9000>

* SQLite 驱动：异步驱动 DSN 推荐使用 sqlite+aiosqlite:///…

* Office 转换失败：确认已安装 LibreOffice，且可执行路径为 /usr/bin/libreoffice（可在 .env 中覆盖）

