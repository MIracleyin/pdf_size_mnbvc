# PDF 大小分类器 

该项目是 MNBVC 计划的一部分，旨在提供一些用于对 PDF 文件进行分类和复制的工具。本分类器希望提供一个命令行工具，可以对大规模 PDF 数据，按照 PDF 文件大小进行分桶。

## 基本使用方法
### default mode
按照文件大小顺序分成指定数量的桶，移动到目标桶路径下
```shell
python pdf_size_classify.py --source_folder PDF文件所在目录  --num_buckets 期望分桶数量 --target_folder PDF目标文件夹
```

## dryrun mode
按照文件大小顺序分成指定数量的桶，生成移动记录，但不移动
```shell
python pdf_size_classify.py --source_folder PDF文件所在目录  --num_buckets 期望分桶数量 --target_folder PDF目标文件夹 --dryrun
```

## MNBVC 计划

本项目是 MNBVC 计划的一部分。更多关于 MNBVC 计划的信息，请访问 [MNBVC GitHub 页面](https://github.com/esbatmop/MNBVC)。

