from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS

import requests
from bs4 import BeautifulSoup

import os
import time

from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# =========================
# ✅ CORS修复
# =========================
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# =========================
# 首页
# =========================
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# 🤖 AI总结（流式）
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
                    {
                        "role": "system",
                        "content": "你是专业的信息整理助手"
                    },
                    {
                        "role": "user",
                        "content": f"""
请总结以下网页内容：

要求：
1. 中文输出
2. 分点总结
3. 提取核心信息
4. 控制在200字以内

内容：
{text[:3000]}
"""
                    }
                ],
                "temperature": 0.3
            },
            timeout=30
        )

        data = response.json()

        print("Kimi总结返回：", data)

        if "choices" not in data:
            yield f"\n❌ AI接口异常：{data}"
            return

        full_text = data["choices"][0]["message"]["content"]

        # 流式输出
        for char in full_text:
            yield char
            time.sleep(0.01)

    except Exception as e:
        yield f"\n❌ AI总结失败：{str(e)}"


# =========================
# 🌐 提取站内链接
# =========================
def extract_links(soup, base_url):

    links = set()

    base_domain = urlparse(base_url).netloc

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if href.startswith("#"):
            continue

        if href.startswith("javascript"):
            continue

        full_url = urljoin(base_url, href)

        # 仅同站
        if urlparse(full_url).netloc == base_domain:
            links.add(full_url)

    return list(links)


# =========================
# 📎 提取附件
# =========================
def extract_attachments(soup, base_url):

    attachments = set()

    file_exts = [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".rar",
        ".csv",
        ".txt"
    ]

    # a标签附件
    for a in soup.find_all("a", href=True):

        href = a["href"]

        if any(ext in href.lower() for ext in file_exts):

            attachments.add(
                urljoin(base_url, href)
            )

    # 图片
    for img in soup.find_all("img", src=True):

        attachments.add(
            urljoin(base_url, img["src"])
        )

    # iframe/embed
    for tag in soup.find_all(["iframe", "embed"]):

        if tag.get("src"):

            attachments.add(
                urljoin(base_url, tag["src"])
            )

    return list(attachments)


# =========================
# 🌐 URL分析接口
# =========================
@app.route("/api/summarize", methods=["POST", "OPTIONS"])
def summarize():

    if request.method == "OPTIONS":
        return '', 200

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "未收到JSON数据"
            }), 400

        url = data.get("url")

        if not url:
            return jsonify({
                "error": "未提供URL"
            }), 400

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

        # 标题
        title = (
            soup.title.string.strip()
            if soup.title
            else "无标题"
        )

        # 正文
        paragraphs = soup.find_all("p")

        main_text = " ".join(
            [p.get_text() for p in paragraphs]
        )

        main_text = " ".join(
            main_text.split()
        )

        # 链接
        links = extract_links(
            soup,
            url
        )[:20]

        # 附件
        attachments = extract_attachments(
            soup,
            url
        )

        # =========================
        # 流式返回
        # =========================
        def generate():

            yield f"📄 标题：{title}\n\n"

            yield "🧠 AI总结：\n"

            for chunk in ai_summary_stream(main_text):
                yield chunk

            # 链接
            yield "\n\n🌐 页面内链接：\n"

            if links:

                for link in links:
                    yield f"- {link}\n"

            else:
                yield "未发现站内链接\n"

            # 附件
            yield "\n📎 页面附件：\n"

            if attachments:

                for file in attachments:
                    yield f"- {file}\n"

            else:
                yield "未发现附件\n"

        return Response(
            generate(),
            content_type="text/plain; charset=utf-8"
        )

    except Exception as e:

        print("summarize错误：", str(e))

        return jsonify({
            "error": str(e)
        }), 500


# =========================
# 💬 AI聊天接口
# =========================
@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        return '', 200

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "未收到JSON数据"
            }), 400

        messages = data.get("messages")

        if not messages:
            return jsonify({
                "error": "messages为空"
            }), 400

        api_key = os.environ.get("KIMI_API_KEY")

        if not api_key:
            return jsonify({
                "error": "未配置KIMI_API_KEY"
            }), 500

        # =========================
        # 流式聊天
        # =========================
        def generate():

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

                print("Kimi聊天返回：", data)

                if "choices" not in data:

                    yield f"❌ AI接口异常：{data}"

                    return

                full_text = data["choices"][0]["message"]["content"]

                for char in full_text:
                    yield char
                    time.sleep(0.01)

            except Exception as e:

                yield f"❌ AI聊天失败：{str(e)}"

        return Response(
            generate(),
            content_type="text/plain; charset=utf-8"
        )

    except Exception as e:

        print("chat接口错误：", str(e))

        return jsonify({
            "error": str(e)
        }), 500


# =========================
# ✅ 全局CORS补充
# =========================
@app.after_request
def after_request(response):

    response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Headers"] = \
        "Content-Type,Authorization"

    response.headers["Access-Control-Allow-Methods"] = \
        "GET,POST,OPTIONS"

    return response


# =========================
# 本地运行
# =========================
if __name__ == "__main__":
    app.run(debug=True)
