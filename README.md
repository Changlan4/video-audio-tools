# 视频 & 音频工具 GUI

将视频处理和音频处理脚本整合到一个统一的 Windows GUI 程序中，支持暗色/浅色主题切换、每个工具独立目录配置、配置自动保存、日志实时输出。

## 功能

### 视频工具

| 序号 | 功能 | 说明 |
|------|------|------|
| 0 | 查重 | 跨文件夹按文件名检测重复文件 |
| 1 | 提取 MP4 文件名 | 扫描目录提取所有 .mp4 文件名保存为 txt |
| 2 | 批量重命名删除 | 删除文件名 `[1]` 前缀，可选清理原始文件 |
| 3 | 视频切割 | 使用 ffmpeg 按 10 分钟分段切割 |
| 4 | 视频转字幕 | 使用 whisper.cpp 生成字幕 |
| 5 | 字幕去重叠 | 删除时间轴重叠的字幕条目 |
| 6 | 一键打开软件 | 同时启动 LM Studio + AITranslator |
| 7 | 文件替换 | 源目录文件替换目标目录同名文件 |
| 8 | 字幕清洗 | 清理字幕中的重复/同义词内容 |

### 音频工具

| 序号 | 功能 | 说明 |
|------|------|------|
| 0 | 音频切割 | 切割并转为 MP3 格式 |
| 1 | 音频转字幕 | 使用 whisper.cpp 生成字幕 |
| 2 | 音频字幕去重叠 | 删除时间轴重叠的字幕条目 |
| 3 | 一键打开软件 A | LM Studio + AITranslator |
| 4 | 文件替换 | 源目录文件替换目标目录 |
| 5 | 字幕清洗 | 清理字幕重复内容 |
| 6 | 一键打开软件 B | GPT-sovits + sp.exe |
| 7 | 左右声道处理 | 基于音量比的音频处理 |
| 8 | 混音覆盖原 MP3 | 混音并替换原文件 |
| 9 | 按序号拼接 MP3 | 按文件名序号拼接音频 |

## 运行

### 方式一：直接运行 exe

下载 Release/video-audio-tools.exe，双击运行。首次使用需在右侧面板配置各工具的工作目录。

### 方式二：Python 运行

```bash
pip install customtkinter soundfile numpy
python main.py
```

## 打包

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon="icon.ico" --add-data "scripts;scripts" --add-data "icon.ico;." --hidden-import soundfile --name "视频音频工具" main.py
```

## 目录结构

```
toolsgui/
├── main.py                 # GUI 主程序
├── icon.ico                # 程序图标
├── build.bat               # 一键打包脚本
├── scripts/
│   ├── 视频相关/            # 视频处理脚本
│   └── 音频相关/            # 音频处理脚本
└── dist/
    └── 视频音频工具.exe     # 打包后的可执行文件
```

## 依赖

- Python 3.10+
- customtkinter
- numpy
- soundfile
- ffmpeg / ffprobe（需在 PATH 中）
- whisper.cpp（视频/音频转字幕功能需要）

## 相关项目

本项目工作流中使用的配套工具：

- [LM Studio](https://lmstudio.ai/) — 在本地和私密环境下运行人工智能模型
- [AITranslator](https://github.com/jxq1997216/AITranslator) — 使用大语言模型来翻译文件的图形化UI软件
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) — 功能强大的少样本语音转换和文本转语音
- [pyvideotrans](https://github.com/jianchang512/pyvideotrans) — 一款功能强大的开源视频翻译/音频转录/AI 配音/字幕翻译工具
- [FFmpeg](https://ffmpeg.org/) — 一个完整的跨平台解决方案，用于录制、转换和流式传输音频和视频
- [whisper.cpp]([https://ffmpeg.org/](https://github.com/ggml-org/whisper.cpp)) — OpenAI 的 Whisper 模型在 C/C++语言中的实现

## 许可

MIT
