#!/usr/bin/env python3
"""
gaojiaqi任务测试脚本
测试浙音文件/2024本科生学生手册.pdf的完整转换流程
"""

import asyncio
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any

# 测试配置
API_BASE_URL = "http://localhost:8000"
TEST_TASK_CONFIG = {
    "task_type": "pdf_to_markdown",
    "bucket_name": "ai-file",
    "file_path": "2024本科生学生手册.pdf",
    "platform": "gaojiaqi",
    "priority": "normal",
    "callback_url": None  # 可以设置回调URL进行测试
}

# 监控关键节点
MONITORING_POINTS = [
    "文件正确下载到指定目录",
    "文件开始转换", 
    "文件转换结果输出到正确的output目录",
    "文件正确上传到ai-file"
]


class TaskTester:
    """任务测试器"""
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.task_id = None
        
    def test_service_health(self) -> bool:
        """测试服务健康状态"""
        try:
            print("🔍 检查服务健康状态...")
            response = self.session.get(f"{self.api_base_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 服务状态: {health_data.get('status', 'unknown')}")
                print(f"📊 处理器状态: {health_data.get('processor_status', {})}")
                return True
            else:
                print(f"❌ 服务健康检查失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 服务连接失败: {e}")
            return False
    
    def create_test_task(self) -> str:
        """创建测试任务"""
        try:
            print("\n🚀 创建gaojiaqi测试任务...")
            print(f"📄 文件: s3://{TEST_TASK_CONFIG['bucket_name']}/{TEST_TASK_CONFIG['file_path']}")
            print(f"🔄 任务类型: {TEST_TASK_CONFIG['task_type']}")
            print(f"🏷️ 平台: {TEST_TASK_CONFIG['platform']}")
            
            response = self.session.post(
                f"{self.api_base_url}/api/tasks/create",
                data=TEST_TASK_CONFIG
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                print(f"✅ 任务创建成功: {task_id}")
                print(f"📝 消息: {result.get('message')}")
                return task_id
            else:
                print(f"❌ 任务创建失败: {response.status_code}")
                print(f"📝 错误: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 任务创建异常: {e}")
            return None
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            response = self.session.get(f"{self.api_base_url}/api/tasks/{task_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取任务状态失败: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ 获取任务状态异常: {e}")
            return {}
    
    def monitor_task_progress(self, task_id: str, timeout: int = 600) -> bool:
        """监控任务进度"""
        print(f"\n👀 开始监控任务 {task_id} 的执行进度...")
        print("🎯 监控关键节点:")
        for i, point in enumerate(MONITORING_POINTS, 1):
            print(f"   {i}. {point}")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            try:
                task_data = self.get_task_status(task_id)
                
                if not task_data:
                    time.sleep(5)
                    continue
                
                current_status = task_data.get('status')
                
                # 状态变化时打印详细信息
                if current_status != last_status:
                    print(f"\n📊 任务状态更新: {last_status} → {current_status}")
                    self._print_task_details(task_data)
                    last_status = current_status
                
                # 检查完成状态
                if current_status == 'completed':
                    print("\n🎉 任务执行成功!")
                    self._print_success_summary(task_data)
                    return True
                elif current_status == 'failed':
                    print("\n💥 任务执行失败!")
                    self._print_failure_summary(task_data)
                    return False
                
                # 显示进度点
                print(".", end="", flush=True)
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n⏹️ 用户中断监控")
                return False
            except Exception as e:
                print(f"\n❌ 监控异常: {e}")
                time.sleep(5)
        
        print(f"\n⏰ 监控超时 ({timeout}秒)")
        return False
    
    def _print_task_details(self, task_data: Dict[str, Any]):
        """打印任务详细信息"""
        print(f"   📋 任务ID: {task_data.get('id')}")
        print(f"   📂 输入路径: {task_data.get('input_path', 'N/A')}")
        print(f"   📤 输出路径: {task_data.get('output_path', 'N/A')}")
        print(f"   📊 文件大小: {task_data.get('file_size_bytes', 0)} bytes")
        print(f"   ⏱️ 创建时间: {task_data.get('created_at', 'N/A')}")
        print(f"   🔄 重试次数: {task_data.get('retry_count', 0)}")
        
        if task_data.get('error_message'):
            print(f"   ❌ 错误信息: {task_data.get('error_message')}")
    
    def _print_success_summary(self, task_data: Dict[str, Any]):
        """打印成功总结"""
        print("=" * 60)
        print("🎊 任务执行成功总结")
        print("=" * 60)
        
        # 关键节点验证
        print("✅ 关键节点验证:")
        
        # 1. 文件下载验证
        if task_data.get('input_path'):
            print(f"   ✅ 1. 文件正确下载到: {task_data.get('input_path')}")
        else:
            print("   ❌ 1. 文件下载信息缺失")
        
        # 2. 文件转换验证
        if task_data.get('result'):
            print("   ✅ 2. 文件转换成功")
        else:
            print("   ❌ 2. 文件转换结果缺失")
        
        # 3. 输出文件验证
        if task_data.get('output_path'):
            print(f"   ✅ 3. 转换结果输出到: {task_data.get('output_path')}")
        else:
            print("   ❌ 3. 输出文件路径缺失")
        
        # 4. S3上传验证
        if task_data.get('s3_urls'):
            print(f"   ✅ 4. 文件正确上传到ai-file: {task_data.get('s3_urls')[0]}")
        else:
            print("   ❌ 4. S3上传信息缺失")
        
        # 性能信息
        print(f"\n📈 性能信息:")
        print(f"   ⏱️ 处理时间: {task_data.get('task_processing_time', 0):.2f}秒")
        print(f"   📊 文件大小: {task_data.get('file_size_bytes', 0)} bytes")
        
        # 访问信息
        if task_data.get('output_url'):
            print(f"\n🔗 访问链接:")
            print(f"   🌐 HTTP URL: {task_data.get('output_url')}")
        
        print("=" * 60)
    
    def _print_failure_summary(self, task_data: Dict[str, Any]):
        """打印失败总结"""
        print("=" * 60)
        print("💥 任务执行失败总结")
        print("=" * 60)
        
        print(f"❌ 错误信息: {task_data.get('error_message', 'Unknown error')}")
        print(f"🔄 重试次数: {task_data.get('retry_count', 0)}")
        print(f"⏱️ 最后重试时间: {task_data.get('last_retry_at', 'N/A')}")
        
        print("\n🔍 故障排查建议:")
        error_msg = task_data.get('error_message', '').lower()
        
        if 'file not found' in error_msg:
            print("   📂 检查输入文件是否存在于指定的S3路径")
        elif 'permission' in error_msg:
            print("   🔐 检查S3访问权限配置")
        elif 'conversion' in error_msg:
            print("   🔄 检查文档转换服务状态")
        elif 'upload' in error_msg:
            print("   📤 检查S3上传配置和权限")
        else:
            print("   📋 查看详细日志获取更多信息")
        
        print("=" * 60)
    
    def run_complete_test(self) -> bool:
        """运行完整测试"""
        print("🧪 开始gaojiaqi任务完整测试")
        print("=" * 60)
        
        # 1. 健康检查
        if not self.test_service_health():
            print("❌ 服务健康检查失败，测试终止")
            return False
        
        # 2. 创建任务
        task_id = self.create_test_task()
        if not task_id:
            print("❌ 任务创建失败，测试终止")
            return False
        
        self.task_id = task_id
        
        # 3. 监控任务执行
        success = self.monitor_task_progress(task_id)
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 gaojiaqi任务测试完成 - 成功")
        else:
            print("💥 gaojiaqi任务测试完成 - 失败")
        print("=" * 60)
        
        return success


def main():
    """主函数"""
    tester = TaskTester()
    
    try:
        success = tester.run_complete_test()
        exit_code = 0 if success else 1
        exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        exit(1)


if __name__ == "__main__":
    main()
