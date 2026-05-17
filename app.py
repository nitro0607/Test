from flask import Flask, request, jsonify, render_template

from flask_cors import CORS

import requests

from bs4 import BeautifulSoup

import os

from apscheduler.schedulers.background import BackgroundScheduler

from crawler import crawl_campus_news

from database import init_db, get_news


app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)


# 初始化数据库
init_db()


# 定时抓取校园资讯
scheduler = BackgroundScheduler()

scheduler.add_job(
    crawl_campus_news,
    'interval',
    minutes=30
)

scheduler.start()


# 首页
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# AI聊天
# =========================
def kimi_chat(messages):

    api_key = os.environ.get("KIMI_API_KEY")

    response = requests.post(
        "https://api.moonshot.cn/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "moonshot-v1-auto",
            "messages": messages,
            "temperature": 0.7
        },
        timeout=30
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]


# =========================
# AI聊天接口
# =========================
@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json()

    messages = data.get("messages")

    reply = kimi_chat(messages)

    return jsonify({
        "reply": reply
    })


# =========================
# URL抓取 + AI总结
# =========================
@app.route("/api/summarize", methods=["POST"])
def summarize():

    data = request.get_json()

    url = data.get("url")

    if not url:

        return jsonify({
            "error": "未提供URL"
        })

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    title = (
        soup.title.string.strip()
        if soup.title
        else "无标题"
    )

    paragraphs = soup.find_all("p")

    content = " ".join(
        [p.get_text() for p in paragraphs]
    )

    content = " ".join(content.split())

    # 页面链接
    links = []

    for a in soup.find_all("a"):

        href = a.get("href")

        text = a.get_text(strip=True)

        if href:

            links.append({
                "text": text,
                "url": href
            })

    # 附件提取
    attachments = []

    for a in soup.find_all("a"):

        href = a.get("href")

        if not href:
            continue

        if any(
            href.lower().endswith(ext)
            for ext in [
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".zip"
            ]
        ):

            attachments.append(href)

    # AI总结
    summary = kimi_chat([
        {
            "role": "system",
            "content": "你是网页信息总结助手"
        },
        {
            "role": "user",
            "content": f"""
请总结以下内容：

{content[:3000]}
"""
        }
    ])

    return jsonify({

        "title": title,

        "summary": summary,

        "links": links[:20],

        "attachments": attachments[:20]
    })


# =========================
# 校园资讯接口
# =========================
@app.route("/api/news")
def news():

    news_list = get_news()

    result = []

    for item in news_list:

        result.append({

            "id": item[0],

            "title": item[1],

            "summary": item[2],

            "url": item[3],

            "time": item[4]
        })

    return jsonify(result)


# =========================
# CORS
# =========================
@app.after_request
def after_request(response):

    response.headers[
        "Access-Control-Allow-Origin"
    ] = "*"

    response.headers[
        "Access-Control-Allow-Headers"
    ] = "Content-Type,Authorization"

    response.headers[
        "Access-Control-Allow-Methods"
    ] = "GET,POST,OPTIONS"

    return response


if __name__ == "__main__":
    app.run(debug=True)
