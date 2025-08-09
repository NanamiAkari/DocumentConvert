#!/usr/bin/env python3
"""
简单的API测试脚本
"""

import sys
sys.path.append('/workspace')

from api.unified_document_api import router, initialize_task_processor
from fastapi import FastAPI
from fastapi.testclient import TestClient

async def test_api():
    """测试API"""
    # 创建测试应用
    app = FastAPI()
    app.include_router(router)

    # 初始化任务处理器
    initialize_task_processor(
        database_type="sqlite",
        database_url="sqlite+aiosqlite:///./test_document_tasks.db"
    )

    # 获取任务处理器并初始化
    from api.unified_document_api import task_processor
    if task_processor:
        await task_processor.initialize()
        await task_processor.start()

    client = TestClient(app)
    
    # 测试健康检查
    print("🔍 测试健康检查...")
    response = client.get("/health")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {response.json()}")
    else:
        print(f"错误: {response.text}")
    
    # 测试创建任务
    print("\n🚀 测试创建gaojiaqi任务...")
    task_data = {
        "task_type": "pdf_to_markdown",
        "bucket_name": "gaojiaqi",
        "file_path": "浙音文件/2024本科生学生手册.pdf",
        "platform": "gaojiaqi",
        "priority": "normal"
    }

    response = client.post("/tasks/create", data=task_data)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"任务ID: {result.get('task_id')}")
        print(f"消息: {result.get('message')}")
        
        # 获取任务状态
        task_id = result.get('task_id')
        if task_id:
            print(f"\n📊 获取任务状态...")
            status_response = client.get(f"/tasks/{task_id}")
            print(f"状态码: {status_response.status_code}")
            if status_response.status_code == 200:
                print(f"任务状态: {status_response.json()}")
            else:
                print(f"错误: {status_response.text}")
    else:
        print(f"错误: {response.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api())
