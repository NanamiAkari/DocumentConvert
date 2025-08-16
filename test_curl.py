#!/usr/bin/env python3
"""
使用curl测试API接口
"""

import subprocess
import json
import datetime

def log_to_file(message, log_file="/workspace/curl_test_results.log"):
    """将消息写入日志文件"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def run_curl_command(url, method="GET", data=None, headers=None):
    """运行curl命令"""
    cmd = ["curl", "-s", "-v"]
    
    if method == "POST":
        cmd.extend(["-X", "POST"])
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)

def main():
    """主函数"""
    # 清空日志文件
    with open("/workspace/curl_test_results.log", "w", encoding="utf-8") as f:
        f.write("")
    
    log_to_file("开始curl API测试...")
    
    # 1. 测试健康检查
    log_to_file("=== 测试健康检查 ===")
    returncode, stdout, stderr = run_curl_command("http://localhost:8000/health")
    log_to_file(f"健康检查返回码: {returncode}")
    log_to_file(f"健康检查响应: {stdout}")
    if stderr:
        log_to_file(f"健康检查错误: {stderr}")
    
    # 2. 测试创建任务
    log_to_file("\n=== 测试创建任务 ===")
    task_data = {
        "task_type": "pdf_to_markdown",
        "input_path": "/workspace/test.pdf",
        "output_path": "/workspace/output/test.md",
        "priority": "normal"
    }
    
    headers = {"Content-Type": "application/json"}
    returncode, stdout, stderr = run_curl_command(
        "http://localhost:8000/api/tasks", 
        method="POST", 
        data=task_data, 
        headers=headers
    )
    
    log_to_file(f"创建任务返回码: {returncode}")
    log_to_file(f"创建任务响应: {stdout}")
    if stderr:
        log_to_file(f"创建任务错误: {stderr}")
    
    # 3. 测试查询任务列表
    log_to_file("\n=== 测试查询任务列表 ===")
    returncode, stdout, stderr = run_curl_command("http://localhost:8000/api/tasks")
    log_to_file(f"查询任务列表返回码: {returncode}")
    log_to_file(f"查询任务列表响应: {stdout}")
    if stderr:
        log_to_file(f"查询任务列表错误: {stderr}")
    
    log_to_file("\n=== curl API测试完成 ===")

if __name__ == "__main__":
    main()
