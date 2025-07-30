#!/usr/bin/env python3
"""
测试PDF转Markdown转换功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.document_service import DocumentService

async def test_pdf_to_markdown():
    """测试PDF转Markdown转换"""
    print("开始测试PDF转Markdown转换...")
    
    # 初始化服务
    doc_service = DocumentService()
    
    # 测试文件路径
    input_pdf = Path("/workspace/test/人人皆可vibe编程.pdf")
    output_md = Path("/workspace/test/converted_output.md")
    
    # 检查输入文件是否存在
    if not input_pdf.exists():
        print(f"错误：输入文件不存在 {input_pdf}")
        return False
    
    try:
        # 执行转换
        print(f"转换文件: {input_pdf} -> {output_md}")
        params = {'force_reprocess': True}  # 强制重新处理
        result = await doc_service._convert_pdf_to_markdown(str(input_pdf), str(output_md), params)
        
        # 检查结果
        if result.get('success'):
            print("✅ 转换成功！")
            print(f"输出文件: {result.get('output_file')}")
            
            # 检查输出文件是否存在
            if output_md.exists():
                print(f"✅ 输出文件已生成: {output_md}")
                
                # 读取并显示前几行内容
                with open(output_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')[:10]  # 前10行
                    print("\n📄 转换后的内容预览:")
                    print("=" * 50)
                    for i, line in enumerate(lines, 1):
                        print(f"{i:2d}: {line}")
                    print("=" * 50)
                    print(f"总字符数: {len(content)}")
                    print(f"总行数: {len(content.split())}")
                
                return True
            else:
                print(f"❌ 输出文件未生成: {output_md}")
                return False
        else:
            print(f"❌ 转换失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 转换过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理输出文件（可选）
        # if output_md.exists():
        #     output_md.unlink()
        #     print(f"已清理输出文件: {output_md}")
        pass

if __name__ == "__main__":
    print("PDF转Markdown转换测试")
    print("=" * 40)
    
    # 运行测试
    success = asyncio.run(test_pdf_to_markdown())
    
    if success:
        print("\n🎉 测试通过！PDF转Markdown转换功能正常工作。")
        sys.exit(0)
    else:
        print("\n💥 测试失败！请检查错误信息。")
        sys.exit(1)