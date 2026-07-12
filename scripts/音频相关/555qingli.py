import os
import re
import sys
import argparse

def clean_subtitle_text(text):
    """
    处理字幕文本中的重复内容（通用版：覆盖所有符号间隔的重复）
    """
    # 1. 处理 "或"、"或者" 引导的重复句子 (例如：没办法嘛 或者：也没辙啊)
    text = re.sub(
        r'^(.+?)\s*(?:或|或者)\s*[：:]\s*.+$', 
        r'\1', 
        text, 
        flags=re.MULTILINE
    )

    # 2. 处理斜杠或竖线分隔的同义词 (例如：给我看一眼 / 让我瞅瞅 / 看一下)
    def process_slash(match):
        parts = re.split(r'\s*[\/|]\s*', match.group(0))
        return parts[0].strip() if parts else match.group(0)
    text = re.sub(r'^.*?[\/|].*?$', process_slash, text, flags=re.MULTILINE)

    # 3. 处理括号内的重复 (例如：我们（大家）)
    text = re.sub(r'(.+?)\（.+?\）', r'\1', text)
    text = re.sub(r'(.+?)\(.+?\)', r'\1', text)

    # 4. 处理连续重复的单字/叠词 (如“嗯嗯啊啊啊啊...” → “嗯啊”)
    def process_repeated_chars(match):
        repeated_str = match.group(0)
        unique_chars = []
        prev_char = None
        for char in repeated_str:
            if char != prev_char:
                unique_chars.append(char)
                prev_char = char
        return ''.join(unique_chars)
    text = re.sub(r'([^\s，。！？、])\1{2,}(?:[^\s，。！？、])*', process_repeated_chars, text)

    # ========== 通用场景：处理【任意符号间隔】的重复内容（单字/词/短句） ==========
    # 逻辑：匹配“核心内容 + 任意分隔符（1个或多个） + 核心内容 + 任意分隔符 + ...”（重复3次及以上）
    # 分隔符定义：任意非文字字符（包括空格、标点、省略号等）
    # 核心内容：1个及以上文字字符（单字、词、短句）
    
    def process_generic_repeated(match):
        """回调函数：提取重复的核心内容，只保留一个"""
        # 从匹配结果中提取核心内容（第一个分组）
        core_content = match.group(1)
        return core_content.strip()
    
    # 正则说明：
    # (\w+?) : 核心内容（1个及以上文字字符，非贪婪匹配）
    # [\s\W]+ : 任意分隔符（1个及以上，包括空格、标点、符号等）
    # (?:\1[\s\W]+){2,} : 核心内容+分隔符 重复2次及以上（加上前面的1次，总共3次及以上）
    # \1 : 最后再跟一个核心内容（确保以核心内容结尾，避免误杀）
    text = re.sub(
        r'(\w+?)[\s\W]+(?:\1[\s\W]+){2,}\1', 
        process_generic_repeated, 
        text
    )

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

    # 备份原文件（如需启用，取消注释）
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
    parser = argparse.ArgumentParser(description='音频字幕清洗')
    parser.add_argument('--target-dir', required=True, help='目标目录')
    args = parser.parse_args()
    target_directory = args.target_dir
    
    main(target_directory)