import sqlite3

DB_NAME = "news.db"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,

        summary TEXT,

        content TEXT,

        source_url TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    conn.close()


def save_news(title, summary, content, source_url):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO news
    (title, summary, content, source_url)
    VALUES (?, ?, ?, ?)
    """, (title, summary, content, source_url))

    conn.commit()

    conn.close()


def get_news(limit=20):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, summary, source_url, created_at
    FROM news
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows