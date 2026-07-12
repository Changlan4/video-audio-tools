#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频 & 音频工具整合 GUI
========================
将所有视频/音频处理脚本整合到统一界面，支持暗色/浅色主题切换、
每个工具独立目录配置、配置文件持久化、日志实时输出。
"""

import os
import sys
import json
import subprocess
import threading
import queue
import io
import runpy
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

# ── 路径常量 ──
if getattr(sys, 'frozen', False):
    EXE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    EXE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = EXE_DIR

CONFIG_FILE = EXE_DIR / "config.json"
SCRIPTS_DIR = BUNDLE_DIR / "scripts"
VIDEO_SCRIPTS = SCRIPTS_DIR / "视频相关"
AUDIO_SCRIPTS = SCRIPTS_DIR / "音频相关"

PYTHON_EXE = sys.executable
IS_FROZEN = getattr(sys, 'frozen', False)

# ── 工具定义 ──
VIDEO_TOOLS = [
    {"id": "video_0", "name": "0. 查重", "type": "script",
     "script": "111查重.py",
     "params": ["--folders", "{video_0_folders}", "--output", "{video_0_output}"],
     "configs": [
         {"key": "video_0_folders", "label": "扫描文件夹", "type": "folder_list"},
         {"key": "video_0_output", "label": "报告输出文件夹", "type": "dir"},
     ]},
    {"id": "video_1", "name": "1. 提取 MP4 文件名", "type": "builtin",
     "builtin": "extract_mp4",
     "configs": [
         {"key": "video_1_source", "label": "源文件夹", "type": "dir"},
         {"key": "video_1_output", "label": "输出文件夹", "type": "dir"},
     ]},
    {"id": "video_2", "name": "2. 批量重命名删除", "type": "script",
     "script": "2.批量重命名.py",
     "params": ["--target-dir", "{video_2_target}", "{video_2_delete_originals}"],
     "param_conditions": {"video_2_delete_originals": "--delete-no-prefix"},
     "configs": [
         {"key": "video_2_target", "label": "目标文件夹", "type": "dir"},
         {"key": "video_2_delete_originals", "label": "删除无[1]前缀的原始文件", "type": "bool"},
     ]},
    {"id": "video_3", "name": "3. 视频切割", "type": "script",
     "script": "1.切割视频.py",
     "params": ["{video_3_input}", "{video_3_delete_original}"],
     "param_conditions": {"video_3_delete_original": "--delete-original"},
     "configs": [
         {"key": "video_3_input", "label": "输入文件夹", "type": "dir"},
         {"key": "video_3_delete_original", "label": "切割后移走原始文件", "type": "bool"},
     ]},
    {"id": "video_4", "name": "4. 视频转字幕", "type": "script",
     "script": "2.字幕识别.py",
     "params": ["--main-folder", "{video_4_main}", "--model-path", "{video_4_model}",
                "--vad-model-path", "{video_4_vad}", "--whisper-cli", "{video_4_whisper_cli}"],
     "configs": [
         {"key": "video_4_main", "label": "主文件夹", "type": "dir"},
         {"key": "video_4_model", "label": "Whisper 模型 (.bin)", "type": "file"},
         {"key": "video_4_vad", "label": "VAD 模型 (.bin)", "type": "file"},
         {"key": "video_4_whisper_cli", "label": "whisper-cli.exe", "type": "file"},
     ]},
    {"id": "video_5", "name": "5. 字幕去重叠", "type": "script",
     "script": "3.去重叠字幕.py", "params": ["--target-dir", "{video_5_target}", "--yes"],
     "configs": [{"key": "video_5_target", "label": "目标目录", "type": "dir"}]},
    {"id": "video_6", "name": "6. 一键打开软件", "type": "launcher",
     "launcher_keys": ["video_6_lmstudio", "video_6_aitranslator"],
     "configs": [
         {"key": "video_6_lmstudio", "label": "LM Studio.exe", "type": "file"},
         {"key": "video_6_aitranslator", "label": "AITranslator.exe", "type": "file"},
     ]},
    {"id": "video_7", "name": "7. 文件替换", "type": "script",
     "script": "4.替换翻译.py",
     "params": ["--source-root", "{video_7_source}", "--target-root", "{video_7_target}", "--yes"],
     "configs": [
         {"key": "video_7_source", "label": "源目录", "type": "dir"},
         {"key": "video_7_target", "label": "目标目录", "type": "dir"},
     ]},
    {"id": "video_8", "name": "8. 字幕清洗", "type": "script",
     "script": "5.清理重叠翻译.py", "params": ["--target-dir", "{video_8_target}"],
     "configs": [{"key": "video_8_target", "label": "目标目录", "type": "dir"}]},
]

AUDIO_TOOLS = [
    {"id": "audio_0", "name": "0. 音频切割", "type": "script",
     "script": "111qiege.py",
     "params": ["{audio_0_input}", "{audio_0_delete_original}"],
     "param_conditions": {"audio_0_delete_original": "--delete-original"},
     "configs": [
         {"key": "audio_0_input", "label": "输入文件夹", "type": "dir"},
         {"key": "audio_0_delete_original", "label": "切割后移走原始文件", "type": "bool"},
     ]},
    {"id": "audio_1", "name": "1. 音频转字幕", "type": "script",
     "script": "222zimu.py",
     "params": ["--main-folder", "{audio_1_main}", "--model-path", "{audio_1_model}",
                "--vad-model-path", "{audio_1_vad}", "--whisper-cli", "{audio_1_whisper_cli}"],
     "configs": [
         {"key": "audio_1_main", "label": "主文件夹", "type": "dir"},
         {"key": "audio_1_model", "label": "Whisper 模型 (.bin)", "type": "file"},
         {"key": "audio_1_vad", "label": "VAD 模型 (.bin)", "type": "file"},
         {"key": "audio_1_whisper_cli", "label": "whisper-cli.exe", "type": "file"},
     ]},
    {"id": "audio_2", "name": "2. 音频字幕去重叠", "type": "script",
     "script": "333quchong.py", "params": ["--target-dir", "{audio_2_target}", "--yes"],
     "configs": [{"key": "audio_2_target", "label": "目标目录", "type": "dir"}]},
    {"id": "audio_3", "name": "3. 一键打开软件 A", "type": "launcher",
     "launcher_keys": ["audio_3_lmstudio", "audio_3_aitranslator"],
     "configs": [
         {"key": "audio_3_lmstudio", "label": "LM Studio.exe", "type": "file"},
         {"key": "audio_3_aitranslator", "label": "AITranslator.exe", "type": "file"},
     ]},
    {"id": "audio_5", "name": "4. 文件替换", "type": "script",
     "script": "444tihuan.py",
     "params": ["--source-root", "{audio_5_source}", "--target-root", "{audio_5_target}", "--yes"],
     "configs": [
         {"key": "audio_5_source", "label": "源目录", "type": "dir"},
         {"key": "audio_5_target", "label": "目标目录", "type": "dir"},
     ]},
    {"id": "audio_6", "name": "5. 字幕清洗", "type": "script",
     "script": "555qingli.py", "params": ["--target-dir", "{audio_6_target}"],
     "configs": [{"key": "audio_6_target", "label": "目标目录", "type": "dir"}]},
    {"id": "audio_4", "name": "6. 一键打开软件 B", "type": "launcher",
     "launcher_keys": ["audio_4_gptsovits", "audio_4_sp"],
     "configs": [
         {"key": "audio_4_gptsovits", "label": "GPT-sovits 启动api.bat", "type": "file"},
         {"key": "audio_4_sp", "label": "sp.exe", "type": "file"},
     ]},
    {"id": "audio_7", "name": "7. 左右声道处理", "type": "script",
     "script": "666chuli.py", "params": ["--root-dir", "{audio_7_root}"],
     "configs": [{"key": "audio_7_root", "label": "根目录", "type": "dir"}]},
    {"id": "audio_8", "name": "8. 混音覆盖原 MP3", "type": "script",
     "script": "777chonghe.py", "params": ["--root-dir", "{audio_8_root}"],
     "configs": [{"key": "audio_8_root", "label": "根目录", "type": "dir"}]},
    {"id": "audio_9", "name": "9. 按序号拼接 MP3", "type": "script",
     "script": "888pinjie.py", "params": ["--root-dir", "{audio_9_root}"],
     "configs": [{"key": "audio_9_root", "label": "根目录", "type": "dir"}]},
]

ALL_TOOLS = VIDEO_TOOLS + AUDIO_TOOLS

def _collect_all_config_keys():
    keys = set()
    for t in ALL_TOOLS:
        for c in t.get("configs", []):
            keys.add(c["key"])
    return keys

ALL_CONFIG_KEYS = _collect_all_config_keys()
DEFAULT_CONFIG = {"theme": "dark", "paths": {k: "" for k in ALL_CONFIG_KEYS}, "geometry": "1200x750"}


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg.setdefault("paths", {})
            for k in ALL_CONFIG_KEYS:
                cfg["paths"].setdefault(k, "")
            cfg.setdefault("theme", "dark")
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    # 原子写入：先写临时文件，成功后再替换，防止写入中断导致配置文件丢失
    tmp_file = CONFIG_FILE.with_suffix(".tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        tmp_file.replace(CONFIG_FILE)
    except Exception as e:
        print(f"[警告] 保存配置失败: {e}")
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except Exception:
                pass


# ── GUI ──
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self._selected_tool = None
        self._running_tool = None
        self._output_queue = queue.Queue()
        self._config_widgets = {}
        self._folder_rows = {}

        self.title("视频 & 音频工具")
        self.geometry(self.config.get("geometry", "1200x750"))
        self.minsize(900, 600)

        # 设置窗口图标
        icon_path = BUNDLE_DIR / "icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        ctk.set_appearance_mode(self.config.get("theme", "dark"))
        ctk.set_default_color_theme("blue")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        top_bar = ctk.CTkFrame(self, height=36)
        top_bar.pack(fill="x", padx=4, pady=(4, 0))
        ctk.CTkLabel(top_bar, text="视频 & 音频工具", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="切换浅色/暗色", width=120, command=self._toggle_theme).pack(side="right", padx=10, pady=2)

        self._main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4, bg=self._get_pane_bg())
        self._main_pane.pack(fill="both", expand=True, padx=4, pady=4)

        left_outer = ctk.CTkFrame(self._main_pane)
        self._main_pane.add(left_outer, minsize=200, width=280)
        left_frame = ctk.CTkScrollableFrame(left_outer, label_text="")
        ctk.CTkLabel(left_frame, text="━━━ 视频工具 ━━━", font=ctk.CTkFont(weight="bold")).pack(pady=(8, 4))
        self._all_btns = {}
        for tool in VIDEO_TOOLS:
            btn = ctk.CTkButton(left_frame, text=tool["name"], height=32, command=lambda t=tool: self._select_tool(t))
            btn.pack(fill="x", padx=8, pady=2)
            self._all_btns[tool["id"]] = btn
        ctk.CTkLabel(left_frame, text="━━━ 音频工具 ━━━", font=ctk.CTkFont(weight="bold")).pack(pady=(16, 4))
        for tool in AUDIO_TOOLS:
            btn = ctk.CTkButton(left_frame, text=tool["name"], height=32, command=lambda t=tool: self._select_tool(t))
            btn.pack(fill="x", padx=8, pady=2)
            self._all_btns[tool["id"]] = btn
        left_frame.pack(fill="both", expand=True)

        right_pane = tk.PanedWindow(self._main_pane, orient=tk.VERTICAL, sashwidth=4, bg=self._get_pane_bg())
        self._main_pane.add(right_pane, minsize=400, width=760)

        self._config_panel = ctk.CTkFrame(right_pane)
        right_pane.add(self._config_panel, minsize=120, height=250)
        self._config_inner = ctk.CTkScrollableFrame(self._config_panel)
        self._config_inner.pack(fill="both", expand=True)
        ctk.CTkLabel(self._config_inner, text="← 点击左侧工具按钮开始配置", font=ctk.CTkFont(size=14)).pack(pady=20)

        log_frame = ctk.CTkFrame(right_pane)
        right_pane.add(log_frame, minsize=150, height=200)
        log_toolbar = ctk.CTkFrame(log_frame, height=30)
        log_toolbar.pack(fill="x")
        ctk.CTkLabel(log_toolbar, text="运行日志", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8)
        ctk.CTkButton(log_toolbar, text="清空", width=60, height=24, command=self._clear_log).pack(side="right", padx=6, pady=2)
        self._log_text = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self._log_text.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        bottom_bar = ctk.CTkFrame(self, height=30)
        bottom_bar.pack(fill="x", padx=4, pady=(0, 4))
        self._status_label = ctk.CTkLabel(bottom_bar, text="就绪", anchor="w")
        self._status_label.pack(side="left", padx=8)
        self._progress = ctk.CTkProgressBar(bottom_bar, width=200)
        self._progress.pack(side="right", padx=8)
        self._progress.set(0)

    def _select_tool(self, tool):
        if self._running_tool:
            messagebox.showinfo("提示", f"正在运行「{self._running_tool}」，请等待完成。")
            return
        self._selected_tool = tool
        self._save_current_panel_paths()
        for w in self._config_inner.winfo_children():
            w.destroy()
        self._config_widgets = {}
        self._folder_rows = {}
        configs = tool.get("configs", [])
        ctk.CTkLabel(self._config_inner, text=tool["name"], font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(8, 6))
        paths = self.config.get("paths", {})
        for cfg in configs:
            if cfg.get("type") == "folder_list":
                self._build_folder_list(cfg, paths)
            elif cfg.get("type") == "bool":
                row = ctk.CTkFrame(self._config_inner)
                row.pack(fill="x", padx=6, pady=2)
                var = ctk.BooleanVar(value=(paths.get(cfg["key"], "") == "1"))
                ctk.CTkCheckBox(row, text=cfg["label"], variable=var).pack(side="left", padx=8, pady=4)
                self._config_widgets[cfg["key"]] = var
            else:
                row = ctk.CTkFrame(self._config_inner)
                row.pack(fill="x", padx=6, pady=2)
                ctk.CTkLabel(row, text=cfg["label"], width=160, anchor="w").pack(side="left", padx=(4, 2))
                entry = ctk.CTkEntry(row, height=26)
                entry.pack(side="left", fill="x", expand=True, padx=2)
                val = paths.get(cfg["key"], "")
                if val:
                    entry.insert(0, val)
                ctk.CTkButton(row, text="浏览", width=50, height=26,
                              command=lambda e=entry, t=cfg["type"]: self._browse(e, t)).pack(side="right", padx=2)
                self._config_widgets[cfg["key"]] = entry
        run_frame = ctk.CTkFrame(self._config_inner)
        run_frame.pack(fill="x", padx=6, pady=(10, 8))
        ctk.CTkButton(run_frame, text="运行", height=34, width=100, command=lambda: self._run_tool(tool)).pack()

    def _build_folder_list(self, cfg, paths):
        key = cfg["key"]
        saved = paths.get(key, "")
        folders = [d.strip() for d in saved.split(";") if d.strip()] or [""]
        outer = ctk.CTkFrame(self._config_inner)
        outer.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(outer, text=cfg["label"], anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=6, pady=(4, 2))
        rows_container = ctk.CTkFrame(outer)
        rows_container.pack(fill="x")
        self._folder_rows[key] = []
        def _add_row(folder_path=""):
            idx = len(self._folder_rows[key]) + 1
            row = ctk.CTkFrame(rows_container)
            row.pack(fill="x", padx=6, pady=1)
            ctk.CTkLabel(row, text=f"文件夹{idx}:", width=60, anchor="w").pack(side="left", padx=(8, 2))
            entry = ctk.CTkEntry(row, height=26)
            entry.pack(side="left", fill="x", expand=True, padx=2)
            if folder_path:
                entry.insert(0, folder_path)
            ctk.CTkButton(row, text="浏览", width=50, height=26, command=lambda e=entry: self._browse(e, "dir")).pack(side="right", padx=2)
            ctk.CTkButton(row, text="✕", width=30, height=26, command=lambda r=row: self._remove_folder_row(key, r)).pack(side="right", padx=1)
            self._folder_rows[key].append(row)
        for f in folders:
            _add_row(f)
        add_frame = ctk.CTkFrame(outer)
        add_frame.pack(fill="x", padx=6, pady=(4, 4))
        ctk.CTkButton(add_frame, text="+ 添加文件夹", width=120, height=28, command=lambda: _add_row()).pack(side="left", padx=8)

    def _remove_folder_row(self, key, row):
        rows = self._folder_rows.get(key, [])
        if row in rows and len(rows) > 1:
            rows.remove(row)
            row.destroy()
            for i, r in enumerate(rows, 1):
                for child in r.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.configure(text=f"文件夹{i}:")
                        break
            self._save_current_panel_paths()
        elif len(rows) <= 1:
            messagebox.showinfo("提示", "至少保留一个文件夹。")

    def _browse(self, entry, cfg_type):
        if cfg_type == "file":
            path = filedialog.askopenfilename(title="选择文件")
            if path:
                entry.delete(0, "end")
                entry.insert(0, path)
        elif cfg_type == "dirs":
            current = entry.get()
            new_dir = filedialog.askdirectory(title="选择文件夹")
            if new_dir:
                if current:
                    dirs = [d.strip() for d in current.split(";") if d.strip()]
                    if new_dir not in dirs:
                        dirs.append(new_dir)
                    entry.delete(0, "end")
                    entry.insert(0, ";".join(dirs))
                else:
                    entry.insert(0, new_dir)
        else:
            path = filedialog.askdirectory(title="选择文件夹")
            if path:
                entry.delete(0, "end")
                entry.insert(0, path)
        self._save_current_panel_paths()

    def _save_current_panel_paths(self):
        for key, widget in self._config_widgets.items():
            if isinstance(widget, ctk.BooleanVar):
                self.config.setdefault("paths", {})[key] = "1" if widget.get() else ""
            else:
                self.config.setdefault("paths", {})[key] = widget.get().strip()
        for key, rows in self._folder_rows.items():
            vals = []
            for row in rows:
                for child in row.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        v = child.get().strip()
                        if v:
                            vals.append(v)
                        break
            self.config.setdefault("paths", {})[key] = ";".join(vals)
        save_config(self.config)

    def _get_pane_bg(self):
        return "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ebebeb"

    def _toggle_theme(self):
        new = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(new)
        self.config["theme"] = new.lower()
        save_config(self.config)
        bg = self._get_pane_bg()
        try:
            self._main_pane.configure(bg=bg)
            for child in self._main_pane.panes():
                if isinstance(child, tk.PanedWindow):
                    child.configure(bg=bg)
        except Exception:
            pass

    def _log(self, text):
        self._output_queue.put(text)

    def _poll_queue(self):
        while not self._output_queue.empty():
            msg = self._output_queue.get_nowait()
            self._log_text.insert("end", msg)
            self._log_text.see("end")
        self.after(100, self._poll_queue)

    def _clear_log(self):
        self._log_text.delete("1.0", "end")

    def _run_tool(self, tool):
        if self._running_tool:
            messagebox.showinfo("提示", f"正在运行「{self._running_tool}」，请等待完成。")
            return
        self._save_current_panel_paths()
        paths = self.config.get("paths", {})
        for cfg in tool.get("configs", []):
            if cfg.get("type") == "bool":
                continue  # 布尔类型不做非空校验
            val = paths.get(cfg["key"], "").strip()
            if not val:
                messagebox.showwarning("缺少配置", f"请先配置「{cfg['label']}」")
                return
        self._running_tool = tool["name"]
        self._set_all_buttons("disabled")
        self._status_label.configure(text=f"运行中: {tool['name']}")
        self._progress.set(0)
        t = threading.Thread(target=self._execute_tool, args=(tool,), daemon=True)
        t.start()

    def _execute_tool(self, tool):
        try:
            ttype = tool.get("type", "script")
            if ttype == "builtin":
                builtin = tool.get("builtin", "")
                if builtin == "extract_mp4":
                    self._builtin_extract_mp4()
                else:
                    self._log(f"[错误] 未知内置功能: {builtin}\n")
            elif ttype == "launcher":
                self._builtin_launch(tool.get("launcher_keys", []))
            else:
                self._run_script(tool)
        except Exception as e:
            self._log(f"\n[错误] {e}\n")
        finally:
            self.after(0, lambda: self._on_tool_done())

    def _run_script(self, tool):
        script_path = VIDEO_SCRIPTS / tool["script"]
        if not script_path.exists():
            script_path = AUDIO_SCRIPTS / tool["script"]
        if not script_path.exists():
            self._log(f"[错误] 脚本不存在: {tool['script']}\n")
            return
        paths = self.config.get("paths", {})
        param_conditions = tool.get("param_conditions", {})
        argv = [str(script_path)]
        for p in tool["params"]:
            if p.startswith("{") and p.endswith("}"):
                key = p[1:-1]
                val = paths.get(key, "")
                # 条件参数（如 --delete-no-prefix）
                if key in param_conditions:
                    if val == "1":
                        argv.append(param_conditions[key])
                    continue
                # video_0_output：目录→拼接文件名
                if key == "video_0_output" and val:
                    val = os.path.join(val, "duplicates_report.txt")
                if ";" in val:
                    for sub in val.split(";"):
                        sub = sub.strip()
                        if sub:
                            argv.append(sub)
                else:
                    argv.append(val)
            else:
                argv.append(p)
        self._log(f"执行: {script_path.name}\n")
        if IS_FROZEN:
            self._run_script_inprocess(script_path, argv)
        else:
            cmd = [PYTHON_EXE] + argv
            self._log(f"命令: {' '.join(cmd)}\n")
            self._run_subprocess(cmd)

    def _run_script_inprocess(self, script_path, argv):
        old_argv, old_stdout = sys.argv, sys.stdout
        app = self  # 捕获引用

        class _ProgressWriter:
            def __init__(self):
                self._buf = io.StringIO()
            def write(self, s):
                self._buf.write(s)
                # 检查进度标记 "PROGRESS:xx"
                if '\n' in s:
                    for line in s.split('\n'):
                        if line.startswith('PROGRESS:'):
                            try:
                                pct = int(line.split(':')[1])
                                app.after(0, lambda v=pct: app._progress.set(v / 100.0))
                            except Exception:
                                pass
                app._log(s)
            def getvalue(self):
                return self._buf.getvalue()
            def flush(self):
                pass

        pw = _ProgressWriter()
        try:
            sys.argv = argv
            sys.stdout = pw
            runpy.run_path(str(script_path), run_name="__main__")
            self._log("\n--- 完成 ---\n")
        except SystemExit as e:
            code = e.code if e.code is not None else 0
            if code != 0:
                self._log(f"\n--- 错误 (退出码: {code}) ---\n")
            else:
                self._log("\n--- 完成 ---\n")
        except Exception as e:
            self._log(f"\n[异常] {e}\n")
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout

    def _builtin_extract_mp4(self):
        paths = self.config.get("paths", {})
        source = paths.get("video_1_source", "")
        output = paths.get("video_1_output", "")
        mp4_files = [f for f in os.listdir(source) if f.lower().endswith('.mp4')]
        if not mp4_files:
            self._log("未找到任何 .mp4 文件。\n")
            return
        os.makedirs(output, exist_ok=True)
        out_file = os.path.join(output, "mp4文件列表.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            for name in mp4_files:
                f.write(name + "\n")
        self._log(f"已提取 {len(mp4_files)} 个文件名，保存到: {out_file}\n")

    def _builtin_launch(self, keys):
        paths = self.config.get("paths", {})
        for key in keys:
            app_path = paths.get(key, "")
            if not os.path.exists(app_path):
                self._log(f"[错误] 文件不存在: {app_path}\n")
                continue
            try:
                if app_path.lower().endswith('.bat'):
                    subprocess.Popen(app_path, shell=True, cwd=os.path.dirname(app_path),
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                else:
                    os.startfile(app_path)
                self._log(f"已启动: {app_path}\n")
            except Exception as e:
                self._log(f"[错误] 启动失败: {app_path} - {e}\n")

    def _run_subprocess(self, cmd):
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", bufsize=1,
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            for line in proc.stdout:
                self._log(line)
            proc.wait()
            self._log(f"\n--- {'完成' if proc.returncode == 0 else f'错误 (退出码: {proc.returncode})'} ---\n")
        except Exception as e:
            self._log(f"\n[异常] {e}\n")

    def _set_all_buttons(self, state):
        for btn in self._all_btns.values():
            btn.configure(state=state)

    def _on_tool_done(self):
        self._running_tool = None
        self._set_all_buttons("normal")
        self._status_label.configure(text="就绪")
        self._progress.set(0)

    def _on_close(self):
        self.config["geometry"] = self.geometry()
        self._save_current_panel_paths()
        self.destroy()


def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
