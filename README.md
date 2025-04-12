# MinerU
MinerU 是一款将 PDF 转化为机器可读格式的工具（如markdown、json），可以很方便地抽取为任意格式。 

本项目是 [MinerU](https://github.com/opendatalab/MinerU/) 在 CNB.COOL 的运行时。

使用 CNB.COOL 的 GPU 进行 PDF 转换。

## 开始使用
使用镜像：
```bash
docker pull docker.cnb.cool/hex/mineru
```
作为云原生开发基础镜像：
```
$:
  vscode:
    - docker:
        # 指定云原生开发启动时的基础镜像为当前镜像
        image: docker.cnb.cool/hex/mineru
      services:
        - vscode
        - docker
```
进入云原生开发的 VSCode，在 Terminal 中启动环境:
```bash
source /opt/mineru_venv/bin/activate
```

## 帮助
- [MinerU 帮助文档](https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md)