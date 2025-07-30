# Office文档直接转Markdown功能说明

## 功能概述

本系统新增了Office文档直接转Markdown的功能，无需用户手动进行两步转换（先转PDF再转Markdown）。系统会在内部自动完成中间PDF转换过程，对用户透明化处理流程，提高用户体验。

## 业务流程

整个Office文档转Markdown的业务流程如下：

1. **用户请求阶段**：
   - 用户通过API接口提交Office文档转Markdown的请求
   - 系统接收请求并验证参数
   - 创建任务并分配任务ID

2. **任务调度阶段**：
   - TaskProcessor将任务加入处理队列
   - 根据任务优先级和系统负载调度任务执行
   - 任务状态从`pending`变为`processing`

3. **文档转换阶段**：
   - 系统创建临时工作目录
   - 第一步：调用DocumentService将Office文档转换为PDF
   - 第二步：调用DocumentService将PDF转换为Markdown
   - 系统记录转换过程中的中间状态和结果

4. **结果处理阶段**：
   - 系统将转换结果保存到指定输出路径
   - 更新任务状态为`completed`或`failed`
   - 返回任务执行结果和相关信息

## API接口

### 1. 单文件转换接口

```
POST /api/tasks/office-to-markdown
```

**参数说明：**

- `input_path`: 输入Office文档路径（必填）
- `output_path`: 输出Markdown文件路径（必填）
- `priority`: 任务优先级，可选值为'low'、'normal'、'high'，默认为'normal'
- `force_reprocess`: 是否强制重新处理，默认为false

**示例请求：**

```bash
curl -X POST "http://localhost:8000/api/tasks/office-to-markdown?input_path=/workspace/test/智涌君.docx&output_path=/workspace/output/智涌君.md&priority=normal"
```

### 2. 批量转换接口

```
POST /api/tasks/batch-office-to-markdown
```

**参数说明：**

- `input_dir`: 输入目录路径（必填）
- `output_dir`: 输出目录路径（必填）
- `priority`: 任务优先级，可选值为'low'、'normal'、'high'，默认为'normal'
- `force_reprocess`: 是否强制重新处理，默认为false
- `recursive`: 是否递归处理子目录，默认为false
- `file_pattern`: 文件名匹配模式，支持正则表达式，默认为null（处理所有Office文档）

**示例请求：**

```bash
curl -X POST "http://localhost:8000/api/tasks/batch-office-to-markdown?input_dir=/workspace/test&output_dir=/workspace/output/markdown&recursive=true"
```

### 3. 通用任务创建接口

除了上述快捷接口外，系统还提供了通用的任务创建接口，可以创建各种类型的文档转换任务：

```
POST /api/tasks
```

**请求体示例：**

```json
{
  "task_type": "office_to_markdown",
  "input_path": "/workspace/test/智涌君.docx",
  "output_path": "/workspace/output/智涌君.md",
  "priority": "normal",
  "params": {
    "force_reprocess": false
  }
}
```

## 实现原理

系统内部实现了两个主要步骤的自动化处理：

1. **Office转PDF**：使用LibreOffice将Office文档转换为PDF
   - 支持多种Office格式（Word、Excel、PowerPoint等）
   - 保留文档格式和布局
   - 生成中间PDF文件到临时目录

2. **PDF转Markdown**：使用MinerU将PDF转换为Markdown
   - 提取文本内容和基本格式
   - 转换为结构化Markdown文档
   - 支持表格、列表等基本格式

这两个步骤在系统内部自动完成，用户只需提供输入Office文档和期望的输出Markdown路径即可。系统会自动创建临时目录存放中间PDF文件，完成转换后可以选择是否保留这些临时文件。

## 核心组件

系统由以下核心组件组成：

1. **API层**：提供RESTful API接口，接收用户请求
   - FastAPI框架实现
   - 支持同步和异步请求处理
   - 提供任务创建、查询、管理接口

2. **任务处理器**：负责任务调度和执行
   - 多队列管理（获取队列、处理队列、更新队列等）
   - 异步并发处理，支持多任务并行执行
   - 错误处理和重试机制

3. **文档服务**：提供文档转换核心功能
   - Office转PDF服务
   - PDF转Markdown服务
   - 批量处理服务

## 支持的文件格式

支持的Office文档格式包括：

- Word文档：.doc, .docx, .rtf
- Excel表格：.xls, .xlsx
- PowerPoint演示文稿：.ppt, .pptx
- OpenDocument格式：.odt, .ods, .odp

## 注意事项

1. 确保系统已安装LibreOffice和MinerU工具
2. 输入文件必须是有效的Office文档格式
3. 输出目录必须有写入权限
4. 对于大型文档或批量处理，可能需要较长时间
5. 转换质量取决于原始文档的格式和复杂度
6. 系统会创建临时目录存放中间文件，确保有足够的磁盘空间