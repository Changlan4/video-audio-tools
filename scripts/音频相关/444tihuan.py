import os
import shutil
import sys
import argparse
from pathlib import Path

# ====================== 请修改下方两个路径 ======================
# 源根目录：所有乱码名xxx2文件夹的上级目录
SOURCE_ROOT = r"C:/path/to/your/TranslatorAI/翻译数据"
# 目标根目录：所有影视名xxx1文件夹的上级目录
TARGET_ROOT = r"C:/path/to/your/asmr/zimu"
# ==================================================================

def batch_replace_duplicate_files(source_root, target_root):
    # 路径转换为Path对象，兼容性更好
    source_root = Path(source_root)
    target_root = Path(target_root)

    # 检查路径是否存在
    if not source_root.exists():
        print(f"❌ 错误：源根目录不存在：{source_root}")
        return
    if not target_root.exists():
        print(f"❌ 错误：目标根目录不存在：{target_root}")
        return

    replace_count = 0
    skip_count = 0
    error_count = 0

    print("=" * 60)
    print(f"🚀 开始批量扫描替换...")
    print(f"   源根目录：{source_root}")
    print(f"   目标根目录：{target_root}")
    print("=" * 60 + "\n")

    # 1. 先遍历目标目录，建立「文件名 -> 完整路径」的映射字典（提高查找效率）
    print("📂 正在预扫描目标目录，建立文件索引...")
    target_file_map = {}
    for root, _, files in os.walk(target_root):
        for file in files:
            # 小写文件名作为key（Windows不区分大小写，避免漏匹配）
            key = file.lower()
            if key not in target_file_map:
                target_file_map[key] = []
            target_file_map[key].append(os.path.join(root, file))
    print(f"✅ 目标目录索引建立完成，共找到 {len(target_file_map)} 个不同文件名\n")

    # 2. 遍历源目录所有文件，进行替换
    print("🔍 开始扫描源文件并执行替换...")
    for root, _, files in os.walk(source_root):
        for file in files:
            source_file = os.path.join(root, file)
            print(f"   正在处理：{file}")

            # 查找目标目录中是否存在同名文件
            key = file.lower()
            if key in target_file_map:
                # 遍历所有匹配的目标文件并替换
                for target_file in target_file_map[key]:
                    try:
                        # copy2保留文件元数据（创建时间、修改时间等）
                        shutil.copy2(source_file, target_file)
                        replace_count += 1
                        print(f"   ✅ 已替换：{target_file}")
                    except PermissionError:
                        error_count += 1
                        print(f"   ⚠️  权限不足，跳过：{target_file}")
                    except Exception as e:
                        error_count += 1
                        print(f"   ⚠️  替换失败：{target_file}，错误：{str(e)}")
            else:
                skip_count += 1
                # 不想看跳过的文件可以注释掉下面这行
                print(f"   ⏭️  目标目录无此文件，跳过：{file}")

    # 3. 输出统计结果
    print("\n" + "=" * 60)
    print("📊 批量替换完成！")
    print(f"   ✅ 成功替换文件数：{replace_count}")
    print(f"   ⏭️  跳过未匹配文件数：{skip_count}")
    print(f"   ⚠️  失败文件数：{error_count}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='音频文件替换')
    parser.add_argument('--source-root', required=True, help='源根目录')
    parser.add_argument('--target-root', required=True, help='目标根目录')
    parser.add_argument('--yes', action='store_true', help='跳过确认提示')
    args = parser.parse_args()
    
    print("⚠️  【重要提醒】文件覆盖不可逆！")
    print("   建议先备份目标根目录，确认无误后再继续！\n")
    if not args.yes:
        confirm = input("输入 y 继续执行，输入其他任意键退出：")
        if confirm.lower() == 'y':
            batch_replace_duplicate_files(args.source_root, args.target_root)
        else:
            print("已取消操作。")
    else:
        batch_replace_duplicate_files(args.source_root, args.target_root)