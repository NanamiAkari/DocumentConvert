#!/usr/bin/env python3
"""
文件名编码处理工具类
参考MediaConvert项目的中文文件名处理方案
"""

import os
import urllib.parse
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EncodingUtils:
    """文件名编码处理工具类"""
    
    # 常见的乱码字符列表
    GARBLED_CHARS = [
        'ã', 'è', '§', 'é', '¢', 'æ', '°', 'æ', 'º', 'å', 'ä', 'ç', 'ï', 'ì', 'í', 'î',
        'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', 'ù', 'ú', 'û', 'ü', 'ý', 'ÿ', 'À', 'Á', 'Â', 'Ã',
        'Ä', 'Å', 'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï', 'Ð', 'Ñ', 'Ò', 'Ó',
        'Ô', 'Õ', 'Ö', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ', 'ß', 'à', 'á', 'â'
    ]
    
    @classmethod
    def decode_url_filename(cls, url_or_path: str) -> str:
        """
        解码URL编码的文件名，支持中文文件名
        参考MediaConvert的实现
        
        Args:
            url_or_path: URL或文件路径
            
        Returns:
            解码后的文件名
        """
        try:
            # 提取文件名部分
            filename = os.path.basename(url_or_path)
            
            # 检查是否包含URL编码字符（%XX格式）
            if '%' in filename and cls._is_url_encoded(filename):
                logger.debug(f"Detected URL-encoded filename: {filename}")
                # 尝试URL解码
                try:
                    decoded_filename = urllib.parse.unquote(filename, encoding='utf-8')
                    logger.debug(f"URL decoded filename: {decoded_filename}")
                    # 验证解码结果
                    if decoded_filename != filename and not cls._has_garbled_chars(decoded_filename):
                        return decoded_filename
                except UnicodeDecodeError as e:
                    logger.warning(f"URL decode failed: {e}")
            
            # 如果文件名已经是正确的UTF-8编码，直接返回
            try:
                filename.encode('utf-8').decode('utf-8')
                # 检查是否包含乱码字符
                if not cls._has_garbled_chars(filename):
                    return filename
            except UnicodeError:
                pass
            
            # 如果仍有问题，尝试修复编码
            fixed_filename = cls.fix_filename_encoding(filename)
            return fixed_filename
            
        except Exception as e:
            logger.warning(f"Failed to decode filename from {url_or_path}: {e}")
            return os.path.basename(url_or_path)
    
    @classmethod
    def fix_filename_encoding(cls, filename: str) -> str:
        """
        修复文件名编码问题
        
        Args:
            filename: 原始文件名
            
        Returns:
            修复后的文件名
        """
        if not filename:
            return filename
            
        try:
            # 检查是否包含常见的乱码字符
            if cls._has_garbled_chars(filename):
                logger.info(f"Detected garbled filename: {filename}")
                
                # 尝试多种编码修复方法
                fixed_name = cls._try_encoding_fixes(filename)
                
                if fixed_name and fixed_name != filename:
                    logger.info(f"Fixed encoding: {filename} -> {fixed_name}")
                    return fixed_name
                else:
                    logger.warning(f"Could not fix encoding for filename: {filename}")
                    
        except Exception as e:
            logger.warning(f"Error during encoding fix for filename {filename}: {e}")
            
        return filename
    
    @classmethod
    def fix_file_path_encoding(cls, file_path: str) -> str:
        """
        修复文件路径编码问题
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            修复后的文件路径
        """
        if not file_path:
            return file_path
            
        try:
            # 检查是否包含常见的乱码字符
            if cls._has_garbled_chars(file_path):
                logger.info(f"Detected garbled file path: {file_path}")
                
                # 尝试多种编码修复方法
                fixed_path = cls._try_encoding_fixes(file_path)
                
                if fixed_path and fixed_path != file_path:
                    logger.info(f"Fixed path encoding: {file_path} -> {fixed_path}")
                    return fixed_path
                else:
                    logger.warning(f"Could not fix encoding for file path: {file_path}")
                    
        except Exception as e:
            logger.warning(f"Error during encoding fix for file path {file_path}: {e}")
            
        return file_path
    
    @classmethod
    def ensure_utf8(cls, text: str) -> str:
        """
        确保文本是正确的UTF-8编码
        
        Args:
            text: 输入文本
            
        Returns:
            UTF-8编码的文本
        """
        if not text:
            return text
            
        try:
            # 尝试编码和解码以验证UTF-8
            text.encode('utf-8').decode('utf-8')
            return text
        except UnicodeError:
            # 如果失败，尝试修复
            return cls.fix_filename_encoding(text)
    
    @classmethod
    def _has_garbled_chars(cls, text: str) -> bool:
        """检查文本是否包含乱码字符"""
        return any(char in text for char in cls.GARBLED_CHARS)
    
    @classmethod
    def _is_url_encoded(cls, text: str) -> bool:
        """检查文本是否包含URL编码字符"""
        import re
        # 检查是否包含%XX格式的URL编码
        url_encoded_pattern = r'%[0-9A-Fa-f]{2}'
        return bool(re.search(url_encoded_pattern, text))
    
    @classmethod
    def _try_encoding_fixes(cls, text: str) -> Optional[str]:
        """
        尝试多种编码修复方法
        
        Args:
            text: 需要修复的文本
            
        Returns:
            修复后的文本，如果无法修复则返回None
        """
        # 方法1：Latin-1 -> UTF-8
        try:
            text_bytes = text.encode('latin-1')
            fixed_text = text_bytes.decode('utf-8')
            if not cls._has_garbled_chars(fixed_text):
                logger.debug(f"Fixed encoding (Latin-1->UTF-8): {fixed_text}")
                return fixed_text
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        
        # 方法2：ISO-8859-1 -> UTF-8
        try:
            text_bytes = text.encode('iso-8859-1')
            fixed_text = text_bytes.decode('utf-8')
            if not cls._has_garbled_chars(fixed_text):
                logger.debug(f"Fixed encoding (ISO-8859-1->UTF-8): {fixed_text}")
                return fixed_text
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        
        # 方法3：直接字节处理
        try:
            byte_data = bytes([ord(c) for c in text])
            fixed_text = byte_data.decode('utf-8')
            if not cls._has_garbled_chars(fixed_text):
                logger.debug(f"Fixed encoding (bytes->UTF-8): {fixed_text}")
                return fixed_text
        except (UnicodeDecodeError, ValueError):
            pass
        
        # 方法4：GBK -> UTF-8（针对中文）
        try:
            if any(ord(c) > 127 for c in text):
                text_bytes = text.encode('gbk')
                fixed_text = text_bytes.decode('utf-8')
                if not cls._has_garbled_chars(fixed_text):
                    logger.debug(f"Fixed encoding (GBK->UTF-8): {fixed_text}")
                    return fixed_text
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        
        return None
