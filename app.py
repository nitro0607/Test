from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

import requests
from bs4 import BeautifulSoup

import os

from apscheduler.schedulers.background import BackgroundScheduler

from crawler import crawl_campus_news
from database import init_db, get_news

from urllib.parse import urljoin


app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)


# ====================================
# 初始化数据库
# ====================================
init_db()


# ====================================
# 定时抓校园资讯
# ====================================
scheduler = BackgroundScheduler()

scheduler.add_job(
    crawl_campus_news,
    "interval",
    minutes=30
)

scheduler.start()


# ====================================
# 首页
# ====================================
@app.route("/")
def index():
    return render_template("index.html")


# ====================================
# Kimi AI
# ====================================
def kimi_chat(messages):

    api_key = os.environ.get("KIMI_API_KEY")

    if not api_key:
        return "未配置 KIMI_API_KEY"

    try:

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

        print("Kimi返回：", data)

        if "choices" not in data:
            return f"AI接口异常：{data}"

        return data["choices"][0]["message"]["content"]

    except Exception as e:

        return f"AI请求失败：{str(e)}"


# ====================================
# AI聊天接口
# ====================================
@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json()

    messages = data.get("messages")

    reply = kimi_chat(messages)

    return jsonify({
        "reply": reply
    })


# ====================================
# URL网页分析
# ====================================
@app.route("/api/summarize", methods=["POST"])
def summarize():

    data = request.get_json()

    url = data.get("url")

    if not url:

        return jsonify({
            "error": "未提供URL"
        })

    try:

        headers = {
            "User-Agent":
                "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        # ====================================
        # 自动识别网页编码（乱码修复）
        # ====================================
        response.encoding = response.apparent_encoding

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # ====================================
        # 标题
        # ====================================
        title = (
            soup.title.string.strip()
            if soup.title
            else "无标题"
        )

        # ====================================
        # 提取正文
        # ====================================
        article = soup.find("article")

        if article:
            paragraphs = article.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        content = " ".join(
            [p.get_text() for p in paragraphs]
        )

        content = " ".join(content.split())

        if not content:
            content = soup.get_text()

        content = content[:5000]

        # ====================================
        # AI总结
        # ====================================
        summary = kimi_chat([

            {
                "role": "system",

                "content":
                    "你是网页总结助手"
            },

            {
                "role": "user",

                "content": f"""

请总结以下网页内容：

要求：

1. 使用中文
2. 提取重点
3. 分点输出
4. 简洁清晰

内容：

{content}

"""
            }
        ])


        # ====================================
        # 页面链接提取（过滤优化）
        # ====================================
        links = []

        seen_links = set()

        for a in soup.find_all("a"):

            href = a.get("href")

            text = a.get_text(strip=True)

            if not href:
                continue

            # 过滤垃圾链接
            if href.startswith("#"):
                continue

            if href.startswith("javascript"):
                continue

            if href.startswith("mailto"):
                continue

            if href.startswith("tel"):
                continue

            full_url = urljoin(url, href)

            # 只保留http
            if not (
                full_url.startswith("http://")
                or
                full_url.startswith("https://")
            ):
                continue

            # 去重
            if full_url in seen_links:
                continue

            seen_links.add(full_url)

            if not text:
                text = full_url

            # 过滤太短文字
            if len(text.strip()) <= 1:
                continue

            links.append({

                "text": text,

                "url": full_url
            })


        # ====================================
        # 页面附件提取
        # ====================================
        attachments = []

        file_keywords = [

            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".zip",
            ".rar",
            ".ppt",
            ".pptx"
        ]

        for a in soup.find_all("a"):

            href = a.get("href")

            text = a.get_text(strip=True)

            if not href:
                continue

            full_url = urljoin(url, href)

            # 文件后缀
            if any(

                ext in full_url.lower()

                for ext in file_keywords
            ):

                attachments.append({

                    "name":
                        text if text else full_url,

                    "url":
                        full_url
                })

                continue

            # download类资源
            if any(

                key in full_url.lower()

                for key in [

                    "download",
                    "upload",
                    "resource",
                    "file",
                    "附件"
                ]
            ):

                attachments.append({

                    "name":
                        text if text else full_url,

                    "url":
                        full_url
                })

        # 去重
        unique = []

        seen = set()

        for item in attachments:

            if item["url"] not in seen:

                seen.add(item["url"])

                unique.append(item)

        attachments = unique


        # ====================================
        # 页面图片提取（优化版）
        # ====================================
        images = []

        seen_images = set()

        img_list = soup.find_all("img")

        for img in img_list:

            src = img.get("src")

            if not src:
                continue

            full_img = urljoin(url, src)

            # 过滤无效图片
            if not (
                full_img.startswith("http://")
                or
                full_img.startswith("https://")
            ):
                continue

            # 去重
            if full_img in seen_images:
                continue

            seen_images.add(full_img)

            # 过滤小图标/logo
            width = img.get("width")
            height = img.get("height")

            try:

                if width and int(width) < 80:
                    continue

                if height and int(height) < 80:
                    continue

            except:
                pass

            images.append(full_img)


        return jsonify({

            "title": title,

            "summary": summary,

            "links": links[:30],

            "attachments": attachments[:30],

            "images": images[:20]
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


# ====================================
# 校园资讯接口
# ====================================
@app.route("/api/news")
def news():

    try:

        # 实时抓取校园资讯
        news_list = crawl_campus_news()

        return jsonify(news_list)

    except Exception as e:

        return jsonify({
            "error": str(e)
        })

# ====================================
# CORS修复
# ====================================
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


# ====================================
# 启动
# ====================================
if __name__ == "__main__":

    app.run(debug=True)
