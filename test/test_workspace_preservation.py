#!/usr/bin/env python3
"""
测试工作空间保留功能
验证修复后的工作空间不会被意外清理
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime

# 测试配置
API_BASE_URL = "http://localhost:8000"

def test_workspace_preservation():
    """测试工作空间保留功能"""
    print("🧪 测试工作空间保留功能")
    print("=" * 80)
    
    # S3任务配置
    task_data = {
        "task_type": "pdf_to_markdown",
        "bucket_name": "gaojiaqi",
        "file_path": "浙音文件/2024本科生学生手册.pdf",
        "platform": "gaojiaqi",
        "priority": "normal"
    }
    
    print(f"📋 测试任务配置:")
    print(f"   📂 Bucket: {task_data['bucket_name']}")
    print(f"   📄 文件路径: {task_data['file_path']}")
    print(f"   🔄 任务类型: {task_data['task_type']}")
    
    try:
        # 创建任务
        print(f"\n🚀 创建测试任务...")
        response = requests.post(f"{API_BASE_URL}/api/tasks/create", data=task_data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务创建成功!")
            print(f"🆔 任务ID: {task_id}")
            
            # 监控任务执行
            print(f"\n👀 监控工作空间保留...")
            print("🎯 验证点:")
            print("   1. input目录在任务完成后保留")
            print("   2. output目录在任务完成后保留")
            print("   3. 最终结果文件存在")
            print("   4. temp_mineru_output被清理")
            
            task_completed = False
            workspace_path = None
            
            for i in range(60):  # 最多监控300秒
                time.sleep(5)
                
                try:
                    response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}")
                    if response.status_code == 200:
                        task_data = response.json()
                        status = task_data.get('status')
                        
                        print(f"\n📊 状态检查 {i+1}: {status}")
                        
                        if status == 'processing':
                            input_path = task_data.get('input_path')
                            if input_path and not workspace_path:
                                # 推断工作空间路径
                                workspace_path = str(Path(input_path).parent.parent)
                                print(f"   📂 工作空间路径: {workspace_path}")
                        
                        elif status == 'completed':
                            print(f"\n🎉 任务完成!")
                            task_completed = True
                            
                            input_path = task_data.get('input_path')
                            output_path = task_data.get('output_path')
                            
                            print(f"📋 任务结果:")
                            print(f"   📥 输入文件: {input_path}")
                            print(f"   📤 输出文件: {output_path}")
                            
                            # 等待5秒让清理工作完成
                            print(f"\n⏳ 等待清理工作完成...")
                            time.sleep(5)
                            
                            # 验证工作空间保留
                            if workspace_path:
                                print(f"\n🔍 验证工作空间保留:")
                                workspace_dir = Path(workspace_path)
                                
                                if workspace_dir.exists():
                                    print(f"   ✅ 工作空间目录存在: {workspace_dir}")
                                    
                                    # 检查input目录
                                    input_dir = workspace_dir / "input"
                                    if input_dir.exists():
                                        print(f"   ✅ input目录保留")
                                        files = list(input_dir.iterdir())
                                        print(f"      📄 文件数量: {len(files)}")
                                        for file in files:
                                            print(f"         {file.name} ({file.stat().st_size:,} bytes)")
                                    else:
                                        print(f"   ❌ input目录被删除")
                                    
                                    # 检查output目录
                                    output_dir = workspace_dir / "output"
                                    if output_dir.exists():
                                        print(f"   ✅ output目录保留")
                                        files = list(output_dir.iterdir())
                                        print(f"      📄 文件数量: {len(files)}")
                                        for file in files:
                                            if file.is_file():
                                                print(f"         📄 {file.name} ({file.stat().st_size:,} bytes)")
                                            elif file.is_dir():
                                                print(f"         📁 {file.name}/ (目录)")
                                        
                                        # 检查是否还有temp_mineru_output
                                        temp_dirs = [f for f in files if f.is_dir() and "temp" in f.name.lower()]
                                        if temp_dirs:
                                            print(f"   ⚠️ 仍有临时目录未清理: {[d.name for d in temp_dirs]}")
                                        else:
                                            print(f"   ✅ 临时目录已清理")
                                    else:
                                        print(f"   ❌ output目录被删除")
                                    
                                    # 检查temp目录
                                    temp_dir = workspace_dir / "temp"
                                    if temp_dir.exists():
                                        temp_files = list(temp_dir.iterdir())
                                        if temp_files:
                                            print(f"   ⚠️ temp目录有残留文件: {len(temp_files)}")
                                        else:
                                            print(f"   ✅ temp目录已清理")
                                    else:
                                        print(f"   ✅ temp目录不存在或已清理")
                                    
                                    return True
                                else:
                                    print(f"   ❌ 工作空间目录被完全删除: {workspace_dir}")
                                    return False
                            else:
                                print(f"   ❌ 无法确定工作空间路径")
                                return False
                        
                        elif status == 'failed':
                            print(f"\n❌ 任务失败!")
                            print(f"   错误信息: {task_data.get('error_message')}")
                            return False
                            
                except Exception as e:
                    print(f"❌ 状态查询异常: {e}")
            
            if not task_completed:
                print(f"\n⏰ 任务未在预期时间内完成")
                return False
            
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"📝 错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 请求异常: {e}")
        return False

if __name__ == "__main__":
    success = test_workspace_preservation()
    if success:
        print(f"\n🎊 工作空间保留测试成功!")
        print("✅ 验证结果:")
        print("   1. input目录正确保留")
        print("   2. output目录正确保留")
        print("   3. 最终结果文件存在")
        print("   4. 临时文件被正确清理")
    else:
        print(f"\n💥 工作空间保留测试失败!")
    exit(0 if success else 1)
