#!/usr/bin/env python3
"""
API功能测试脚本
测试文档转换API的各项功能
"""

import requests
import time
import json
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查接口"""
    print("\n=== 健康检查测试 ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            except:
                print(f"响应内容: {response.text}")
                return response.status_code == 200
        else:
            print(f"健康检查失败: {response.text}")
            return False
    except Exception as e:
        print(f"健康检查异常: {e}")
        return False

def test_create_office_to_pdf_task():
    """测试创建Office转PDF任务"""
    print("\n=== Office转PDF任务测试 ===")
    
    # 检查测试文件是否存在
    test_file = "/workspace/test.doc"
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return None
    
    try:
        payload = {
            "task_type": "office_to_pdf",
            "input_path": test_file,
            "priority": "normal"
        }
        
        print(f"创建任务请求: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        response = requests.post(f"{API_BASE_URL}/api/tasks/create", 
                               json=payload, timeout=30)
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"任务创建成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data.get('task_id')
        else:
            print(f"任务创建失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建任务异常: {e}")
        return None

def test_query_task_status(task_id):
    """测试查询任务状态"""
    print(f"\n=== 查询任务状态测试 (Task ID: {task_id}) ===")
    
    if not task_id:
        print("任务ID为空，跳过状态查询")
        return None
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"任务状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        else:
            print(f"查询失败: {response.text}")
            return None
    except Exception as e:
        print(f"查询异常: {e}")
        return None

def monitor_task_completion(task_id, max_wait_time=120):
    """监控任务完成状态"""
    print(f"\n=== 监控任务完成 (Task ID: {task_id}) ===")
    
    if not task_id:
        print("任务ID为空，跳过监控")
        return None
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        task_data = test_query_task_status(task_id)
        if task_data:
            status = task_data.get('status')
            print(f"当前状态: {status}")
            
            if status in ['completed', 'failed']:
                print(f"任务最终状态: {status}")
                return task_data
        
        print("等待5秒后再次检查...")
        time.sleep(5)
    
    print(f"监控超时 ({max_wait_time}秒)")
    return None

def test_create_pdf_to_markdown_task():
    """测试创建PDF转Markdown任务"""
    print("\n=== PDF转Markdown任务测试 ===")
    
    # 检查测试文件是否存在
    test_file = "/workspace/test.pdf"
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return None
    
    try:
        payload = {
            "task_type": "pdf_to_markdown",
            "input_path": test_file,
            "priority": "normal"
        }
        
        print(f"创建任务请求: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        response = requests.post(f"{API_BASE_URL}/api/tasks/create", 
                               json=payload, timeout=30)
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"任务创建成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data.get('task_id')
        else:
            print(f"任务创建失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建任务异常: {e}")
        return None

def main():
    """主测试函数"""
    print("开始API功能测试...")
    
    # 1. 健康检查
    if not test_health_check():
        print("❌ 健康检查失败，服务可能未启动")
        return
    
    print("✅ 健康检查通过")
    
    # 2. 测试Office转PDF
    office_task_id = test_create_office_to_pdf_task()
    if office_task_id:
        print(f"✅ Office转PDF任务创建成功: {office_task_id}")
        
        # 监控任务完成
        final_result = monitor_task_completion(office_task_id)
        if final_result and final_result.get('status') == 'completed':
            print("✅ Office转PDF任务完成")
        else:
            print("❌ Office转PDF任务未完成或失败")
    else:
        print("❌ Office转PDF任务创建失败")
    
    # 3. 测试PDF转Markdown
    pdf_task_id = test_create_pdf_to_markdown_task()
    if pdf_task_id:
        print(f"✅ PDF转Markdown任务创建成功: {pdf_task_id}")
        
        # 监控任务完成
        final_result = monitor_task_completion(pdf_task_id)
        if final_result and final_result.get('status') == 'completed':
            print("✅ PDF转Markdown任务完成")
        else:
            print("❌ PDF转Markdown任务未完成或失败")
    else:
        print("❌ PDF转Markdown任务创建失败")
    
    print("\n=== API功能测试完成 ===")

if __name__ == "__main__":
    main()