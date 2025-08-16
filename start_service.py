#!/usr/bin/env python3
"""
服务启动脚本 - 将启动日志输出到文件
"""

import subprocess
import sys
import os
import time
import datetime

def log_to_file(message, log_file="/workspace/service_startup.log"):
    """将消息写入日志文件"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def start_service():
    """启动服务"""
    log_file = "/workspace/service_startup.log"
    
    # 清空日志文件
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("")
    
    log_to_file("开始启动服务...")
    
    try:
        # 检查当前目录
        cwd = os.getcwd()
        log_to_file(f"当前工作目录: {cwd}")
        
        # 检查main.py是否存在
        if not os.path.exists("main.py"):
            log_to_file("错误: main.py文件不存在")
            return False
        
        log_to_file("找到main.py文件")
        
        # 启动服务
        cmd = ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
        log_to_file(f"执行命令: {' '.join(cmd)}")
        
        # 使用subprocess启动服务，将输出重定向到文件
        with open("/workspace/service_output.log", "w") as output_file:
            process = subprocess.Popen(
                cmd,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                cwd=cwd
            )
        
        log_to_file(f"服务进程已启动，PID: {process.pid}")
        
        # 等待几秒钟让服务启动
        time.sleep(5)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            log_to_file("服务进程正在运行")
            
            # 测试连接
            import requests
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                log_to_file(f"健康检查响应: {response.status_code}")
                if response.status_code == 200:
                    log_to_file("✅ 服务启动成功")
                    return True
                else:
                    log_to_file(f"❌ 健康检查失败: {response.status_code}")
            except Exception as e:
                log_to_file(f"❌ 连接测试失败: {e}")
        else:
            log_to_file(f"❌ 服务进程已退出，退出码: {process.poll()}")
        
        return False
        
    except Exception as e:
        log_to_file(f"启动服务时发生错误: {e}")
        import traceback
        log_to_file(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = start_service()
    if success:
        print("服务启动成功")
        sys.exit(0)
    else:
        print("服务启动失败")
        sys.exit(1)