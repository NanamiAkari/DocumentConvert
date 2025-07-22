import os
import subprocess
import gc
import argparse

# 尝试导入torch，如果可用的话
try:
    import torch
    has_torch = True
except ImportError:
    has_torch = False

# 解析命令行参数
parser = argparse.ArgumentParser(description='批量将文件转换为Markdown格式')
parser.add_argument('--force', action='store_true', help='强制重新转换所有文件，即使输出文件已存在')
args = parser.parse_args()

# 支持的输入文件类型
SUPPORTED_EXTS = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png']

test_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(test_dir, 'md_output')
os.makedirs(output_dir, exist_ok=True)

for fname in os.listdir(test_dir):
    ext = os.path.splitext(fname)[1].lower()
    if ext in SUPPORTED_EXTS:
        in_path = os.path.join(test_dir, fname)
        md_name = os.path.splitext(fname)[0] + '.md'
        md_path = os.path.join(output_dir, md_name)
        if os.path.exists(md_path) and not args.force:
            print(f"[跳过] 已存在: {md_path}")
            continue
        print(f"[转换] {in_path} -> {md_path}")
        cmd = [
            'magic-pdf',
            '-p', in_path,
            '-o', md_path
        ]
        try:
            # 执行垃圾回收以避免CUDA OOM
            gc.collect()
            if has_torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
                print(f"[内存] 已执行垃圾回收和CUDA缓存清理")
            
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[失败] {in_path}: {e}")

print("批量转换完成。md文件输出在:", output_dir) 