#!/usr/bin/env python3
"""
数据库迁移脚本：将任务ID从UUID改为自增整数
"""

import os
import sys
import sqlite3
import asyncio
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, DocumentTask
from utils.logging_utils import configure_logging

logger = configure_logging(name=__name__)


async def migrate_sqlite_to_autoincrement():
    """迁移SQLite数据库，将UUID ID改为自增整数ID"""
    
    # 获取数据库URL
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./document_tasks.db")
    
    if not database_url.startswith("sqlite"):
        logger.error("This migration script only supports SQLite databases")
        return False
    
    # 转换为同步SQLite URL进行迁移
    sync_db_path = database_url.replace("sqlite+aiosqlite://", "").replace("sqlite://", "")
    if sync_db_path.startswith("/"):
        sync_db_path = sync_db_path[1:]  # 移除开头的斜杠
    
    logger.info(f"Migrating SQLite database: {sync_db_path}")
    
    try:
        # 检查数据库文件是否存在
        if not Path(sync_db_path).exists():
            logger.info("Database file does not exist, creating new database with autoincrement ID")
            # 创建新的数据库
            engine = create_async_engine(database_url)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await engine.dispose()
            logger.info("New database created successfully")
            return True
        
        # 备份原数据库
        backup_path = f"{sync_db_path}.backup"
        import shutil
        shutil.copy2(sync_db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        
        # 连接到数据库
        conn = sqlite3.connect(sync_db_path)
        cursor = conn.cursor()
        
        # 检查是否已经是自增ID
        cursor.execute("PRAGMA table_info(document_tasks)")
        columns = cursor.fetchall()
        id_column = next((col for col in columns if col[1] == 'id'), None)
        
        if id_column and 'INTEGER' in id_column[2].upper():
            logger.info("Database already uses autoincrement ID, no migration needed")
            conn.close()
            return True
        
        # 检查是否有数据
        cursor.execute("SELECT COUNT(*) FROM document_tasks")
        row_count = cursor.fetchone()[0]
        
        if row_count > 0:
            logger.warning(f"Found {row_count} existing tasks. Migration will assign new sequential IDs.")
            
            # 创建新表结构
            cursor.execute("""
                CREATE TABLE document_tasks_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    priority VARCHAR(20) DEFAULT 'normal' NOT NULL,
                    input_path TEXT,
                    output_path TEXT,
                    file_url TEXT,
                    bucket_name VARCHAR(255),
                    file_path TEXT,
                    file_name VARCHAR(255),
                    file_size_bytes INTEGER,
                    output_url VARCHAR(500),
                    s3_urls JSON,
                    params JSON,
                    decode_options JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME,
                    started_at DATETIME,
                    completed_at DATETIME,
                    task_processing_time FLOAT,
                    result JSON,
                    error_message TEXT,
                    pages_processed INTEGER,
                    conversion_quality VARCHAR(20),
                    retry_count INTEGER DEFAULT 0 NOT NULL,
                    max_retry_count INTEGER DEFAULT 3 NOT NULL,
                    last_retry_at DATETIME,
                    callback_url VARCHAR(500),
                    callback_status_code INTEGER,
                    callback_message VARCHAR(512),
                    callback_time DATETIME,
                    platform VARCHAR(100),
                    engine_name VARCHAR(50),
                    workspace_path TEXT,
                    temp_files JSON
                )
            """)
            
            # 迁移数据（除了ID字段）- 包含所有现有列
            cursor.execute("""
                INSERT INTO document_tasks_new (
                    task_type, status, priority, input_path, output_path, file_url,
                    bucket_name, file_path, file_name, file_size_bytes, output_url, s3_urls,
                    params, decode_options, created_at, updated_at, started_at, completed_at,
                    task_processing_time, result, error_message, pages_processed, conversion_quality,
                    retry_count, max_retry_count, last_retry_at, callback_url,
                    callback_status_code, callback_message, callback_time, platform, engine_name
                )
                SELECT
                    task_type, status, priority, input_path, output_path, file_url,
                    bucket_name, file_path, file_name, file_size_bytes, output_url, s3_urls,
                    params, decode_options, created_at, updated_at, started_at, completed_at,
                    task_processing_time, result, error_message, pages_processed, conversion_quality,
                    retry_count, max_retry_count, last_retry_at, callback_url,
                    callback_status_code, callback_message, callback_time, platform, engine_name
                FROM document_tasks
                ORDER BY created_at
            """)
            
            # 删除旧表
            cursor.execute("DROP TABLE document_tasks")
            
            # 重命名新表
            cursor.execute("ALTER TABLE document_tasks_new RENAME TO document_tasks")
            
            logger.info(f"Migrated {row_count} tasks with new sequential IDs")
        else:
            logger.info("No existing data found, recreating table with autoincrement ID")
            
            # 删除旧表并创建新表
            cursor.execute("DROP TABLE document_tasks")
            
            # 使用SQLAlchemy创建新表结构
            conn.close()
            
            # 重新创建表结构
            engine = create_async_engine(database_url)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await engine.dispose()
        
        if row_count > 0:
            conn.commit()
            conn.close()
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


async def main():
    """主函数"""
    logger.info("Starting database migration to autoincrement ID...")
    
    success = await migrate_sqlite_to_autoincrement()
    
    if success:
        logger.info("✅ Database migration completed successfully!")
        logger.info("🔄 Please restart the application to use the new database structure.")
    else:
        logger.error("❌ Database migration failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
