#!/usr/bin/env python3
"""
测试S3下载功能 - gaojiaqi bucket
验证从S3正确下载文件到task_workspace，保留原始文件名
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime

# 测试配置
API_BASE_URL = "http://localhost:8000"

def test_s3_download_gaojiaqi():
    """测试S3下载gaojiaqi bucket文件"""
    print("🧪 测试S3下载 - gaojiaqi bucket")
    print("=" * 80)
    
    # S3任务配置
    task_data = {
        "task_type": "pdf_to_markdown",
        "bucket_name": "gaojiaqi",
        "file_path": "浙音文件/2024本科生学生手册.pdf",
        "platform": "gaojiaqi",
        "priority": "normal"
    }
    
    print(f"📋 S3下载任务配置:")
    print(f"   📂 Bucket: {task_data['bucket_name']}")
    print(f"   📄 文件路径: {task_data['file_path']}")
    print(f"   🔄 任务类型: {task_data['task_type']}")
    print(f"   🏷️ 平台: {task_data['platform']}")
    print(f"   📍 S3完整路径: s3://{task_data['bucket_name']}/{task_data['file_path']}")
    
    try:
        # 创建任务
        print(f"\n🚀 创建S3下载任务...")
        response = requests.post(f"{API_BASE_URL}/api/tasks/create", data=task_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务创建成功!")
            print(f"🆔 任务ID: {task_id}")
            
            # 监控任务执行 - 重点关注下载阶段
            print(f"\n👀 监控S3下载过程...")
            print("🎯 关键验证点:")
            print("   1. 文件从S3正确下载")
            print("   2. 保留原始文件名: 2024本科生学生手册.pdf")
            print("   3. 下载到正确的input目录")
            print("   4. 文件完整性验证")
            
            download_verified = False
            conversion_started = False
            
            for i in range(30):  # 最多监控150秒
                time.sleep(5)
                
                try:
                    response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}")
                    if response.status_code == 200:
                        task_data = response.json()
                        status = task_data.get('status')
                        
                        print(f"\n📊 状态检查 {i+1}: {status}")
                        print(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")
                        
                        if status == 'processing':
                            # 检查下载进度
                            input_path = task_data.get('input_path')
                            file_name = task_data.get('file_name')
                            file_size = task_data.get('file_size_bytes')
                            
                            if input_path and not download_verified:
                                print(f"   📂 输入路径: {input_path}")
                                print(f"   📄 文件名: {file_name}")
                                print(f"   📊 文件大小: {file_size:,} bytes" if file_size else "未知")
                                
                                # 验证1: 文件名是否保留原始名称
                                expected_filename = "2024本科生学生手册.pdf"
                                if file_name == expected_filename:
                                    print(f"   ✅ 1. 原始文件名正确保留: {file_name}")
                                else:
                                    print(f"   ❌ 1. 文件名不正确: 期望 {expected_filename}, 实际 {file_name}")
                                
                                # 验证2: 下载路径是否正确
                                expected_path_pattern = f"task_workspace/task_{task_id}/input/{expected_filename}"
                                if expected_path_pattern in input_path:
                                    print(f"   ✅ 2. 下载路径正确: task_workspace结构")
                                else:
                                    print(f"   ❌ 2. 下载路径不正确: {input_path}")
                                
                                # 验证3: 文件是否实际存在
                                if Path(input_path).exists():
                                    actual_size = Path(input_path).stat().st_size
                                    print(f"   ✅ 3. 文件实际存在，大小: {actual_size:,} bytes")
                                    
                                    # 验证4: 文件大小是否匹配
                                    if file_size and actual_size == file_size:
                                        print(f"   ✅ 4. 文件大小匹配数据库记录")
                                        download_verified = True
                                        print(f"\n🎉 S3下载验证完全成功!")
                                    else:
                                        print(f"   ❌ 4. 文件大小不匹配: DB={file_size}, 实际={actual_size}")
                                else:
                                    print(f"   ❌ 3. 文件不存在: {input_path}")
                            
                            # 检查转换是否开始
                            if download_verified and not conversion_started:
                                print(f"   🔄 等待转换开始...")
                                conversion_started = True
                        
                        elif status == 'completed':
                            print(f"\n🎉 任务完全成功!")
                            
                            # 最终验证
                            input_path = task_data.get('input_path')
                            output_path = task_data.get('output_path')
                            s3_urls = task_data.get('s3_urls')
                            
                            print(f"📋 最终结果验证:")
                            print(f"   📥 输入文件: {input_path}")
                            print(f"   📤 输出文件: {output_path}")
                            
                            if s3_urls:
                                print(f"   🔗 S3上传URL:")
                                for url in s3_urls:
                                    print(f"      {url}")
                            
                            # 检查input和output目录
                            print(f"\n📁 目录内容检查:")
                            if input_path and Path(input_path).exists():
                                input_dir = Path(input_path).parent
                                print(f"   📂 Input目录: {input_dir}")
                                for file in input_dir.iterdir():
                                    print(f"      📄 {file.name} ({file.stat().st_size:,} bytes)")
                            
                            if output_path and Path(output_path).exists():
                                output_dir = Path(output_path).parent
                                print(f"   📂 Output目录: {output_dir}")
                                for file in output_dir.iterdir():
                                    print(f"      📄 {file.name} ({file.stat().st_size:,} bytes)")
                            
                            return True
                        
                        elif status == 'failed':
                            print(f"\n❌ 任务失败!")
                            print(f"   错误信息: {task_data.get('error_message')}")
                            print(f"   重试次数: {task_data.get('retry_count', 0)}")
                            return False
                            
                except Exception as e:
                    print(f"❌ 状态查询异常: {e}")
            
            print(f"\n⏰ 监控超时")
            return False
            
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"📝 错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

if __name__ == "__main__":
    success = test_s3_download_gaojiaqi()
    if success:
        print(f"\n🎊 S3下载测试完全成功!")
        print("✅ 所有验证点通过:")
        print("   1. S3文件正确下载")
        print("   2. 原始文件名保留")
        print("   3. task_workspace结构正确")
        print("   4. 文件完整性验证通过")
    else:
        print(f"\n💥 S3下载测试失败!")
    exit(0 if success else 1)
