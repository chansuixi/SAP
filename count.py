import os

def count_files(directory):
    file_count = 0
    for root, dirs, files in os.walk(directory):
        file_count += len(files)
    return file_count

# 用法示例
folder_path = "/Users/yangkaixuan/Downloads/SmartGift-main/trcode_with_input"
result = count_files(folder_path)

print(f"The folder {folder_path} contains {result} files.")