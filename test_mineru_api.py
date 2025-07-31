#!/usr/bin/env python3
"""
测试MinerU 2.0 API的正确用法
"""

import os
import tempfile
from pathlib import Path
from mineru import Dataset

def test_mineru_api():
    """测试MinerU API"""
    print("=== 测试MinerU 2.0 API ===")
    
    # 检查test目录中的PDF文件
    test_dir = Path("test")
    pdf_files = list(test_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("未找到PDF文件进行测试")
        return
    
    pdf_file = pdf_files[0]
    print(f"测试文件: {pdf_file}")
    
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"临时目录: {temp_path}")
        
        try:
            # 创建Dataset
            print("创建Dataset...")
            dataset = Dataset(data_dir=str(temp_path))
            
            # 添加PDF文件
            print("添加PDF文件...")
            dataset.add_pdf(str(pdf_file))
            
            # 执行转换
            print("执行PDF转Markdown...")
            dataset.apply(lambda x: x.pdf_to_markdown())
            
            # 查找生成的文件
            print("查找生成的文件...")
            output_files = list(temp_path.rglob("*"))
            
            print(f"生成的文件数量: {len(output_files)}")
            for file in output_files:
                if file.is_file():
                    print(f"  - {file.relative_to(temp_path)} ({file.stat().st_size} bytes)")
            
            # 查找markdown文件
            md_files = list(temp_path.glob("**/*.md"))
            if md_files:
                print(f"\n找到 {len(md_files)} 个Markdown文件:")
                for md_file in md_files:
                    print(f"  - {md_file}")
                    # 读取前几行内容
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()[:500]
                            print(f"    内容预览: {content[:100]}...")
                    except Exception as e:
                        print(f"    读取错误: {e}")
            else:
                print("未找到Markdown文件")
                
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_mineru_api()
