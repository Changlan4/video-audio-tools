import os
import subprocess
import glob
import shutil
import sys
import argparse
from pathlib import Path

def main(main_folder=None, model_path=None, vad_model_path=None, whisper_cli=None):
    # ================== 配置区域 ==================
    # 主文件夹路径（包含a,b,c等子文件夹）
    if main_folder is None:
        main_folder = r"C:/path/to/your/videos/new"
    
    # Whisper模型文件路径（确保路径正确）
    if model_path is None:
        model_path = r"C:/path/to/whisper/ggml-large-v3-turbo.bin"
    
    # VAD模型文件路径
    if vad_model_path is None:
        vad_model_path = r"C:/path/to/whisper/ggml-silero-v5.1.2.bin"
    
    # Whisper-cli可执行文件路径
    if whisper_cli is None:
        whisper_cli = r"C:/path/to/whisper/whisper-cli.exe"
    
    # 确保路径存在（可选，用于调试）
    assert os.path.exists(model_path), f"模型文件不存在: {model_path}"
    assert os.path.exists(vad_model_path), f"VAD模型文件不存在: {vad_model_path}"
    assert os.path.exists(whisper_cli), f"whisper-cli不存在: {whisper_cli}"
    
    # ================== 处理逻辑 ==================
    print(f"开始处理主文件夹: {main_folder}")
    
    # 遍历所有子文件夹
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)
        
        # 检查是否是文件夹
        if not os.path.isdir(subfolder_path):
            continue
            
        print(f"\n处理子文件夹: {subfolder_path}")
        
        # 查找所有MP4文件
        mp4_files = glob.glob(os.path.join(subfolder_path, "*.mp4"))
        
        if not mp4_files:
            print(f"  - 未找到MP4文件，跳过")
            continue
            
        # 处理每个MP4文件
        for mp4_file in mp4_files:
            filename = os.path.splitext(os.path.basename(mp4_file))[0]
            wav_file = os.path.join(subfolder_path, f"{filename}.wav")
            srt_file = os.path.join(subfolder_path, f"{filename}.srt")
            
            print(f"  - 处理: {filename}.mp4")
            
            # 步骤1: 转换为16kHz WAV
            print(f"    [1/3] 转换为WAV: {wav_file}")
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",  # 覆盖输出文件
                "-i", mp4_file,
                "-ar", "16000",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                wav_file
            ]
            subprocess.run(ffmpeg_cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            
            # 步骤2: 使用whisper-cli转录
            print(f"    [2/3] 生成字幕: {srt_file}")
            whisper_cmd = [
                whisper_cli,
                "-m", model_path,
                "-osrt",
                "-l", "ja",
                wav_file,
                "-of", os.path.join(subfolder_path, filename),
                "--vad",
                "--vad-model", vad_model_path
            ]
            subprocess.run(whisper_cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            
            # 步骤3: 删除WAV文件
            print(f"    [3/3] 删除WAV: {wav_file}")
            os.remove(wav_file)
            
            print(f"  ✓ 处理完成: {filename}.srt")
    
    print("\n所有文件处理完成！")
    print("字幕文件已保存在原始视频所在文件夹中")
    print("WAV文件已自动删除")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='视频转字幕（Whisper）')
    parser.add_argument('--main-folder', required=True, help='主文件夹路径')
    parser.add_argument('--model-path', required=True, help='Whisper模型文件路径')
    parser.add_argument('--vad-model-path', required=True, help='VAD模型文件路径')
    parser.add_argument('--whisper-cli', required=True, help='whisper-cli可执行文件路径')
    args = parser.parse_args()
    main(main_folder=args.main_folder, model_path=args.model_path,
         vad_model_path=args.vad_model_path, whisper_cli=args.whisper_cli)