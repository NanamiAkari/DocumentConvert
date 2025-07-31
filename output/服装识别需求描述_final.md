# PDF转换错误 (MinerU 2.0 Python API)

文件: 服装识别需求描述.pdf
转换时间: 2025-07-31 13:10:59

## 错误分析

模型加载错误 - 检查模型文件是否完整下载

## 详细错误信息

```
CUDA error: out of memory
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUNCH_BLOCKING=1
Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.

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
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/batch_analyze.py", line 32, in __call__
    self.model = self.model_manager.get_model(
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/pipeline_analyze.py", line 34, in get_model
    self._models[key] = custom_model_init(
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/pipeline_analyze.py", line 61, in custom_model_init
    custom_model = MineruPipelineModel(**model_input)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/model_init.py", line 144, in __init__
    self.mfd_model = atom_model_manager.get_atom_model(
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/model_init.py", line 89, in get_atom_model
    self._models[key] = atom_model_init(model_name=atom_model_name, **kwargs)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/model_init.py", line 100, in atom_model_init
    atom_model = mfd_model_init(
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/backend/pipeline/model_init.py", line 31, in mfd_model_init
    mfd_model = YOLOv8MFDModel(weight, device)
  File "/opt/mineru_venv/lib/python3.10/site-packages/mineru/model/mfd/yolo_v8.py", line 17, in __init__
    self.model = YOLO(weight).to(device)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1355, in to
    return self._apply(convert)
  File "/opt/mineru_venv/lib/python3.10/site-packages/ultralytics/engine/model.py", line 877, in _apply
    self = super()._apply(fn)  # noqa
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 915, in _apply
    module._apply(fn)
  File "/opt/mineru_venv/lib/python3.10/site-packages/ultralytics/nn/tasks.py", line 289, in _apply
    self = super()._apply(fn)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 915, in _apply
    module._apply(fn)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 915, in _apply
    module._apply(fn)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 915, in _apply
    module._apply(fn)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 942, in _apply
    param_applied = fn(param)
  File "/opt/mineru_venv/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1341, in convert
    return t.to(
RuntimeError: CUDA error: out of memory
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUNCH_BLOCKING=1
Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.


```

## 建议解决方案

1. 检查GPU内存是否足够
2. 检查CUDA和PyTorch是否正确安装
3. 检查PDF文件是否损坏或格式不支持
4. 尝试重启Python进程释放资源
