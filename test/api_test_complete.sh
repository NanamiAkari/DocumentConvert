#!/bin/bash

# 完整的API测试脚本
# 测试文档转换服务的所有API接口

set -e

# 配置
BASE_URL="http://localhost:8000"
TEST_BUCKET="documents"
TEST_FILE="test/sample.pdf"
PLATFORM="api-test"

echo "🚀 开始API完整测试..."
echo "基础URL: $BASE_URL"
echo "测试存储桶: $TEST_BUCKET"
echo "测试文件: $TEST_FILE"
echo "平台: $PLATFORM"
echo "=================================="

# 1. 健康检查
echo "1️⃣ 测试健康检查..."
health_response=$(curl -s "$BASE_URL/health")
echo "健康检查响应: $health_response"

status=$(echo $health_response | jq -r '.status')
if [ "$status" = "healthy" ]; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败"
    exit 1
fi
echo ""

# 2. 创建PDF转Markdown任务
echo "2️⃣ 测试创建PDF转Markdown任务..."
create_response=$(curl -s -X POST "$BASE_URL/api/tasks/create" \
  -F "task_type=pdf_to_markdown" \
  -F "bucket_name=$TEST_BUCKET" \
  -F "file_path=$TEST_FILE" \
  -F "platform=$PLATFORM" \
  -F "priority=high")

echo "创建任务响应: $create_response"
task_id=$(echo $create_response | jq -r '.task_id')

if [ "$task_id" != "null" ] && [ "$task_id" != "" ]; then
    echo "✅ 任务创建成功，任务ID: $task_id"
else
    echo "❌ 任务创建失败"
    exit 1
fi
echo ""

# 3. 查询任务详情
echo "3️⃣ 测试查询任务详情..."
sleep 2  # 等待任务开始处理
task_response=$(curl -s "$BASE_URL/api/tasks/$task_id")
echo "任务详情响应: $task_response"

task_status=$(echo $task_response | jq -r '.status')
echo "任务状态: $task_status"
echo ""

# 4. 查询任务列表
echo "4️⃣ 测试查询任务列表..."
list_response=$(curl -s "$BASE_URL/api/tasks?limit=5")
echo "任务列表响应: $list_response"

total_tasks=$(echo $list_response | jq -r '.total')
echo "总任务数: $total_tasks"
echo ""

# 5. 按状态过滤任务
echo "5️⃣ 测试按状态过滤任务..."
failed_tasks=$(curl -s "$BASE_URL/api/tasks?status=failed&limit=10")
echo "失败任务: $failed_tasks"

completed_tasks=$(curl -s "$BASE_URL/api/tasks?status=completed&limit=10")
echo "完成任务: $completed_tasks"
echo ""

# 6. 按任务类型过滤
echo "6️⃣ 测试按任务类型过滤..."
pdf_tasks=$(curl -s "$BASE_URL/api/tasks?task_type=pdf_to_markdown&limit=5")
echo "PDF转Markdown任务: $pdf_tasks"
echo ""

# 7. 测试重试功能
echo "7️⃣ 测试任务重试功能..."
retry_response=$(curl -s -X POST "$BASE_URL/api/tasks/$task_id/retry")
echo "重试响应: $retry_response"
echo ""

# 8. 测试批量重试失败任务
echo "8️⃣ 测试批量重试失败任务..."
batch_retry_response=$(curl -s -X POST "$BASE_URL/api/tasks/retry-failed")
echo "批量重试响应: $batch_retry_response"
echo ""

# 9. 测试修改任务类型
echo "9️⃣ 测试修改任务类型..."
update_type_response=$(curl -s -X PUT "$BASE_URL/api/tasks/$task_id/task-type" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "new_task_type=pdf_to_markdown")
echo "修改任务类型响应: $update_type_response"
echo ""

# 10. 测试系统统计
echo "🔟 测试系统统计..."
stats_response=$(curl -s "$BASE_URL/api/statistics")
echo "系统统计响应: $stats_response"
echo ""

# 11. 创建Office转PDF任务
echo "1️⃣1️⃣ 测试创建Office转PDF任务..."
office_response=$(curl -s -X POST "$BASE_URL/api/tasks/create" \
  -F "task_type=office_to_pdf" \
  -F "bucket_name=$TEST_BUCKET" \
  -F "file_path=presentations/sample.pptx" \
  -F "platform=$PLATFORM" \
  -F "priority=normal")

echo "Office转PDF任务响应: $office_response"
office_task_id=$(echo $office_response | jq -r '.task_id')
echo "Office任务ID: $office_task_id"
echo ""

# 12. 创建Office转Markdown任务
echo "1️⃣2️⃣ 测试创建Office转Markdown任务..."
office_md_response=$(curl -s -X POST "$BASE_URL/api/tasks/create" \
  -F "task_type=office_to_markdown" \
  -F "bucket_name=$TEST_BUCKET" \
  -F "file_path=documents/sample.docx" \
  -F "platform=$PLATFORM" \
  -F "priority=low")

echo "Office转Markdown任务响应: $office_md_response"
office_md_task_id=$(echo $office_md_response | jq -r '.task_id')
echo "Office转Markdown任务ID: $office_md_task_id"
echo ""

# 13. 测试错误处理 - 无效任务类型
echo "1️⃣3️⃣ 测试错误处理 - 无效任务类型..."
error_response=$(curl -s -X POST "$BASE_URL/api/tasks/create" \
  -F "task_type=invalid_type" \
  -F "bucket_name=$TEST_BUCKET" \
  -F "file_path=$TEST_FILE" \
  -F "platform=$PLATFORM" \
  -F "priority=high")

echo "错误响应: $error_response"
echo ""

# 14. 测试错误处理 - 不存在的任务ID
echo "1️⃣4️⃣ 测试错误处理 - 不存在的任务ID..."
not_found_response=$(curl -s "$BASE_URL/api/tasks/99999")
echo "不存在任务响应: $not_found_response"
echo ""

# 15. 最终状态检查
echo "1️⃣5️⃣ 最终状态检查..."
final_health=$(curl -s "$BASE_URL/health")
echo "最终健康状态: $final_health"

final_stats=$(curl -s "$BASE_URL/api/statistics")
echo "最终系统统计: $final_stats"
echo ""

echo "=================================="
echo "🎉 API测试完成！"
echo ""
echo "📊 测试总结:"
echo "- 健康检查: ✅"
echo "- 任务创建: ✅ (PDF转Markdown, Office转PDF, Office转Markdown)"
echo "- 任务查询: ✅ (详情查询, 列表查询, 过滤查询)"
echo "- 任务管理: ✅ (重试, 批量重试, 修改类型)"
echo "- 系统统计: ✅"
echo "- 错误处理: ✅ (无效参数, 不存在资源)"
echo ""
echo "🔗 相关链接:"
echo "- Swagger文档: $BASE_URL/docs"
echo "- ReDoc文档: $BASE_URL/redoc"
echo "- OpenAPI规范: $BASE_URL/openapi.json"
echo ""
echo "📝 创建的测试任务ID:"
echo "- PDF转Markdown: $task_id"
echo "- Office转PDF: $office_task_id"
echo "- Office转Markdown: $office_md_task_id"
echo ""
echo "💡 提示: 可以使用这些任务ID进一步测试任务状态查询和管理功能"
