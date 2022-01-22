from flask import Flask, render_template
from flask import request
from flask_cors import CORS
from wordcloud import WordCloud
import io
import base64
from kbqa_test import KBQA

app = Flask(__name__,
            template_folder="/Users/beerpig/hello-world/dist",
            static_folder="/Users/beerpig/hello-world/dist/static")

CORS(app)


# 真正调用词云库生成图片
def get_word_cloud(text):
    # font = "./SimHei.ttf"
    # pil_img = WordCloud(width=500, height=500, font_path=font).generate(text=text).to_image()

    pil_img = WordCloud(width=800, height=300, background_color="white").generate(text=text).to_image()
    img = io.BytesIO()
    pil_img.save(img, "PNG")
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()
    return img_base64


# 主页面
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


# 生成词云图片接口，以base64格式返回
@app.route('/word/cloud/generate', methods=["POST"])
def cloud():
    text = request.json.get("word")
    print(text)
    handler = KBQA()
    res = handler.qa_main(text)
    return res


if __name__ == '__main__':
    app.run()
