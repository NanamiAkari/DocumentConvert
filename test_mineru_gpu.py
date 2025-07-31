#!/usr/bin/env python3
"""
测试MinerU GPU模式转换
"""

import requests
import json
import time
import os
from pathlib import Path

def test_mineru_gpu():
    """测试MinerU GPU模式"""
    base_url = "http://localhost:8000"
    
    # 确保输出目录存在
    output_dir = Path("/workspace/output")
    output_dir.mkdir(exist_ok=True)
    
    print("=== 测试MinerU GPU模式转换 ===")
    
    # 1. 测试健康检查
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"健康检查状态: {response.status_code}")
        health_data = response.json()
        print(f"任务处理器运行: {health_data['task_processor_running']}")
        print(f"队列统计: {health_data['queue_stats']}")
    except Exception as e:
        print(f"健康检查失败: {e}")
        return
    
    # 2. 测试最小的PDF文件
    test_file = {
        "name": "小PDF文件",
        "input": "/workspace/test/服装识别需求描述.pdf",
        "output": "/workspace/output/服装识别需求描述_gpu_test.md",
        "task_type": "pdf_to_markdown"
    }
    
    print(f"\n2. 测试{test_file['name']}转换...")
    
    # 检查输入文件
    if not os.path.exists(test_file['input']):
        print(f"  输入文件不存在: {test_file['input']}")
        return
    
    file_size = os.path.getsize(test_file['input'])
    print(f"  输入文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
        
    # 创建任务
    task_data = {
        "task_type": test_file['task_type'],
        "input_path": test_file['input'],
        "output_path": test_file['output'],
        "priority": "high",  # 高优先级
        "params": {"force_reprocess": True}
    }
    
    try:
        print(f"  创建任务: {test_file['input']} -> {test_file['output']}")
        response = requests.post(
            f"{base_url}/api/tasks",
            json=task_data,
            timeout=30
        )
        
        if response.status_code == 200:
            task_info = response.json()
            task_id = task_info['task_id']
            print(f"  任务创建成功，ID: {task_id}")
            
            # 等待任务完成
            print("  等待任务完成...")
            max_wait = 300  # 最多等待5分钟
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    status_response = requests.get(f"{base_url}/api/tasks/{task_id}")
                    if status_response.status_code == 200:
                        task_status = status_response.json()
                        status = task_status.get('status', 'unknown')
                        
                        elapsed = time.time() - start_time
                        print(f"  任务状态: {status} (已用时: {elapsed:.1f}秒)")
                        
                        if status == 'completed':
                            print(f"  ✅ 任务完成成功! (总用时: {elapsed:.1f}秒)")
                            
                            # 检查输出文件
                            if os.path.exists(test_file['output']):
                                output_size = os.path.getsize(test_file['output'])
                                print(f"  输出文件: {test_file['output']} ({output_size} bytes)")
                                
                                # 显示文件内容预览
                                try:
                                    with open(test_file['output'], 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        print(f"  内容长度: {len(content)} 字符")
                                        print(f"  内容预览:")
                                        print("  " + "="*50)
                                        preview = content[:500] if len(content) > 500 else content
                                        for line in preview.split('\n')[:10]:
                                            print(f"  {line}")
                                        if len(content) > 500:
                                            print("  ...")
                                        print("  " + "="*50)
                                except Exception as e:
                                    print(f"  读取文件错误: {e}")
                            else:
                                print(f"  ⚠️ 输出文件不存在: {test_file['output']}")
                            break
                            
                        elif status == 'failed':
                            print(f"  ❌ 任务失败")
                            if 'error' in task_status:
                                print(f"  错误信息: {task_status['error']}")
                            
                            # 检查是否有错误输出文件
                            if os.path.exists(test_file['output']):
                                print(f"  检查错误输出文件...")
                                try:
                                    with open(test_file['output'], 'r', encoding='utf-8') as f:
                                        error_content = f.read()
                                        print(f"  错误文件内容:")
                                        print("  " + "="*50)
                                        for line in error_content.split('\n')[:20]:
                                            print(f"  {line}")
                                        print("  " + "="*50)
                                except Exception as e:
                                    print(f"  读取错误文件失败: {e}")
                            break
                            
                        elif status in ['pending', 'processing']:
                            time.sleep(5)  # 等待5秒后再检查
                        else:
                            print(f"  未知状态: {status}")
                            break
                    else:
                        print(f"  获取任务状态失败: {status_response.status_code}")
                        break
                except Exception as e:
                    print(f"  检查任务状态错误: {e}")
                    break
            else:
                print(f"  ⏰ 任务超时 (>{max_wait}秒)")
                
        else:
            print(f"  创建任务失败: {response.status_code}")
            print(f"  响应: {response.text}")
            
    except Exception as e:
        print(f"  测试失败: {e}")
    
    print("\n=== MinerU GPU测试完成 ===")

if __name__ == "__main__":
    test_mineru_gpu()
