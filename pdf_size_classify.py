'''
Author: Miracleyin miracleyin@live.com
Date: 2023-08-18 20:21:49
LastEditTime: 2023-08-18 21:44:20
'''
import argparse
from collections import defaultdict
from datetime import datetime
from loguru import logger
import json
from pathlib import Path
from os import stat
from operator import itemgetter
from typing import List
from tqdm import tqdm
import jsonlines

class PDFDistributor:
    def __init__(self, file_dir: str, file_format="*") -> None:
        self.file_dir = file_dir
        self._file_format = file_format 

    @property
    def files(self) -> List[Path]:
        files = Path(self.file_dir).glob(f'*.{self._file_format}') # 保证只抓 pdf
        return [x for x in files if x.is_file()]

    @property
    def file_sizes(self):
        return [(x, self.get_file_size(file=x, byte_prefix=False)) for x in self.files]

    @staticmethod
    def get_file_size(file: str, byte_prefix=True):
        def convert_bytes(num: float) -> str:
            for x in ["bytes", "KB", "MB", "GB", "TB", "PB"]:
                if num < 1024.0:
                    return "%d%s" % (num, x)
                num /= 1024.0
        
        file_info = stat(file)
        return convert_bytes(file_info.st_size) if byte_prefix else file_info.st_size
    
    def distribute_file_by_size(self, num_buckets: int) -> List[List[Path]]:

        total_files = len(self.file_sizes)
        files_per_bucket = total_files // num_buckets

        cur_bucket = 0
        cur_bucket_size = 0
        buckets = defaultdict(list)
        for item in sorted(self.file_sizes, key=itemgetter(1), reverse=True):
            file_path, _ = item
            if cur_bucket_size >= files_per_bucket and cur_bucket < num_buckets - 1:
                cur_bucket += 1 
                cur_bucket_size = 0 # full bucket reset to 0

            buckets[cur_bucket].append(file_path)
            cur_bucket_size += 1 # put a pdf into bucket
        return [bucket_files for _, bucket_files in buckets.items()] 
    
    def copy_file_by_size(self, buckets: List[List[Path]], target_path: str, jsonl_path: str):
        target_path = Path(target_path)
        target_path.mkdir(exist_ok=True)
        with open(jsonl_path, 'w', encoding='utf-8') as file:
            writer = jsonlines.Writer(file)
            for bucket in tqdm(buckets):
                min_size, max_size = self.get_file_size(bucket[-1]), self.get_file_size(bucket[0]) # for set bucket propetry 
                target_bucket_path = target_path / f"{min_size}-{max_size}"
                target_bucket_path.mkdir(exist_ok=True)
                for file in bucket:
                    target_pdf_path = target_bucket_path / file.name
                    with target_pdf_path.open(mode='xb') as fid: 
                        fid.write(file.read_bytes())
                    writer.write({'original_path': str(file), 'output_path': str(target_pdf_path)})
                    

    def dryrun_file_by_size(self, buckets: List[List[Path]], target_path: str, jsonl_path: str) -> None:
        target_path = Path(target_path)
        with open(jsonl_path, 'w', encoding='utf-8') as file:
            writer = jsonlines.Writer(file) 
            for bucket in buckets:
                min_size, max_size = self.get_file_size(bucket[-1]), self.get_file_size(bucket[0]) # for set bucket propetry
                target_bucket_path = target_path / f"{min_size}-{max_size}" 
                for file in bucket:
                    target_pdf_path = target_bucket_path / file.name 
                    writer.write({'original_path': str(file), 'output_path': str(target_pdf_path)})
    

def parse_arguments():
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source_folder",
        type=str,
        required=True,
        help="The source folder containing the PDF files to be classified.",
    )   
    parser.add_argument(
        "--num_buckets",
        type=int,
        default=10,
        required=True,
        help="The numbers of buckets that PDF files will be distribute."
    )
    parser.add_argument(
        "--target_folder",
        type=str,
        required=True,
        help="The target folder that PDF files will be moved."
    )
    parser.add_argument(
        "--log_directory",
        type=str,
        default='./log',
        help="The directory where the log files will be saved.",
    )
    parser.add_argument(
        "--jsonl_directory",
        type=str,
        default='./mv.jsonl',
        help="The mv history",
    )
    parser.add_argument(
        "--dryrun",
        action='store_true',
        default=False,
        help="Dry run this tools"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    # 获取时间戳 配置logger
    start_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logger.add(f"{args.log_directory}/pdf_classifier_{start_timestamp}.log", rotation="500 MB") 
    logger.info(f"PDF size classification started at {start_timestamp}")


    fd = PDFDistributor(args.source_folder, 'pdf')
    fd_dis = fd.distribute_file_by_size(args.num_buckets)
    if args.dryrun:
        logger.info(f"dry run mode") 
        fd.dryrun_file_by_size(fd_dis, args.target_folder, args.jsonl_directory)
    else:
        fd.copy_file_by_size(fd_dis, args.target_folder, args.jsonl_directory)

    end_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logger.info(f"PDF size using {int(end_timestamp) - int(start_timestamp)} s")
    logger.info(f"PDF size classification completed at {end_timestamp}")

if __name__ == "__main__":
    main()