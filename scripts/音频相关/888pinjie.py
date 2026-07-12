import re
import numpy as np
import soundfile as sf
import subprocess
import tempfile
import sys
import argparse
from pathlib import Path
from collections import defaultdict

def load_audio(path):
    """替代 librosa.load: 返回 (channels, samples) 数组和采样率"""
    data, sr = sf.read(str(path), dtype='float32')
    if data.ndim == 1:
        data = data.reshape(1, -1)
    else:
        data = data.T
    return data, sr

def resample_audio(audio, orig_sr, target_sr):
    """简单重采样 (numpy 线性插值)"""
    ratio = target_sr / orig_sr
    n_orig = audio.shape[-1]
    n_new = int(n_orig * ratio)
    if audio.ndim == 1:
        idx = np.linspace(0, n_orig - 1, n_new)
        return np.interp(idx, np.arange(n_orig), audio)
    else:
        result = np.zeros((audio.shape[0], n_new), dtype=audio.dtype)
        for ch in range(audio.shape[0]):
            idx = np.linspace(0, n_orig - 1, n_new)
            result[ch] = np.interp(idx, np.arange(n_orig), audio[ch])
        return result

ROOT_DIR = Path(r"C:/path/to/your/asmr/zimu")
FFMPEG_PATH = "ffmpeg"

def natural_sort_key(filepath):
    filename = filepath.name
    parts = re.split(r'(\d+)', filename)
    return [int(part) if part.isdigit() else part.lower() for part in parts]

def extract_prefix(filename):
    name = Path(filename).stem
    result = re.sub(r'[_-]?\d+$', '', name)
    return result if result else name

def concatenate_audio(file_list, output_path):
    if not file_list:
        return

    print(f"  正在按顺序拼接:")
    for f in file_list:
        print(f"    -> {f.name}")

    segments = []
    sr = None

    for f in file_list:
        try:
            audio, current_sr = load_audio(f)
            if sr is None:
                sr = current_sr
            elif current_sr != sr:
                audio = resample_audio(audio, current_sr, sr)
            segments.append(audio)
        except Exception as e:
            print(f"    [警告] 跳过 {f.name}: {e}")

    if not segments:
        print("  [错误] 没有可拼接的音频\n")
        return

    final_audio = np.concatenate(segments, axis=1)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        tmp_path = Path(tmp_wav.name)

    try:
        sf.write(str(tmp_path), final_audio.T, sr)
        cmd = [FFMPEG_PATH, "-y", "-i", str(tmp_path), "-codec:a", "libmp3lame", "-q:a", "2", str(output_path)]
        subprocess.run(cmd, check=True, capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        print(f"  [完成] 已保存: {output_path.name}\n")
    except Exception as e:
        print(f"  [错误] 保存失败: {e}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def main(root_dir=None):
    if root_dir is None:
        root_dir = ROOT_DIR
    print("===== 开始按序号顺序拼接音频 =====\n")

    subfolders = [f for f in root_dir.iterdir() if f.is_dir() and f.name.lower() != "output"]
    if not subfolders:
        print("未找到子文件夹。")
        return

    for folder in subfolders:
        print(f"处理文件夹: {folder.name}")
        mp3_files = list(folder.glob("*.mp3"))
        if not mp3_files:
            print(f"  未找到 mp3，跳过\n")
            continue

        mp3_files.sort(key=natural_sort_key)
        groups = defaultdict(list)
        for f in mp3_files:
            prefix = extract_prefix(f.name)
            groups[prefix].append(f)

        for prefix, files in groups.items():
            output_file = root_dir / f"{prefix}.mp3"
            print(f"\n目标: {output_file.name}")
            concatenate_audio(files, output_file)

    print("🎉 全部结束！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='按序号拼接MP3')
    parser.add_argument('--root-dir', required=True, help='根目录')
    args = parser.parse_args()
    root = Path(args.root_dir)
    main(root_dir=root)
