#!/usr/bin/env python3
"""
测试本地文件复制到task_workspace功能
验证修复后的本地文件处理逻辑
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime

# 测试配置
API_BASE_URL = "http://localhost:8000"

def test_local_file_copy():
    """测试本地文件复制功能"""
    print("🧪 测试本地文件复制到task_workspace")
    print("=" * 80)
    
    # 确认测试文件存在
    test_file = "/workspace/test/人人皆可vibe编程.pdf"
    if not Path(test_file).exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    file_size = Path(test_file).stat().st_size
    print(f"📄 测试文件: {test_file}")
    print(f"📊 文件大小: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # 创建任务
    task_data = {
        "task_type": "pdf_to_markdown",
        "input_path": test_file,
        "platform": "test_local",
        "priority": "normal"
    }
    
    print(f"\n🚀 创建本地文件任务...")
    print(f"📋 任务配置:")
    print(f"   📄 输入路径: {task_data['input_path']}")
    print(f"   🔄 任务类型: {task_data['task_type']}")
    print(f"   🏷️ 平台: {task_data['platform']}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/tasks/create", data=task_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"\n✅ 任务创建成功!")
            print(f"🆔 任务ID: {task_id}")
            
            # 监控任务执行
            print(f"\n👀 监控任务执行...")
            
            for i in range(20):  # 最多监控100秒
                time.sleep(5)
                
                try:
                    response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}")
                    if response.status_code == 200:
                        task_data = response.json()
                        status = task_data.get('status')
                        
                        print(f"📊 状态检查 {i+1}: {status}")
                        
                        if status == 'processing':
                            # 检查文件是否被正确复制到input目录
                            input_path = task_data.get('input_path')
                            if input_path:
                                print(f"   📂 输入路径: {input_path}")
                                
                                # 验证文件是否在正确的task_workspace目录
                                if f"task_workspace/task_{task_id}/input/" in input_path:
                                    print(f"   ✅ 文件正确复制到task_workspace目录")
                                    
                                    # 验证文件是否实际存在
                                    if Path(input_path).exists():
                                        copied_size = Path(input_path).stat().st_size
                                        print(f"   ✅ 文件存在，大小: {copied_size:,} bytes")
                                        
                                        if copied_size == file_size:
                                            print(f"   ✅ 文件大小匹配原始文件")
                                            return True
                                        else:
                                            print(f"   ❌ 文件大小不匹配: {copied_size} vs {file_size}")
                                    else:
                                        print(f"   ❌ 文件不存在: {input_path}")
                                else:
                                    print(f"   ❌ 文件路径不正确: {input_path}")
                        
                        elif status == 'completed':
                            print(f"✅ 任务完成!")
                            input_path = task_data.get('input_path')
                            if input_path and f"task_workspace/task_{task_id}/input/" in input_path:
                                print(f"✅ 文件正确复制到: {input_path}")
                                return True
                            else:
                                print(f"❌ 文件路径不正确: {input_path}")
                                return False
                        
                        elif status == 'failed':
                            print(f"❌ 任务失败: {task_data.get('error_message')}")
                            return False
                            
                except Exception as e:
                    print(f"❌ 状态查询异常: {e}")
            
            print(f"⏰ 监控超时")
            return False
            
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"📝 错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

if __name__ == "__main__":
    success = test_local_file_copy()
    if success:
        print(f"\n🎉 本地文件复制测试成功!")
    else:
        print(f"\n💥 本地文件复制测试失败!")
    exit(0 if success else 1)
