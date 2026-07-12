import os
import subprocess
import re
import sys
import argparse
import shutil

def create_safe_folder_name(name):
    """创建安全的文件夹名，保留字母、数字、中文字符、下划线和空格"""
    return re.sub(r'[^\w\s\u4e00-\u9fff]', '', name)

def main(input_folder, delete_original=False):
    if not os.path.exists(input_folder):
        print(f"错误: 文件夹 '{input_folder}' 不存在")
        return
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpg', '.mpeg']
    
    video_files = []
    for ext in video_extensions:
        video_files.extend([f for f in os.listdir(input_folder) if f.lower().endswith(ext)])
    
    if not video_files:
        print(f"错误: 在 '{input_folder}' 中未找到任何视频文件")
        return
    
    if delete_original:
        backup_dir = os.path.join(input_folder, ".原始备份")
        os.makedirs(backup_dir, exist_ok=True)
    
    total = len(video_files)
    for i, video_file in enumerate(video_files, 1):
        pct = int(i / total * 100)
        print(f"PROGRESS:{pct}")
        print(f"[{i}/{total}] 正在处理: {video_file}")
        video_path = os.path.join(input_folder, video_file)
        filename = os.path.splitext(video_file)[0]
        folder_name = create_safe_folder_name(filename)
        
        output_folder = os.path.join(input_folder, folder_name)
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"正在处理: {video_file} -> {folder_name}")
        
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        try:
            duration = float(subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0).decode().strip())
        except Exception as e:
            print(f"错误获取视频时长: {e}")
            continue
        
        segment_time = 600
        num_segments = int(duration // segment_time) + 1
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,
            '-c', 'copy',
            '-f', 'segment',
            '-segment_time', str(segment_time),
            '-reset_timestamps', '1',
            os.path.join(output_folder, f"{folder_name}_%03d.mp4")
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            print(f"成功切割 {video_file} 到 {folder_name} 文件夹")
            # 切割成功后移走原文件
            if delete_original:
                dst = os.path.join(backup_dir, video_file)
                shutil.move(video_path, dst)
                print(f"[移走] {video_file} -> .原始备份/")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg处理失败: {e}")
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量切割视频文件')
    parser.add_argument('input_folder', type=str, help='要处理的视频文件夹路径')
    parser.add_argument('--delete-original', action='store_true', help='切割后移走原始文件')
    args = parser.parse_args()
    
    main(args.input_folder, delete_original=args.delete_original)
