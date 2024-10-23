import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'SimHei'  # 或其他支持中文的字体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# 定义文件路径
file_path = 'txt_file\REVIEW.txt'

# 定义要统计的词汇，合并大小写
words_to_count = ['novelty','methods','methodology','originality','significance']

# 初始化计数器
counts = {word: 0 for word in words_to_count}

# 读取文件并统计词汇出现次数，合并大小写
with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        # 将行转换为小写以统计不区分大小写的词汇
        line_lower = line.lower()
        for word in words_to_count:
            counts[word] += line_lower.count(word)

# 打印统计结果
for word, count in counts.items():
    print(f"'{word}' 出现了 {count} 次")

# 可视化结果
plt.bar(counts.keys(), counts.values(), color=['blue','black','green','yellow','red'])
plt.xlabel('词汇')
plt.ylabel('出现次数')
plt.title('特定词汇出现次数统计')
plt.show()