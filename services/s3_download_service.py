#!/usr/bin/env python3
"""
S3文件下载服务
复刻MediaConvert的S3下载逻辑，支持多种云存储服务
"""

import os
import boto3
import aiofiles
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

from utils.logging_utils import configure_logging

logger = configure_logging(name=__name__)


class S3DownloadService:
    """S3文件下载服务类"""
    
    def __init__(self):
        """初始化S3下载服务"""
        self.default_config = self._get_default_download_config()
    
    def _get_default_download_config(self) -> Dict[str, Any]:
        """获取默认下载配置（兼容多种环境变量命名）"""
        return {
            # 访问密钥ID：优先使用下载/通用S3命名，再兼容AWS与MinIO常见命名
            "aws_access_key_id": (
                os.getenv("S3_ACCESS_KEY_ID")
                or os.getenv("S3_ACCESS_KEY")
                or os.getenv("AWS_ACCESS_KEY_ID")
                or os.getenv("MINIO_ACCESS_KEY")
                or os.getenv("MINIO_ROOT_USER")
            ),
            # 访问密钥：优先使用下载/通用S3命名，再兼容AWS与MinIO常见命名
            "aws_secret_access_key": (
                os.getenv("S3_SECRET_ACCESS_KEY")
                or os.getenv("S3_SECRET_KEY")
                or os.getenv("AWS_SECRET_ACCESS_KEY")
                or os.getenv("MINIO_SECRET_KEY")
                or os.getenv("MINIO_ROOT_PASSWORD")
            ),
            # 端点：兼容 S3_ENDPOINT_URL / S3_ENDPOINT / MINIO_ENDPOINT
            "s3_endpoint_url": (
                os.getenv("S3_ENDPOINT_URL")
                or os.getenv("S3_ENDPOINT")
                or os.getenv("MINIO_ENDPOINT")
            ),
            # 区域：兼容 S3_REGION / AWS_REGION，默认 us-east-1
            "aws_region": os.getenv("S3_REGION") or os.getenv("AWS_REGION", "us-east-1"),
            # 存储桶：兼容 S3_BUCKET（若不存在则使用默认 ai-file）
            "bucket_name": (
                os.getenv("S3_BUCKET")
                or os.getenv("UPLOAD_S3_BUCKET")  # 若只配置了上传桶名，下载也可复用
                or "ai-file"
            ),
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
            
            logger.info(f"S3 download client created successfully for endpoint: {config.get('s3_endpoint_url', 'AWS S3')}")
            return s3_client
            
        except NoCredentialsError:
            raise ValueError("S3 credentials not provided or invalid")
        except ClientError as e:
            raise ValueError(f"Failed to create S3 client: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error creating S3 client: {str(e)}")
    
    async def download_file(self,
                          bucket_name: str,
                          s3_key: str,
                          local_file_path: str,
                          s3_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        从S3下载文件到本地

        Args:
            bucket_name: S3存储桶名称
            s3_key: S3对象键
            local_file_path: 本地文件保存路径
            s3_config: S3配置，如果为None则使用默认配置

        Returns:
            下载结果字典
        """
        start_time = datetime.now()

        try:
            # 应用MediaConvert的中文文件名处理方案
            from utils.encoding_utils import EncodingUtils

            # 确保S3 key是正确的UTF-8编码
            s3_key = EncodingUtils.ensure_utf8(s3_key)
            logger.debug(f"Processed S3 key: {s3_key}")

            # 使用配置或默认配置
            config = s3_config or self.default_config

            # 创建S3客户端
            s3_client = self.create_s3_client(config)
            
            # 确保本地目录存在
            local_path = Path(local_file_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting download from s3://{bucket_name}/{s3_key} to {local_file_path}")
            
            # 获取文件信息
            try:
                head_response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                file_size = head_response.get('ContentLength', 0)
                last_modified = head_response.get('LastModified')
                content_type = head_response.get('ContentType', 'application/octet-stream')
                
                logger.info(f"File info - Size: {file_size} bytes, Type: {content_type}, Modified: {last_modified}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise FileNotFoundError(f"File not found in S3: s3://{bucket_name}/{s3_key}")
                else:
                    raise
            
            # 在线程池中执行下载（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: s3_client.download_file(bucket_name, s3_key, str(local_path))
            )
            
            # 验证下载的文件
            if not local_path.exists():
                raise FileNotFoundError(f"Downloaded file not found: {local_file_path}")
            
            downloaded_size = local_path.stat().st_size
            if downloaded_size != file_size:
                raise ValueError(f"File size mismatch. Expected: {file_size}, Got: {downloaded_size}")
            
            end_time = datetime.now()
            download_time = (end_time - start_time).total_seconds()
            
            logger.info(f"Successfully downloaded {downloaded_size} bytes in {download_time:.2f}s")
            
            return {
                'success': True,
                'local_path': str(local_path),
                'file_size': downloaded_size,
                'download_time': download_time,
                'content_type': content_type,
                's3_url': f"s3://{bucket_name}/{s3_key}",
                'last_modified': last_modified.isoformat() if last_modified else None
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
            logger.error(f"Unexpected error during download: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    async def check_file_exists(self, 
                              bucket_name: str,
                              s3_key: str,
                              s3_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        检查S3文件是否存在
        
        Args:
            bucket_name: S3存储桶名称
            s3_key: S3对象键
            s3_config: S3配置
            
        Returns:
            检查结果字典
        """
        try:
            config = s3_config or self.default_config
            s3_client = self.create_s3_client(config)
            
            head_response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            
            return {
                'exists': True,
                'file_size': head_response.get('ContentLength', 0),
                'last_modified': head_response.get('LastModified'),
                'content_type': head_response.get('ContentType', 'application/octet-stream'),
                'etag': head_response.get('ETag', '').strip('"')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'exists': False}
            else:
                logger.error(f"Error checking file existence: {e}")
                return {
                    'exists': False,
                    'error': str(e)
                }
        except Exception as e:
            logger.error(f"Unexpected error checking file: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    async def get_download_url(self, 
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
            
            logger.debug(f"Generated presigned URL for s3://{bucket_name}/{s3_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def parse_s3_url(self, s3_url: str) -> Optional[Dict[str, str]]:
        """
        解析S3 URL
        
        Args:
            s3_url: S3 URL (格式: s3://bucket/key 或 https://...)
            
        Returns:
            包含bucket和key的字典，或None
        """
        try:
            if s3_url.startswith('s3://'):
                # s3://bucket/key 格式
                parts = s3_url[5:].split('/', 1)
                if len(parts) == 2:
                    return {'bucket': parts[0], 'key': parts[1]}
            elif 'amazonaws.com' in s3_url or 's3.' in s3_url:
                # https://bucket.s3.region.amazonaws.com/key 格式
                from urllib.parse import urlparse
                parsed = urlparse(s3_url)
                
                if parsed.hostname:
                    # 提取bucket名称
                    if parsed.hostname.startswith('s3.'):
                        # https://s3.region.amazonaws.com/bucket/key
                        path_parts = parsed.path.lstrip('/').split('/', 1)
                        if len(path_parts) == 2:
                            return {'bucket': path_parts[0], 'key': path_parts[1]}
                    else:
                        # https://bucket.s3.region.amazonaws.com/key
                        bucket = parsed.hostname.split('.')[0]
                        key = parsed.path.lstrip('/')
                        if bucket and key:
                            return {'bucket': bucket, 'key': key}
            
            logger.warning(f"Unable to parse S3 URL: {s3_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing S3 URL {s3_url}: {e}")
            return None
