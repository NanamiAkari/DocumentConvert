# PDF转换错误 (MinerU 2.0 Python API)

文件: 服装识别需求描述.pdf
转换时间: 2025-07-31 15:33:17

## 错误分析

未知错误 - name 'input_path' is not defined...

## 详细错误信息

```
name 'input_path' is not defined
```

## 完整堆栈跟踪

```
Traceback (most recent call last):
  File "/workspace/services/document_service.py", line 208, in _convert_pdf_to_markdown
    self._clear_gpu_memory()
  File "/workspace/services/document_service.py", line 366, in _clear_gpu_memory
    'input_path': input_path,
NameError: name 'input_path' is not defined

```

## 建议解决方案

1. 检查GPU内存是否足够
2. 检查CUDA和PyTorch是否正确安装
3. 检查PDF文件是否损坏或格式不支持
4. 尝试重启Python进程释放资源
