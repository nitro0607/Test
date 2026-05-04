from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

app = Flask(__name__)
CORS(app)


def split_sentences(text):
    text = text.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n')
    sentences = [s.strip() for s in text.splitlines() if s.strip()]
    return sentences


def simple_summary(text, max_sentences=3):
    sentences = split_sentences(text)
    return ''.join(sentences[:max_sentences])


def summarize_text(text, sentence_count=4):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer('chinese'))
        summarizer = TextRankSummarizer()
        summary_sentences = summarizer(parser.document, sentence_count)
        return ''.join(str(s) for s in summary_sentences)
    except:
        return simple_summary(text)


def extract_main_info(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.title.string if soup.title else "无标题"

        paragraphs = soup.find_all('p')
        main_text = ' '.join([p.get_text() for p in paragraphs])
        main_text = ' '.join(main_text.split())

        summary = summarize_text(main_text)

        return {
            "title": title,
            "summary": summary
        }
    except Exception as e:
        return {"error": str(e)}


@app.route('/api/summarize', methods=['POST'])
def summarize():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "缺少URL"}), 400

    result = extract_main_info(url)
    return jsonify(result)


if __name__ == '__main__':
    app.run()