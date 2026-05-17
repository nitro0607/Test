import requests

from bs4 import BeautifulSoup

from urllib.parse import urljoin

from database import save_news


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

        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        news_items = soup.find_all("a")

        count = 0

        for item in news_items:

            title = item.get_text(strip=True)

            href = item.get("href")

            if not title:
                continue

            if not href:
                continue

            if len(title) < 8:
                continue

            full_url = urljoin(
                NEWS_URL,
                href
            )

            save_news(
                title,
                "武汉理工大学校园资讯",
                full_url
            )

            count += 1

            if count >= 20:
                break

    except Exception as e:

        print("校园资讯抓取失败：", e)
