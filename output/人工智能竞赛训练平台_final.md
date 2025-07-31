# PDF转换错误 (MinerU 2.0 Python API)

文件: 人工智能竞赛训练平台 v20250629.pdf
转换时间: 2025-07-31 13:14:21

## 错误分析

GPU内存不足错误 - 需要释放GPU内存或使用更小的batch size

## 详细错误信息

```
CUDA out of memory. Tried to allocate 282.00 MiB. GPU 0 has a total capacity of 44.53 GiB of which 260.62 MiB is free. Process 899595 has 14.52 GiB memory in use. Process 1039101 has 3.11 GiB memory in use. Process 1603024 has 6.96 GiB memory in use. Process 2007660 has 9.48 GiB memory in use. Process 785200 has 8.47 GiB memory in use. Process 795316 has 1.71 GiB memory in use. Of the allocated memory 1.29 GiB is allocated by PyTorch, and 56.25 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
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
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/batch_analyze.py", line 256, in __call__
    html_code, table_cell_bboxes, logic_points, elapse = table_model.predict(table_res_dict['table_img'])
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/table/rapid_table.py", line 70, in predict
    ocr_result = self.ocr_engine.ocr(bgr_image)[0]
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/pytorch_paddle.py", line 120, in ocr
    dt_boxes, rec_res = self.__call__(img, mfd_res=mfd_res)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/pytorch_paddle.py", line 185, in __call__
    rec_res, elapse = self.text_recognizer(img_crop_list)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/tools/infer/predict_rec.py", line 423, in __call__
    prob_out = self.net(inp)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/pytorchocr/modeling/architectures/base_model.py", line 74, in forward
    x = self.backbone(x)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/pytorchocr/modeling/backbones/rec_hgnet.py", line 244, in forward
    x = stage(x)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/pytorchocr/modeling/backbones/rec_hgnet.py", line 148, in forward
    x = self.blocks(x)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/container.py", line 240, in forward
    input = module(input)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1751, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1762, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/ocr/paddleocr2pytorch/pytorchocr/modeling/backbones/rec_hgnet.py", line 102, in forward
    x = torch.cat(output, dim=1)
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 282.00 MiB. GPU 0 has a total capacity of 44.53 GiB of which 260.62 MiB is free. Process 899595 has 14.52 GiB memory in use. Process 1039101 has 3.11 GiB memory in use. Process 1603024 has 6.96 GiB memory in use. Process 2007660 has 9.48 GiB memory in use. Process 785200 has 8.47 GiB memory in use. Process 795316 has 1.71 GiB memory in use. Of the allocated memory 1.29 GiB is allocated by PyTorch, and 56.25 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

```

## 建议解决方案

1. 检查GPU内存是否足够
2. 检查CUDA和PyTorch是否正确安装
3. 检查PDF文件是否损坏或格式不支持
4. 尝试重启Python进程释放资源
