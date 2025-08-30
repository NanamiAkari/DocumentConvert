#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio应用 - 文档转换服务Web界面
提供用户友好的文档转换功能，支持多种格式转换
"""

import gradio as gr
import requests
import json
import time
import os
from typing import Optional, Tuple, List
import mimetypes

# 配置
API_BASE_URL = "http://localhost:8001"
MINIO_BASE_URL = "http://localhost:9003"
SUPPORTED_FORMATS = {
    "pdf": [".pdf"],
    "office": [".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"]
}

CONVERSION_OPTIONS = {
    "PDF转Markdown": "pdf_to_markdown",
    "Office转PDF": "office_to_pdf", 
    "Office转Markdown": "office_to_markdown"
}

class DocumentConverter:
    """文档转换器类"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def check_service_health(self) -> bool:
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{API_BASE_URL}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def upload_and_convert(self, file_path, conversion_type: str, 
                          priority: str = "normal") -> Tuple[bool, str, Optional[str]]:
        """上传文件并创建转换任务"""
        try:
            if not file_path:
                return False, "❌ 文件路径无效", None
            
            # 获取文件名
            filename = os.path.basename(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "❌ 文件不存在或路径无效", None
            
            # 准备转换请求数据
            data = {
                'task_type': conversion_type,
                'priority': priority,
                'input_path': file_path
            }
            
            # 发送转换请求
            response = self.session.post(
                f"{API_BASE_URL}/api/tasks/create",
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                return True, "任务创建成功", task_id
            else:
                error_msg = response.json().get('detail', '未知错误')
                return False, f"任务创建失败: {error_msg}", None
                
        except Exception as e:
            return False, f"上传失败: {str(e)}", None
    
    def get_task_status(self, task_id: str, conversion_type: str = None) -> Tuple[str, str, List[str]]:
        """获取任务状态和下载链接"""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/tasks/{task_id}")
            
            if response.status_code == 200:
                task_info = response.json()
                status = task_info.get('status', 'unknown')
                message = task_info.get('message', '')
                
                # 获取下载链接
                download_links = []
                if status == 'completed':
                    # 首先尝试从result.files获取文件信息（新格式）
                    result = task_info.get('result', {})
                    files = result.get('files', [])
                    
                    # 定义期望的文件扩展名
                    expected_extensions = self._get_expected_extensions(conversion_type)
                    
                    if files:
                        # 新格式：从result.files获取文件信息
                        valid_files = []
                        for file_info in files:
                            if isinstance(file_info, dict):
                                file_name = file_info.get('relative_path', '未知文件')
                                
                                # 过滤文件：只显示期望的转换结果文件
                                if self._is_main_result_file(file_name, expected_extensions):
                                    valid_files.append((file_name, file_info))
                        
                        # 从有效文件中选择最佳的一个（文件名最短且最简洁的）
                        if valid_files:
                            # 按文件名长度排序，选择最短的文件名
                            best_file = min(valid_files, key=lambda x: len(x[0]))
                            file_name, file_info = best_file
                            
                            # 优先使用http_url，如果没有则使用API代理接口
                            http_url = file_info.get('http_url')
                            if http_url:
                                download_links.append(f'<a href="{http_url}" target="_blank" download="{file_name}" style="display: inline-block; margin: 5px 10px 5px 0; padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">📥 {file_name}</a>')
                            else:
                                s3_url = file_info.get('s3_url', '')
                                if s3_url:
                                    # 使用API代理接口而不是直接的MinIO地址
                                    proxy_url = f"{API_BASE_URL}/api/download/{task_id}/{file_name}"
                                    download_links.append(f'<a href="{proxy_url}" target="_blank" download="{file_name}" style="display: inline-block; margin: 5px 10px 5px 0; padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">📥 {file_name}</a>')
                    else:
                        # 兼容旧格式：从s3_urls获取
                        s3_urls = task_info.get('s3_urls', [])
                        valid_files = []
                        
                        for s3_url in s3_urls:
                            if isinstance(s3_url, str) and s3_url:
                                # 从S3 URL中提取文件名
                                file_name = s3_url.split('/')[-1] if '/' in s3_url else s3_url
                                
                                # 过滤文件：只显示期望的转换结果文件
                                if self._is_main_result_file(file_name, expected_extensions):
                                    valid_files.append((file_name, s3_url, 'string'))
                            elif isinstance(s3_url, dict):
                                # 兼容旧格式（如果API返回的是字典格式）
                                file_name = s3_url.get('file_name', '未知文件')
                                url = s3_url.get('s3_url', '')
                                
                                # 过滤文件：只显示期望的转换结果文件
                                if url and self._is_main_result_file(file_name, expected_extensions):
                                    valid_files.append((file_name, url, 'dict'))
                        
                        # 从有效文件中选择最佳的一个（文件名最短且最简洁的）
                        if valid_files:
                            # 按文件名长度排序，选择最短的文件名
                            best_file = min(valid_files, key=lambda x: len(x[0]))
                            file_name, url, file_type = best_file
                            
                            # 使用API代理接口而不是直接的MinIO地址
                            proxy_url = f"{API_BASE_URL}/api/download/{task_id}/{file_name}"
                            download_links.append(f'<a href="{proxy_url}" target="_blank" download="{file_name}" style="display: inline-block; margin: 5px 10px 5px 0; padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">📥 {file_name}</a>')
                
                return status, message, download_links
            else:
                return 'error', '获取任务状态失败', []
                
        except Exception as e:
            return 'error', f'查询失败: {str(e)}', []
    
    def _get_expected_extensions(self, conversion_type: str) -> List[str]:
        """根据转换类型获取期望的文件扩展名"""
        if conversion_type == "pdf_to_markdown":
            return [".md", ".markdown"]
        elif conversion_type == "office_to_pdf":
            return [".pdf"]
        elif conversion_type == "office_to_markdown":
            return [".md", ".markdown"]
        else:
            # 如果转换类型未知，返回所有可能的结果文件类型
            return [".md", ".markdown", ".pdf"]
    
    def _is_main_result_file(self, file_name: str, expected_extensions: List[str]) -> bool:
        """判断文件是否为主要的转换结果文件"""
        if not file_name:
            return False
        
        # 获取文件扩展名
        file_ext = os.path.splitext(file_name.lower())[1]
        
        # 检查是否为期望的扩展名
        if file_ext not in expected_extensions:
            return False
        
        # 排除临时文件和中间文件
        file_name_lower = file_name.lower()
        exclude_patterns = [
            'temp', 'tmp', 'cache', 'intermediate', 
            'partial', 'processing', 'backup', 'log',
            '.tmp', '.temp', '.bak', '.log', 'debug',
            'test', 'sample', 'example', 'draft',
            'copy', 'duplicate', 'version', 'v1', 'v2',
            'old', 'new', 'original', 'converted_',
            'output_', 'result_', 'final_', 'processed_'
        ]
        
        for pattern in exclude_patterns:
            if pattern in file_name_lower:
                return False
        
        # 进一步过滤：优先选择最简洁的文件名
        # 如果文件名包含过多的标识符或哈希值，可能是中间文件
        if len(file_name) > 100:  # 文件名过长，可能包含哈希值
            return False
            
        # 检查是否包含过多的数字或特殊字符（可能是哈希值）
        import re
        # 如果文件名中连续的数字或字母超过32个字符，可能是哈希值
        if re.search(r'[a-f0-9]{32,}', file_name_lower):
            return False
        
        return True

# 创建转换器实例
converter = DocumentConverter()

def validate_file_format(file_path: str, conversion_type: str) -> Tuple[bool, str]:
    """验证文件格式是否支持所选转换类型"""
    if not file_path:
        return False, "请选择文件"
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if conversion_type == "pdf_to_markdown":
        if file_ext not in SUPPORTED_FORMATS["pdf"]:
            return False, "PDF转Markdown只支持PDF文件"
    elif conversion_type in ["office_to_pdf", "office_to_markdown"]:
        if file_ext not in SUPPORTED_FORMATS["office"]:
            return False, "Office转换只支持DOC、DOCX、PPT、PPTX、XLS、XLSX文件"
    
    return True, "文件格式验证通过"

def convert_document(file, conversion_option: str, priority: str = "normal") -> Tuple[str, str, str]:
    """转换文档的主函数"""
    # 添加调试日志
    print(f"[DEBUG] convert_document called with file: {file}, type: {type(file)}")
    
    # 检查服务状态
    if not converter.check_service_health():
        return "❌ 服务不可用", "文档转换服务未启动或无法访问", ""
    
    if file is None:
        print("[DEBUG] File is None")
        return "❌ 错误", "请上传文件", ""
    
    # 处理Gradio文件输入 - 添加详细调试
    try:
        print(f"[DEBUG] File object attributes: {dir(file) if hasattr(file, '__dict__') else 'No attributes'}")
        
        if hasattr(file, 'name'):
            # Gradio文件对象，直接使用文件路径
            file_path = file.name
            print(f"[DEBUG] Using file.name: {file_path}")
        elif isinstance(file, str):
            # 字符串路径
            file_path = file
            print(f"[DEBUG] Using string path: {file_path}")
        else:
            print(f"[DEBUG] Invalid file object type: {type(file)}")
            return "❌ 错误", f"无效的文件对象类型: {type(file)}", ""
            
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"[DEBUG] File does not exist: {file_path}")
            return "❌ 错误", f"文件不存在: {file_path}", ""
        
        # 检查文件权限
        if not os.access(file_path, os.R_OK):
            print(f"[DEBUG] File not readable: {file_path}")
            return "❌ 错误", f"文件无法读取: {file_path}", ""
            
        print(f"[DEBUG] File validation passed: {file_path}")
            
    except Exception as e:
        print(f"[DEBUG] File processing exception: {str(e)}")
        return "❌ 错误", f"文件处理失败: {str(e)}", "请重新上传文件"
    
    # 获取转换类型
    conversion_type = CONVERSION_OPTIONS.get(conversion_option)
    if not conversion_type:
        return "❌ 错误", "不支持的转换类型", ""
    
    # 验证文件格式
    is_valid, validation_msg = validate_file_format(file_path, conversion_type)
    if not is_valid:
        file_ext = os.path.splitext(file_path)[1].lower()
        if conversion_type == "pdf_to_markdown":
            supported_formats = SUPPORTED_FORMATS["pdf"]
        else:
            supported_formats = SUPPORTED_FORMATS["office"]
        return "❌ 格式错误", f"文件格式 '{file_ext}' 不支持 '{conversion_type}' 转换\n支持的格式: {', '.join(supported_formats)}", "请选择正确的文件格式或转换类型"
    
    success, message, task_id = converter.upload_and_convert(
        file_path, conversion_type, priority
    )
    
    if not success:
        return "❌ 上传失败", message, ""
    
    # 等待任务完成并获取结果
    status_msg = "🔄 任务处理中..."
    max_wait_time = 300  # 最大等待5分钟
    wait_time = 0
    
    while wait_time < max_wait_time:
        status, msg, download_links = converter.get_task_status(task_id, conversion_type)
        
        if status == 'completed':
            if download_links:
                links_html = "\n".join(download_links)
                return "✅ 转换完成", f"任务ID: {task_id}\n{msg}", links_html
            else:
                return "⚠️ 转换完成", f"任务ID: {task_id}\n{msg}", "未找到下载链接"
        elif status == 'failed':
            # 改进错误信息显示，包含具体的失败原因
            error_detail = msg if msg else "转换过程中发生未知错误"
            return "❌ 转换失败", f"任务ID: {task_id}\n错误详情: {error_detail}", "请检查文件格式是否正确，或稍后重试"
        elif status in ['pending', 'processing']:
            status_msg = f"🔄 任务处理中... (状态: {status})"
            time.sleep(2)
            wait_time += 2
        elif status == 'error':
            # 处理查询任务状态时的错误
            return "❌ 查询失败", f"任务ID: {task_id}\n{msg}", "无法获取任务状态，请稍后重试"
        else:
            return "❓ 未知状态", f"任务ID: {task_id}\n状态: {status}\n{msg}", "请联系管理员或稍后重试"
    
    return "⏰ 超时", f"任务ID: {task_id}\n处理超时，请稍后查询任务状态", ""

def create_gradio_interface():
    """创建Gradio界面"""
    
    # 自定义CSS样式
    css = """
    .gradio-container {
        max-width: 800px !important;
        margin: auto !important;
    }
    .status-success { color: #28a745 !important; }
    .status-error { color: #dc3545 !important; }
    .status-processing { color: #007bff !important; }
    """
    
    with gr.Blocks(css=css, title="文档转换服务") as demo:
        gr.Markdown(
            """
            # 📄 文档转换服务
            
            支持多种文档格式转换，转换后的文件将保存到MinIO存储桶中。
            
            **支持的转换类型：**
            - PDF → Markdown
            - Office文档 → PDF (DOC, DOCX, PPT, PPTX, XLS, XLSX)
            - Office文档 → Markdown
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                # 文件上传 - 优化Gradio 3.50.2兼容性
                file_input = gr.File(
                    label="📁 选择文档文件",
                    file_types=[".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"]
                )
                
                # 转换选项
                conversion_option = gr.Dropdown(
                    choices=list(CONVERSION_OPTIONS.keys()),
                    label="🔄 选择转换格式",
                    value="PDF转Markdown"
                )
                
                # 优先级选择
                priority_option = gr.Dropdown(
                    choices=["low", "normal", "high"],
                    label="⚡ 任务优先级",
                    value="normal"
                )
                
                # 转换按钮
                convert_btn = gr.Button(
                    "🚀 开始转换", 
                    variant="primary",
                    size="lg"
                )
            
            with gr.Column(scale=3):
                # 状态显示
                status_output = gr.Textbox(
                    label="📊 转换状态",
                    interactive=False,
                    lines=1
                )
                
                # 消息显示
                message_output = gr.Textbox(
                    label="💬 详细信息",
                    interactive=False,
                    lines=3
                )
                
                # 下载链接
                download_output = gr.HTML(
                    label="🔗 下载链接",
                    value="<p>转换完成后，下载链接将显示在这里</p>"
                )
        
        # 使用说明
        gr.Markdown(
            """
            ---
            
            **使用说明：**
            1. 选择要转换的文档文件
            2. 选择目标转换格式
            3. 设置任务优先级（可选）
            4. 点击"开始转换"按钮
            5. 等待转换完成，获取下载链接
            
            **注意事项：**
            - 文件大小限制：建议不超过100MB
            - 转换时间：根据文件大小和复杂度，通常需要几秒到几分钟
            - 下载链接：转换完成的文件将保存在MinIO存储桶中
            """
        )
        
        # 绑定转换事件
        convert_btn.click(
            fn=convert_document,
            inputs=[file_input, conversion_option, priority_option],
            outputs=[status_output, message_output, download_output]
        )
    
    return demo

if __name__ == "__main__":
    # 检查服务状态
    print("正在检查文档转换服务状态...")
    if converter.check_service_health():
        print("✅ 文档转换服务运行正常")
    else:
        print("❌ 警告: 文档转换服务不可用，请确保服务已启动")
    
    # 创建并启动Gradio应用
    demo = create_gradio_interface()
    
    print("\n🚀 启动Gradio应用...")
    print(f"📍 API服务地址: {API_BASE_URL}")
    print(f"📍 MinIO地址: {MINIO_BASE_URL}")
    
    # 启动应用
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        quiet=False,
        inbrowser=False
    )