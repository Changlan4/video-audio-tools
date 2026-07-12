import os
import re
import sys
import argparse

def clean_subtitle_text(text):
    """
    处理字幕文本中的重复内容
    """
    # 1. 处理 "或"、"或者" 引导的重复句子 (例如：没办法嘛 或者：也没辙啊)
    # 匹配模式：前一句 + 或/或者 + 冒号 + 后一句
    text = re.sub(
        r'^(.+?)\s*(?:或|或者)\s*[：:]\s*.+$', 
        r'\1', 
        text, 
        flags=re.MULTILINE
    )

    # 2. 处理斜杠或竖线分隔的同义词 (例如：给我看一眼 / 让我瞅瞅 / 看一下)
    def process_slash(match):
        # 按 / 或 | 分割，去除空白后取第一部分
        parts = re.split(r'\s*[\/|]\s*', match.group(0))
        return parts[0].strip() if parts else match.group(0)
    
    # 只处理包含 / 且看起来不是网址的行
    text = re.sub(r'^.*?[\/|].*?$', process_slash, text, flags=re.MULTILINE)

    # 3. 处理括号内的重复 (例如：我们（大家）)
    # 中文括号 （）
    text = re.sub(r'(.+?)\（.+?\）', r'\1', text)
    # 英文括号 ()
    text = re.sub(r'(.+?)\(.+?\)', r'\1', text)
    text = re.sub(r'[“”]', '', text)

    return text.strip()

def process_single_srt(file_path):
    """
    处理单个SRT文件
    """
    # 读取文件 (尝试 UTF-8，失败则尝试 GBK)
    encoding = 'utf-8'
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        encoding = 'gbk'
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

    # 按SRT标准格式分割块 (空行分隔)
    blocks = re.split(r'\n\s*\n', content.strip())
    processed_blocks = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) < 3:
            # 格式异常的块直接保留
            processed_blocks.append(block)
            continue

        # 分离序号、时间码和文本
        index_line = lines[0]
        timecode_line = lines[1]
        text_lines = lines[2:]
        
        # 合并文本行进行处理，再拆分回来（保持换行）
        original_text = '\n'.join(text_lines)
        cleaned_text = clean_subtitle_text(original_text)

        # 重组块
        new_block = f"{index_line}\n{timecode_line}\n{cleaned_text}"
        processed_blocks.append(new_block)

    # 生成新内容
    new_content = '\n\n'.join(processed_blocks) + '\n\n'

    # 备份原文件
    """ backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        os.rename(file_path, backup_path)
        print(f"[备份] 原文件已保存为: {backup_path}")"""

    # 写入处理后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"[处理完成] {file_path}")

def main(root_folder):
    """
    递归遍历文件夹处理所有SRT
    """
    if not os.path.isdir(root_folder):
        print(f"错误：路径不存在 - {root_folder}")
        return

    count = 0
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith('.srt') and not filename.lower().endswith('.bak'):
                full_path = os.path.join(dirpath, filename)
                try:
                    process_single_srt(full_path)
                    count += 1
                except Exception as e:
                    print(f"[错误] 处理 {full_path} 失败: {e}")

    print(f"\n全部完成！共处理了 {count} 个文件。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='字幕清洗')
    parser.add_argument('--target-dir', required=True, help='目标目录')
    args = parser.parse_args()
    target_directory = args.target_dir
    
    main(target_directory)