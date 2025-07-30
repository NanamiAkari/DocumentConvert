#!/usr/bin/env python3
"""
MinerU Python API测试脚本

基于官方demo.py示例，测试MinerU的Python API调用功能
"""

import os
import sys
from pathlib import Path
import logging

# 添加当前目录到Python路径
sys.path.append('/workspace')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_fn(path):
    """读取文件内容"""
    with open(path, 'rb') as f:
        return f.read()

def parse_doc(path_list, output_dir, backend="pipeline", lang="auto", method="auto", server_url=None, start_page_id=0, end_page_id=None):
    """
    解析文档
    
    Args:
        path_list: PDF文件路径列表
        output_dir: 输出目录
        backend: 后端类型，可选值：pipeline, vlm-transformers, vlm-sglang-engine
        lang: 语言，默认auto自动检测
        method: 解析方法，默认auto
        server_url: 服务器URL，用于vlm-sglang-client模式
        start_page_id: 开始页面ID，默认0
        end_page_id: 结束页面ID，默认None（解析到文档末尾）
    """
    try:
        # 导入MinerU相关模块
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.config.enums import SupportedPdfParseMethod
        
        file_name_list = []
        pdf_bytes_list = []
        lang_list = []
        
        for path in path_list:
            file_name = str(Path(path).stem)
            pdf_bytes = read_fn(path)
            file_name_list.append(file_name)
            pdf_bytes_list.append(pdf_bytes)
            lang_list.append(lang)
        
        # 调用MinerU的解析函数
        from magic_pdf.pipe.UNIPipe import UNIPipe
        from magic_pdf.pipe.OCRPipe import OCRPipe
        from magic_pdf.pipe.TXTPipe import TXTPipe
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理每个PDF文件
        for i, (file_name, pdf_bytes, lang) in enumerate(zip(file_name_list, pdf_bytes_list, lang_list)):
            logger.info(f"Processing file {i+1}/{len(file_name_list)}: {file_name}")
            
            # 创建文件特定的输出目录
            file_output_dir = os.path.join(output_dir, file_name)
            os.makedirs(file_output_dir, exist_ok=True)
            
            # 创建数据写入器
            image_writer = FileBasedDataWriter(os.path.join(file_output_dir, "images"))
            md_writer = FileBasedDataWriter(file_output_dir)
            
            # 创建数据集
            dataset = PymuDocDataset(file_name)
            
            if backend == "pipeline":
                # 使用pipeline模式
                pipe = UNIPipe(pdf_bytes, {"_pdf_type": "", "model_list": []}, image_writer)
            else:
                # 使用VLM模式
                pipe = UNIPipe(pdf_bytes, {"_pdf_type": "", "model_list": []}, image_writer)
            
            # 执行解析
            pipe_ret = pipe.pipe_analyze()
            
            # 保存结果
            md_content = pipe_ret.get("content_list", [])
            if md_content:
                md_path = os.path.join(file_output_dir, f"{file_name}.md")
                with open(md_path, 'w', encoding='utf-8') as f:
                    for content in md_content:
                        f.write(str(content) + '\n')
                logger.info(f"Markdown saved to: {md_path}")
            
            logger.info(f"Completed processing: {file_name}")
            
    except Exception as e:
        logger.exception(f"Error processing documents: {e}")
        raise

def test_single_pdf():
    """测试单个PDF文件转换"""
    logger.info("Testing single PDF conversion...")
    
    # 测试文件路径
    test_pdf = "/workspace/test/人人皆可vibe编程.pdf"
    output_dir = "/workspace/test/mineru_api_output"
    
    if not os.path.exists(test_pdf):
        logger.error(f"Test PDF file not found: {test_pdf}")
        return False
    
    try:
        # 解析文档
        parse_doc([test_pdf], output_dir, backend="pipeline")
        
        # 检查输出
        expected_md = os.path.join(output_dir, "人人皆可vibe编程", "人人皆可vibe编程.md")
        if os.path.exists(expected_md):
            logger.info(f"✅ Success! Markdown file created: {expected_md}")
            
            # 显示文件大小
            file_size = os.path.getsize(expected_md)
            logger.info(f"📄 Markdown file size: {file_size} bytes")
            
            # 显示前几行内容
            with open(expected_md, 'r', encoding='utf-8') as f:
                content = f.read(500)  # 读取前500字符
                logger.info(f"📝 Content preview:\n{content}...")
            
            return True
        else:
            logger.error(f"❌ Expected markdown file not found: {expected_md}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    logger.info("🚀 Starting MinerU Python API test...")
    
    # 设置环境变量（如果需要使用modelscope镜像）
    # os.environ['MINERU_MODEL_SOURCE'] = "modelscope"
    
    # 运行测试
    success = test_single_pdf()
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Tests failed!")
        sys.exit(1)