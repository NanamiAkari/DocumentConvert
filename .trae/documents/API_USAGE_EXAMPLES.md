# 文档转换服务API使用指南

本文档提供完整的API使用示例，包括详细的curl命令、响应格式和实际使用场景。

## 🌐 API基础信息

* **基础URL**: `http://localhost:8000` (本地部署) 或 `http://your-server:33081` (生产环境)

* **API版本**: v2.0

* **文档地址**: `http://localhost:8000/docs` (Swagger UI)

* **内容类型**: `application/json` 或 `multipart/form-data`

## 🚀 快速开始

### 1. 服务健康检查

检查服务是否正常运行，获取系统状态信息。

```bash
curl -s http://localhost:8000/health
```

**响应示例**:

```json
{
  "status": "healthy",
  "message": "Document Conversion Service is running",
  "timestamp": "2025-08-09T12:00:00Z",
  "processor_status": {
    "running": true,
    "total_tasks": 25,
    "active_tasks": 0,
    "completed_tasks": 23,
    "failed_tasks": 2
  },
  "queue_status": {
    "fetch_queue": 25,
    "task_processing_queue": 0,
    "high_priority_queue": 0,
    "normal_priority_queue": 0,
    "low_priority_queue": 0,
    "update_queue": 0,
    "cleanup_queue": 0,
    "callback_queue": 0
  },
  "workspace_status": {
    "base_workspace_dir": "/app/task_workspace",
    "temp_files_dir": "/app/temp_files",
    "active_task_workspaces": 25,
    "temp_files_count": 0,
    "total_workspace_size": 64200518,
    "temp_files_size": 0
  }
}
```

**状态说明**:

* `status`: `healthy` 表示服务正常，`unhealthy` 表示服务异常

* `processor_status`: 任务处理器状态和统计信息

* `queue_status`: 各个队列的任务数量

* `workspace_status`: 工作空间使用情况

## 📄 任务创建

### 2.1 PDF转Markdown任务

将PDF文件转换为Markdown格式，同时提取图片和结构化数据。

```bash
curl -X POST "http://localhost:33081/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=gaojiaqi" \
  -F "file_path=Gemini for Google Workspace 提示指南 101（Gemini 工作区提示指南 101）.pdf" \
  -F "priority=high"
```

**参数说明**:

* `task_type`: 固定值 `pdf_to_markdown`

* `bucket_name`: S3存储桶名称 (例如: `documents`, `ai-file`, `reports`)

* `file_path`: 文件在S3中的路径 (例如: `reports/annual_report.pdf`)

* `platform`: 平台标识，用于任务分类 (例如: `web-app`, `api-client`)

* `priority`: 任务优先级 (`high`, `normal`, `low`)

**响应示例**:

```json
{
  "task_id": 26,
  "message": "Document conversion task 26 created successfully",
  "status": "pending"
}
```

**输出文件**:

* `annual_report.md`: 主要的Markdown文件

* `annual_report.json`: 文档结构化数据

* `images/`: 提取的图片文件夹

### 2.2 Office转PDF任务

将Office文档(Word/Excel/PowerPoint)转换为PDF格式。

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "bucket_name=documents" \
  -F "file_path=presentations/quarterly_review.pptx" \
  -F "platform=your-platform" \
  -F "priority=normal"
```

**支持的文件格式**:

* Word: `.doc`, `.docx`

* Excel: `.xls`, `.xlsx`

* PowerPoint: `.ppt`, `.pptx`

**响应示例**:

```json
{
  "task_id": 27,
  "message": "Document conversion task 27 created successfully",
  "status": "pending"
}
```

### 2.3 Office转Markdown任务 (两步转换)

将Office文档先转换为PDF，再转换为Markdown，适用于复杂格式的文档。

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_markdown" \
  -F "bucket_name=documents" \
  -F "file_path=reports/financial_report.xlsx" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**处理流程**:

1. Office文档 → PDF (使用LibreOffice)
2. PDF → Markdown (使用MinerU)

**输出文件**:

* `financial_report.md`: Markdown文件

* `financial_report.json`: 结构化数据

* `images/`: 图片和图表

## 🔍 任务查询和状态监控

### 3.1 查询特定任务详情

根据任务ID获取任务的完整状态信息，包括输入输出路径、处理时间、S3 URLs等。

```bash
curl -s "http://localhost:8000/api/tasks/26"
```

**响应示例 - 已完成的PDF转Markdown任务**:

```json
{
  "id": 26,
  "task_type": "pdf_to_markdown",
  "status": "completed",
  "priority": "high",
  "bucket_name": "documents",
  "file_path": "reports/annual_report.pdf",
  "platform": "your-platform",
  "input_path": "/app/task_workspace/task_26/input/annual_report.pdf",
  "output_path": "/app/task_workspace/task_26/output/annual_report.md",
  "output_url": "s3://ai-file/documents/annual_report/markdown/annual_report.md",
  "s3_urls": [
    "s3://ai-file/documents/annual_report/markdown/annual_report.md",
    "s3://ai-file/documents/annual_report/markdown/annual_report.json",
    "s3://ai-file/documents/annual_report/markdown/images/chart1.jpg",
    "s3://ai-file/documents/annual_report/markdown/images/table1.jpg",
    "s3://ai-file/documents/annual_report/markdown/images/diagram1.jpg"
  ],
  "file_size_bytes": 1048576,
  "created_at": "2025-08-09T10:00:00",
  "started_at": "2025-08-09T10:01:00",
  "completed_at": "2025-08-09T10:03:30",
  "task_processing_time": 150.5,
  "result": {
    "success": true,
    "conversion_type": "pdf_to_markdown",
    "upload_result": {
      "success": true,
      "total_files": 5,
      "total_size": 2097152
    }
  },
  "error_message": null
}
```

**响应字段说明**:

* `output_url`: 主要输出文件的S3路径 (通常是.md文件)

* `s3_urls`: 所有输出文件的S3路径列表

* `task_processing_time`: 任务处理耗时(秒)

* `file_size_bytes`: 输入文件大小

* `result.upload_result.total_files`: 上传的文件总数

* `result.upload_result.total_size`: 上传的文件总大小

**响应示例 - 失败的任务**:

```json
{
  "id": 27,
  "task_type": "pdf_to_markdown",
  "status": "failed",
  "priority": "normal",
  "bucket_name": "documents",
  "file_path": "reports/missing_file.pdf",
  "platform": "your-platform",
  "created_at": "2025-08-09T11:00:00",
  "started_at": "2025-08-09T11:01:00",
  "failed_at": "2025-08-09T11:01:30",
  "error_message": "Failed to download file from S3: NoSuchKey - The specified key does not exist.",
  "retry_count": 2
}
```

### 3.2 查询任务列表

支持多种过滤条件的任务列表查询，用于监控和管理任务。

#### 基础查询

```bash
# 查询所有任务 (默认返回最近20个)
curl -s "http://localhost:8000/api/tasks"
```

#### 按状态过滤

```bash
# 查询已完成的任务
curl -s "http://localhost:8000/api/tasks?status=completed&limit=10"

# 查询失败的任务
curl -s "http://localhost:8000/api/tasks?status=failed"

# 查询正在处理的任务
curl -s "http://localhost:8000/api/tasks?status=processing"

# 查询等待处理的任务
curl -s "http://localhost:8000/api/tasks?status=pending"
```

#### 按任务类型过滤

```bash
# 查询PDF转Markdown任务
curl -s "http://localhost:8000/api/tasks?task_type=pdf_to_markdown&limit=5"

# 查询Office转PDF任务
curl -s "http://localhost:8000/api/tasks?task_type=office_to_pdf"

# 查询Office转Markdown任务
curl -s "http://localhost:8000/api/tasks?task_type=office_to_markdown"
```

#### 组合过滤和分页

```bash
# 查询已完成的PDF转Markdown任务，按时间倒序
curl -s "http://localhost:8000/api/tasks?status=completed&task_type=pdf_to_markdown&limit=10"

# 分页查询 (第2页，每页10条)
curl -s "http://localhost:8000/api/tasks?offset=10&limit=10"

# 查询特定平台的任务
curl -s "http://localhost:8000/api/tasks?platform=web-app&limit=20"

# 查询高优先级任务
curl -s "http://localhost:8000/api/tasks?priority=high"
```

**响应示例**:

```json
{
  "tasks": [
    {
      "id": 25,
      "task_type": "pdf_to_markdown",
      "status": "completed",
      "priority": "high",
      "bucket_name": "documents",
      "file_path": "reports/annual_report.pdf",
      "platform": "web-app",
      "output_url": "s3://ai-file/documents/annual_report/markdown/annual_report.md",
      "created_at": "2025-08-09T11:42:53",
      "started_at": "2025-08-09T11:42:56",
      "completed_at": "2025-08-09T11:43:18",
      "task_processing_time": 21.89,
      "file_size_bytes": 577084
    },
    {
      "id": 24,
      "task_type": "office_to_pdf",
      "status": "completed",
      "priority": "normal",
      "bucket_name": "documents",
      "file_path": "presentations/quarterly.pptx",
      "platform": "api-client",
      "output_url": "s3://ai-file/documents/quarterly/pdf/quarterly.pdf",
      "created_at": "2025-08-09T11:41:55",
      "completed_at": "2025-08-09T11:42:08",
      "task_processing_time": 7.80,
      "file_size_bytes": 436736
    }
  ],
  "total": 25,
  "offset": 0,
  "limit": 20,
  "filters": {
    "status": "completed",
    "task_type": null,
    "priority": null,
    "platform": null
  }
}
```

**响应字段说明**:

* `tasks`: 任务列表数组

* `total`: 符合条件的任务总数

* `offset`: 当前分页偏移量

* `limit`: 当前分页大小

* `filters`: 应用的过滤条件

## 📁 S3路径规则详解

系统采用标准化的S3路径规则，确保文件组织清晰、易于管理。

### 4.1 输入文件路径格式

```
s3://{bucket_name}/{file_path}
```

**示例**:

* `s3://documents/reports/annual_report.pdf`

* `s3://presentations/2024/quarterly_review.pptx`

* `s3://ai-file/test/sample/document.pdf`

### 4.2 输出文件路径格式

```
s3://ai-file/{original_bucket}/{file_name_without_ext}/{conversion_type}/{output_files}
```

**路径组成说明**:

* `ai-file`: 固定的输出存储桶

* `{original_bucket}`: 原始文件所在的存储桶名称

* `{file_name_without_ext}`: 原始文件名(去掉扩展名)

* `{conversion_type}`: 转换类型目录 (`pdf`, `markdown`)

* `{output_files}`: 具体的输出文件

### 4.3 路径转换示例

#### PDF转Markdown示例

```
输入: s3://documents/reports/annual_report.pdf
输出: s3://ai-file/documents/annual_report/markdown/
      ├── annual_report.md          # 主要Markdown文件
      ├── annual_report.json        # 结构化数据
      └── images/                   # 提取的图片
          ├── chart_1.jpg
          ├── table_1.jpg
          └── diagram_1.jpg
```

#### Office转PDF示例

```
输入: s3://presentations/2024/quarterly_review.pptx
输出: s3://ai-file/presentations/quarterly_review/pdf/
      └── quarterly_review.pdf      # 转换后的PDF文件
```

#### Office转Markdown示例 (两步转换)

```
输入: s3://documents/financial_report.xlsx
中间: s3://ai-file/documents/financial_report/pdf/financial_report.pdf
输出: s3://ai-file/documents/financial_report/markdown/
      ├── financial_report.md
      ├── financial_report.json
      └── images/
          └── charts/
```

### 4.4 特殊路径处理

#### 嵌套目录结构

```
输入: s3://company/dept/team/project/document.pdf
输出: s3://ai-file/company/document/markdown/document.md
```

> 注意: 系统会提取文件名作为主目录，忽略中间的目录结构

#### 中文文件名支持

```
输入: s3://test/杭电申报-428定.doc
输出: s3://ai-file/test/杭电申报-428定/pdf/杭电申报-428定.pdf
```

#### ai-file存储桶内的文件

```
输入: s3://ai-file/test/sample/document.pdf
解析: 原始bucket=test, 文件名=document
输出: s3://ai-file/test/document/markdown/document.md
```

### 4.5 获取转换结果的S3路径

#### 从任务详情获取

```bash
# 查询任务详情
curl -s "http://localhost:8000/api/tasks/26" | jq '.s3_urls'

# 输出示例
[
  "s3://ai-file/documents/annual_report/markdown/annual_report.md",
  "s3://ai-file/documents/annual_report/markdown/annual_report.json",
  "s3://ai-file/documents/annual_report/markdown/images/chart1.jpg",
  "s3://ai-file/documents/annual_report/markdown/images/table1.jpg"
]
```

#### 主要输出文件路径

```bash
# 获取主要输出文件URL
curl -s "http://localhost:8000/api/tasks/26" | jq -r '.output_url'

# 输出示例
s3://ai-file/documents/annual_report/markdown/annual_report.md
```

## 🔄 任务管理

### 重试失败任务

```bash
curl -X POST "http://localhost:8000/api/tasks/26/retry"
```

**响应示例**:

```json
{
  "message": "Task 26 has been reset and queued for retry",
  "task_id": 26,
  "status": "pending"
}
```

### 批量重试失败任务

```bash
curl -X POST "http://localhost:8000/api/tasks/retry-failed"
```

**响应示例**:

```json
{
  "message": "3 failed tasks have been reset and queued for retry",
  "retried_task_ids": [15, 18, 22]
}
```

### 修改任务类型

```bash
curl -X PUT "http://localhost:8000/api/tasks/26/task-type" \
  -H "Content-Type: application/json" \
  -d '{"new_task_type": "pdf_to_markdown"}'
```

**响应示例**:

```json
{
  "message": "Task 26 type updated from office_to_pdf to pdf_to_markdown",
  "task_id": 26,
  "old_task_type": "office_to_pdf",
  "new_task_type": "pdf_to_markdown"
}
```

## 📊 系统状态

### 查看系统统计

```bash
curl -s "http://localhost:8000/api/stats"
```

**响应示例**:

```json
{
  "total_tasks": 25,
  "completed_tasks": 23,
  "failed_tasks": 1,
  "pending_tasks": 1,
  "processing_tasks": 0,
  "queue_status": {
    "high_priority": 0,
    "normal_priority": 1,
    "low_priority": 0
  },
  "processor_status": {
    "running": true,
    "max_concurrent_tasks": 3,
    "active_workers": 3
  }
}
```

## 🗂 S3路径规则

### 输入路径格式

```
s3://{bucket_name}/{file_path}
```

### 输出路径格式

```
s3://ai-file/{original_bucket}/{file_name_without_ext}/{conversion_type}/{output_files}
```

### 路径示例

| 输入                                  | 输出                                                    |
| ----------------------------------- | ----------------------------------------------------- |
| `s3://documents/reports/annual.pdf` | `s3://ai-file/documents/annual/markdown/annual.md`    |
| `s3://test/presentation.pptx`       | `s3://ai-file/test/presentation/pdf/presentation.pdf` |
| `s3://ai-file/test/doc/file.pdf`    | `s3://ai-file/test/doc/markdown/file.md`              |

## ⚠️ 错误处理

### 任务失败响应

```json
{
  "id": 28,
  "task_type": "pdf_to_markdown",
  "status": "failed",
  "error_message": "Failed to download file from S3: NoSuchKey",
  "created_at": "2025-08-09T12:00:00",
  "failed_at": "2025-08-09T12:01:30"
}
```

### 常见错误码

| 错误码   | 描述      | 解决方案     |
| ----- | ------- | -------- |
| `400` | 请求参数错误  | 检查必需参数   |
| `404` | 任务不存在   | 确认任务ID正确 |
| `500` | 服务器内部错误 | 查看服务日志   |

## 🔧 高级用法

### 批量创建任务

```bash
# 创建多个PDF转Markdown任务
for file in document1.pdf document2.pdf document3.pdf; do
  curl -X POST "http://localhost:8000/api/tasks/create" \
    -F "task_type=pdf_to_markdown" \
    -F "bucket_name=batch-docs" \
    -F "file_path=pdfs/$file" \
    -F "platform=batch-system" \
    -F "priority=normal"
  sleep 1
done
```

### 监控任务进度

```bash
# 持续监控任务状态
task_id=26
while true; do
  status=$(curl -s "http://localhost:8000/api/tasks/$task_id" | jq -r '.status')
  echo "Task $task_id status: $status"
  if [[ "$status" == "completed" || "$status" == "failed" ]]; then
    break
  fi
  sleep 5
done
```

### 获取完整任务信息

```bash
# 获取任务详细信息并格式化输出
curl -s "http://localhost:8000/api/tasks/26" | jq '{
  id: .id,
  type: .task_type,
  status: .status,
  input: .file_path,
  output: .output_url,
  processing_time: .task_processing_time,
  files_count: (.s3_urls | length)
}'
```

## 📝 注意事项

1. **文件路径**: 确保S3中的文件路径正确且文件存在
2. **任务类型**: 选择正确的任务类型匹配文件格式
3. **优先级**: 合理设置任务优先级，避免阻塞重要任务
4. **监控**: 定期检查任务状态和系统健康状况
5. **重试**: 失败任务可以重试，但要检查失败原因

