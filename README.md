# MinerU
MinerU 是一款将 PDF 转化为机器可读格式的工具（如markdown、json），可以很方便地抽取为任意格式。 

本项目是 [MinerU](https://github.com/opendatalab/MinerU/) 在 CNB.COOL 的运行时。

使用 CNB.COOL 的 GPU 进行 PDF, PPT, PPTX, DOC, DOCX, PNG, JPG 到 Markdown, Json转换。

![badge](https://cnb.cool/hex/MinerU/-/badge/git/latest/ci/git-clone-yyds) ![badge](https://cnb.cool/hex/MinerU/-/badge/git/latest/ci/status/tag_push) 

## 开始使用

### A.快速开始（推荐）

访问 https://cnb.cool/hex/MinerU-Runtime 项目，Fork项目，即可开始使用。

### B.使用镜像（高级用户）

```bash
docker pull docker.cnb.cool/hex/mineru:latest
```
作为云原生开发基础镜像，可通过 cpus 指定 CPU 核心数量。
```
$:
  vscode:
    - docker:
        image: docker.cnb.cool/hex/mineru:latest
      runner:
        cpus: 16
        tags: cnb:arch:amd64:gpu
      services:
        - vscode
        - docker
      stages:
        - name: ll
          script: ls -la
```
进入云原生开发的 VSCode，在 Terminal 中使用 MinerU 相关命令执行转换即可。
```
## command line example
magic-pdf -p {some_pdf} -o {some_output_dir} -m auto
```

## 帮助
- [MinerU 帮助文档](https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md)