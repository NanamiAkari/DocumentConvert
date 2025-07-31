# PDF批量转Markdown脚本说明

## 功能
- 批量扫描当前test目录下所有PDF文件，自动调用magic-pdf转换为Markdown（.md）文件
- 已存在的md文件自动跳过，避免重复转换
- 所有md文件输出到`md_output`子目录

## 使用方法
1. 确保已安装magic-pdf，并已激活相关环境
2. 将待转换的PDF文件放入test目录
3. 运行脚本：

```bash
python pdf2md_batch.py
```

4. 转换结果在`md_output`目录下

## 依赖
- Python 3.x
- magic-pdf（需在命令行可用）

## 备注
- 脚本可复用于任意PDF批量转md场景
- 如需自定义输出目录，可修改脚本中的`output_dir`变量 