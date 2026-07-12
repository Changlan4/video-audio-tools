import numpy as np
import soundfile as sf
import subprocess
import tempfile
import sys
import argparse
from pathlib import Path

def load_audio(path):
    """替代 librosa.load: 返回 (channels, samples) 数组和采样率"""
    data, sr = sf.read(str(path), dtype='float32')
    if data.ndim == 1:
        data = data.reshape(1, -1)
    else:
        data = data.T
    return data, sr

ROOT_DIR = Path(r"C:/path/to/your/asmr/zimu")
PROC_VOLUME = 0.6
FFMPEG_PATH = "ffmpeg"

def mix_audio_and_replace(file_mp3: Path, file_processed: Path):
    print(f"正在处理 (将覆盖原文件):")
    print(f"  目标文件: {file_mp3.name}")

    try:
        audio_mp3, sr = load_audio(file_mp3)
        audio_proc, _ = load_audio(file_processed)
    except Exception as e:
        print(f"  [错误] 加载失败: {e}\n")
        return

    n_samples = min(audio_mp3.shape[1], audio_proc.shape[1])
    audio_mp3 = audio_mp3[:, :n_samples]
    audio_proc = audio_proc[:, :n_samples]

    mixed = audio_mp3 + (audio_proc * PROC_VOLUME)
    peak = np.max(np.abs(mixed))
    if peak > 1.0:
        mixed = mixed / peak

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        tmp_path = Path(tmp_wav.name)

    try:
        sf.write(str(tmp_path), mixed.T, sr)
        cmd = [FFMPEG_PATH, "-y", "-i", str(tmp_path), "-codec:a", "libmp3lame", "-q:a", "2", str(file_mp3)]
        subprocess.run(cmd, check=True, capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        print(f"  [完成] 已成功替换原文件: {file_mp3.name}\n")
    except subprocess.CalledProcessError as e:
        print(f"  [错误] FFmpeg 转换失败，请检查 FFmpeg 是否安装正确。")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def main(root_dir=None):
    if root_dir is None:
        root_dir = ROOT_DIR
    print("="*50)
    print("⚠️  警告：此操作将不可逆地覆盖原 MP3 文件！")
    print("="*50)

    subfolders = [f for f in root_dir.iterdir() if f.is_dir() and f.name.lower() != "output"]
    if not subfolders:
        print("未找到子文件夹。")
        return

    total_replaced = 0
    for folder in subfolders:
        print(f"===== 扫描文件夹: {folder.name} =====")
        output_dir = folder / "output"
        if not output_dir.exists():
            continue
        mp3_files = sorted(folder.glob("*.mp3"))
        for mp3_file in mp3_files:
            processed_file = output_dir / f"{mp3_file.stem}_processed.wav"
            if processed_file.exists():
                mix_audio_and_replace(mp3_file, processed_file)
                total_replaced += 1

    print(f"🎉 全部完成！共替换 {total_replaced} 个文件。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='混音覆盖原MP3')
    parser.add_argument('--root-dir', required=True, help='根目录')
    args = parser.parse_args()
    root = Path(args.root_dir)
    main(root_dir=root)
