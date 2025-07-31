#!/usr/bin/env python3
"""
测试所有文档转换功能
"""

import requests
import json
import time
import os
from pathlib import Path

def test_all_conversions():
    """测试所有文档转换"""
    base_url = "http://localhost:8000"
    
    # 确保输出目录存在
    output_dir = Path("/workspace/output")
    output_dir.mkdir(exist_ok=True)
    
    print("=== 测试所有文档转换功能 ===")
    
    # 测试文件列表
    test_files = [
        {
            "name": "小PDF文件 (MinerU)",
            "input": "/workspace/test/服装识别需求描述.pdf",
            "output": "/workspace/output/服装识别需求描述_final.md",
            "task_type": "pdf_to_markdown"
        },
        {
            "name": "中等PDF文件 (MinerU)",
            "input": "/workspace/test/人工智能与教育报告.pdf",
            "output": "/workspace/output/人工智能与教育报告_final.md",
            "task_type": "pdf_to_markdown"
        },
        {
            "name": "Word文档转Markdown",
            "input": "/workspace/test/智涌君.docx",
            "output": "/workspace/output/智涌君_final.md",
            "task_type": "office_to_markdown"
        },
        {
            "name": "Excel文档转Markdown", 
            "input": "/workspace/test/人工智能竞赛训练平台 v20250629.xlsx",
            "output": "/workspace/output/人工智能竞赛训练平台_final.md",
            "task_type": "office_to_markdown"
        },
        {
            "name": "PowerPoint文档转Markdown",
            "input": "/workspace/test/AI通识课程建设方案.pptx", 
            "output": "/workspace/output/AI通识课程建设方案_final.md",
            "task_type": "office_to_markdown"
        }
    ]
    
    successful_conversions = []
    failed_conversions = []
    
    for i, test_file in enumerate(test_files, 1):
        print(f"\n{i}. 测试{test_file['name']}...")
        
        # 检查输入文件是否存在
        if not os.path.exists(test_file['input']):
            print(f"  ❌ 输入文件不存在: {test_file['input']}")
            failed_conversions.append(test_file['name'])
            continue
            
        file_size = os.path.getsize(test_file['input'])
        print(f"  输入文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
        
        # 删除之前的输出文件
        if os.path.exists(test_file['output']):
            os.remove(test_file['output'])
            
        # 创建任务
        task_data = {
            "task_type": test_file['task_type'],
            "input_path": test_file['input'],
            "output_path": test_file['output'],
            "priority": "high",
            "params": {"force_reprocess": True}
        }
        
        try:
            print(f"  创建任务: {os.path.basename(test_file['input'])} -> {os.path.basename(test_file['output'])}")
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
                max_wait = 600  # 最多等待10分钟
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    try:
                        status_response = requests.get(f"{base_url}/api/tasks/{task_id}")
                        if status_response.status_code == 200:
                            task_status = status_response.json()
                            status = task_status.get('status', 'unknown')
                            
                            elapsed = time.time() - start_time
                            
                            if status == 'completed':
                                print(f"  ✅ 任务完成成功! (用时: {elapsed:.1f}秒)")
                                
                                # 检查输出文件
                                if os.path.exists(test_file['output']):
                                    output_size = os.path.getsize(test_file['output'])
                                    print(f"  输出文件: {output_size} bytes")
                                    
                                    # 显示内容预览
                                    try:
                                        with open(test_file['output'], 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            print(f"  内容长度: {len(content)} 字符")
                                            if len(content) > 100:
                                                preview = content[:100].replace('\n', ' ')
                                                print(f"  内容预览: {preview}...")
                                            else:
                                                print(f"  内容: {content}")
                                    except Exception as e:
                                        print(f"  读取文件错误: {e}")
                                    
                                    successful_conversions.append(test_file['name'])
                                else:
                                    print(f"  ⚠️ 输出文件不存在")
                                    failed_conversions.append(test_file['name'])
                                break
                                
                            elif status == 'failed':
                                print(f"  ❌ 任务失败 (用时: {elapsed:.1f}秒)")
                                if 'error' in task_status:
                                    print(f"  错误信息: {task_status['error']}")
                                failed_conversions.append(test_file['name'])
                                break
                                
                            elif status in ['pending', 'processing']:
                                if int(elapsed) % 30 == 0:  # 每30秒打印一次状态
                                    print(f"  处理中... (已用时: {elapsed:.1f}秒)")
                                time.sleep(5)
                            else:
                                print(f"  未知状态: {status}")
                                failed_conversions.append(test_file['name'])
                                break
                        else:
                            print(f"  获取任务状态失败: {status_response.status_code}")
                            failed_conversions.append(test_file['name'])
                            break
                    except Exception as e:
                        print(f"  检查任务状态错误: {e}")
                        failed_conversions.append(test_file['name'])
                        break
                else:
                    print(f"  ⏰ 任务超时 (>{max_wait}秒)")
                    failed_conversions.append(test_file['name'])
                    
            else:
                print(f"  创建任务失败: {response.status_code}")
                print(f"  响应: {response.text}")
                failed_conversions.append(test_file['name'])
                
        except Exception as e:
            print(f"  测试失败: {e}")
            failed_conversions.append(test_file['name'])
    
    # 总结
    print(f"\n=== 转换测试总结 ===")
    print(f"总测试文件: {len(test_files)}")
    print(f"成功转换: {len(successful_conversions)}")
    print(f"失败转换: {len(failed_conversions)}")
    
    if successful_conversions:
        print(f"\n✅ 成功转换的文件:")
        for name in successful_conversions:
            print(f"  - {name}")
    
    if failed_conversions:
        print(f"\n❌ 失败转换的文件:")
        for name in failed_conversions:
            print(f"  - {name}")
    
    print(f"\n转换成功率: {len(successful_conversions)/len(test_files)*100:.1f}%")

if __name__ == "__main__":
    test_all_conversions()
