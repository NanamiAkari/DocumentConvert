#!/usr/bin/env python3
"""
S3上传服务
复刻MediaConvert的S3上传逻辑，支持将转换结果上传到ai-file目录
"""

import os
import boto3
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

from utils.logging_utils import configure_logging

logger = configure_logging(name=__name__)


class S3UploadService:
    """S3上传服务类"""
    
    def __init__(self):
        """初始化S3上传服务"""
        self.default_config = self._get_default_upload_config()
    
    def _get_default_upload_config(self) -> Dict[str, Any]:
        """获取默认上传配置"""
        # 从环境变量获取上传S3配置，如果不存在则回退到通用S3配置
        return {
            "aws_access_key_id": os.getenv("UPLOAD_S3_ACCESS_KEY_ID") or os.getenv("S3_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("UPLOAD_S3_SECRET_ACCESS_KEY") or os.getenv("S3_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
            "s3_endpoint_url": os.getenv("UPLOAD_S3_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL"),
            "aws_region": os.getenv("UPLOAD_S3_REGION") or os.getenv("S3_REGION") or os.getenv("AWS_REGION", "us-east-1"),
            "bucket_name": os.getenv("UPLOAD_S3_BUCKET", "ai-file")  # 默认上传到ai-file存储桶
        }
    
    def create_s3_client(self, config: Optional[Dict[str, Any]] = None) -> boto3.client:
        """
        创建S3客户端
        
        Args:
            config: S3配置字典，如果为None则使用默认配置
            
        Returns:
            boto3 S3客户端
        """
        if config is None:
            config = self.default_config
            
        try:
            client_config = {
                "aws_access_key_id": config.get("aws_access_key_id"),
                "aws_secret_access_key": config.get("aws_secret_access_key"),
                "region_name": config.get("aws_region", "us-east-1")
            }
            
            # 如果提供了自定义endpoint，使用它
            if config.get("s3_endpoint_url"):
                client_config["endpoint_url"] = config["s3_endpoint_url"]
            
            s3_client = boto3.client("s3", **client_config)
            
            # 测试连接
            s3_client.list_buckets()
            
            logger.info(f"S3 upload client created successfully for endpoint: {config.get('s3_endpoint_url', 'AWS S3')}")
            return s3_client
            
        except NoCredentialsError:
            raise ValueError("S3 credentials not provided or invalid")
        except ClientError as e:
            raise ValueError(f"Failed to create S3 client: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error creating S3 client: {str(e)}")
    
    async def upload_file(self, 
                         local_file_path: str,
                         s3_key: str,
                         bucket_name: Optional[str] = None,
                         s3_config: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        上传文件到S3
        
        Args:
            local_file_path: 本地文件路径
            s3_key: S3对象键
            bucket_name: S3存储桶名称，如果为None则使用默认配置
            s3_config: S3配置，如果为None则使用默认配置
            metadata: 文件元数据
            
        Returns:
            上传结果字典
        """
        start_time = datetime.now()
        
        try:
            # 使用配置或默认配置
            config = s3_config or self.default_config
            bucket = bucket_name or config.get("bucket_name", "ai-file")
            
            # 检查本地文件是否存在
            local_path = Path(local_file_path)
            if not local_path.exists():
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            
            file_size = local_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"Local file is empty: {local_file_path}")
            
            # 创建S3客户端
            s3_client = self.create_s3_client(config)
            
            logger.info(f"Starting upload from {local_file_path} to s3://{bucket}/{s3_key}")
            
            # 准备上传参数 - MinIO兼容
            extra_args = {}

            # 添加元数据
            if metadata:
                extra_args['Metadata'] = metadata

            # 自动检测Content-Type
            content_type = self._get_content_type(local_path)
            if content_type:
                extra_args['ContentType'] = content_type

            # 在线程池中执行上传（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: s3_client.upload_file(
                    str(local_path),
                    bucket,
                    s3_key,
                    ExtraArgs=extra_args if extra_args else None
                )
            )
            
            # 验证上传结果
            try:
                head_response = s3_client.head_object(Bucket=bucket, Key=s3_key)
                uploaded_size = head_response.get('ContentLength', 0)
                
                if uploaded_size != file_size:
                    raise ValueError(f"Upload size mismatch. Expected: {file_size}, Got: {uploaded_size}")
                
            except ClientError as e:
                raise ValueError(f"Failed to verify uploaded file: {e}")
            
            end_time = datetime.now()
            upload_time = (end_time - start_time).total_seconds()
            
            # 生成访问URL
            s3_url = f"s3://{bucket}/{s3_key}"
            
            # 尝试生成HTTP访问URL
            http_url = None
            try:
                if config.get("s3_endpoint_url"):
                    # 自定义endpoint
                    endpoint = config["s3_endpoint_url"].rstrip('/')
                    http_url = f"{endpoint}/{bucket}/{s3_key}"
                else:
                    # AWS S3
                    region = config.get("aws_region", "us-east-1")
                    if region == "us-east-1":
                        http_url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
                    else:
                        http_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
            except Exception as e:
                logger.warning(f"Failed to generate HTTP URL: {e}")
            
            logger.info(f"Successfully uploaded {file_size} bytes in {upload_time:.2f}s to {s3_url}")
            
            return {
                'success': True,
                'bucket': bucket,
                's3_key': s3_key,
                's3_url': s3_url,
                'http_url': http_url,
                'file_size': file_size,
                'upload_time': upload_time,
                'content_type': content_type,
                'metadata': metadata
            }
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'FileNotFoundError'
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"S3 client error ({error_code}): {error_message}")
            return {
                'success': False,
                'error': f"S3 error: {error_message}",
                'error_type': 'S3ClientError',
                'error_code': error_code
            }
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    async def upload_directory(self,
                             local_dir_path: str,
                             s3_prefix: str,
                             bucket_name: Optional[str] = None,
                             s3_config: Optional[Dict[str, Any]] = None,
                             metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        上传整个目录到S3

        Args:
            local_dir_path: 本地目录路径
            s3_prefix: S3前缀路径
            bucket_name: S3存储桶名称
            s3_config: S3配置
            metadata: 文件元数据

        Returns:
            上传结果字典
        """
        try:
            local_dir = Path(local_dir_path)
            if not local_dir.exists() or not local_dir.is_dir():
                raise ValueError(f"Local directory not found or not a directory: {local_dir_path}")

            uploaded_files = []
            failed_files = []
            total_size = 0

            # 递归遍历目录中的所有文件
            for file_path in local_dir.rglob("*"):
                if file_path.is_file():
                    # 计算相对路径
                    relative_path = file_path.relative_to(local_dir)
                    s3_key = f"{s3_prefix.rstrip('/')}/{relative_path.as_posix()}"

                    try:
                        # 为每个文件添加特定的元数据（使用base64编码处理中文）
                        file_metadata = metadata.copy() if metadata else {}
                        import base64
                        relative_path_b64 = base64.b64encode(str(relative_path).encode('utf-8')).decode('ascii')
                        file_metadata.update({
                            'relative-path-base64': relative_path_b64,
                            'file-type': file_path.suffix.lower(),
                            'upload-batch': 'directory-upload'
                        })

                        result = await self.upload_file(
                            local_file_path=str(file_path),
                            s3_key=s3_key,
                            bucket_name=bucket_name,
                            s3_config=s3_config,
                            metadata=file_metadata
                        )

                        if result['success']:
                            uploaded_files.append({
                                'local_path': str(file_path),
                                'relative_path': str(relative_path),
                                's3_key': s3_key,
                                's3_url': result['s3_url'],
                                'file_size': result['file_size']
                            })
                            total_size += result['file_size']
                            logger.info(f"Uploaded file: {relative_path} -> {s3_key}")
                        else:
                            failed_files.append({
                                'local_path': str(file_path),
                                'relative_path': str(relative_path),
                                's3_key': s3_key,
                                'error': result.get('error')
                            })
                            logger.error(f"Failed to upload file: {relative_path} - {result.get('error')}")

                    except Exception as e:
                        failed_files.append({
                            'local_path': str(file_path),
                            'relative_path': str(relative_path),
                            's3_key': s3_key,
                            'error': str(e)
                        })
                        logger.error(f"Exception uploading file: {relative_path} - {e}")

            success = len(failed_files) == 0
            return {
                'success': success,
                'uploaded_files': uploaded_files,
                'failed_files': failed_files,
                'total_files': len(uploaded_files) + len(failed_files),
                'uploaded_count': len(uploaded_files),
                'failed_count': len(failed_files),
                'total_size': total_size,
                's3_prefix': s3_prefix
            }

        except Exception as e:
            logger.error(f"Failed to upload directory {local_dir_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    async def upload_converted_document(self,
                                      local_path: str,
                                      task_id: int,
                                      original_filename: Optional[str] = None,
                                      original_bucket: Optional[str] = None,
                                      original_folder: Optional[str] = None,
                                      task_type: str = "document-conversion") -> Dict[str, Any]:
        """
        上传转换后的文档到ai-file目录，遵循Media-Convert路径规则

        Args:
            local_path: 本地文件路径
            task_id: 任务ID (自增整数)
            original_filename: 原始文件名
            original_bucket: 原始文件所在的bucket
            original_folder: 原始文件所在的文件夹
            task_type: 任务类型

        Returns:
            上传结果字典
        """
        try:
            # 构建S3键名 - 遵循Media-Convert路径规则
            local_file = Path(local_path)
            filename = original_filename or local_file.name

            # 按照要求的路径规则构建：{original_bucket}/{原来文件的文件夹路径+文件名(去掉后缀)}/{类型(pdf/markdown)}/{filename}
            if original_bucket and original_folder and original_filename:
                # 清理文件夹路径，移除开头和结尾的斜杠
                folder_path = original_folder.strip('/')
                # 获取原始文件名（去掉后缀）
                original_name_without_ext = Path(original_filename).stem
                # 根据任务类型确定类型目录
                if task_type == "pdf_to_markdown":
                    type_dir = "markdown"
                elif task_type == "office_to_pdf":
                    type_dir = "pdf"
                else:
                    type_dir = "converted"

                # 构建路径：{original_bucket}/{文件夹路径+原始文件名(无后缀)}/{类型}/{filename}
                s3_key = f"{original_bucket}/{folder_path}/{original_name_without_ext}/{type_dir}/{filename}"
            else:
                # 使用原有的converted/{task_id}结构作为后备
                s3_key = f"converted/{task_id}/{filename}"
            
            # 添加元数据 - S3 metadata只支持ASCII字符
            import base64
            # 对中文文件名进行Base64编码以符合S3 metadata要求
            encoded_filename = base64.b64encode(filename.encode('utf-8')).decode('ascii')
            # 对中文文件夹名也进行Base64编码
            encoded_folder = base64.b64encode((original_folder or "").encode('utf-8')).decode('ascii') if original_folder else ""

            metadata = {
                'task-id': str(task_id),
                'upload-time': datetime.now().isoformat(),
                'original-filename-base64': encoded_filename,  # Base64编码的文件名
                'original-filename-utf8': filename.encode('utf-8').hex(),  # 十六进制编码的文件名
                'conversion-type': task_type,
                'original-bucket': original_bucket or "",
                'original-folder-base64': encoded_folder,  # Base64编码的文件夹名
                'original-folder-utf8': (original_folder or "").encode('utf-8').hex() if original_folder else ""  # 十六进制编码的文件夹名
            }
            
            result = await self.upload_file(
                local_file_path=local_path,
                s3_key=s3_key,
                metadata=metadata
            )
            
            if result['success']:
                logger.info(f"Document uploaded successfully for task {task_id}: {result['s3_url']}")
            
            return result

        except Exception as e:
            logger.error(f"Failed to upload converted document for task {task_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    async def upload_complete_conversion_result(self,
                                              output_dir_path: str,
                                              task_id: int,
                                              original_filename: Optional[str] = None,
                                              original_bucket: Optional[str] = None,
                                              original_folder: Optional[str] = None,
                                              task_type: str = "document-conversion") -> Dict[str, Any]:
        """
        上传完整的转换结果（包括Markdown、JSON、图片等所有文件）

        Args:
            output_dir_path: 输出目录路径
            task_id: 任务ID
            original_filename: 原始文件名
            original_bucket: 原始文件所在的bucket
            original_folder: 原始文件所在的文件夹
            task_type: 任务类型

        Returns:
            上传结果字典
        """
        try:
            output_dir = Path(output_dir_path)
            if not output_dir.exists() or not output_dir.is_dir():
                raise ValueError(f"Output directory not found: {output_dir_path}")

            # 构建S3前缀路径 - 使用统一的路径规则
            if original_bucket and original_folder and original_filename:
                folder_path = original_folder.strip('/')
                # 获取原始文件名（去掉后缀）
                original_name_without_ext = Path(original_filename).stem
                # 根据任务类型确定类型目录
                if task_type == "pdf_to_markdown":
                    type_dir = "markdown"
                elif task_type == "office_to_pdf":
                    type_dir = "pdf"
                else:
                    type_dir = "converted"

                # 构建前缀路径：{original_bucket}/{文件夹路径+原始文件名(无后缀)}/{类型}
                s3_prefix = f"{original_bucket}/{folder_path}/{original_name_without_ext}/{type_dir}"
            else:
                s3_prefix = f"converted/{task_id}"

            # 准备元数据
            import base64
            encoded_filename = base64.b64encode((original_filename or "").encode('utf-8')).decode('ascii') if original_filename else ""
            encoded_folder = base64.b64encode((original_folder or "").encode('utf-8')).decode('ascii') if original_folder else ""

            metadata = {
                'task-id': str(task_id),
                'upload-time': datetime.now().isoformat(),
                'conversion-type': task_type,
                'original-bucket': original_bucket or "",
                'original-filename-base64': encoded_filename,
                'original-folder-base64': encoded_folder,
                'upload-type': 'complete-conversion-result'
            }

            # 上传整个目录
            result = await self.upload_directory(
                local_dir_path=str(output_dir),
                s3_prefix=s3_prefix,
                metadata=metadata
            )

            if result['success']:
                logger.info(f"Complete conversion result uploaded for task {task_id}: {result['uploaded_count']} files, {result['total_size']} bytes")

                # 构建主要文件的URL（通常是Markdown文件）
                main_file_url = None
                for uploaded_file in result['uploaded_files']:
                    if uploaded_file['relative_path'].endswith('.md'):
                        main_file_url = uploaded_file['s3_url']
                        break

                return {
                    'success': True,
                    's3_prefix': s3_prefix,
                    's3_url': main_file_url,  # 主要文件URL（兼容现有代码）
                    'uploaded_files': result['uploaded_files'],
                    'total_files': result['uploaded_count'],
                    'total_size': result['total_size'],
                    'file_size': result['total_size'],  # 兼容现有代码
                    'upload_time': (datetime.now() - datetime.fromisoformat(metadata['upload-time'].replace('Z', '+00:00'))).total_seconds()
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Failed to upload complete conversion result for task {task_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _get_content_type(self, file_path: Path) -> Optional[str]:
        """根据文件扩展名获取Content-Type"""
        content_types = {
            '.pdf': 'application/pdf',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.zip': 'application/zip',
            '.json': 'application/json',
            '.html': 'text/html',
            '.htm': 'text/html'
        }
        
        suffix = file_path.suffix.lower()
        return content_types.get(suffix, 'application/octet-stream')
    
    async def generate_download_url(self, 
                                  bucket_name: str,
                                  s3_key: str,
                                  expires_in: int = 3600,
                                  s3_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        生成预签名下载URL
        
        Args:
            bucket_name: S3存储桶名称
            s3_key: S3对象键
            expires_in: URL过期时间(秒)
            s3_config: S3配置
            
        Returns:
            预签名URL或None
        """
        try:
            config = s3_config or self.default_config
            s3_client = self.create_s3_client(config)
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            
            logger.debug(f"Generated presigned download URL for s3://{bucket_name}/{s3_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
