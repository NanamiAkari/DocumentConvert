#!/usr/bin/env python3
"""
文档转换调度系统启动脚本
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_demo_tasks():
    """创建演示任务"""
    from processors.task_processor import TaskProcessor
    
    # 初始化任务处理器
    task_processor = TaskProcessor(
        max_concurrent_tasks=3,
        task_check_interval=5
    )
    
    # 启动任务处理器
    await task_processor.start()
    
    logger.info("创建演示任务...")
    
    # 定义test目录下的文件
    test_files = [
        {
            'name': '2025年浙江省杭州市中考语文试卷.doc',
            'task_type': 'office_to_pdf',
            'input_path': '/workspace/test/2025年浙江省杭州市中考语文试卷.doc',
            'output_path': '/workspace/output/2025年浙江省杭州市中考语文试卷.pdf'
        },
        {
            'name': '2025年杭州中考科学试卷及答案.doc', 
            'task_type': 'office_to_pdf',
            'input_path': '/workspace/test/2025年杭州中考科学试卷及答案.doc',
            'output_path': '/workspace/output/2025年杭州中考科学试卷及答案.pdf'
        },
        {
            'name': 'AI通识课程建设方案.pptx',
            'task_type': 'office_to_pdf', 
            'input_path': '/workspace/test/AI通识课程建设方案.pptx',
            'output_path': '/workspace/output/AI通识课程建设方案.pdf'
        }
    ]
    
    # 创建任务
    task_ids = []
    for file_info in test_files:
        if os.path.exists(file_info['input_path']):
            task_id = await task_processor.create_task(
                task_type=file_info['task_type'],
                input_path=file_info['input_path'],
                output_path=file_info['output_path'],
                params={}
            )
            task_ids.append(task_id)
            logger.info(f"创建任务 {task_id}: {file_info['name']}")
        else:
            logger.warning(f"文件不存在: {file_info['input_path']}")
    
    # 等待所有任务完成
    logger.info(f"等待 {len(task_ids)} 个任务完成...")
    
    while task_ids:
        completed_tasks = []
        for task_id in task_ids:
            status = task_processor.get_task_status(task_id)
            if status and status['status'] in ['completed', 'failed']:
                completed_tasks.append(task_id)
                logger.info(f"任务 {task_id} 状态: {status['status']}")
                if status['status'] == 'failed' and status.get('error_message'):
                    logger.error(f"任务 {task_id} 错误: {status['error_message']}")
        
        # 移除已完成的任务
        for task_id in completed_tasks:
            task_ids.remove(task_id)
        
        if task_ids:
            await asyncio.sleep(2)
    
    # 显示统计信息
    stats = task_processor.get_queue_stats()
    logger.info(f"任务统计 - 已完成: {stats['completed_tasks']}, 失败: {stats['failed_tasks']}")
    
    # 停止任务处理器
    await task_processor.stop()
    logger.info("演示任务完成")


def start_api_server():
    """启动API服务器"""
    import uvicorn
    from api.main import app

    logger.info("启动API服务器...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


async def main():
    """主函数"""
    logger.info("=== 文档转换调度系统启动 ===")

    try:
        # 启动API服务器
        start_api_server()

    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 可以选择运行演示任务或启动API服务器
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # 运行演示任务
        asyncio.run(create_demo_tasks())
    else:
        # 启动API服务器
        start_api_server()