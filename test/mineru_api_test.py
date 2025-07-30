#!/usr/bin/env python3
"""
MinerU官方API测试脚本

测试调用官方API进行PDF转Markdown转换的可行性
"""

import requests
import json
import time
import os
from pathlib import Path


class MinerUAPIClient:
    """MinerU官方API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://mineru.net/api/v4"):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
    
    def extract_pdf_from_url(self, pdf_url: str, is_ocr: bool = True, enable_formula: bool = False):
        """
        从URL提取PDF内容
        
        Args:
            pdf_url: PDF文件URL
            is_ocr: 是否启用OCR
            enable_formula: 是否启用公式识别
            
        Returns:
            dict: API响应结果
        """
        url = f"{self.base_url}/extract/task"
        
        payload = {
            "url": pdf_url,
            "is_ocr": is_ocr,
            "enable_formula": enable_formula
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None
    
    def get_task_status(self, task_id: str):
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务状态信息
        """
        url = f"{self.base_url}/extract/task/{task_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取任务状态失败: {e}")
            return None
    
    def wait_for_completion(self, task_id: str, max_wait_time: int = 300, check_interval: int = 10):
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            dict: 最终任务状态
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_task_status(task_id)
            if not status:
                return None
            
            print(f"任务状态: {status.get('status', 'unknown')}")
            
            if status.get('status') == 'completed':
                return status
            elif status.get('status') == 'failed':
                print(f"任务失败: {status.get('error', 'unknown error')}")
                return status
            
            time.sleep(check_interval)
        
        print(f"任务超时，等待时间超过{max_wait_time}秒")
        return None


def test_mineru_api():
    """测试MinerU API"""
    # 注意：这里需要真实的API密钥
    api_key = "your_api_key_here"  # 需要替换为真实的API密钥
    
    if api_key == "your_api_key_here":
        print("错误：请先设置真实的API密钥")
        return False
    
    client = MinerUAPIClient(api_key)
    
    # 测试PDF URL
    test_pdf_url = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
    
    print(f"开始测试MinerU API...")
    print(f"PDF URL: {test_pdf_url}")
    
    # 创建提取任务
    result = client.extract_pdf_from_url(
        pdf_url=test_pdf_url,
        is_ocr=True,
        enable_formula=False
    )
    
    if not result:
        print("创建任务失败")
        return False
    
    print(f"任务创建成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    task_id = result.get('task_id')
    if not task_id:
        print("未获取到任务ID")
        return False
    
    # 等待任务完成
    print(f"等待任务完成，任务ID: {task_id}")
    final_status = client.wait_for_completion(task_id)
    
    if final_status:
        print(f"任务最终状态: {json.dumps(final_status, indent=2, ensure_ascii=False)}")
        return final_status.get('status') == 'completed'
    
    return False


def test_concurrent_api_calls():
    """测试并发API调用"""
    import threading
    import concurrent.futures
    
    api_key = "your_api_key_here"  # 需要替换为真实的API密钥
    
    if api_key == "your_api_key_here":
        print("错误：请先设置真实的API密钥")
        return False
    
    client = MinerUAPIClient(api_key)
    test_pdf_url = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
    
    def create_task():
        """创建单个任务"""
        return client.extract_pdf_from_url(
            pdf_url=test_pdf_url,
            is_ocr=True,
            enable_formula=False
        )
    
    print("测试并发API调用（2个进程）...")
    
    # 使用线程池测试并发
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create_task) for _ in range(2)]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                print(f"任务创建结果: {result}")
            except Exception as e:
                print(f"任务创建异常: {e}")
                results.append(None)
    
    success_count = sum(1 for r in results if r is not None)
    print(f"成功创建任务数: {success_count}/2")
    
    return success_count > 0


if __name__ == "__main__":
    print("=== MinerU官方API测试 ===")
    
    # 基础API测试
    print("\n1. 基础API功能测试")
    basic_test_result = test_mineru_api()
    print(f"基础测试结果: {'成功' if basic_test_result else '失败'}")
    
    # 并发测试
    print("\n2. 并发API调用测试")
    concurrent_test_result = test_concurrent_api_calls()
    print(f"并发测试结果: {'成功' if concurrent_test_result else '失败'}")
    
    print("\n=== 测试总结 ===")
    print(f"基础功能: {'✓' if basic_test_result else '✗'}")
    print(f"并发调用: {'✓' if concurrent_test_result else '✗'}")
    
    if basic_test_result and concurrent_test_result:
        print("\n结论: MinerU官方API支持并发调用，可以集成到现有系统中")
    else:
        print("\n结论: 需要进一步调试API调用问题")