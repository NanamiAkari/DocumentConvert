# API使用示例

本文档提供完整的API使用示例，包括curl命令和响应格式。

## 🚀 快速开始

### 1. 健康检查

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
    "completed_tasks": 25,
    "failed_tasks": 0
  },
  "queue_status": {
    "fetch_queue": 25,
    "task_processing_queue": 0,
    "high_priority_queue": 0,
    "normal_priority_queue": 0,
    "low_priority_queue": 0
  }
}
```

## 📄 任务创建

### PDF转Markdown

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=ai-file" \
  -F "file_path=test/document.pdf" \
  -F "platform=your-platform" \
  -F "priority=high"
```

**响应示例**:
```json
{
  "task_id": 26,
  "message": "Document conversion task 26 created successfully",
  "status": "pending"
}
```

### Office转PDF

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "bucket_name=documents" \
  -F "file_path=reports/annual_report.docx" \
  -F "platform=your-platform" \
  -F "priority=normal"
```

**响应示例**:
```json
{
  "task_id": 27,
  "message": "Document conversion task 27 created successfully",
  "status": "pending"
}
```

### Office转Markdown (两步转换)

```bash
curl -X POST "http://localhost:8000/api/tasks/create" \
  -F "task_type=office_to_markdown" \
  -F "bucket_name=documents" \
  -F "file_path=reports/quarterly_report.pptx" \
  -F "platform=your-platform" \
  -F "priority=high"
```

## 🔍 任务查询

### 查询特定任务

```bash
curl -s "http://localhost:8000/api/tasks/26"
```

**响应示例**:
```json
{
  "id": 26,
  "task_type": "pdf_to_markdown",
  "status": "completed",
  "priority": "high",
  "bucket_name": "ai-file",
  "file_path": "test/document.pdf",
  "platform": "your-platform",
  "input_path": "/app/task_workspace/task_26/input/document.pdf",
  "output_path": "/app/task_workspace/task_26/output/document.md",
  "output_url": "s3://ai-file/test/document/markdown/document.md",
  "s3_urls": [
    "s3://ai-file/test/document/markdown/document.md",
    "s3://ai-file/test/document/markdown/document.json",
    "s3://ai-file/test/document/markdown/images/image1.jpg",
    "s3://ai-file/test/document/markdown/images/image2.jpg"
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
      "total_files": 4,
      "total_size": 2097152
    }
  },
  "error_message": null
}
```

### 查询任务列表

```bash
# 查询所有任务
curl -s "http://localhost:8000/api/tasks"

# 按状态过滤
curl -s "http://localhost:8000/api/tasks?status=completed&limit=10"

# 按任务类型过滤
curl -s "http://localhost:8000/api/tasks?task_type=pdf_to_markdown&limit=5"

# 分页查询
curl -s "http://localhost:8000/api/tasks?offset=10&limit=10"
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
      "bucket_name": "ai-file",
      "file_path": "test/杭电申报-428定/pdf/杭电申报-428定.pdf",
      "output_url": "s3://ai-file/test/杭电申报-428定/markdown/杭电申报-428定.md",
      "created_at": "2025-08-09T11:42:53",
      "completed_at": "2025-08-09T11:43:18",
      "task_processing_time": 21.89
    }
  ],
  "total": 25,
  "offset": 0,
  "limit": 50
}
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

| 输入 | 输出 |
|------|------|
| `s3://documents/reports/annual.pdf` | `s3://ai-file/documents/annual/markdown/annual.md` |
| `s3://test/presentation.pptx` | `s3://ai-file/test/presentation/pdf/presentation.pdf` |
| `s3://ai-file/test/doc/file.pdf` | `s3://ai-file/test/doc/markdown/file.md` |

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

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| `400` | 请求参数错误 | 检查必需参数 |
| `404` | 任务不存在 | 确认任务ID正确 |
| `500` | 服务器内部错误 | 查看服务日志 |

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
