# PDF转换错误 (MinerU 2.0 Python API)

文件: 智涌君.pdf
转换时间: 2025-07-31 13:13:09

## 错误分析

GPU内存不足错误 - 需要释放GPU内存或使用更小的batch size

## 详细错误信息

```
CUDA out of memory. Tried to allocate 136.00 MiB. GPU 0 has a total capacity of 44.53 GiB of which 32.62 MiB is free. Process 899595 has 14.52 GiB memory in use. Process 1039101 has 3.03 GiB memory in use. Process 1603024 has 6.96 GiB memory in use. Process 2007660 has 9.48 GiB memory in use. Process 785200 has 8.47 GiB memory in use. Process 795316 has 2.02 GiB memory in use. Of the allocated memory 1.50 GiB is allocated by PyTorch, and 167.00 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
```

## 完整堆栈跟踪

```
Traceback (most recent call last):
  File "/workspace/services/document_service.py", line 215, in _convert_pdf_to_markdown
    infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/pipeline_analyze.py", line 128, in doc_analyze
    batch_results = batch_image_analyze(batch_image, formula_enable, table_enable)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/pipeline_analyze.py", line 194, in batch_image_analyze
    results = batch_model(images_with_extra_info)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/batch_analyze.py", line 47, in __call__
    images_layout_res += self.model.layout_model.batch_predict(
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/layout/doclayout_yolo.py", line 63, in batch_predict
    predictions = self.model.predict(
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/engine/model.py", line 444, in predict
    return self.predictor.predict_cli(source=source) if is_cli else self.predictor(source=source, stream=stream)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/engine/predictor.py", line 168, in __call__
    return list(self.stream_inference(source, model, *args, **kwargs))  # merge list of Result into one
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/utils/_contextlib.py", line 36, in generator_context
    response = gen.send(None)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/engine/predictor.py", line 248, in stream_inference
    preds = self.inference(im, *args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/engine/predictor.py", line 142, in inference
    return self.model(im, augment=self.args.augment, visualize=visualize, embed=self.args.embed, *args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/nn/autobackend.py", line 420, in forward
    y = self.model(im, augment=augment, visualize=visualize, embed=embed)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/nn/tasks.py", line 96, in forward
    return self.predict(x, *args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/nn/tasks.py", line 114, in predict
    return self._predict_once(x, profile, visualize, embed)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/nn/tasks.py", line 136, in _predict_once
    x = m(x)  # run
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/nn/modules/block.py", line 234, in forward
    return self.cv2(torch.cat(y, 1))
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/doclayout_yolo/nn/modules/conv.py", line 50, in forward
    return self.act(self.bn(self.conv(x)))
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/conv.py", line 554, in forward
    return self._conv_forward(input, self.weight, self.bias)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/conv.py", line 549, in _conv_forward
    return F.conv2d(
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 136.00 MiB. GPU 0 has a total capacity of 44.53 GiB of which 32.62 MiB is free. Process 899595 has 14.52 GiB memory in use. Process 1039101 has 3.03 GiB memory in use. Process 1603024 has 6.96 GiB memory in use. Process 2007660 has 9.48 GiB memory in use. Process 785200 has 8.47 GiB memory in use. Process 795316 has 2.02 GiB memory in use. Of the allocated memory 1.50 GiB is allocated by PyTorch, and 167.00 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

```

## 建议解决方案

1. 检查GPU内存是否足够
2. 检查CUDA和PyTorch是否正确安装
3. 检查PDF文件是否损坏或格式不支持
4. 尝试重启Python进程释放资源
