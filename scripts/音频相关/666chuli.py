import numpy as np
import soundfile as sf
import sys
import argparse
from pathlib import Path

def load_audio(path):
    """替代 librosa.load: soundfile 加载，返回 (channels, samples) 数组和采样率"""
    data, sr = sf.read(str(path), dtype='float32')
    if data.ndim == 1:
        data = data.reshape(1, -1)
    else:
        data = data.T
    return data, sr

# ================= 配置区域 =================
ROOT_DIR = Path(r"C:/path/to/your/asmr/zimu")
CHUNK_DURATION = 0.3
VOLUME_RATIO_THRESHOLD = 4.0

def get_rms(audio_block):
    return np.sqrt(np.mean(audio_block**2))

def process_audio_pair(file_a: Path, file_b: Path, output_path: Path):
    print(f"├─ 控制音: {file_a.name}")
    print(f"└─ 被控制: {file_b.name}")

    try:
        audio_a, sr = load_audio(file_a)
        audio_b, _ = load_audio(file_b)
    except Exception as e:
        print(f"⚠️  加载失败: {e}\n")
        return

    if audio_a.ndim != 2 or audio_b.ndim != 2:
        print(f"⚠️  非立体声，跳过\n")
        return

    n_samples = min(audio_a.shape[1], audio_b.shape[1])
    a_left, a_right = audio_a[0, :n_samples], audio_a[1, :n_samples]
    b_left, b_right = audio_b[0, :n_samples], audio_b[1, :n_samples]

    out_left = np.zeros_like(b_left)
    out_right = np.zeros_like(b_right)
    hop_length = int(CHUNK_DURATION * sr)
    total_frames = int(np.ceil(n_samples / hop_length))

    for i in range(total_frames):
        start, end = i * hop_length, min((i+1)*hop_length, n_samples)
        al, ar = a_left[start:end], a_right[start:end]
        bl, br = b_left[start:end], b_right[start:end]

        rms_l = max(get_rms(al), 1e-5)
        rms_r = max(get_rms(ar), 1e-5)
        ratio = rms_l / rms_r

        if ratio > VOLUME_RATIO_THRESHOLD:
            out_left[start:end] = 0.0
            out_right[start:end] = br
        elif (1 / ratio) > VOLUME_RATIO_THRESHOLD:
            out_left[start:end] = bl
            out_right[start:end] = 0.0
        else:
            out_left[start:end] = bl
            out_right[start:end] = br

    final_audio = np.vstack([out_left, out_right]).T
    sf.write(str(output_path), final_audio, sr)
    print(f"✅ 处理完成，保存至: {output_path.parent.name}/{output_path.name}\n")

def main(root_dir=None):
    if root_dir is None:
        root_dir = ROOT_DIR
    subfolders = [f for f in root_dir.iterdir() if f.is_dir() and f.name.lower() != "output"]
    if not subfolders:
        print("未找到任何音频文件夹！")
        return

    total_count = 0
    for folder in subfolders:
        print(f"\n===== 正在扫描文件夹: {folder.name} =====")
        mp3_list = sorted(folder.glob("*.mp3")) + sorted(folder.glob("*.MP3"))
        wav_list = sorted(folder.glob("*.wav")) + sorted(folder.glob("*.WAV"))

        print(f"🔍 找到MP3文件: {[f.name for f in mp3_list]}")
        print(f"🔍 找到WAV文件: {[f.name for f in wav_list]}")

        if not mp3_list and not wav_list:
            print(f"⚠️  文件夹无音频文件，跳过\n")
            continue

        output_dir = folder / "output"
        output_dir.mkdir(exist_ok=True)

        wav_dict = {w.stem.strip().lower(): w for w in wav_list}
        for mp3_file in mp3_list:
            mp3_stem = mp3_file.stem.strip().lower()
            if mp3_stem in wav_dict:
                wav_file = wav_dict[mp3_stem]
                output_file = output_dir / f"{mp3_file.stem}_processed.wav"
                process_audio_pair(mp3_file, wav_file, output_file)
                total_count += 1
            else:
                print(f"⚠️  未找到匹配WAV（MP3名：{mp3_file.name} | 匹配键：{mp3_stem}）\n")

    print(f"\n🎉 全部处理完成！总计处理 {total_count} 个音频")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='左右声道音量比处理')
    parser.add_argument('--root-dir', required=True, help='根目录')
    args = parser.parse_args()
    root = Path(args.root_dir)
    main(root_dir=root)
