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
        main_folder = r"C:/path/to/your/asmr/zimu"
    
    # Whisper模型文件路径（确保路径正确）
    if model_path is None:
        model_path = r"C:/path/to/whisper/ggml-large-v3-turbo.bin"
    
    # VAD模型文件路径
    if vad_model_path is None:
        vad_model_path = r"C:/path/to/whisper/ggml-silero-v5.1.2.bin"
    
    # Whisper-cli可执行文件路径
    if whisper_cli is None:
        whisper_cli = r"C:/path/to/whisper/whisper-cli.exe"

    # 支持的视频/音频格式（可根据需要扩展）
    SUPPORTED_FORMATS = [
        # 视频格式
        "mp4", "mkv", "avi", "mov", "flv", "wmv", "webm", "mpeg", "mpg", "m4v","ts",
        # 音频格式
        "mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "ape", "alac"
    ]
    
    # ================== 前置检查 ==================
    # 确保路径存在
    assert os.path.exists(model_path), f"模型文件不存在: {model_path}"
    assert os.path.exists(vad_model_path), f"VAD模型文件不存在: {vad_model_path}"
    assert os.path.exists(whisper_cli), f"whisper-cli不存在: {whisper_cli}"
    
    # ================== 处理逻辑 ==================
    print(f"开始处理主文件夹: {main_folder}")
    print(f"支持的文件格式: {', '.join(SUPPORTED_FORMATS)}")
    
    # 遍历所有子文件夹
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)
        
        # 检查是否是文件夹
        if not os.path.isdir(subfolder_path):
            continue
            
        print(f"\n========== 处理子文件夹: {subfolder_path} ==========")
        
        # 收集所有支持的媒体文件（不区分大小写）
        media_files = []
        for ext in SUPPORTED_FORMATS:
            # 匹配小写扩展名
            media_files.extend(glob.glob(os.path.join(subfolder_path, f"*.{ext.lower()}")))
            # 匹配大写扩展名
            media_files.extend(glob.glob(os.path.join(subfolder_path, f"*.{ext.upper()}")))
        
        # 去重（避免大小写重复匹配）
        media_files = list(set(media_files))
        
        if not media_files:
            print(f"  → 未找到支持的媒体文件，跳过")
            continue
            
        print(f"  → 找到 {len(media_files)} 个待处理文件")
        
        # 处理每个媒体文件
        for media_file in media_files:
            try:
                # 获取文件名（不含扩展名）和扩展名
                file_basename = os.path.basename(media_file)
                filename = os.path.splitext(file_basename)[0]
                file_ext = os.path.splitext(file_basename)[1].lower()
                
                # 定义临时WAV文件和输出SRT文件路径
                wav_file = os.path.join(subfolder_path, f"{filename}_temp.wav")
                srt_file = os.path.join(subfolder_path, f"{filename}.srt")
                
                print(f"\n  处理文件: {file_basename}")
                
                # 步骤1: 转换为16kHz单声道WAV（ffmpeg自动识别输入格式）
                print(f"    [1/3] 转换为WAV格式: {wav_file}")
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",  # 覆盖输出文件
                    "-hide_banner",  # 隐藏ffmpeg启动横幅
                    "-loglevel", "error",  # 只显示错误信息
                    "-i", media_file,
                    "-ar", "16000",  # 16kHz采样率
                    "-ac", "1",     # 单声道
                    "-acodec", "pcm_s16le",  # 16位PCM编码
                    wav_file
                ]
                ffmpeg_result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                
                # 步骤2: 使用whisper-cli转录生成SRT字幕
                print(f"    [2/3] 生成日语字幕: {srt_file}")
                whisper_cmd = [
                    whisper_cli,
                    "-m", model_path,
                    "-osrt",        # 输出SRT格式
                    "-l", "ja",     # 日语识别
                    wav_file,
                    "-of", os.path.join(subfolder_path, filename),  # 输出文件名前缀
                    "--vad",        # 启用VAD静音检测
                    "--vad-model", vad_model_path
                ]
                whisper_result = subprocess.run(whisper_cmd, check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                
                # 步骤3: 删除临时WAV文件
                print(f"    [3/3] 清理临时WAV文件")
                if os.path.exists(wav_file):
                    os.remove(wav_file)
                
                print(f"  ✅ 处理完成: {filename}.srt")
                
            except subprocess.CalledProcessError as e:
                # 单个文件处理失败，记录错误并继续处理下一个
                print(f"  ❌ 处理失败: {file_basename}")
                print(f"    错误信息: {e.stderr if e.stderr else e.stdout}")
                # 清理临时WAV文件
                if os.path.exists(wav_file):
                    os.remove(wav_file)
                continue
            except Exception as e:
                # 其他未知错误
                print(f"  ❌ 处理异常: {file_basename}")
                print(f"    异常信息: {str(e)}")
                if os.path.exists(wav_file):
                    os.remove(wav_file)
                continue
    
    print("\n=====================================")
    print("所有文件夹处理完成！")
    print("字幕文件已保存在原始媒体文件所在文件夹中")
    print("临时WAV文件已自动清理")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='音频转字幕（Whisper）')
    parser.add_argument('--main-folder', required=True, help='主文件夹路径')
    parser.add_argument('--model-path', required=True, help='Whisper模型文件路径')
    parser.add_argument('--vad-model-path', required=True, help='VAD模型文件路径')
    parser.add_argument('--whisper-cli', required=True, help='whisper-cli可执行文件路径')
    args = parser.parse_args()
    main(main_folder=args.main_folder, model_path=args.model_path,
         vad_model_path=args.vad_model_path, whisper_cli=args.whisper_cli)