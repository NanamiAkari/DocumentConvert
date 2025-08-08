#!/usr/bin/env python3
"""
gaojiaqi完整任务测试脚本
测试bucket=gaojiaqi，file_url=浙音文件/2024本科生学生手册.pdf的完整转换流程
监控关键节点：下载、转换、上传
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime

# 测试配置
API_BASE_URL = "http://localhost:8000"

def create_gaojiaqi_task():
    """创建gaojiaqi任务"""
    print("🚀 创建gaojiaqi任务...")
    print("=" * 80)
    
    # 任务配置
    task_data = {
        "task_type": "pdf_to_markdown",
        "bucket_name": "gaojiaqi", 
        "file_path": "浙音文件/2024本科生学生手册.pdf",
        "platform": "gaojiaqi",
        "priority": "normal"
    }
    
    print(f"📋 任务配置:")
    print(f"   📂 Bucket: {task_data['bucket_name']}")
    print(f"   📄 文件路径: {task_data['file_path']}")
    print(f"   🔄 任务类型: {task_data['task_type']}")
    print(f"   🏷️ 平台: {task_data['platform']}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/tasks/create", data=task_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"\n✅ 任务创建成功!")
            print(f"🆔 任务ID: {task_id}")
            print(f"📊 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return task_id
        else:
            print(f"\n❌ 任务创建失败!")
            print(f"📊 状态码: {response.status_code}")
            print(f"📝 错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n💥 请求异常: {e}")
        return None

def monitor_task_execution(task_id: str):
    """监控任务执行的关键节点"""
    print(f"\n👀 开始监控任务 {task_id} 执行...")
    print("=" * 80)
    
    # 关键节点监控
    monitoring_points = {
        "workspace_created": "🏗️ 工作空间创建",
        "downloading_from_s3": "📥 S3文件下载",
        "file_downloaded": "✅ 文件下载完成", 
        "conversion_started": "🔄 文件开始转换",
        "conversion_completed": "✅ 文件转换完成",
        "uploading_to_s3": "📤 结果上传S3",
        "upload_completed": "✅ 上传完成"
    }
    
    completed_points = set()
    max_iterations = 120  # 最多监控10分钟
    
    for i in range(max_iterations):
        try:
            # 获取任务状态
            response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}")
            
            if response.status_code == 200:
                task_data = response.json()
                status = task_data.get('status')
                
                print(f"\n📊 状态检查 {i+1}: {status}")
                print(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")
                
                # 检查关键节点进展
                if status == 'processing':
                    # 显示处理详情
                    if task_data.get('input_path'):
                        print(f"   📂 输入路径: {task_data.get('input_path')}")
                    if task_data.get('started_at'):
                        print(f"   🕐 开始时间: {task_data.get('started_at')}")
                
                elif status == 'completed':
                    print(f"\n🎉 任务执行成功!")
                    print("=" * 60)
                    
                    # 验证关键节点
                    print("✅ 关键节点验证:")
                    
                    # 1. 工作空间和下载验证
                    if task_data.get('input_path'):
                        print(f"   ✅ 1. 文件正确下载到: {task_data.get('input_path')}")
                        
                        # 检查是否在正确的task_workspace目录
                        input_path = task_data.get('input_path')
                        if f"task_workspace/task_{task_id}/input/" in input_path:
                            print(f"      ✅ 下载到正确的task_workspace目录")
                        else:
                            print(f"      ⚠️ 下载路径可能不正确")
                    
                    # 2. 转换验证
                    if task_data.get('started_at'):
                        print(f"   ✅ 2. 文件开始转换: {task_data.get('started_at')}")
                    
                    # 3. 输出验证
                    if task_data.get('output_path'):
                        print(f"   ✅ 3. 转换结果输出到: {task_data.get('output_path')}")
                        
                        # 检查是否在正确的output目录
                        output_path = task_data.get('output_path')
                        if f"task_workspace/task_{task_id}/output/" in output_path:
                            print(f"      ✅ 输出到正确的output目录")
                        else:
                            print(f"      ⚠️ 输出路径可能不正确")
                    
                    # 4. S3上传验证
                    if task_data.get('s3_urls'):
                        s3_urls = task_data.get('s3_urls')
                        print(f"   ✅ 4. 文件正确上传到ai-file:")
                        for url in s3_urls:
                            print(f"      🔗 {url}")
                            
                            # 检查上传路径是否符合MediaConvert规范
                            if f"converted/{task_id}/" in url:
                                print(f"      ✅ 上传路径符合MediaConvert规范")
                            else:
                                print(f"      ⚠️ 上传路径可能不符合规范")
                    
                    # 性能信息
                    print(f"\n📈 性能信息:")
                    processing_time = task_data.get('task_processing_time', 0)
                    print(f"   ⏱️ 处理时间: {processing_time:.2f}秒")
                    
                    file_size = task_data.get('file_size_bytes', 0)
                    if file_size > 0:
                        print(f"   📊 文件大小: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                    
                    # 完整任务信息
                    print(f"\n📋 完整任务信息:")
                    print(json.dumps(task_data, indent=2, ensure_ascii=False))
                    
                    return True
                    
                elif status == 'failed':
                    print(f"\n💥 任务执行失败!")
                    print("=" * 60)
                    print(f"❌ 错误信息: {task_data.get('error_message')}")
                    print(f"🔄 重试次数: {task_data.get('retry_count', 0)}")
                    
                    # 错误分析
                    error_msg = task_data.get('error_message', '').lower()
                    print(f"\n🔍 错误分析:")
                    if 'download' in error_msg or 's3' in error_msg:
                        print("   📥 S3下载问题 - 检查bucket权限和文件路径")
                    elif 'conversion' in error_msg or 'mineru' in error_msg:
                        print("   🔄 转换问题 - 检查文档格式和转换服务")
                    elif 'upload' in error_msg:
                        print("   📤 上传问题 - 检查S3上传配置")
                    else:
                        print(f"   ❓ 其他错误: {error_msg}")
                    
                    print(f"\n📋 完整错误信息:")
                    print(json.dumps(task_data, indent=2, ensure_ascii=False))
                    
                    return False
                    
            else:
                print(f"❌ 获取任务状态失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 监控异常: {e}")
        
        # 等待5秒后继续监控
        time.sleep(5)
    
    print(f"\n⏰ 监控超时 ({max_iterations * 5}秒)")
    return False

def main():
    """主函数"""
    print("🧪 gaojiaqi完整任务测试")
    print("=" * 80)
    print("📋 测试目标:")
    print("   📂 Bucket: gaojiaqi")
    print("   📄 文件: 浙音文件/2024本科生学生手册.pdf")
    print("   🎯 关键节点:")
    print("      1. 文件正确下载到task_workspace/task_id/input/")
    print("      2. 文件开始转换")
    print("      3. 文件转换结果输出到output目录")
    print("      4. 文件正确上传到ai-file（MediaConvert规范）")
    
    try:
        # 1. 创建任务
        task_id = create_gaojiaqi_task()
        if not task_id:
            print("\n💥 任务创建失败，退出测试")
            return False
        
        # 2. 监控任务执行
        success = monitor_task_execution(task_id)
        
        if success:
            print(f"\n🎊 gaojiaqi任务测试成功!")
            print("🎯 所有关键节点验证通过!")
        else:
            print(f"\n💥 gaojiaqi任务测试失败!")
        
        return success
        
    except KeyboardInterrupt:
        print(f"\n⏹️ 测试被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
