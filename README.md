### 本系统是一个基于gpt3.5和gpt4.0设计的虚拟审稿人系统。

主要的文件或文件夹解释：

文件：

`Similarity.py`：是评估本虚拟审稿人结果的准确性，采用的是余弦相似度

`get_paper_.py`：用来获取paper对象，对稿件中的各个章节用罗马数字分开，包含自然语言处理的过程。

`evaluate.py`：评估审稿结果中，真实审稿人的侧重点在哪？该部分的结论用于生成提示词。

文件夹：

`Virtual_review_results`：存放的是虚拟审稿人的结果。

`True_review_results`：存放的是真实审稿人的结果。

`txt_file`：存放的是根据知识库设计的提示词；

`themes`：各种主题

`history`：历史记录