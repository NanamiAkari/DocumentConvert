# 文档转换调度系统 API 接口文档

## 概述

文档转换调度系统提供RESTful API接口，支持多种文档格式的转换和批量处理。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1.0.0
- **内容类型**: `application/json`

## 认证

当前版本无需认证，后续版本将支持API Key认证。

## 核心接口

### 1. 健康检查

**接口**: `GET /health`

**描述**: 检查系统健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "task_processor_running": true,
  "queue_stats": {
    "fetch_queue": 0,
    "processing_queue": 0,
    "total_tasks": 5,
    "completed_tasks": 5,
    "failed_tasks": 0
  }
}
```

### 2. 创建转换任务

**接口**: `POST /api/tasks`

**描述**: 创建文档转换任务

**请求体**:
```json
{
  "task_type": "office_to_markdown",
  "input_path": "/workspace/test/document.docx",
  "output_path": "/workspace/output/document.md",
  "priority": "normal",
  "params": {
    "force_reprocess": false
  }
}
```

**参数说明**:
- `task_type`: 任务类型 (必填)
- `input_path`: 输入文件路径 (必填)
- `output_path`: 输出文件路径 (必填)
- `priority`: 任务优先级 (`low`, `normal`, `high`)
- `params`: 额外参数 (可选)

**支持的任务类型**:
- `office_to_pdf`: Office文档转PDF
- `pdf_to_markdown`: PDF转Markdown
- `office_to_markdown`: Office文档直接转Markdown
- `batch_office_to_pdf`: 批量Office转PDF
- `batch_pdf_to_markdown`: 批量PDF转Markdown
- `batch_office_to_markdown`: 批量Office转Markdown

**响应示例**:
```json
{
  "task_id": 1,
  "message": "Task 1 created successfully"
}
```

### 3. 查询任务状态

**接口**: `GET /api/tasks/{task_id}`

**描述**: 查询指定任务的状态

**路径参数**:
- `task_id`: 任务ID

**响应示例**:
```json
{
  "task_id": 1,
  "task_type": "office_to_markdown",
  "status": "completed",
  "input_path": "/workspace/test/document.docx",
  "output_path": "/workspace/output/document.md",
  "priority": "normal",
  "created_at": "2025-07-31T02:31:37.414084",
  "started_at": "2025-07-31T02:31:37.414565",
  "completed_at": "2025-07-31T02:31:45.956892",
  "error_message": null,
  "retry_count": 0
}
```

**任务状态说明**:
- `pending`: 等待处理
- `processing`: 正在处理
- `completed`: 处理完成
- `failed`: 处理失败

### 4. 列出所有任务

**接口**: `GET /api/tasks`

**描述**: 列出所有任务

**查询参数**:
- `status`: 按状态过滤 (可选)
- `limit`: 返回数量限制 (默认100)

**响应示例**:
```json
{
  "tasks": [
    {
      "task_id": 1,
      "task_type": "batch_office_to_markdown",
      "status": "completed",
      "input_path": "/workspace/test",
      "output_path": "/workspace/output/markdown",
      "priority": "normal",
      "created_at": "2025-07-31T02:31:37.414084",
      "completed_at": "2025-07-31T02:31:45.956892",
      "error_message": null,
      "retry_count": 0
    }
  ],
  "total": 1,
  "filter_status": null
}
```

### 5. 获取队列统计

**接口**: `GET /api/stats`

**描述**: 获取任务队列统计信息

**响应示例**:
```json
{
  "fetch_queue": 0,
  "processing_queue": 0,
  "update_queue": 0,
  "cleanup_queue": 0,
  "callback_queue": 0,
  "total_tasks": 1,
  "pending_tasks": 0,
  "processing_tasks": 0,
  "completed_tasks": 1,
  "failed_tasks": 0
}
```

## 快捷接口

### 批量Office转Markdown

**接口**: `GET /api/shortcuts/batch-office-to-markdown`

**描述**: 快速创建批量Office转Markdown任务

**查询参数**:
- `input_path`: 输入目录路径 (必填)
- `output_path`: 输出目录路径 (必填)
- `priority`: 任务优先级 (默认normal)
- `force_reprocess`: 是否强制重新处理 (默认false)
- `recursive`: 是否递归处理子目录 (默认false)

**示例**:
```bash
GET /api/shortcuts/batch-office-to-markdown?input_path=/workspace/test&output_path=/workspace/output/markdown&recursive=false
```

## 支持的文件格式

### Office文档
- Word: `.doc`, `.docx`, `.rtf`
- Excel: `.xls`, `.xlsx`
- PowerPoint: `.ppt`, `.pptx`
- OpenDocument: `.odt`, `.ods`, `.odp`

### PDF文档
- `.pdf`

## 错误处理

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码
- `400`: 请求参数错误
- `404`: 任务不存在
- `500`: 服务器内部错误
- `503`: 服务不可用

## 使用示例

### 完整的转换流程

1. **创建批量转换任务**:
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "batch_office_to_markdown",
    "input_path": "/workspace/test",
    "output_path": "/workspace/output/markdown",
    "priority": "normal",
    "params": {"force_reprocess": true}
  }'
```

2. **查询任务状态**:
```bash
curl "http://localhost:8000/api/tasks/1"
```

3. **等待任务完成后查看结果**:
```bash
ls -la /workspace/output/markdown/
```

### 性能建议

- 批量处理时建议设置合理的并发数量
- 大文件转换可能需要较长时间，请耐心等待
- 定期清理输出目录以节省磁盘空间
- 监控系统资源使用情况

## 更新日志

### v1.0.0 (2025-07-31)
- 初始版本发布
- 支持Office文档转PDF和Markdown
- 支持批量处理
- 提供RESTful API接口
- 异步任务处理和状态跟踪