#!/usr/bin/env python3
"""
本地文件上传测试脚本
测试API的本地文件上传功能，绕过S3依赖
"""

import requests
import json
from pathlib import Path
from datetime import datetime

def log_to_file(message):
    """记录日志到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open("/workspace/local_upload_test_results.log", "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def test_local_file_upload():
    """测试本地文件上传功能"""
    log_to_file("开始本地文件上传测试...")
    
    try:
        # 1. 健康检查
        log_to_file("=== 健康检查 ===")
        response = requests.get("http://localhost:8000/health", timeout=10)
        log_to_file(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            log_to_file("✅ 服务健康检查通过")
        else:
            log_to_file("❌ 服务健康检查失败")
            return
        
        # 2. 测试本地文件上传 - 使用 /api/tasks/create 接口
        test_files = [
            ("/workspace/test.pdf", "pdf_to_markdown"),
            ("/workspace/test.doc", "office_to_pdf")
        ]
        
        for file_path, task_type in test_files:
            if not Path(file_path).exists():
                log_to_file(f"⚠️ 测试文件不存在: {file_path}")
                continue
                
            log_to_file(f"=== 测试本地文件上传: {file_path} ===")
            
            # 准备文件上传
            with open(file_path, 'rb') as f:
                files = {'file_upload': (Path(file_path).name, f, 'application/octet-stream')}
                data = {
                    'task_type': task_type,
                    'platform': 'test',
                    'priority': 'normal'
                }
                
                log_to_file(f"上传文件: {Path(file_path).name}")
                log_to_file(f"任务类型: {task_type}")
                
                response = requests.post(
                    "http://localhost:8000/api/tasks/create",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                log_to_file(f"状态码: {response.status_code}")
                log_to_file(f"响应内容: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get('task_id')
                    log_to_file(f"✅ 任务创建成功，ID: {task_id}")
                    
                    # 查询任务状态
                    log_to_file(f"=== 查询任务 {task_id} 状态 ===")
                    status_response = requests.get(
                        f"http://localhost:8000/api/tasks/{task_id}",
                        timeout=10
                    )
                    log_to_file(f"任务状态查询: {status_response.status_code}")
                    if status_response.status_code == 200:
                        task_info = status_response.json()
                        log_to_file(f"任务状态: {task_info.get('status')}")
                        log_to_file(f"错误信息: {task_info.get('error_message')}")
                        log_to_file("✅ 任务状态查询成功")
                    else:
                        log_to_file("❌ 任务状态查询失败")
                        
                else:
                    log_to_file(f"❌ 任务创建失败: {response.text}")
        
        # 3. 测试 /api/upload-and-convert 接口
        log_to_file("=== 测试 /api/upload-and-convert 接口 ===")
        test_file = "/workspace/test.doc"
        if Path(test_file).exists():
            with open(test_file, 'rb') as f:
                files = {'file': (Path(test_file).name, f, 'application/msword')}
                data = {
                    'conversion_type': 'office_to_pdf',
                    'priority': 'normal'
                }
                
                response = requests.post(
                    "http://localhost:8000/api/upload-and-convert",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                log_to_file(f"upload-and-convert 状态码: {response.status_code}")
                log_to_file(f"upload-and-convert 响应: {response.text}")
                
                if response.status_code == 200:
                    log_to_file("✅ upload-and-convert 接口测试成功")
                else:
                    log_to_file("❌ upload-and-convert 接口测试失败")
        else:
            log_to_file("⚠️ 测试文件不存在，跳过 upload-and-convert 测试")
        
        log_to_file("=== 本地文件上传测试完成 ===")
        
    except Exception as e:
        log_to_file(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        log_to_file(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    # 清空之前的日志
    with open("/workspace/local_upload_test_results.log", "w", encoding="utf-8") as f:
        f.write("")
    
    test_local_file_upload()