#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量删除MP4文件名前缀 [1]
遍历指定目录下所有 .mp4 文件，如果文件名以 [1] 开头则删除该前缀并重命名。
可选：重命名前将无 [1] 前缀的原始文件移到备份文件夹。
"""

import os
import sys
import argparse
import shutil


def batch_rename(target_dir, delete_no_prefix=False):
    if not os.path.isdir(target_dir):
        print(f"[错误] 目录不存在: {target_dir}")
        return

    mp4_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.mp4')]
    if not mp4_files:
        print("未找到任何 .mp4 文件。")
        return

    # 步骤1：移动无前缀的原始文件到备份文件夹
    moved_count = 0
    if delete_no_prefix:
        backup_dir = os.path.join(target_dir, ".原始备份")
        os.makedirs(backup_dir, exist_ok=True)
        print(f"--- 移走无前缀原始文件 -> {backup_dir} ---")
        for filename in list(mp4_files):
            if not filename.startswith('[1]'):
                src = os.path.join(target_dir, filename)
                dst = os.path.join(backup_dir, filename)
                try:
                    shutil.move(src, dst)
                    moved_count += 1
                    print(f"[移走] {filename}")
                    mp4_files.remove(filename)
                except Exception as e:
                    print(f"[错误] 移动失败: {filename} - {e}")
        print(f"已移走 {moved_count} 个原始文件\n")

    # 步骤2：重命名有前缀的文件
    print("--- 重命名 ---")
    renamed_count = 0
    skipped_count = 0

    for filename in mp4_files:
        if not filename.startswith('[1]'):
            skipped_count += 1
            continue

        old_path = os.path.join(target_dir, filename)
        new_name = filename[3:]  # 删除前3个字符 "[1]"
        new_path = os.path.join(target_dir, new_name)

        if os.path.exists(new_path):
            print(f"[跳过] {filename} -> {new_name}（目标文件已存在）")
            skipped_count += 1
            continue

        os.rename(old_path, new_path)
        renamed_count += 1
        print(f"[{renamed_count}] {filename} -> {new_name}")

    print(f"\n处理完成！移走: {moved_count}，重命名: {renamed_count}，跳过: {skipped_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量删除MP4文件名前缀 [1]')
    parser.add_argument('--target-dir', required=True, help='目标目录')
    parser.add_argument('--delete-no-prefix', action='store_true', help='重命名前移走无[1]前缀的原始文件')
    args = parser.parse_args()
    batch_rename(args.target_dir, delete_no_prefix=args.delete_no_prefix)
