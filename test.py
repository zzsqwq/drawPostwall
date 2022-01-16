# app.py
import base64

from flask import Flask, request

app = Flask(__name__)


@app.route('/test', methods=['post'])
def hello_world():
    return 'Hello World!'


@app.route('/image', methods=['post'])
def draw_image():
    data = request.get_json()
    print(data)
    with open("./zzsqwq.png", "rb") as f:
        base64str = base64.b64encode(f.read())
    print(base64str)
    return base64str


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
