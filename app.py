from openai import OpenAI
from get_paper_ import Paper
import jieba
from io import BytesIO
import time
import openai, tenacity
import tiktoken
import PyPDF2
import gradio as gr
from toolbox import get_conf
from themes.theme import load_dynamic_theme,js_code_for_css_changing
AVAIL_THEMES, THEME=get_conf('AVAIL_THEMES', 'THEME')

import os
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"

# 指定历史记录文件的目录
history_dir = 'history'

# 获取目录中的所有文件名
def get_files_list():
    # 只列出 .txt 文件
    files = [f for f in os.listdir(history_dir) if f.endswith('.txt')]
    return files


# 读取指定文件的内容
# 读取指定文件的内容
def load_file_content(file_name):
    file_path = os.path.join(history_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content, file_path


# 下载指定文件
def download_file(file_name):
    file_path = os.path.join(history_dir, file_name)
    return file_path


def contains_chinese(text):
    for ch in text:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

#文本 text 按照换行符 \n 分割成多行文本，并存储在 lines 列表中
def insert_sentence(text, sentence, interval):
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        if contains_chinese(line):
            words = list(jieba.cut(line))
            separator = ''
        else:
            words = line.split()
            separator = ' '

        new_words = []
        count = 0

        for word in words:
            new_words.append(word)
            count += 1

            if count % interval == 0:
                new_words.append(sentence)

        new_lines.append(separator.join(new_words))

    return '\n'.join(new_lines)


with open('txt_file/result_zh.txt', 'r', encoding='UTF-8') as file:  # 读取特定的审稿格式
    result = file.read()

with open('txt_file/computer_eng.txt', 'r', encoding='UTF-8') as file:  # 读取特定的审稿格式
    computer = file.read()

with open('txt_file/Instract.txt', 'r', encoding='UTF-8') as file:  # 读取特定的审稿格式
    logic = file.read()
# prompt_computer = (
#     f"-You are a professional reviewer in the computer science and Artificial intelligence realm. "
#     f"-You need follow the prompt:{computer} when you are reviewing the dissertation. "
# )

prompt_computer = (
    f"-You are a professional reviewer in the computer science and Artificial intelligence realm. "
    f"-You need follow the prompt:{computer} when you are reviewing the dissertation. "
    f"-Please NOTE: Finally,you should give the author your review result,please refer to {result}.This is very important"
)

# openai.api_key = 'sk-1SWMJzlmDYazLQQzF1B7BfBbB83245FaBdA706E5752e5623'  # openai api, api2d api
# openai.api_base ='https://api.lqqq.ltd/v1'  # api地址
# models = ['gpt-3.5-turbo', 'gpt-4']
api_key = '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'  # openai api, api2d api
client = OpenAI(api_key=api_key)
models = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k','gpt-4']


# 定义Reviewer类
class Reviewer:
    # 初始化方法，设置属性
    def __init__(self, model, review_prompt, paper_pdf, language):
        self.model = model
        if review_prompt == '工科类':
            self.review_prompt = prompt_computer
        self.language = language
        self.paper_pdf = paper_pdf
        self.max_token_num = 12000
        self.encoding = tiktoken.get_encoding("gpt2")

    def review_by_chatgpt(self, paper_list):
        htmls = []
        for paper_index, paper in enumerate(paper_list):
            sections_of_interest = self.stage_1(paper)
            # extract the essential parts of the paper
            text = ''
            text += '[Title]:' + paper.title + '. '
            text += '[Abstract]: ' + paper.section_texts['Abstract']
            intro_title = next((item for item in paper.section_names if 'introduction' in item.lower()), None)
            if intro_title is not None:
                text += '[Introduction]: ' + paper.section_texts[intro_title]
            # Similar for conclusion section
            conclusion_title = next((item for item in paper.section_names if 'conclusion' in item), None)
            if conclusion_title is not None:
                text += '[Conclusion]: ' + paper.section_texts[conclusion_title]
            for heading in sections_of_interest:
                if heading in paper.section_names:
                    text += heading + ': ' + paper.section_texts[heading]
            chat_review_text,usage = self.chat_review(text=text)
        #     review_result, review_usage = self.chat_review(text=text)
        #     messages = [
        #         {"role": "system",
        #          "content": f"I will give you a paragraph of text"
        #                     f"and you need to check if the text meets my template:{computer}"
        #                     f"If it does not, you need to modify the format of my text to meet the template format."
        #                     f"And if it does,don't change it ,just show my text to me"
        #                     f"be sure to give me your answer in {self.language}"
        #          },
        #         {"role": "user",
        #          "content": f"This is my text:{review_result}"
        #          }
        #     ]
        #     response = client.chat.completions.create(
        #         model=self.model,
        #         messages=messages,
        #         temperature=0.5
        #     )
        #     result = ''
        #     for choice in response.choices:
        #         result += choice.message.content
        # return result, review_usage
        return chat_review_text,usage
        # text = self.extract_chapter(self.paper_pdf)
        # chat_review_text, total_token_used = self.chat_review(text=text)
        # return chat_review_text, total_token_used

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                    stop=tenacity.stop_after_attempt(5),
                    reraise=True)

    def chat_review(self, text):
        # openai.api_key = 'sk-1SWMJzlmDYazLQQzF1B7BfBbB83245FaBdA706E5752e5623'  # openai api, api2d api
        openai.api_key = api_key
        review_prompt_token = 1000
        try:
            text_token = len(self.encoding.encode(text))
        except:
            text_token = 13000
        input_text_index = int(len(text) * (self.max_token_num - review_prompt_token) / (text_token + 1))
        input_text = "This is the paper for your review:" + text[:input_text_index]

        messages = [
            {"role": "system",
             "content": "-You are a professional reviewer. "
                        f"-I will give you a paper. when you review the paper, you must refer to the {logic} and then give your review answer. "
                        f"-ATTENTION: your answer must comply to the template:" + self.review_prompt + "."
                        "-Be careful: Make sure to use {} answers".format(self.language)
             },
            {"role": "user", "content": input_text + ". ATTENTION!! YOU must translate the output into {}.".format(self.language)},
        ]
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5
            )
            result = ''
            for choice in response.choices:
                result += choice.message.content
            result = insert_sentence(result, '**Generated by ChatGPT, no copying allowed!**', 100)
            result += "\n\n⚠伦理声明/Ethics statement：\n--禁止直接复制生成的评论用于任何论文审稿工作！\n--Direct copying of generated comments for any paper review work is prohibited!"
            usage = response.usage.total_tokens
        except Exception as e:
            # 处理其他的异常
            result = "⚠：非常抱歉>_<，生了一个错误：" + str(e)
            usage = 'xxxxx'
        print("********" * 10)
        print(result)
        print("********" * 10)
        return result, usage

    def stage_1(self, paper):
        htmls = []
        text = ''
        text += 'Title: ' + paper.title + '. '
        text += 'Abstract: ' + paper.section_texts['Abstract']
        text_token = len(self.encoding.encode(text))#text_token：272
        if text_token > self.max_token_num/2 - 800:
            input_text_index = int(len(text)*((self.max_token_num/2)-800)/text_token)#？
            text = text[:input_text_index]
        openai.api_key = api_key
        messages = [
            {"role": "system",
             "content": f"I will give you a paper. You need to review this paper and discuss the novelty and originality of ideas, correctness, clarity, the significance of results, potential impact and quality of the presentation. "
                        f"Due to the length limitations, I am only allowed to provide you the abstract, introduction, conclusion and at most two sections of this paper."
                        f"Now I will give you the title and abstract and the headings of potential sections. "
                        f"You need to reply at most two headings. Then I will further provide you the full information, includes aforementioned sections and at most two sections you called for.\n\n"
                        f"Title: {paper.title}\n\n"
                        f"Abstract: {paper.section_texts['Abstract']}\n\n"
                        f"Potential Sections: {paper.section_names[2:-1]}\n\n"
                        f"Follow the following format to output your choice of sections:"
                        f"{{chosen section 1}}, {{chosen section 2}}\n\n"},
            {"role": "user", "content": text},
        ]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ''
        for choice in response.choices:
            result += choice.message.content
        print(result)
        return result.split(',')

    # def extract_chapter(self, pdf_path):
    #     file_object = BytesIO(pdf_path)
    #     pdf_reader = PyPDF2.PdfReader(file_object)
    #     # 获取PDF的总页数
    #     num_pages = len(pdf_reader.pages)
    #     # 初始化提取状态和提取文本
    #     extraction_started = False
    #     extracted_text = ""
    #     # 遍历PDF中的每一页
    #     for page_number in range(num_pages):
    #         page = pdf_reader.pages[page_number]
    #         page_text = page.extract_text()
    #         # 开始提取
    #         extraction_started = True
    #         page_number_start = page_number
    #         # 如果提取已开始，将页面文本添加到提取文本中
    #         if extraction_started:
    #             extracted_text += page_text
    #             # 停止提取
    #             if page_number_start + 1 < page_number:
    #                 break
    #     return extracted_text


def main(model, review_prompt, path, language):
    start_time = time.time()
    comments = ''
    output2 = ''
    if not model or not review_prompt or not path:
        comments = "⚠：论文格式不明确，请检测！"
        output2 = "⚠：论文格式不明确，请检测！"
    # 判断PDF文件
    else:
        # 创建一个Reader对象
        reviewer1 = Reviewer(model, review_prompt, path.name, language)
        paper_list=[]
        paper_list.append(Paper(path=path.name))  #[<get_paper_from_pdf.Paper object at 0x0000020B2060C0A0>]
        # 开始判断是路径还是文件：
        comments, total_token_used = reviewer1.review_by_chatgpt(paper_list=paper_list)#b'%PDF-1.5\n%\x8f\n136 0 obj\n<< /Filter /FlateDecode /Length 4732 >>\nstream\nx\
        time_used = time.time() - start_time
        output2 = "使用token数：" + str(total_token_used) + "\n花费时间：" + str(round(time_used, 2)) + "秒"
        txt_name = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime()) + ".txt"
        # 使用 'with' 语句打开文件，确保自动关闭文件
        with open("history/"+txt_name, 'w', encoding='utf-8') as file:
            # 写入中文文本
            file.write(comments)
    return comments, output2


# 标题
title = "🤖基于大语言模型的虚拟审稿人🤖"
# # 描述
#
# description = '''<div align='left'>
# <strong>这是一款基于ChatGPT-3.5的API开发的智能论文分析与建议助手。</strong>：
# </div>
# '''
# 创建 Gradio界面

with gr.Blocks(title="🤖基于大语言模型的虚拟审稿人🤖",theme="default") as demo:
    secret_css = gr.Textbox(visible=False)
    gr.Markdown('''<div align='center'>
<h1>🤖基于大语言模型的虚拟审稿人</h1></strong>
</div>
<h5>这是一款基于ChatGPT🤖的API开发的智能论文分析与审稿助手📖。</h5>
    ⭐⭐⭐<strong>建议:</strong>
    <ul>
      <li>建议普通用户每篇稿件📚<strong>提交2-3次</strong>综合评判大语言模型给出的结果</li>
      <li>假如多次提交的意见分歧严重，建议修改稿件</li>
      <li>对于<strong>医学类</strong>🚑💊或者<strong>艺术类</strong>🎨图片较多的论文，推荐使用支持多模态的gpt4作为虚拟审稿人</li>
    </ul>
''')
    with gr.Row():
        with gr.Tab("审稿",elem_id="review-panel"):
            with gr.Column():
                model = gr.Radio(models,label="请选择使用模型", interactive=True)
                prompt = gr.Dropdown(
                           choices=[
                               "工科类",
                               "医学类",
                               "生物类",
                               "化学类",
                               "车辆工程类"],label="Prompts", info="文章所属的类别", allow_custom_value=True)
                File_loader = gr.File(label="请上传论文PDF文件(请务必等pdf上传完成后再点击开始审稿！)", type='filepath')
                langan = gr.Radio(choices=["English", "Chinese", "French", "German", "Japenese"],
                                    label="选择输出语言")
            with gr.Column():
                outputs = [gr.Textbox(lines=20, label="分析结果"),
                                                      gr.Textbox(lines=2, label="资源统计")]
            btn = gr.Button("开始审稿")
            btn.click(fn=main, inputs=[model, prompt, File_loader, langan], outputs=outputs)
        with gr.Tab("聊天",elem_id="interact-panel"):
            chat_prompt = "你是一个专业的AI和计算机科学领域的审稿人，用户会对你提出问题，请你以专业正式的语言，保持中立的态度回复用户的问题。回复用户问题时请再三思考，确保回答的正确。"
            # 定义一个描述机器人的角色、行为和语气的提示
            role_prompt = {
                "role": "system",
                "content":chat_prompt
            }
            # 初始化对话历史格式，包括角色提示
            history_openai_format = [role_prompt]

            def predict(message, history):
                for human, assistant in history:
                    history_openai_format.append({"role": "user", "content": human})
                    history_openai_format.append({"role": "assistant", "content": assistant})
                history_openai_format.append({"role": "user", "content": message})

                response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=history_openai_format,
                    temperature=1.0,
                    stream=True
                )

                partial_message = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        partial_message = partial_message + chunk.choices[0].delta.content
                        yield partial_message

            gr.ChatInterface(predict,examples=["我使用随机梯度下降算法对模型进行训练，并在训练过程中加入动量项以加速收敛，请你评价该方法的科学性，并提出改进建议。"],theme=gr.themes.Soft())
        with gr.Tab("历史记录", elem_id="history-panel"):
            with gr.Column(scale=1):
                # 文件内容显示
                file_content = gr.Textbox(label="文件内容", lines=20, interactive=False, elem_id="file_content")
                # 文件路径（隐藏）
                file_path = gr.File(label="")
                # 下载按钮点击事件，将文件路径作为按钮的输出

            with gr.Column(scale=2):
                # 获取历史记录文件列表，并将其添加到 file_list 列
                files = get_files_list()

            for file_name in files:
                with gr.Row():
                    # 为每个文件创建一个按钮
                    file_button = gr.Button(file_name)
                    # 为按钮添加事件，当点击按钮时，加载文件内容
                    file_button.click(load_file_content, inputs=file_button, outputs=[file_content, file_path])
        with gr.Tab("界面外观", elem_id="beautiful-panel"):
            theme_dropdown = gr.Dropdown(AVAIL_THEMES, value=THEME, label="更换UI主题")
            gr.Markdown("请更换界面外观")

    def on_theme_dropdown_changed(theme, secret_css):
        adjust_theme, css_part1, _, adjust_dynamic_theme = load_dynamic_theme(theme)
        if adjust_dynamic_theme:
            css_part2 = adjust_dynamic_theme._get_theme_css()
        else:
            css_part2 = adjust_theme()._get_theme_css()
        return css_part2 + css_part1


    theme_handle = theme_dropdown.select(on_theme_dropdown_changed, [theme_dropdown, secret_css], [secret_css])
    theme_handle.then(
        None,
        [secret_css],
        None,
        js=js_code_for_css_changing
    )
demo.queue().launch()
