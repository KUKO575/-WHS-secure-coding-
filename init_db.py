import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'tinyshop.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# users 테이블
cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    intro_text TEXT DEFAULT '',
    is_admin INTEGER DEFAULT 0,
    is_suspended INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0
)
''')

# items 테이블 (image_url 컬럼 포함)
cur.execute('''
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    image_url TEXT,
    FOREIGN KEY (seller_id) REFERENCES users(id)
)
''')

# reports 테이블
cur.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL,
    target_user_id INTEGER,
    target_item_id INTEGER,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id),
    FOREIGN KEY (target_item_id) REFERENCES items(id)
)
''')

# messages 테이블
cur.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()
print("✅ 모든 테이블 생성 완료")
