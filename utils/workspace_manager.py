#!/usr/bin/env python3
"""
工作空间管理器
复刻MediaConvert的工作空间管理逻辑，统一管理任务工作目录和临时文件
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.logging_utils import configure_logging

logger = configure_logging(name=__name__)


class WorkspaceManager:
    """工作空间管理器"""
    
    def __init__(self, base_workspace_dir: Optional[str] = None):
        """
        初始化工作空间管理器
        
        Args:
            base_workspace_dir: 基础工作空间目录，如果为None则使用默认目录
        """
        # 设置基础工作空间目录，与MediaConvert保持一致
        if base_workspace_dir:
            self.base_workspace_dir = Path(base_workspace_dir)
        else:
            # 默认使用 /app/task_workspace，与MediaConvert一致
            self.base_workspace_dir = Path("/app/task_workspace")
        
        # 临时文件目录，与MediaConvert保持一致
        self.temp_files_dir = Path("/app/temp_files")
        
        # 确保目录存在
        self._ensure_directories()
        
        logger.info(f"WorkspaceManager initialized - Base: {self.base_workspace_dir}, Temp: {self.temp_files_dir}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            self.base_workspace_dir.mkdir(parents=True, exist_ok=True)
            self.temp_files_dir.mkdir(parents=True, exist_ok=True)
            
            # 设置目录权限
            os.chmod(self.base_workspace_dir, 0o755)
            os.chmod(self.temp_files_dir, 0o755)
            
        except Exception as e:
            logger.error(f"Failed to create workspace directories: {e}")
            raise
    
    def create_task_workspace(self, task_id: str) -> Path:
        """
        为任务创建专用工作空间
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务工作空间路径
        """
        try:
            task_workspace = self.base_workspace_dir / f"task_{task_id}"
            task_workspace.mkdir(parents=True, exist_ok=True)
            
            # 创建子目录
            (task_workspace / "input").mkdir(exist_ok=True)
            (task_workspace / "output").mkdir(exist_ok=True)
            (task_workspace / "temp").mkdir(exist_ok=True)
            
            logger.info(f"Created task workspace: {task_workspace}")
            return task_workspace
            
        except Exception as e:
            logger.error(f"Failed to create task workspace for {task_id}: {e}")
            raise
    
    def get_task_workspace(self, task_id: str) -> Path:
        """
        获取任务工作空间路径
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务工作空间路径
        """
        return self.base_workspace_dir / f"task_{task_id}"
    
    def get_task_input_dir(self, task_id: str) -> Path:
        """获取任务输入目录"""
        return self.get_task_workspace(task_id) / "input"
    
    def get_task_output_dir(self, task_id: str) -> Path:
        """获取任务输出目录"""
        return self.get_task_workspace(task_id) / "output"
    
    def get_task_temp_dir(self, task_id: str) -> Path:
        """获取任务临时目录"""
        return self.get_task_workspace(task_id) / "temp"
    
    def get_downloaded_file_path(self, task_id: str, filename: str) -> Path:
        """
        获取下载文件的存储路径
        
        Args:
            task_id: 任务ID
            filename: 文件名
            
        Returns:
            下载文件路径
        """
        input_dir = self.get_task_input_dir(task_id)
        return input_dir / filename
    
    def get_output_file_path(self, task_id: str, filename: str) -> Path:
        """
        获取输出文件的存储路径
        
        Args:
            task_id: 任务ID
            filename: 文件名
            
        Returns:
            输出文件路径
        """
        output_dir = self.get_task_output_dir(task_id)
        return output_dir / filename
    
    def get_temp_file_path(self, task_id: str, filename: str) -> Path:
        """
        获取临时文件的存储路径
        
        Args:
            task_id: 任务ID
            filename: 文件名
            
        Returns:
            临时文件路径
        """
        temp_dir = self.get_task_temp_dir(task_id)
        return temp_dir / filename
    
    def create_temp_file(self, suffix: str = "", prefix: str = "temp_") -> Path:
        """
        创建临时文件
        
        Args:
            suffix: 文件后缀
            prefix: 文件前缀
            
        Returns:
            临时文件路径
        """
        try:
            # 使用tempfile创建临时文件
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix,
                prefix=prefix,
                dir=str(self.temp_files_dir)
            )
            os.close(fd)  # 关闭文件描述符
            
            temp_file = Path(temp_path)
            logger.debug(f"Created temp file: {temp_file}")
            return temp_file
            
        except Exception as e:
            logger.error(f"Failed to create temp file: {e}")
            raise
    
    def cleanup_task_workspace(self, task_id: str) -> bool:
        """
        清理任务工作空间
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否清理成功
        """
        try:
            task_workspace = self.get_task_workspace(task_id)
            
            if task_workspace.exists():
                shutil.rmtree(task_workspace)
                logger.info(f"Cleaned up task workspace: {task_workspace}")
                return True
            else:
                logger.debug(f"Task workspace does not exist: {task_workspace}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cleanup task workspace for {task_id}: {e}")
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理旧的临时文件
        
        Args:
            max_age_hours: 最大保留时间(小时)
            
        Returns:
            清理的文件数量
        """
        try:
            if not self.temp_files_dir.exists():
                return 0
            
            current_time = datetime.now()
            cleaned_count = 0
            
            for temp_file in self.temp_files_dir.iterdir():
                if temp_file.is_file():
                    # 检查文件年龄
                    file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        try:
                            temp_file.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up old temp file: {temp_file}")
                        except Exception as e:
                            logger.warning(f"Failed to delete temp file {temp_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old temp files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0
    
    def get_workspace_stats(self) -> Dict[str, Any]:
        """
        获取工作空间统计信息
        
        Returns:
            工作空间统计字典
        """
        try:
            stats = {
                'base_workspace_dir': str(self.base_workspace_dir),
                'temp_files_dir': str(self.temp_files_dir),
                'active_task_workspaces': 0,
                'temp_files_count': 0,
                'total_workspace_size': 0,
                'temp_files_size': 0
            }
            
            # 统计活跃的任务工作空间
            if self.base_workspace_dir.exists():
                for item in self.base_workspace_dir.iterdir():
                    if item.is_dir() and item.name.startswith('task_'):
                        stats['active_task_workspaces'] += 1
                        stats['total_workspace_size'] += self._get_dir_size(item)
            
            # 统计临时文件
            if self.temp_files_dir.exists():
                for item in self.temp_files_dir.iterdir():
                    if item.is_file():
                        stats['temp_files_count'] += 1
                        stats['temp_files_size'] += item.stat().st_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get workspace stats: {e}")
            return {}
    
    def _get_dir_size(self, directory: Path) -> int:
        """获取目录大小"""
        try:
            total_size = 0
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size
        except Exception:
            return 0
    
    def ensure_output_directory(self, output_path: str) -> Path:
        """
        确保输出目录存在
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            输出文件路径对象
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            return output_file
        except Exception as e:
            logger.error(f"Failed to ensure output directory for {output_path}: {e}")
            raise


# 全局工作空间管理器实例
workspace_manager = WorkspaceManager()
