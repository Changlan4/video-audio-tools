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
    # 确保输入文件夹存在
    if not os.path.exists(input_folder):
        print(f"错误: 文件夹 '{input_folder}' 不存在")
        return
    
    # 支持的音视频文件扩展名（包含常见视频+音频格式）
    media_extensions = [
        # 视频格式
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpg', '.mpeg', '.m4v', '.webm', '.ts',
        # 音频格式
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.ape', '.acc', '.opus'
    ]
    
    # 获取所有音视频文件
    media_files = []
    for ext in media_extensions:
        media_files.extend([f for f in os.listdir(input_folder) if f.lower().endswith(ext)])
    
    if not media_files:
        print(f"错误: 在 '{input_folder}' 中未找到任何音视频文件")
        return

    if delete_original:
        backup_dir = os.path.join(input_folder, ".原始备份")
        os.makedirs(backup_dir, exist_ok=True)
    
    # 处理每个音视频文件
    total = len(media_files)
    for i, media_file in enumerate(media_files, 1):
        pct = int(i / total * 100)
        print(f"PROGRESS:{pct}")
        print(f"[{i}/{total}] 正在处理: {media_file}")
        media_path = os.path.join(input_folder, media_file)
        filename = os.path.splitext(media_file)[0]
        folder_name = create_safe_folder_name(filename)
        
        # 创建同名文件夹
        output_folder = os.path.join(input_folder, folder_name)
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"正在处理: {media_file} -> {folder_name} (转为MP3并按10分钟分割)")
        
        # 获取媒体文件时长（音频/视频通用）
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', media_path]
        try:
            duration = float(subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0).decode().strip())
        except Exception as e:
            print(f"错误获取 {media_file} 时长: {e}")
            continue
        
        # 计算需要切割的段数（10分钟/段，可自行调整segment_time值）
        segment_time = 600  # 单位：秒（600秒=10分钟）
        num_segments = int(duration // segment_time) + 1
        
        # 生成FFmpeg命令：切割并统一转为MP3格式
        # 关键参数说明：
        # -vn: 禁用视频流（只保留音频，处理视频文件时自动剥离视频）
        # -c:a libmp3lame: 使用MP3编码（需要ffmpeg内置该编码器）
        # -q:a 2: 音质参数（0-9，0=最高质，2=接近无损，默认5）
        # -f segment: 按时间分段
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', media_path,          # 输入文件
            '-vn',                     # 忽略视频流（仅保留音频）
            '-c:a', 'libmp3lame',      # 指定MP3编码器
            '-q:a', '2',               # 音质等级（推荐2，平衡音质和体积）
            '-f', 'segment',           # 分段模式
            '-segment_time', str(segment_time),  # 分段时长
            '-reset_timestamps', '1',  # 重置每个分段的时间戳为0
            '-avoid_negative_ts', 'make_zero',  # 修复时间戳异常问题
            os.path.join(output_folder, f"{folder_name}_%03d.mp3")  # 输出MP3文件（固定后缀）
        ]
        
        # 执行FFmpeg命令
        try:
            # 隐藏ffmpeg的输出（如需调试可注释stdout/stderr参数）
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            print(f"✅ 成功处理 {media_file} -> {folder_name} 文件夹（MP3格式）")
            if delete_original:
                dst = os.path.join(backup_dir, media_file)
                shutil.move(media_path, dst)
                print(f"[移走] {media_file} -> .原始备份/")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg处理 {media_file} 失败: {e}")
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量切割音视频文件并转为MP3格式（按10分钟/段分割）')
    parser.add_argument('input_folder', type=str, help='要处理的音视频文件夹路径')
    parser.add_argument('--delete-original', action='store_true', help='切割后移走原始文件')
    args = parser.parse_args()
    
    main(args.input_folder, delete_original=args.delete_original)