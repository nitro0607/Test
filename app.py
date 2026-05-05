from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
import time

app = Flask(__name__)
CORS(app)

# 首页
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# 🌐 网页总结（流式）
# =========================
def ai_summary_stream(text):
    try:
        api_key = os.environ.get("KIMI_API_KEY")

        if not api_key:
            yield "❌ 未配置 KIMI_API_KEY"
            return

        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-auto",
                "messages": [
                    {"role": "system", "content": "你是一个信息总结助手"},
                    {"role": "user", "content": f"请总结以下内容：\n{text[:2000]}"}
                ]
            },
            timeout=20
        )

        data = response.json()

        if "choices" not in data:
            yield f"❌ AI接口异常：{data}"
            return

        full_text = data["choices"][0]["message"]["content"]

        for char in full_text:
            yield char
            time.sleep(0.01)

    except Exception as e:
        yield f"❌ AI总结失败：{str(e)}"


# 🌐 API：网页总结
@app.route("/api/summarize", methods=["POST", "OPTIONS"])
def summarize():
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "未提供URL"})

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title else "无标题"

        paragraphs = soup.find_all("p")
        main_text = " ".join([p.get_text() for p in paragraphs])
        main_text = " ".join(main_text.split())

        def generate():
            yield f"📄 标题：{title}\n\n🧠 AI总结：\n"
            for chunk in ai_summary_stream(main_text):
                yield chunk

        return Response(generate(), content_type='text/plain; charset=utf-8')

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# 💬 多轮对话（流式）
# =========================
@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 200

    data = request.get_json()
    messages = data.get("messages")

    if not messages:
        return jsonify({"error": "未提供消息"})

    def generate():
        try:
            api_key = os.environ.get("KIMI_API_KEY")

            response = requests.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "moonshot-v1-auto",
                    "messages": messages
                },
                timeout=20
            )

            data = response.json()

            if "choices" not in data:
                yield "❌ AI接口异常"
                return

            full_text = data["choices"][0]["message"]["content"]

            for char in full_text:
                yield char
                time.sleep(0.01)

        except Exception as e:
            yield f"❌ 错误：{str(e)}"

    return Response(generate(), content_type='text/plain; charset=utf-8')


# =========================
# ✅ CORS兜底
# =========================
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response


if __name__ == "__main__":
    app.run(debug=True)
