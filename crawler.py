import requests

from bs4 import BeautifulSoup

from urllib.parse import urljoin


NEWS_URL = "https://news.whut.edu.cn/"


def crawl_campus_news():

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            NEWS_URL,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        # 中文编码修复
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        news_items = []

        links = soup.find_all("a")

        seen = set()

        for item in links:

            title = item.get_text(strip=True)

            href = item.get("href")

            if not title:
                continue

            if not href:
                continue

            # 标题太短过滤
            if len(title) < 8:
                continue

            # 过滤无效链接
            if href.startswith("#"):
                continue

            if href.startswith("javascript"):
                continue

            full_url = urljoin(
                NEWS_URL,
                href
            )

            # 去重
            if full_url in seen:
                continue

            seen.add(full_url)

            # 只保留新闻页
            if not (
                "/2026/" in full_url
                or
                "/xw/" in full_url
                or
                "/zhxw/" in full_url
            ):
                continue

            news_items.append({

                "title": title,

                "summary": "武汉理工大学校园资讯",

                "url": full_url
            })

            if len(news_items) >= 20:
                break

        print("校园资讯抓取成功：", len(news_items))

        return news_items

    except Exception as e:

        print("校园资讯抓取失败：", e)

        return []
