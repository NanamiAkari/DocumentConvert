#!/usr/bin/env python3
"""
文档转换服务模块

集成LibreOffice转换、MinerU PDF转Markdown等功能，
提供统一的文档转换接口。
"""

import asyncio
import os
import subprocess
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
# MinerU Python API
from pathlib import Path as PathlibPath
from mineru.cli.common import read_fn
from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.cli.common import prepare_env
from mineru.utils.enum_class import MakeMode


class DocumentService:
    """文档转换服务
    
    集成多种文档转换工具：
    1. LibreOffice: Office文档转PDF
    2. MinerU: PDF转Markdown
    3. 其他格式转换
    """
    
    def __init__(self,
                 libreoffice_path: str = "/usr/bin/libreoffice"):
        """
        初始化文档转换服务

        Args:
            libreoffice_path: LibreOffice可执行文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.libreoffice_path = libreoffice_path
        
        # 支持的文件格式
        self.office_formats = {
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.odt', '.ods', '.odp', '.rtf'
        }
        
        self.pdf_formats = {'.pdf'}
        
        self.image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # 检查依赖
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查转换工具依赖"""
        # 检查LibreOffice
        if not os.path.exists(self.libreoffice_path):
            self.logger.warning(f"LibreOffice not found at {self.libreoffice_path}")
        else:
            self.logger.info(f"LibreOffice found at {self.libreoffice_path}")
    
    async def convert_document(self, 
                              input_path: str,
                              output_path: str,
                              conversion_type: str,
                              params: Dict[str, Any] = None) -> Dict[str, Any]:
        """转换文档
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            conversion_type: 转换类型
            params: 转换参数
            
        Returns:
            转换结果字典
        """
        params = params or {}
        
        try:
            if conversion_type == 'office_to_pdf':
                return await self._convert_office_to_pdf(input_path, output_path, params)
            elif conversion_type == 'pdf_to_markdown':
                return await self._convert_pdf_to_markdown(input_path, output_path, params)
            elif conversion_type == 'batch_office_to_pdf':
                return await self._batch_convert_office_to_pdf(input_path, output_path, params)
            elif conversion_type == 'batch_pdf_to_markdown':
                return await self._batch_convert_pdf_to_markdown(input_path, output_path, params)
            else:
                raise ValueError(f"Unsupported conversion type: {conversion_type}")
                
        except Exception as e:
            self.logger.error(f"Document conversion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_path': input_path,
                'output_path': output_path
            }
    
    async def _convert_office_to_pdf(self, 
                                   input_path: str, 
                                   output_path: str, 
                                   params: Dict[str, Any]) -> Dict[str, Any]:
        """Office文档转PDF"""
        self.logger.info(f"Converting Office document to PDF: {input_path} -> {output_path}")
        
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        # 检查输入文件
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if input_file.suffix.lower() not in self.office_formats:
            raise ValueError(f"Unsupported office format: {input_file.suffix}")
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建LibreOffice命令
        cmd = [
            self.libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(output_file.parent),
            str(input_file)
        ]
        
        # 执行转换
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
            raise RuntimeError(f"LibreOffice conversion failed: {error_msg}")
        
        # 检查输出文件
        expected_output = output_file.parent / f"{input_file.stem}.pdf"
        if not expected_output.exists():
            raise RuntimeError("PDF file was not created")
        
        # 如果输出路径不同，移动文件
        if expected_output != output_file:
            shutil.move(str(expected_output), str(output_file))
        
        return {
            'success': True,
            'input_path': input_path,
            'output_path': str(output_file),
            'file_size': output_file.stat().st_size,
            'conversion_type': 'office_to_pdf'
        }
    
    async def _convert_pdf_to_markdown(self, 
                                     input_path: str, 
                                     output_path: str, 
                                     params: Dict[str, Any]) -> Dict[str, Any]:
        """PDF转Markdown"""
        self.logger.info(f"Converting PDF to Markdown: {input_path} -> {output_path}")
        
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        # 检查输入文件
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if input_file.suffix.lower() != '.pdf':
            raise ValueError(f"Expected PDF file, got: {input_file.suffix}")
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果输出文件已存在且不强制重新处理，则跳过
        if output_file.exists() and not params.get('force_reprocess', False):
            self.logger.info(f"Output file already exists, skipping: {output_path}")
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'markdown_files': [output_path],
                'file_count': 1,
                'conversion_type': 'pdf_to_markdown',
                'skipped': True
            }
        
        # 使用MinerU 2.0 Python API进行PDF转Markdown
        temp_output_dir = output_file.parent / "temp_mineru_output"
        temp_output_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.logger.info(f"Using MinerU 2.0 Python API to convert PDF: {input_file}")

            # 清理GPU内存
            self._clear_gpu_memory()

            # 读取PDF文件
            pdf_bytes = read_fn(str(input_file))
            pdf_file_name = input_file.stem

            self.logger.info(f"PDF file loaded: {pdf_file_name}, size: {len(pdf_bytes)} bytes")

            # 使用pipeline模式进行分析
            self.logger.info("Starting MinerU pipeline analysis...")
            infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(
                [pdf_bytes],
                ["ch"],  # 中文语言
                parse_method="auto",
                formula_enable=True,
                table_enable=True
            )

            self.logger.info(f"MinerU analysis completed, processing results...")

            # 处理结果
            if infer_results and len(infer_results) > 0:
                model_list = infer_results[0]
                images_list = all_image_lists[0] if all_image_lists and len(all_image_lists) > 0 else []
                pdf_doc = all_pdf_docs[0] if all_pdf_docs and len(all_pdf_docs) > 0 else None
                _lang = lang_list[0] if lang_list and len(lang_list) > 0 else "ch"
                _ocr_enable = ocr_enabled_list[0] if ocr_enabled_list and len(ocr_enabled_list) > 0 else True

                # 准备输出环境
                local_image_dir, local_md_dir = prepare_env(str(temp_output_dir), pdf_file_name, "auto")
                image_writer = FileBasedDataWriter(local_image_dir)

                # 转换为中间JSON格式
                middle_json = pipeline_result_to_middle_json(
                    model_list, images_list, pdf_doc, image_writer, _lang, _ocr_enable, True
                )

                # 检查middle_json是否有效
                if middle_json and "pdf_info" in middle_json:
                    # 生成Markdown内容
                    pdf_info = middle_json["pdf_info"]
                    image_dir = str(os.path.basename(local_image_dir))
                    md_content_str = pipeline_union_make(pdf_info, MakeMode.MM_MD, image_dir)

                    # 写入输出文件
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(md_content_str)

                    self.logger.info(f"MinerU conversion completed successfully: {output_file}")

                    # 返回成功结果
                    return {
                        'success': True,
                        'input_path': input_path,
                        'output_path': str(output_file),
                        'markdown_files': [str(output_file)],
                        'file_count': 1,
                        'conversion_type': 'pdf_to_markdown'
                    }
                else:
                    raise RuntimeError("MinerU middle_json generation failed")
            else:
                raise RuntimeError("MinerU analysis returned no results")


        except Exception as e:
            self.logger.error(f"MinerU Python API conversion failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # 分析错误类型
            error_str = str(e)
            error_analysis = self._analyze_mineru_python_error(error_str, traceback.format_exc())

            # 创建详细错误信息的markdown文件
            md_content = f"""# PDF转换错误 (MinerU 2.0 Python API)

文件: {input_file.name}
转换时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 错误分析

{error_analysis}

## 详细错误信息

```
{error_str}
```

## 完整堆栈跟踪

```
{traceback.format_exc()}
```

## 建议解决方案

1. 检查GPU内存是否足够
2. 检查CUDA和PyTorch是否正确安装
3. 检查PDF文件是否损坏或格式不支持
4. 尝试重启Python进程释放资源
"""

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # 返回错误结果而不是抛出异常
            return {
                'success': False,
                'error': f"MinerU Python API conversion failed: {error_analysis}",
                'input_path': input_path,
                'output_path': str(output_file),
                'conversion_type': 'pdf_to_markdown'
            }

        finally:
            # 清理GPU内存
            self._clear_gpu_memory()

            # 清理临时目录
            if temp_output_dir.exists():
                shutil.rmtree(str(temp_output_dir))
                self.logger.info(f"Cleaned up temporary directory: {temp_output_dir}")

    def _analyze_mineru_python_error(self, error_str: str, traceback_str: str) -> str:
        """分析MinerU Python API错误信息"""
        full_error = error_str + " " + traceback_str

        if "CUDA out of memory" in full_error or "OutOfMemoryError" in full_error:
            return "GPU内存不足错误 - 需要释放GPU内存或使用更小的batch size"
        elif "No module named" in full_error:
            return "Python模块缺失错误 - 检查MinerU及其依赖是否正确安装"
        elif "CUDA" in full_error and ("not available" in full_error or "unavailable" in full_error):
            return "CUDA不可用错误 - 检查CUDA驱动、PyTorch和GPU设置"
        elif "Permission denied" in full_error or "PermissionError" in full_error:
            return "权限错误 - 检查文件和目录的读写权限"
        elif "FileNotFoundError" in full_error or "No such file" in full_error:
            return "文件未找到错误 - 检查输入文件路径是否正确"
        elif "ImportError" in full_error:
            return "导入错误 - 检查MinerU依赖包是否完整安装"
        elif "RuntimeError" in full_error and "model" in full_error.lower():
            return "模型加载错误 - 检查模型文件是否完整下载"
        elif "ValueError" in full_error:
            return "参数值错误 - 检查输入参数是否正确"
        elif "TypeError" in full_error:
            return "类型错误 - 可能是API调用参数类型不匹配"
        elif "AttributeError" in full_error:
            return "属性错误 - 可能是MinerU版本不兼容"
        elif error_str.strip():
            return f"未知错误 - {error_str[:200]}..."
        else:
            return "无具体错误信息，可能是静默失败"

    def _clear_gpu_memory(self):
        """清理GPU内存"""
        try:
            import torch
            import gc
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
                self.logger.info("GPU memory cleared")
        except Exception as e:
            self.logger.warning(f"Failed to clear GPU memory: {e}")
    
    async def _batch_convert_office_to_pdf(self, 
                                         input_path: str, 
                                         output_path: str, 
                                         params: Dict[str, Any]) -> Dict[str, Any]:
        """批量Office文档转PDF"""
        self.logger.info(f"Batch converting Office documents to PDF: {input_path} -> {output_path}")
        
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        
        # 检查输入目录
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: {input_path}")
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建批量转换命令
        cmd = [
            'python3', self.batch_convert_script,
            '--input_dir', str(input_dir),
            '--output_dir', str(output_dir)
        ]
        
        # 添加额外参数
        if params.get('recursive'):
            cmd.append('--recursive')
        
        if params.get('file_pattern'):
            cmd.extend(['--pattern', params['file_pattern']])
        
        # 执行批量转换
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd='/workspace/test'
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
            raise RuntimeError(f"Batch conversion failed: {error_msg}")
        
        # 统计转换结果
        pdf_files = list(output_dir.glob('*.pdf'))
        
        return {
            'success': True,
            'input_path': input_path,
            'output_path': str(output_dir),
            'pdf_files': [str(f) for f in pdf_files],
            'file_count': len(pdf_files),
            'conversion_type': 'batch_office_to_pdf'
        }
    
    async def _batch_convert_pdf_to_markdown(self, 
                                           input_path: str, 
                                           output_path: str, 
                                           params: Dict[str, Any]) -> Dict[str, Any]:
        """批量PDF转Markdown"""
        self.logger.info(f"Batch converting PDF to Markdown: {input_path} -> {output_path}")
        
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        
        # 检查输入目录
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: {input_path}")
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建MinerU批量转换命令
        cmd = [
            'python3', self.mineru_script,
            '--input_dir', str(input_dir),
            '--output_dir', str(output_dir)
        ]
        
        # 添加额外参数
        if params.get('force_reprocess'):
            cmd.append('--force')
        
        if params.get('file_pattern'):
            cmd.extend(['--pattern', params['file_pattern']])
        
        # 执行批量转换
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd='/workspace/test'
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
            raise RuntimeError(f"Batch PDF to Markdown conversion failed: {error_msg}")
        
        # 统计转换结果
        markdown_files = list(output_dir.glob('*.md'))
        
        return {
            'success': True,
            'input_path': input_path,
            'output_path': str(output_dir),
            'markdown_files': [str(f) for f in markdown_files],
            'file_count': len(markdown_files),
            'conversion_type': 'batch_pdf_to_markdown'
        }
    
    async def convert_office_to_pdf(self, input_path: str, output_path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Office文档转PDF公共接口"""
        return await self._convert_office_to_pdf(input_path, output_path, params or {})
    
    async def convert_pdf_to_markdown(self, input_path: str, output_path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """PDF转Markdown公共接口"""
        return await self._convert_pdf_to_markdown(input_path, output_path, params or {})
    
    async def convert_office_to_markdown(self, input_path: str, output_path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Office文档直接转Markdown公共接口
        
        将Office文档先转换为PDF，再将PDF转换为Markdown，对用户透明化中间PDF过程
        
        Args:
            input_path: 输入Office文档路径
            output_path: 输出Markdown文件路径
            params: 转换参数
            
        Returns:
            转换结果字典
        """
        params = params or {}
        
        try:
            # 创建临时PDF文件路径
            input_file = Path(input_path)
            temp_dir = Path(output_path).parent / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_pdf_path = str(temp_dir / f"{input_file.stem}.pdf")
            
            # 第一步：Office转PDF
            pdf_result = await self._convert_office_to_pdf(input_path, temp_pdf_path, params)
            if not pdf_result['success']:
                raise RuntimeError(f"Office to PDF conversion failed: {pdf_result.get('error', 'Unknown error')}")
            
            # 第二步：PDF转Markdown
            md_result = await self._convert_pdf_to_markdown(temp_pdf_path, output_path, params)
            if not md_result or not md_result.get('success', False):
                error_msg = md_result.get('error', 'Unknown error') if md_result else 'No result returned'
                raise RuntimeError(f"PDF to Markdown conversion failed: {error_msg}")

            # 合并结果
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'temp_pdf_path': temp_pdf_path,
                'markdown_files': md_result.get('markdown_files', [output_path]) if md_result else [output_path],
                'file_count': 1,
                'conversion_type': 'office_to_markdown'
            }
            
        except Exception as e:
            self.logger.error(f"Office to Markdown conversion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_path': input_path,
                'output_path': output_path
            }
    
    async def batch_convert_office_to_markdown(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """批量Office文档直接转Markdown公共接口
        
        批量将Office文档转换为Markdown，对用户透明化中间PDF过程
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            **kwargs: 其他参数
            
        Returns:
            转换结果字典
        """
        self.logger.info(f"Batch converting Office documents to Markdown: {input_dir} -> {output_dir}")
        
        input_dir_path = Path(input_dir)
        output_dir_path = Path(output_dir)
        
        # 检查输入目录
        if not input_dir_path.exists() or not input_dir_path.is_dir():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # 确保输出目录存在
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # 创建临时PDF目录
        temp_dir = output_dir_path / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # 获取所有Office文档
        recursive = kwargs.get('recursive', False)
        file_pattern = kwargs.get('file_pattern', None)
        
        if recursive:
            files = [f for f in input_dir_path.glob('**/*') if f.is_file() and f.suffix.lower() in self.office_formats]
        else:
            files = [f for f in input_dir_path.glob('*') if f.is_file() and f.suffix.lower() in self.office_formats]
        
        if file_pattern:
            import re
            pattern = re.compile(file_pattern)
            files = [f for f in files if pattern.search(f.name)]
        
        # 转换每个文件
        results = []
        for file in files:
            try:
                # 计算相对路径，保持目录结构
                rel_path = file.relative_to(input_dir_path)
                output_md_path = output_dir_path / f"{rel_path.stem}.md"
                output_md_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 转换文件
                result = await self.convert_office_to_markdown(
                    input_path=str(file),
                    output_path=str(output_md_path),
                    params=kwargs
                )
                
                if result['success']:
                    results.append({
                        'input_file': str(file),
                        'output_file': str(output_md_path),
                        'success': True
                    })
                else:
                    results.append({
                        'input_file': str(file),
                        'error': result.get('error', 'Unknown error'),
                        'success': False
                    })
                    
            except Exception as e:
                self.logger.error(f"Error converting {file}: {e}")
                results.append({
                    'input_file': str(file),
                    'error': str(e),
                    'success': False
                })
        
        # 统计结果
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        return {
            'success': True,
            'input_dir': input_dir,
            'output_dir': output_dir,
            'converted_files': [r['output_file'] for r in successful],
            'failed_files': [r['input_file'] for r in failed],
            'total_files': len(files),
            'successful_conversions': len(successful),
            'failed_conversions': len(failed),
            'conversion_type': 'batch_office_to_markdown'
        }
    
    async def batch_convert_pdf_to_markdown(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """批量PDF转Markdown公共接口"""
        return await self._batch_convert_pdf_to_markdown(input_dir, output_dir, kwargs)
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文件格式"""
        return {
            'office_formats': list(self.office_formats),
            'pdf_formats': list(self.pdf_formats),
            'image_formats': list(self.image_formats)
        }
    
    def validate_input_file(self, file_path: str, expected_formats: set) -> bool:
        """验证输入文件格式"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in expected_formats
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        file_obj = Path(file_path)
        
        if not file_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_obj.stat()
        
        return {
            'path': str(file_obj),
            'name': file_obj.name,
            'stem': file_obj.stem,
            'suffix': file_obj.suffix,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified_time': stat.st_mtime,
            'is_office_format': file_obj.suffix.lower() in self.office_formats,
            'is_pdf_format': file_obj.suffix.lower() in self.pdf_formats,
            'is_image_format': file_obj.suffix.lower() in self.image_formats
        }