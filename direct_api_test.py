#!/usr/bin/env python3
"""
直接API测试脚本 - 绕过终端输出问题
"""

import requests
import json
import sys
import traceback
from pathlib import Path

def test_service_connection():
    """测试服务连接"""
    try:
        print("=== 测试服务连接 ===")
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError as e:
        print(f"连接错误: {e}")
        return False
    except Exception as e:
        print(f"其他错误: {e}")
        traceback.print_exc()
        return False

def test_create_task():
    """测试创建任务"""
    try:
        print("\n=== 测试创建任务 ===")
        
        # 检查测试文件
        test_files = ["/workspace/test.pdf", "/workspace/test.doc"]
        available_file = None
        for file_path in test_files:
            if Path(file_path).exists():
                available_file = file_path
                print(f"找到测试文件: {file_path}")
                break
        
        if not available_file:
            print("没有找到测试文件")
            return None
        
        # 根据文件类型选择任务类型
        if available_file.endswith('.pdf'):
            task_type = "pdf_to_markdown"
        else:
            task_type = "office_to_pdf"
        
        payload = {
            "task_type": task_type,
            "input_path": available_file,
            "priority": "normal"
        }
        
        print(f"创建任务请求: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            "http://localhost:8000/api/tasks/create",
            json=payload,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('task_id')
        else:
            return None
            
    except Exception as e:
        print(f"创建任务错误: {e}")
        traceback.print_exc()
        return None

def test_query_task(task_id):
    """测试查询任务"""
    try:
        print(f"\n=== 查询任务 {task_id} ===")
        
        response = requests.get(f"http://localhost:8000/api/tasks/{task_id}", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"查询任务错误: {e}")
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("开始直接API测试...")
    
    # 1. 测试服务连接
    if not test_service_connection():
        print("❌ 服务连接失败")
        sys.exit(1)
    
    print("✅ 服务连接成功")
    
    # 2. 测试创建任务
    task_id = test_create_task()
    if task_id:
        print(f"✅ 任务创建成功: {task_id}")
        
        # 3. 测试查询任务
        task_data = test_query_task(task_id)
        if task_data:
            print(f"✅ 任务查询成功")
            print(f"任务状态: {task_data.get('status')}")
        else:
            print("❌ 任务查询失败")
    else:
        print("❌ 任务创建失败")
    
    print("\n=== 直接API测试完成 ===")

if __name__ == "__main__":
    main()