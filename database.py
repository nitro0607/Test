import sqlite3

DB_NAME = "campus_news.db"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS news (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT,

            summary TEXT,

            url TEXT UNIQUE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    """)

    conn.commit()

    conn.close()


def save_news(title, summary, url):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""

        INSERT OR IGNORE INTO news
        (title, summary, url)

        VALUES (?, ?, ?)

    """, (title, summary, url))

    conn.commit()

    conn.close()


def get_news():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""

        SELECT
            id,
            title,
            summary,
            url,
            created_at

        FROM news

        ORDER BY id DESC

        LIMIT 20

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows
