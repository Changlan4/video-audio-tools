#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨文件夹重复文件检测工具（按文件名匹配）
==========================================
递归扫描多个文件夹，按文件名找出重复文件，结果输出为 TXT 报告。
"""

import os
import sys
import argparse
from collections import defaultdict

# ============================================================
# 要检查的文件夹
# ============================================================
FOLDERS = [
    r"C:/path/to/your/movies"
    r"C:/path/to/your/movies/new"
    r"F:/path/to/your/srt",
]

# 报告输出路径
OUTPUT = r"C:/path/to/your/duplicates_report.txt"


def normalize_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def format_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def collect_files(folders):
    """递归收集所有文件，路径去重。"""
    seen = set()
    files = []

    for folder in folders:
        norm = normalize_path(folder)
        if not os.path.exists(norm):
            print(f"[警告] 文件夹不存在，已跳过: {norm}")
            continue
        if not os.path.isdir(norm):
            print(f"[警告] 路径不是文件夹，已跳过: {norm}")
            continue

        count = 0
        for root, dirs, filenames in os.walk(norm):
            for fname in filenames:
                full = normalize_path(os.path.join(root, fname))
                if full not in seen:
                    seen.add(full)
                    files.append(full)
                    count += 1
        print(f"[扫描] {norm}  →  {count} 个文件")

    return files


def find_duplicates_by_name(file_list):
    """按文件名分组，找出出现多次的文件名。"""
    name_map = defaultdict(list)
    for fp in file_list:
        name_map[os.path.basename(fp)].append(fp)

    # 只保留重复的
    return {name: paths for name, paths in name_map.items() if len(paths) > 1}


def generate_report(duplicates, total_files):
    """生成 TXT 报告内容。"""
    lines = []
    lines.append("=" * 70)
    lines.append("           重 复 文 件 报 告（按文件名匹配）")
    lines.append("=" * 70)
    lines.append(f"  扫描文件总数    : {total_files}")
    lines.append(f"  重复文件名组数  : {len(duplicates)}")
    dup_file_count = sum(len(v) for v in duplicates.values())
    lines.append(f"  涉及重复文件数  : {dup_file_count}")
    lines.append("=" * 70)

    if not duplicates:
        lines.append("")
        lines.append("  ✓ 未发现重复文件。")
        return "\n".join(lines)

    # 统计
    same_count = 0
    diff_count = 0
    for paths in duplicates.values():
        sizes = set()
        for p in paths:
            try:
                sizes.add(os.path.getsize(p))
            except OSError:
                pass
        if len(sizes) <= 1:
            same_count += 1
        else:
            diff_count += 1

    idx = 0
    for name in sorted(duplicates.keys()):
        paths = duplicates[name]
        idx += 1

        # 获取大小
        sizes = []
        for p in paths:
            try:
                sizes.append(os.path.getsize(p))
            except OSError:
                sizes.append(-1)
        all_same_size = len(set(sizes)) == 1

        status = "大小一致 ✓" if all_same_size else "大小不同 ✗"
        lines.append("")
        lines.append(f"┌─ [{idx}] {name}")
        lines.append(f"├─ 状态: {status}  |  {len(paths)} 份")

        for i, (p, sz) in enumerate(zip(paths, sizes)):
            size_str = format_size(sz) if sz >= 0 else "N/A"
            marker = "├" if i < len(paths) - 1 else "└"
            lines.append(f"{marker}── [{size_str}]  {p}")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  汇总")
    lines.append(f"    大小一致（高概率重复）: {same_count} 组")
    lines.append(f"    大小不同（可能非重复）: {diff_count} 组")
    lines.append("=" * 70)

    return "\n".join(lines)


def main(folders=None, output=None):
    if folders is None:
        folders = FOLDERS
    if output is None:
        output = OUTPUT
    print("要检查的文件夹：")
    for f in folders:
        print(f"  {f}")

    # 收集文件
    all_files = collect_files(folders)
    print(f"\n共收集到 {len(all_files)} 个唯一文件。")

    if len(all_files) < 2:
        print("文件数量不足，无法比较。")
        with open(output, "w", encoding="utf-8") as f:
            f.write("文件数量不足，无法比较。\n")
        sys.exit(0)

    # 按文件名查找重复
    duplicates = find_duplicates_by_name(all_files)
    print(f"发现 {len(duplicates)} 组重复文件名。")

    # 生成并写入报告
    report = generate_report(duplicates, len(all_files))
    with open(output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已保存到: {output}")
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='跨文件夹重复文件检测')
    parser.add_argument('--folders', nargs='+', required=True, help='要检查的文件夹列表')
    parser.add_argument('--output', required=True, help='报告输出路径')
    args = parser.parse_args()
    main(folders=args.folders, output=args.output)
