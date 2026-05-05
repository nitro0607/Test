from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 首页
@app.route("/")
def index():
    return render_template("index.html")

# 👉 AI总结函数（Kimi）
def ai_summary(text):
    try:
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('KIMI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-8k",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的信息整理助手。"
                    },
                    {
                        "role": "user",
                        "content": f"""
请对以下网页内容进行总结：
1. 用简洁中文
2. 提取核心观点
3. 分点输出
4. 控制在200字以内

内容：
{text[:4000]}
"""
                    }
                ],
                "temperature": 0.3
            },
            timeout=20
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"AI总结失败：{str(e)}"


# 👉 抓网页 + AI总结
@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.get_json()
    url = data.get("url")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "无标题"

        paragraphs = soup.find_all("p")
        main_text = " ".join([p.get_text() for p in paragraphs])
        main_text = " ".join(main_text.split())

        summary = ai_summary(main_text)

        return jsonify({
            "title": title,
            "summary": summary
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
