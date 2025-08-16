#!/usr/bin/env python3
"""
文件输出测试脚本 - 将结果写入文件绕过终端问题
"""

import requests
import json
import sys
import traceback
import datetime
from pathlib import Path

def log_to_file(message, log_file="/workspace/api_test_results.log"):
    """将消息写入日志文件"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)  # 同时输出到终端

def test_service_connection():
    """测试服务连接"""
    try:
        log_to_file("=== 测试服务连接 ===")
        response = requests.get("http://localhost:8000/health", timeout=5)
        log_to_file(f"状态码: {response.status_code}")
        log_to_file(f"响应头: {dict(response.headers)}")
        log_to_file(f"响应内容: {response.text}")
        
        success = response.status_code == 200
        log_to_file(f"连接测试结果: {'成功' if success else '失败'}")
        return success
        
    except requests.exceptions.ConnectionError as e:
        log_to_file(f"连接错误: {e}")
        return False
    except Exception as e:
        log_to_file(f"其他错误: {e}")
        log_to_file(f"错误详情: {traceback.format_exc()}")
        return False

def check_test_files():
    """检查测试文件"""
    log_to_file("=== 检查测试文件 ===")
    test_files = ["/workspace/test.pdf", "/workspace/test.doc"]
    available_files = []
    
    for file_path in test_files:
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            log_to_file(f"找到测试文件: {file_path} (大小: {file_size} bytes)")
            available_files.append(file_path)
        else:
            log_to_file(f"测试文件不存在: {file_path}")
    
    return available_files

def test_create_task(file_path):
    """测试创建任务"""
    try:
        log_to_file(f"=== 测试创建任务 (文件: {file_path}) ===")
        
        # 根据文件类型选择任务类型
        if file_path.endswith('.pdf'):
            task_type = "pdf_to_markdown"
        else:
            task_type = "office_to_pdf"
        
        # 创建任务请求数据 - 使用正确的API格式
        task_data = {
            "task_type": task_type,
            "bucket_name": "documents",
            "file_path": Path(file_path).name,
            "priority": "normal",
            "platform": "test"
        }
        
        log_to_file(f"创建任务请求: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
        
        # 发送POST请求创建任务
        response = requests.post(
            "http://localhost:8000/api/tasks/create",
            data=task_data,
            timeout=10
        )
        
        log_to_file(f"状态码: {response.status_code}")
        log_to_file(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            log_to_file(f"任务创建成功，ID: {task_id}")
            return task_id
        else:
            log_to_file(f"任务创建失败")
            return None
            
    except Exception as e:
        log_to_file(f"创建任务错误: {e}")
        log_to_file(f"错误详情: {traceback.format_exc()}")
        return None

def test_query_task(task_id):
    """测试查询任务"""
    try:
        log_to_file(f"=== 查询任务 {task_id} ===")
        
        response = requests.get(f"http://localhost:8000/api/tasks/{task_id}", timeout=10)
        log_to_file(f"状态码: {response.status_code}")
        log_to_file(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            log_to_file(f"任务查询成功")
            log_to_file(f"任务状态: {data.get('status')}")
            log_to_file(f"错误信息: {data.get('error_message', 'None')}")
            return data
        else:
            log_to_file(f"任务查询失败")
            return None
            
    except Exception as e:
        log_to_file(f"查询任务错误: {e}")
        log_to_file(f"错误详情: {traceback.format_exc()}")
        return None

def main():
    """主函数"""
    # 清空日志文件
    log_file = "/workspace/api_test_results.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("")
    
    log_to_file("开始API功能测试...")
    
    # 1. 测试服务连接
    if not test_service_connection():
        log_to_file("❌ 服务连接失败，测试终止")
        return
    
    log_to_file("✅ 服务连接成功")
    
    # 2. 检查测试文件
    available_files = check_test_files()
    if not available_files:
        log_to_file("❌ 没有可用的测试文件")
        return
    
    # 3. 测试创建任务
    for file_path in available_files:
        task_id = test_create_task(file_path)
        if task_id:
            log_to_file(f"✅ 任务创建成功: {task_id}")
            
            # 4. 测试查询任务
            task_data = test_query_task(task_id)
            if task_data:
                log_to_file(f"✅ 任务查询成功")
            else:
                log_to_file(f"❌ 任务查询失败")
        else:
            log_to_file(f"❌ 任务创建失败: {file_path}")
    
    log_to_file("=== API功能测试完成 ===")
    log_to_file(f"详细结果已保存到: {log_file}")

if __name__ == "__main__":
    main()