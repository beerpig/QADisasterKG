from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/send_message', methods=['GET'])
def send_message():
    global message_get
    message_get = ""

    message_get = request.args['message']
    print("收到前端发过来的信息：%s" % message_get)
    print("收到数据的类型为：" + str(type(message_get)))

    return "收到消息"


@app.route('/change_to_json', methods=['GET'])
def change_to_json():
    global message_get
    message_json = {
        "message": message_get
    }

    return jsonify(message_json)


if __name__ == '__main__':
    app.run()
