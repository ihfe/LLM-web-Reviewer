import random
import matplotlib
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os


# 指定默认字体
matplotlib.rcParams['font.family'] = 'SimHei'  # 或其他支持中文的字体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

def read_txt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def calculate_cosine_similarity(text1, text2):
    vectorizer = CountVectorizer(stop_words='english').fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    return cosine_similarity(vectors)[0, 1]

txt_files_dir1 = "True_review_results"
txt_files1 = os.listdir(txt_files_dir1)

txt_files_dir2 = "Virtual_review_results"
txt_files2 = os.listdir(txt_files_dir2)

results = {}

for i in range(len(txt_files1)):
    file1_path = os.path.join(txt_files_dir1, txt_files1[i])
    file2_path = os.path.join(txt_files_dir2, txt_files2[i])

    text1 = read_txt_file(file1_path)
    text2 = read_txt_file(file2_path)

    similarity = calculate_cosine_similarity(text1, text2)
    key = f"{txt_files1[i]}"
    results[key] = similarity

#保存values
values_list = list(results.values())

# 输出结果
# for key, value in results.items():
#     print(f"{key}: {value}")


# 根据条件进行分类
categories = []
for value in values_list:
    if value >= 0.3 and value <= 1:
        categories.append("较强")
    elif value >= -0.3 and value <= 0.3:
        categories.append("适中")
    elif value >= -1 and value < -0.3:
        categories.append("较弱")

# 可视化展示
plt.figure(figsize=(10, 6))
plt.bar(range(1, 10), values_list, color='skyblue')
plt.xticks(range(1, 10))
plt.xlabel('样本编号')
plt.ylabel('随机数据值')
plt.title('相关性展示')
for i, category in enumerate(categories):
    plt.text(i + 1, values_list[i], category, ha='center', va='bottom')
plt.show()