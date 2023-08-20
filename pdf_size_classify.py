import argparse
import jsonlines
import os
import shutil
from collections import defaultdict
from datetime import datetime
from loguru import logger
from pathlib import Path
from tqdm import tqdm
from typing import List

class PDFDistributor:
    def __init__(self, file_dir: str) -> None:
        self.file_dir = file_dir

    @property
    def files(self) -> List[Path]:
        pdf_files = []
        for root, _, filenames in os.walk(self.file_dir):
            for filename in filenames:
                if filename.endswith('.pdf'):
                    pdf_files.append(Path(os.path.join(root, filename)))
        return pdf_files

    @staticmethod
    def get_file_size(file: Path) -> int:
        return os.stat(str(file)).st_size
    
    @staticmethod
    def convert_bytes(num: int) -> str:
        for x in ["bytes", "KB", "MB", "GB", "TB", "PB"]:
            if num < 1024:
                return f"{int(num)}{x}"
            num /= 1024

    def get_bucket_name(self, bucket: List[Path]) -> str:
        min_size = self.convert_bytes(self.get_file_size(bucket[-1]))
        max_size = self.convert_bytes(self.get_file_size(bucket[0]))
        return f"{min_size}-{max_size}"

    def distribute_file_by_size(self, num_buckets: int) -> List[List[Path]]:
        file_sizes = sorted([(x, self.get_file_size(x)) for x in self.files], key=lambda item: item[1], reverse=True)
        total_files = len(file_sizes)
        files_per_bucket = total_files // num_buckets

        cur_bucket = 0
        cur_bucket_size = 0
        buckets = defaultdict(list)
        for file_path, _ in file_sizes:
            if cur_bucket_size >= files_per_bucket and cur_bucket < num_buckets - 1:
                cur_bucket += 1
                cur_bucket_size = 0

            buckets[cur_bucket].append(file_path)
            cur_bucket_size += 1
        return [bucket_files for _, bucket_files in buckets.items()]

    def bucket_statistics(self, buckets: List[List[Path]]) -> None:
        logger.info("桶的统计信息：")
        for i, bucket in enumerate(buckets):
            bucket_name = self.get_bucket_name(bucket)
            num_files = len(bucket)
            total_size = sum(self.get_file_size(file) for file in bucket)
            avg_size = self.convert_bytes(total_size / num_files) if num_files > 0 else 0
            logger.info(f"桶 {bucket_name}: 文件数量 = {num_files}, 总大小 = {self.convert_bytes(total_size)}, 平均大小 = {avg_size}")

    def dryrun_file_by_size(self, buckets: List[List[Path]], target_path: str, jsonl_path: str):
        with open(jsonl_path, 'w', encoding='utf-8') as file:
            writer = jsonlines.Writer(file)
            for bucket in buckets:
                count = 0
                subfolder_num = 0
                bucket_name = self.get_bucket_name(bucket)
                target_bucket_path = Path(target_path) / bucket_name 

                for file in bucket:
                    count += 1
                    if count % 10000 == 1:
                        subfolder_num += 1
                        subfolder_name = str(subfolder_num).zfill(4)

                    new_filename = f"{count:04}.pdf"
                    target_pdf_path = target_bucket_path / subfolder_name / new_filename

                    writer.write({'original_path': str(file), 'output_path': str(target_pdf_path)})

        logger.info("干运行完成。")
        logger.info(f"JSON文件保存在: {jsonl_path}")

    def move_files_from_jsonl(self, jsonl_path: str):
        with open(jsonl_path, 'r', encoding='utf-8') as file:
            reader = jsonlines.Reader(file)
            total_items = sum(1 for _ in reader)  # Count the total number of items in the reader
            file.seek(0)  # Reset the file pointer
            for item in tqdm(reader, ncols=100, total=total_items):
                original_path = item['original_path']
                output_path = item['output_path']
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                # Debug的时候用
                # shutil.copy(original_path, output_path)
                shutil.move(original_path, output_path)
        logger.info("移动文件完成")

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_folder", type=str, required=True, help="The source folder containing the PDF files to be classified.")
    parser.add_argument("--num_buckets", type=int, default=10, required=True, help="The numbers of buckets that PDF files will be distribute.")
    parser.add_argument("--target_folder", type=str, required=True, help="The target folder that PDF files will be moved.")
    parser.add_argument("--log_directory", type=str, default='./log', help="The directory where the log files will be saved.")
    parser.add_argument("--jsonl_directory", type=str, default='./mv.jsonl', help="The mv history")
    parser.add_argument("--dryrun", action='store_true', default=False, help="Dry run this tools")
    return parser.parse_args()

def main():
    args = parse_arguments()

    start_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logger.add(f"{args.log_directory}/pdf_classifier_{start_timestamp}.log", rotation="500 MB")
    logger.info(f"PDF size classification started at {start_timestamp}")

    fd = PDFDistributor(args.source_folder)
    buckets = fd.distribute_file_by_size(args.num_buckets)

    # 无论如何都运行 dryrun
    fd.dryrun_file_by_size(buckets, args.target_folder, args.jsonl_directory)
    
    fd.bucket_statistics(buckets)

    # 只有当 args.dryrun 为 False 时才执行移动操作
    if not args.dryrun:
        logger.warning(f"开始移动文件，请勿中断！")
        fd.move_files_from_jsonl(args.jsonl_directory)

    end_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logger.info(f"PDF size using {int(end_timestamp) - int(start_timestamp)} s")
    logger.info(f"PDF size classification completed at {end_timestamp}")

if __name__ == "__main__":
    main()
