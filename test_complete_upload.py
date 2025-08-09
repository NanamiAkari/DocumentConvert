#!/usr/bin/env python3
"""
测试完整上传功能
"""

import requests
import time
import os
from pathlib import Path

def test_complete_upload():
    """测试完整的上传功能"""
    
    # 创建新的测试任务
    print("🚀 创建新的PDF转换任务...")
    task_data = {
        "task_type": "pdf_to_markdown",
        "input_path": "/workspace/test/服装识别需求描述.pdf",  # 使用一个较小的文件
        "platform": "local",
        "priority": "high"
    }
    
    response = requests.post("http://localhost:8000/api/tasks/create", data=task_data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        task_id = result.get('task_id')
        print(f"任务ID: {task_id}")
        
        # 等待任务完成
        print("⏳ 等待任务完成...")
        max_wait_time = 300  # 最多等待5分钟
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(f"http://localhost:8000/api/tasks/{task_id}")
            if status_response.status_code == 200:
                status = status_response.json()
                current_status = status.get('status')
                progress = status.get('progress', 0)
                
                print(f"📊 任务状态: {current_status}, 进度: {progress}%")
                
                if current_status in ['completed', 'failed']:
                    break
                    
            time.sleep(10)  # 每10秒检查一次
        
        # 检查最终状态和上传结果
        final_response = requests.get(f"http://localhost:8000/api/tasks/{task_id}")
        if final_response.status_code == 200:
            final_status = final_response.json()
            print(f"\n✅ 最终状态: {final_status.get('status')}")
            
            if final_status.get('status') == 'completed':
                # 检查输出文件
                workspace_path = f"/app/task_workspace/task_{task_id}"
                output_path = f"{workspace_path}/output"
                
                print(f"\n📁 检查输出目录: {output_path}")
                
                if os.path.exists(output_path):
                    print("📄 本地输出文件列表:")
                    for root, dirs, files in os.walk(output_path):
                        level = root.replace(output_path, '').count(os.sep)
                        indent = '  ' * level
                        print(f"{indent}{os.path.basename(root)}/")
                        subindent = '  ' * (level + 1)
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_size = os.path.getsize(file_path)
                            print(f"{subindent}{file} ({file_size} bytes)")
                    
                    # 检查S3上传结果
                    s3_urls = final_status.get('s3_urls', [])
                    print(f"\n☁️ S3上传结果:")
                    print(f"  上传的文件数量: {len(s3_urls)}")
                    
                    if s3_urls:
                        print(f"  上传的文件URL:")
                        for i, url in enumerate(s3_urls[:10]):  # 只显示前10个
                            print(f"    {i+1}. {url}")
                        if len(s3_urls) > 10:
                            print(f"    ... 还有 {len(s3_urls) - 10} 个文件")
                    
                    # 检查主要输出URL
                    output_url = final_status.get('output_url')
                    if output_url:
                        print(f"\n🔗 主要输出文件URL: {output_url}")
                    
                    # 统计文件类型
                    md_count = len([url for url in s3_urls if url.endswith('.md')])
                    json_count = len([url for url in s3_urls if url.endswith('.json')])
                    img_count = len([url for url in s3_urls if any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])])
                    
                    print(f"\n📊 上传文件统计:")
                    print(f"  Markdown文件: {md_count}")
                    print(f"  JSON文件: {json_count}")
                    print(f"  图片文件: {img_count}")
                    print(f"  其他文件: {len(s3_urls) - md_count - json_count - img_count}")
                    
                    # 验证上传完整性
                    local_files = []
                    for root, dirs, files in os.walk(output_path):
                        for file in files:
                            local_files.append(file)
                    
                    uploaded_filenames = [url.split('/')[-1] for url in s3_urls]
                    missing_files = [f for f in local_files if f not in uploaded_filenames]
                    
                    if missing_files:
                        print(f"\n⚠️ 未上传的文件: {missing_files}")
                    else:
                        print(f"\n✅ 所有文件都已成功上传到MinIO!")
                
                else:
                    print("❌ 输出目录不存在")
            else:
                print(f"❌ 任务失败: {final_status.get('error_message', '未知错误')}")
        
    else:
        print(f"❌ 创建任务失败: {response.text}")

if __name__ == "__main__":
    test_complete_upload()
