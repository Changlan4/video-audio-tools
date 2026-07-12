import re
import os
import glob
import sys
import argparse

def time_str_to_seconds(time_str):
    """将 SRT 时间字符串转换为总秒数"""
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_str)
    if not match:
        raise ValueError(f"时间格式错误: {time_str}")
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0

def seconds_to_time_str(seconds):
    """将总秒数转换回 SRT 时间字符串格式"""
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_srt(file_path):
    """读取并解析 SRT 文件"""
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    blocks = re.split(r'\n\s*\n', content)
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        time_line = lines[1]
        text = '\n'.join(lines[2:])
        
        try:
            start_str, end_str = time_line.split(' --> ')
            start_sec = time_str_to_seconds(start_str)
            end_sec = time_str_to_seconds(end_str)
            
            subtitles.append({
                'start': start_sec,
                'end': end_sec,
                'text': text
            })
        except Exception as e:
            print(f"  [警告] 跳过无法解析的块: {e}")
            continue
            
    return subtitles

def remove_overlaps(subtitles):
    """删除时间轴重叠的字幕（保留第一条）"""
    kept = []
    for sub in subtitles:
        is_overlapping = False
        for k in kept:
            if sub['start'] < k['end'] and k['start'] < sub['end']:
                is_overlapping = True
                break
        if not is_overlapping:
            kept.append(sub)
    return kept

def process_single_srt(file_path):
    """处理单个 SRT 文件：解析 -> 去重 -> 替换原文件"""
    temp_file = file_path + ".tmp"
    
    try:
        # 1. 读取和解析
        subs = parse_srt(file_path)
        original_count = len(subs)
        
        # 2. 去重叠
        cleaned_subs = remove_overlaps(subs)
        final_count = len(cleaned_subs)
        
        # 如果没有变化，也可以选择跳过写入，这里为了保证序号统一，依然重写
        # if original_count == final_count:
        #     return True, "无需处理"

        # 3. 写入临时文件
        with open(temp_file, 'w', encoding='utf-8') as f:
            for idx, sub in enumerate(cleaned_subs, 1):
                start_str = seconds_to_time_str(sub['start'])
                end_str = seconds_to_time_str(sub['end'])
                f.write(f"{idx}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{sub['text']}\n\n")
        
        # 4. 替换原文件 (先删原文件，再重命名临时文件)
        os.remove(file_path)
        os.rename(temp_file, file_path)
        
        return True, f"成功 ({original_count} -> {final_count} 条)"

    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_file):
            try: os.remove(temp_file)
            except: pass
        return False, str(e)

def batch_process(root_dir):
    """批量处理 root_dir 下所有子文件夹中的 srt 文件"""
    # 查找所有 .srt 文件 (递归搜索)
    search_pattern = os.path.join(root_dir, "**", "*.srt")
    all_srt_files = glob.glob(search_pattern, recursive=True)
    
    if not all_srt_files:
        print("未找到任何 .srt 文件。")
        return

    print(f"找到 {len(all_srt_files)} 个字幕文件，准备开始处理...\n")
    
    success_count = 0
    fail_count = 0
    
    for file_path in all_srt_files:
        # 打印相对路径，保持整洁
        relative_path = os.path.relpath(file_path, root_dir)
        print(f"处理: {relative_path} ... ", end="")
        
        is_ok, msg = process_single_srt(file_path)
        
        if is_ok:
            print(f"✅ {msg}")
            success_count += 1
        else:
            print(f"❌ 失败: {msg}")
            fail_count += 1

    print(f"\n全部处理完成！成功: {success_count}, 失败: {fail_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='字幕去重叠')
    parser.add_argument('--target-dir', required=True, help='目标目录')
    parser.add_argument('--yes', action='store_true', help='跳过确认提示')
    args = parser.parse_args()
    target_directory = args.target_dir
    
    if os.path.exists(target_directory):
        print(f"即将处理目录: {target_directory}")
        print("注意：原文件将被直接修改（覆盖），建议重要文件先备份！")
        
        if not args.yes:
            confirm = input("输入 y 继续，其他键取消: ")
            if confirm.lower() != 'y':
                print("已取消。")
                sys.exit(0)
            
        batch_process(target_directory)
    else:
        print(f"错误：找不到目录 {target_directory}，请检查路径设置。")