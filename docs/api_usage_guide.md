# 文档转换调度系统 - API使用指导

## 📋 目录

1. [快速开始](#快速开始)
2. [API接口概览](#api接口概览)
3. [任务管理接口](#任务管理接口)
4. [快捷接口](#快捷接口)
5. [文件上传接口](#文件上传接口)
6. [使用示例](#使用示例)
7. [错误处理](#错误处理)
8. [最佳实践](#最佳实践)

## 🚀 快速开始

### 基础信息

- **服务地址**: `http://localhost:8000`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

### 健康检查

在开始使用API之前，建议先检查服务状态：

```bash
curl http://localhost:8000/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-07T23:25:54.123456",
  "version": "1.0.0"
}
```

## 📊 API接口概览

### 接口分类

| 分类 | 接口数量 | 用途 | 适用场景 |
|------|----------|------|----------|
| **任务管理** | 4个 | 创建、查询、管理任务 | 完整的任务控制 |
| **快捷接口** | 6个 | 一键式转换操作 | 简单快速转换 |
| **文件上传** | 1个 | 上传并转换文件 | Web界面集成 |
| **系统监控** | 2个 | 状态监控和统计 | 系统运维 |

### 支持的转换类型

| 转换类型 | 输入格式 | 输出格式 | 说明 |
|----------|----------|----------|------|
| **office_to_pdf** | .doc, .docx, .ppt, .pptx, .xls, .xlsx | .pdf | Office文档转PDF |
| **pdf_to_markdown** | .pdf | .md | PDF转Markdown |
| **office_to_markdown** | Office格式 | .md | Office直接转Markdown |
| **batch_office_to_pdf** | 目录 | 目录 | 批量Office转PDF |
| **batch_pdf_to_markdown** | 目录 | 目录 | 批量PDF转Markdown |
| **batch_office_to_markdown** | 目录 | 目录 | 批量Office转Markdown |

## 🔧 任务管理接口

### 1. 创建任务

**接口**: `POST /api/tasks`

**功能**: 创建一个新的文档转换任务

#### 请求参数

```json
{
  "task_type": "office_to_markdown",
  "input_path": "/workspace/input/document.docx",
  "output_path": "/workspace/output/document.md",
  "priority": "normal",
  "params": {
    "force_reprocess": true,
    "recursive": false
  }
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| **task_type** | string | 是 | 转换类型 | "office_to_markdown" |
| **input_path** | string | 是 | 输入文件/目录路径 | "/workspace/input/doc.docx" |
| **output_path** | string | 是 | 输出文件/目录路径 | "/workspace/output/doc.md" |
| **priority** | string | 否 | 优先级 | "normal" (默认), "high", "low" |
| **params** | object | 否 | 额外参数 | 见下表 |

#### params参数详解

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| **force_reprocess** | boolean | false | 强制重新处理已存在的输出文件 |
| **recursive** | boolean | false | 批量处理时是否递归子目录 |
| **output_format** | string | "markdown" | 输出格式 |

#### 响应示例

**成功响应** (200):
```json
{
  "task_id": 1,
  "message": "Task 1 created successfully"
}
```

**错误响应** (400):
```json
{
  "detail": "Invalid task type. Supported types: {'office_to_pdf', 'pdf_to_markdown', 'office_to_markdown', 'batch_office_to_pdf', 'batch_pdf_to_markdown', 'batch_office_to_markdown'}"
}
```

#### 使用示例

```bash
# 创建Office转Markdown任务
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_markdown",
    "input_path": "/workspace/input/report.docx",
    "output_path": "/workspace/output/report.md",
    "priority": "high",
    "params": {
      "force_reprocess": true
    }
  }'

# 创建批量转换任务
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "batch_office_to_markdown",
    "input_path": "/workspace/input/documents",
    "output_path": "/workspace/output/markdown",
    "params": {
      "recursive": true,
      "force_reprocess": false
    }
  }'
```

### 2. 查询任务状态

**接口**: `GET /api/tasks/{task_id}`

**功能**: 获取指定任务的详细状态信息

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| **task_id** | integer | 任务ID |

#### 响应示例

**成功响应** (200):
```json
{
  "task_id": 1,
  "task_type": "office_to_markdown",
  "status": "completed",
  "input_path": "/workspace/input/report.docx",
  "output_path": "/workspace/output/report.md",
  "priority": "high",
  "created_at": "2025-08-07T23:25:54.646180",
  "started_at": "2025-08-07T23:25:54.646674",
  "completed_at": "2025-08-07T23:28:50.348557",
  "error_message": null,
  "retry_count": 0,
  "params": {
    "force_reprocess": true
  }
}
```

**任务不存在** (404):
```json
{
  "detail": "Task 999 not found"
}
```

#### 状态说明

| 状态 | 说明 | 后续操作 |
|------|------|----------|
| **pending** | 等待处理 | 继续等待 |
| **processing** | 正在处理 | 继续等待 |
| **completed** | 处理完成 | 可以获取结果文件 |
| **failed** | 处理失败 | 查看error_message |

#### 使用示例

```bash
# 查询任务状态
curl http://localhost:8000/api/tasks/1

# 使用jq美化输出
curl http://localhost:8000/api/tasks/1 | jq '.'

# 只获取状态字段
curl http://localhost:8000/api/tasks/1 | jq '.status'
```

### 3. 获取所有任务

**接口**: `GET /api/tasks`

**功能**: 获取所有任务的列表

#### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| **status** | string | 否 | 按状态过滤 | "completed" |
| **task_type** | string | 否 | 按类型过滤 | "office_to_markdown" |
| **limit** | integer | 否 | 限制返回数量 | 10 |

#### 响应示例

```json
{
  "tasks": [
    {
      "task_id": 1,
      "task_type": "office_to_markdown",
      "status": "completed",
      "created_at": "2025-08-07T23:25:54.646180",
      "completed_at": "2025-08-07T23:28:50.348557"
    },
    {
      "task_id": 2,
      "task_type": "pdf_to_markdown",
      "status": "processing",
      "created_at": "2025-08-07T23:30:15.123456",
      "started_at": "2025-08-07T23:30:15.234567"
    }
  ],
  "total": 2
}
```

#### 使用示例

```bash
# 获取所有任务
curl http://localhost:8000/api/tasks

# 只获取已完成的任务
curl "http://localhost:8000/api/tasks?status=completed"

# 获取最近10个任务
curl "http://localhost:8000/api/tasks?limit=10"
```

### 4. 获取队列统计

**接口**: `GET /api/stats`

**功能**: 获取系统队列和任务统计信息

#### 响应示例

```json
{
  "fetch_queue": 0,
  "processing_queue": 1,
  "update_queue": 0,
  "cleanup_queue": 0,
  "callback_queue": 0,
  "total_tasks": 5,
  "pending_tasks": 1,
  "processing_tasks": 1,
  "completed_tasks": 3,
  "failed_tasks": 0
}
```

#### 字段说明

| 字段 | 说明 |
|------|------|
| **fetch_queue** | 待获取队列长度 |
| **processing_queue** | 处理队列长度 |
| **update_queue** | 更新队列长度 |
| **cleanup_queue** | 清理队列长度 |
| **callback_queue** | 回调队列长度 |
| **total_tasks** | 总任务数 |
| **pending_tasks** | 等待中任务数 |
| **processing_tasks** | 处理中任务数 |
| **completed_tasks** | 已完成任务数 |
| **failed_tasks** | 失败任务数 |

#### 使用示例

```bash
# 获取统计信息
curl http://localhost:8000/api/stats

# 监控队列状态（每5秒刷新）
watch -n 5 'curl -s http://localhost:8000/api/stats | jq .'
```

## ⚡ 快捷接口

快捷接口提供一键式转换操作，无需手动创建任务，适合简单的转换需求。

### 1. Office转PDF

**接口**: `GET /api/shortcuts/office-to-pdf`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **input_path** | string | 是 | 输入文件路径 |
| **output_path** | string | 是 | 输出文件路径 |
| **force_reprocess** | boolean | 否 | 强制重新处理 |

#### 使用示例

```bash
curl -G "http://localhost:8000/api/shortcuts/office-to-pdf" \
  -d "input_path=/workspace/input/document.docx" \
  -d "output_path=/workspace/output/document.pdf" \
  -d "force_reprocess=true"
```

### 2. PDF转Markdown

**接口**: `GET /api/shortcuts/pdf-to-markdown`

#### 使用示例

```bash
curl -G "http://localhost:8000/api/shortcuts/pdf-to-markdown" \
  -d "input_path=/workspace/input/document.pdf" \
  -d "output_path=/workspace/output/document.md"
```

### 3. Office转Markdown

**接口**: `GET /api/shortcuts/office-to-markdown`

#### 使用示例

```bash
curl -G "http://localhost:8000/api/shortcuts/office-to-markdown" \
  -d "input_path=/workspace/input/report.docx" \
  -d "output_path=/workspace/output/report.md" \
  -d "force_reprocess=true"
```

### 4. 批量Office转PDF

**接口**: `GET /api/shortcuts/batch-office-to-pdf`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **input_path** | string | 是 | 输入目录路径 |
| **output_path** | string | 是 | 输出目录路径 |
| **recursive** | boolean | 否 | 是否递归子目录 |
| **force_reprocess** | boolean | 否 | 强制重新处理 |

#### 使用示例

```bash
curl -G "http://localhost:8000/api/shortcuts/batch-office-to-pdf" \
  -d "input_path=/workspace/input/documents" \
  -d "output_path=/workspace/output/pdfs" \
  -d "recursive=true"
```

### 5. 批量PDF转Markdown

**接口**: `GET /api/shortcuts/batch-pdf-to-markdown`

#### 使用示例

```bash
curl -G "http://localhost:8000/api/shortcuts/batch-pdf-to-markdown" \
  -d "input_path=/workspace/input/pdfs" \
  -d "output_path=/workspace/output/markdown" \
  -d "recursive=false"
```

### 6. 批量Office转Markdown

**接口**: `GET /api/shortcuts/batch-office-to-markdown`

#### 使用示例

```bash
curl -G "http://localhost:8000/api/shortcuts/batch-office-to-markdown" \
  -d "input_path=/workspace/input/documents" \
  -d "output_path=/workspace/output/markdown" \
  -d "recursive=true" \
  -d "force_reprocess=false"

## 📤 文件上传接口

### 上传并转换

**接口**: `POST /api/upload-and-convert`

**功能**: 上传文件并立即进行转换，适合Web界面集成

#### 请求格式

使用 `multipart/form-data` 格式上传文件：

```bash
curl -X POST "http://localhost:8000/api/upload-and-convert" \
  -F "file=@/local/path/document.docx" \
  -F "task_type=office_to_markdown" \
  -F "output_filename=converted_document.md"
```

#### 表单参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **file** | file | 是 | 要上传的文件 |
| **task_type** | string | 是 | 转换类型 |
| **output_filename** | string | 否 | 输出文件名（默认自动生成） |

#### 响应示例

**成功响应**:
```json
{
  "task_id": 3,
  "message": "File uploaded and task 3 created successfully",
  "uploaded_file": "/workspace/uploads/document_20250807_232554.docx",
  "output_path": "/workspace/output/converted_document.md"
}
```

#### 支持的文件类型

| 转换类型 | 支持的上传格式 |
|----------|----------------|
| **office_to_pdf** | .doc, .docx, .ppt, .pptx, .xls, .xlsx |
| **office_to_markdown** | .doc, .docx, .ppt, .pptx, .xls, .xlsx |
| **pdf_to_markdown** | .pdf |

#### JavaScript示例

```javascript
// 使用fetch API上传文件
const uploadFile = async (file, taskType) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('task_type', taskType);

  const response = await fetch('/api/upload-and-convert', {
    method: 'POST',
    body: formData
  });

  return await response.json();
};

// 使用示例
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const result = await uploadFile(file, 'office_to_markdown');
console.log('Task ID:', result.task_id);
```

## 💡 使用示例

### 完整工作流示例

以下是一个完整的文档转换工作流示例：

#### 1. 单文件转换流程

```bash
#!/bin/bash

# 1. 检查服务状态
echo "检查服务状态..."
curl -s http://localhost:8000/health | jq '.status'

# 2. 创建转换任务
echo "创建转换任务..."
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_markdown",
    "input_path": "/workspace/input/report.docx",
    "output_path": "/workspace/output/report.md",
    "priority": "normal"
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
echo "任务ID: $TASK_ID"

# 3. 轮询任务状态
echo "等待任务完成..."
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/tasks/$TASK_ID" | jq -r '.status')
  echo "当前状态: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    echo "任务完成！"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "任务失败！"
    curl -s "http://localhost:8000/api/tasks/$TASK_ID" | jq '.error_message'
    exit 1
  fi

  sleep 5
done

# 4. 验证输出文件
if [ -f "/workspace/output/report.md" ]; then
  echo "转换成功，输出文件已生成"
  ls -la /workspace/output/report.md
else
  echo "输出文件未找到"
  exit 1
fi
```

#### 2. 批量转换流程

```bash
#!/bin/bash

# 批量转换Office文档为Markdown
echo "开始批量转换..."

# 创建批量任务
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "batch_office_to_markdown",
    "input_path": "/workspace/input/documents",
    "output_path": "/workspace/output/markdown",
    "params": {
      "recursive": true,
      "force_reprocess": false
    }
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
echo "批量任务ID: $TASK_ID"

# 监控进度
while true; do
  TASK_INFO=$(curl -s "http://localhost:8000/api/tasks/$TASK_ID")
  STATUS=$(echo $TASK_INFO | jq -r '.status')

  echo "状态: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    echo "批量转换完成！"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "批量转换失败："
    echo $TASK_INFO | jq '.error_message'
    exit 1
  fi

  # 显示系统统计
  curl -s http://localhost:8000/api/stats | jq '{processing_tasks, completed_tasks, failed_tasks}'

  sleep 10
done
```

#### 3. Python客户端示例

```python
import requests
import time
import json

class DocumentConverterClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def create_task(self, task_type, input_path, output_path, **params):
        """创建转换任务"""
        data = {
            "task_type": task_type,
            "input_path": input_path,
            "output_path": output_path,
            "params": params
        }

        response = requests.post(f"{self.base_url}/api/tasks", json=data)
        response.raise_for_status()
        return response.json()["task_id"]

    def get_task_status(self, task_id):
        """获取任务状态"""
        response = requests.get(f"{self.base_url}/api/tasks/{task_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, task_id, timeout=300):
        """等待任务完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            task_info = self.get_task_status(task_id)
            status = task_info["status"]

            if status == "completed":
                return task_info
            elif status == "failed":
                raise Exception(f"Task failed: {task_info.get('error_message')}")

            time.sleep(5)

        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

    def convert_office_to_markdown(self, input_path, output_path, wait=True):
        """便捷方法：Office转Markdown"""
        task_id = self.create_task(
            task_type="office_to_markdown",
            input_path=input_path,
            output_path=output_path
        )

        if wait:
            return self.wait_for_completion(task_id)
        else:
            return {"task_id": task_id}

# 使用示例
client = DocumentConverterClient()

# 转换单个文件
result = client.convert_office_to_markdown(
    input_path="/workspace/input/document.docx",
    output_path="/workspace/output/document.md"
)
print(f"转换完成: {result}")

# 批量转换
task_id = client.create_task(
    task_type="batch_office_to_markdown",
    input_path="/workspace/input/documents",
    output_path="/workspace/output/markdown",
    recursive=True
)

print(f"批量任务已创建: {task_id}")
```

## ⚠️ 错误处理

### 常见错误码

| HTTP状态码 | 错误类型 | 说明 | 解决方案 |
|------------|----------|------|----------|
| **400** | 请求参数错误 | 参数格式不正确或缺少必填参数 | 检查请求参数 |
| **404** | 资源不存在 | 任务ID不存在或文件路径无效 | 确认资源存在 |
| **422** | 参数验证失败 | 参数类型或值不符合要求 | 修正参数值 |
| **500** | 服务器内部错误 | 系统异常或转换失败 | 查看错误信息 |
| **503** | 服务不可用 | 任务处理器未启动 | 检查服务状态 |

### 错误响应格式

```json
{
  "detail": "错误描述信息",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-08-07T23:30:15.123456"
}
```

### 任务失败处理

当任务状态为 `failed` 时，可以通过以下方式获取详细错误信息：

```bash
# 获取失败任务的错误信息
curl http://localhost:8000/api/tasks/1 | jq '.error_message'
```

常见的任务失败原因：

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| **文件不存在** | 输入文件路径无效 | 检查文件路径 |
| **权限不足** | 无法读取输入文件或写入输出文件 | 检查文件权限 |
| **格式不支持** | 文件格式不在支持列表中 | 使用支持的格式 |
| **GPU内存不足** | MinerU处理时GPU内存不足 | 等待其他任务完成或重启服务 |
| **转换工具错误** | LibreOffice或MinerU执行失败 | 检查工具状态和依赖 |

## 🎯 最佳实践

### 1. 任务管理最佳实践

#### 合理设置优先级

```bash
# 紧急任务使用高优先级
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_markdown",
    "input_path": "/workspace/urgent/report.docx",
    "output_path": "/workspace/output/urgent_report.md",
    "priority": "high"
  }'

# 批量任务使用低优先级
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "batch_office_to_markdown",
    "input_path": "/workspace/batch/documents",
    "output_path": "/workspace/output/batch",
    "priority": "low"
  }'
```

#### 监控队列状态

```bash
# 定期检查队列状态，避免任务积压
watch -n 10 'curl -s http://localhost:8000/api/stats | jq "{processing_queue, total_tasks, processing_tasks}"'
```

### 2. 文件路径最佳实践

#### 使用绝对路径

```bash
# 推荐：使用绝对路径
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_markdown",
    "input_path": "/workspace/input/document.docx",
    "output_path": "/workspace/output/document.md"
  }'
```

#### 确保目录存在

```bash
# 在创建任务前确保输出目录存在
mkdir -p /workspace/output/reports

curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "office_to_markdown",
    "input_path": "/workspace/input/report.docx",
    "output_path": "/workspace/output/reports/report.md"
  }'
```

### 3. 批量处理最佳实践

#### 合理组织文件结构

```
input/
├── documents/
│   ├── reports/
│   │   ├── report1.docx
│   │   └── report2.docx
│   └── presentations/
│       ├── ppt1.pptx
│       └── ppt2.pptx
└── pdfs/
    ├── doc1.pdf
    └── doc2.pdf
```

#### 使用递归处理

```bash
# 递归处理所有子目录
curl -G "http://localhost:8000/api/shortcuts/batch-office-to-markdown" \
  -d "input_path=/workspace/input/documents" \
  -d "output_path=/workspace/output/markdown" \
  -d "recursive=true"
```

### 4. 错误处理最佳实践

#### 实现重试机制

```python
import requests
import time

def create_task_with_retry(data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post("http://localhost:8000/api/tasks", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # 指数退避
```

#### 监控任务状态

```python
def monitor_task(task_id, check_interval=10):
    while True:
        try:
            response = requests.get(f"http://localhost:8000/api/tasks/{task_id}")
            task_info = response.json()

            status = task_info["status"]
            print(f"Task {task_id} status: {status}")

            if status in ["completed", "failed"]:
                return task_info

        except Exception as e:
            print(f"Error checking task status: {e}")

        time.sleep(check_interval)
```

### 5. 性能优化建议

#### 控制并发数量

```bash
# 避免同时提交过多任务，建议分批提交
for file in /workspace/input/*.docx; do
  # 检查当前处理中的任务数
  processing_count=$(curl -s http://localhost:8000/api/stats | jq '.processing_tasks')

  # 如果处理中任务过多，等待
  while [ $processing_count -gt 2 ]; do
    echo "等待处理中任务完成..."
    sleep 30
    processing_count=$(curl -s http://localhost:8000/api/stats | jq '.processing_tasks')
  done

  # 提交新任务
  curl -X POST "http://localhost:8000/api/tasks" \
    -H "Content-Type: application/json" \
    -d "{
      \"task_type\": \"office_to_markdown\",
      \"input_path\": \"$file\",
      \"output_path\": \"/workspace/output/$(basename $file .docx).md\"
    }"
done
```

#### 使用快捷接口

对于简单的转换需求，使用快捷接口可以减少API调用次数：

```bash
# 使用快捷接口，一步完成转换
curl -G "http://localhost:8000/api/shortcuts/office-to-markdown" \
  -d "input_path=/workspace/input/document.docx" \
  -d "output_path=/workspace/output/document.md"
```

## 📞 技术支持

### 常见问题

**Q: 任务一直处于pending状态怎么办？**
A: 检查系统统计，确认是否有工作协程在运行。可能是系统负载过高或GPU内存不足。

**Q: 批量转换时部分文件失败怎么办？**
A: 批量转换会跳过失败的文件继续处理其他文件。可以查看任务的error_message了解具体失败原因。

**Q: 如何提高转换速度？**
A: 1) 确保GPU内存充足；2) 避免同时处理过多任务；3) 使用SSD存储；4) 定期清理临时文件。

### 联系方式

- **技术文档**: [technical_documentation.md](./technical_documentation.md)
- **项目仓库**: https://cnb.cool/l8ai/document/MediaConvert.git
- **问题反馈**: 通过API返回的错误信息进行问题定位

---

**文档版本**: v1.0.0
**最后更新**: 2025年8月7日
**适用系统版本**: 文档转换调度系统 v1.0.0
```
