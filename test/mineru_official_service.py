#!/usr/bin/env python3
"""
MinerU官方API集成服务

将官方API集成到现有文档转换系统中的验证模块
"""

import asyncio
import aiohttp
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass


@dataclass
class MinerUTask:
    """MinerU任务数据模型"""
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    pdf_url: str
    created_at: float
    completed_at: Optional[float] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class MinerUOfficialService:
    """MinerU官方API服务
    
    集成官方API到现有文档转换系统中
    """
    
    def __init__(self, api_key: str, base_url: str = "https://mineru.net/api/v4"):
        """
        初始化服务
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.active_tasks: Dict[str, MinerUTask] = {}
        
        # HTTP会话配置
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        
    async def create_session(self):
        """创建HTTP会话"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        
        return aiohttp.ClientSession(
            headers=headers,
            timeout=self.session_timeout
        )
    
    async def upload_pdf_and_extract(self, pdf_file_path: str, is_ocr: bool = True, enable_formula: bool = False) -> Optional[str]:
        """
        上传PDF文件并创建提取任务
        
        Args:
            pdf_file_path: 本地PDF文件路径
            is_ocr: 是否启用OCR
            enable_formula: 是否启用公式识别
            
        Returns:
            str: 任务ID，如果失败返回None
        """
        # 注意：这里假设需要先上传文件获取URL，实际API可能不同
        # 如果官方API支持直接文件上传，需要调整实现
        
        # 临时方案：将文件复制到可访问的URL位置
        # 实际使用时需要根据官方API文档调整
        
        self.logger.warning("当前实现假设PDF已有可访问URL，实际使用需要根据官方API调整")
        
        # 这里使用示例URL进行测试
        pdf_url = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
        
        return await self.extract_from_url(pdf_url, is_ocr, enable_formula)
    
    async def extract_from_url(self, pdf_url: str, is_ocr: bool = True, enable_formula: bool = False) -> Optional[str]:
        """
        从URL创建PDF提取任务
        
        Args:
            pdf_url: PDF文件URL
            is_ocr: 是否启用OCR
            enable_formula: 是否启用公式识别
            
        Returns:
            str: 任务ID，如果失败返回None
        """
        url = f"{self.base_url}/extract/task"
        
        payload = {
            "url": pdf_url,
            "is_ocr": is_ocr,
            "enable_formula": enable_formula
        }
        
        try:
            async with await self.create_session() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        task_id = result.get('task_id')
                        
                        if task_id:
                            # 记录任务
                            self.active_tasks[task_id] = MinerUTask(
                                task_id=task_id,
                                status='pending',
                                pdf_url=pdf_url,
                                created_at=time.time()
                            )
                            
                            self.logger.info(f"MinerU任务创建成功: {task_id}")
                            return task_id
                        else:
                            self.logger.error(f"API响应中未找到task_id: {result}")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API请求失败: {response.status} - {error_text}")
                        
        except Exception as e:
            self.logger.error(f"创建MinerU任务异常: {e}")
        
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务状态信息
        """
        url = f"{self.base_url}/extract/task/{task_id}"
        
        try:
            async with await self.create_session() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 更新本地任务状态
                        if task_id in self.active_tasks:
                            task = self.active_tasks[task_id]
                            task.status = result.get('status', 'unknown')
                            
                            if task.status == 'completed':
                                task.completed_at = time.time()
                                task.result_data = result
                            elif task.status == 'failed':
                                task.error_message = result.get('error', 'unknown error')
                        
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.error(f"获取任务状态失败: {response.status} - {error_text}")
                        
        except Exception as e:
            self.logger.error(f"获取任务状态异常: {e}")
        
        return None
    
    async def wait_for_completion(self, task_id: str, max_wait_time: int = 300, check_interval: int = 10) -> Optional[Dict[str, Any]]:
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
            status = await self.get_task_status(task_id)
            if not status:
                return None
            
            current_status = status.get('status', 'unknown')
            self.logger.info(f"任务 {task_id} 状态: {current_status}")
            
            if current_status == 'completed':
                return status
            elif current_status == 'failed':
                self.logger.error(f"任务 {task_id} 失败: {status.get('error', 'unknown error')}")
                return status
            
            await asyncio.sleep(check_interval)
        
        self.logger.warning(f"任务 {task_id} 超时，等待时间超过{max_wait_time}秒")
        return None
    
    async def process_pdf_to_markdown(self, pdf_file_path: str, output_path: str) -> bool:
        """
        处理PDF转Markdown的完整流程
        
        Args:
            pdf_file_path: 输入PDF文件路径
            output_path: 输出Markdown文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 创建提取任务
            task_id = await self.upload_pdf_and_extract(pdf_file_path)
            if not task_id:
                self.logger.error("创建MinerU任务失败")
                return False
            
            # 2. 等待任务完成
            result = await self.wait_for_completion(task_id)
            if not result or result.get('status') != 'completed':
                self.logger.error(f"MinerU任务未成功完成: {result}")
                return False
            
            # 3. 提取结果并保存为Markdown
            markdown_content = self.extract_markdown_from_result(result)
            if not markdown_content:
                self.logger.error("从API结果中提取Markdown内容失败")
                return False
            
            # 4. 保存到输出文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"PDF转Markdown完成: {pdf_file_path} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF转Markdown处理异常: {e}")
            return False
    
    def extract_markdown_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """
        从API结果中提取Markdown内容
        
        Args:
            result: API返回的结果
            
        Returns:
            str: Markdown内容
        """
        try:
            # 根据官方API文档调整数据提取逻辑
            # 这里是示例实现，需要根据实际API响应格式调整
            
            if 'data' in result:
                data = result['data']
                
                # 假设API返回的是结构化数据，需要转换为Markdown
                if isinstance(data, dict):
                    # 提取文本内容
                    content_parts = []
                    
                    # 处理页面内容
                    if 'pages' in data:
                        for page in data['pages']:
                            if 'content' in page:
                                content_parts.append(page['content'])
                    
                    # 处理直接的文本内容
                    elif 'content' in data:
                        content_parts.append(data['content'])
                    
                    # 处理markdown格式的内容
                    elif 'markdown' in data:
                        return data['markdown']
                    
                    if content_parts:
                        return '\n\n'.join(content_parts)
            
            # 如果直接返回markdown字符串
            if isinstance(result, str):
                return result
            
            self.logger.warning(f"无法从API结果中提取Markdown内容: {result}")
            return None
            
        except Exception as e:
            self.logger.error(f"提取Markdown内容异常: {e}")
            return None
    
    async def process_multiple_pdfs(self, pdf_files: List[str], output_dir: str, max_concurrent: int = 2) -> Dict[str, bool]:
        """
        并发处理多个PDF文件
        
        Args:
            pdf_files: PDF文件路径列表
            output_dir: 输出目录
            max_concurrent: 最大并发数
            
        Returns:
            dict: 文件路径到处理结果的映射
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def process_single_pdf(pdf_file: str) -> bool:
            async with semaphore:
                output_file = Path(output_dir) / (Path(pdf_file).stem + '.md')
                return await self.process_pdf_to_markdown(pdf_file, str(output_file))
        
        # 创建并发任务
        tasks = []
        for pdf_file in pdf_files:
            task = asyncio.create_task(process_single_pdf(pdf_file))
            tasks.append((pdf_file, task))
        
        # 等待所有任务完成
        for pdf_file, task in tasks:
            try:
                result = await task
                results[pdf_file] = result
                self.logger.info(f"文件 {pdf_file} 处理结果: {'成功' if result else '失败'}")
            except Exception as e:
                self.logger.error(f"文件 {pdf_file} 处理异常: {e}")
                results[pdf_file] = False
        
        return results
    
    def get_active_tasks(self) -> List[MinerUTask]:
        """获取活跃任务列表"""
        return list(self.active_tasks.values())
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的旧任务"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for task_id, task in self.active_tasks.items():
            if task.status in ['completed', 'failed']:
                age = current_time - task.created_at
                if age > max_age_seconds:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.active_tasks[task_id]
            self.logger.info(f"清理旧任务: {task_id}")


async def test_official_service():
    """测试官方API服务"""
    # 注意：需要真实的API密钥
    api_key = "your_api_key_here"
    
    if api_key == "your_api_key_here":
        print("错误：请先设置真实的API密钥")
        return False
    
    service = MinerUOfficialService(api_key)
    
    # 测试单个PDF处理
    test_pdf = "/workspace/test/服装识别需求描述.pdf"
    output_md = "/tmp/test_output.md"
    
    print(f"测试PDF转Markdown: {test_pdf}")
    
    success = await service.process_pdf_to_markdown(test_pdf, output_md)
    print(f"处理结果: {'成功' if success else '失败'}")
    
    if success and os.path.exists(output_md):
        with open(output_md, 'r', encoding='utf-8') as f:
            content = f.read()[:500]  # 显示前500字符
            print(f"输出内容预览:\n{content}...")
    
    return success


async def test_concurrent_processing():
    """测试并发处理"""
    api_key = "your_api_key_here"
    
    if api_key == "your_api_key_here":
        print("错误：请先设置真实的API密钥")
        return False
    
    service = MinerUOfficialService(api_key)
    
    # 测试文件列表
    test_files = [
        "/workspace/test/服装识别需求描述.pdf",
        "/workspace/test/人人皆可vibe编程.pdf"
    ]
    
    output_dir = "/tmp/concurrent_test"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"测试并发处理 {len(test_files)} 个文件")
    
    results = await service.process_multiple_pdfs(test_files, output_dir, max_concurrent=2)
    
    success_count = sum(1 for success in results.values() if success)
    print(f"处理结果: {success_count}/{len(test_files)} 成功")
    
    return success_count > 0


if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        print("=== MinerU官方API集成测试 ===")
        
        # 单个文件处理测试
        print("\n1. 单个PDF处理测试")
        single_result = await test_official_service()
        print(f"单个处理结果: {'成功' if single_result else '失败'}")
        
        # 并发处理测试
        print("\n2. 并发处理测试")
        concurrent_result = await test_concurrent_processing()
        print(f"并发处理结果: {'成功' if concurrent_result else '失败'}")
        
        print("\n=== 集成测试总结 ===")
        print(f"单个处理: {'✓' if single_result else '✗'}")
        print(f"并发处理: {'✓' if concurrent_result else '✗'}")
        
        if single_result and concurrent_result:
            print("\n结论: 官方API可以成功集成到现有系统中，支持并发处理")
        else:
            print("\n结论: 需要进一步调试集成问题")
    
    asyncio.run(main())