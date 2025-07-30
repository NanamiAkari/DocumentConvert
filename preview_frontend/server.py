#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LibreOffice文档预览服务器
提供静态文件服务和PDF预览功能
"""

import http.server
import socketserver
import os
import json
from pathlib import Path
from urllib.parse import unquote

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """自定义请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='/workspace', **kwargs)
    
    def translate_path(self, path):
        """重写路径转换方法，修复PDF文件访问路径"""
        # 解码URL路径
        path = unquote(path)
        
        # 移除查询参数
        if '?' in path:
            path = path.split('?')[0]
        
        # 处理特殊路径映射
        if path.startswith('/test/pdf_output/'):
            # 直接映射到实际文件系统路径
            file_path = '/workspace' + path
            return file_path
        
        # 其他路径使用默认处理
        return super().translate_path(path)
    
    def end_headers(self):
        # 添加CORS头部
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # 处理API请求
        if self.path == '/api/files':
            self.handle_file_list()
        elif self.path.startswith('/api/'):
            self.send_error(404, "API endpoint not found")
        else:
            # 处理静态文件请求
            super().do_GET()
    
    def handle_file_list(self):
        """返回文件列表API"""
        try:
            pdf_dir = Path('/workspace/test/pdf_output')
            files = []
            
            if pdf_dir.exists():
                for pdf_file in pdf_dir.glob('*.pdf'):
                    # 推断原始文件类型
                    original_type = 'PDF'
                    if '试卷' in pdf_file.name or '.doc' in pdf_file.name:
                        original_type = 'DOC'
                    elif '课程' in pdf_file.name or '.ppt' in pdf_file.name:
                        original_type = 'PPTX'
                    elif '平台' in pdf_file.name or '.xls' in pdf_file.name:
                        original_type = 'XLSX'
                    elif '.docx' in pdf_file.name:
                        original_type = 'DOCX'
                    
                    files.append({
                        'name': pdf_file.name,
                        'type': 'PDF',
                        'path': f'/test/pdf_output/{pdf_file.name}',
                        'originalType': original_type,
                        'size': pdf_file.stat().st_size
                    })
            
            # 返回JSON响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'success': True,
                'files': files,
                'total': len(files)
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.address_string()}] {format % args}")

def start_server(port=8080):
    """启动预览服务器"""
    try:
        with socketserver.TCPServer(("", port), PreviewHandler) as httpd:
            print(f"\n🚀 LibreOffice文档预览服务器启动成功!")
            print(f"📍 服务地址: http://localhost:{port}/preview_frontend/")
            print(f"📁 文件目录: /workspace/test/pdf_output/")
            print(f"⏹️  按 Ctrl+C 停止服务\n")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LibreOffice文档预览服务器')
    parser.add_argument('-p', '--port', type=int, default=8080, help='服务端口 (默认: 8080)')
    
    args = parser.parse_args()
    start_server(args.port)
