# PDF 分类器 

该项目是 MNBVC 计划的一部分，旨在提供一些用于对 PDF 文件进行分类和复制的工具。本分类器希望提供一个命令行工具，可以对大规模 PDF 数据，按照 PDF 文件大小进行分桶。
## 使用方法

### PDF 复制和重命名


### PDF 分类


#### 分类结果说明

  


#### 分类结果说明
  


### 复制分类结果

在完成分类并得到多个 JSONL 文件后，可以运行 `copy_files.py` 脚本将某个 JSONL 文件中的 PDF 文件复制到指定目录。

```shell
python copy_files.py --src_path '/Users/tanlu/Documents/PDF_classifier/pdf_CN_EN_filter_mnbvc/pdf_classification.jsonl' --tgt_folder 'CN_PDF'
```

以上命令将复制指定 JSONL 文件中的 PDF 文件到 `CN_PDF` 目录中。

## 功能特点


## MNBVC 计划

本项目是 MNBVC 计划的一部分。更多关于 MNBVC 计划的信息，请访问 [MNBVC GitHub 页面](https://github.com/esbatmop/MNBVC)。

