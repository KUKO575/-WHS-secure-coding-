import os
import sqlite3
import bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), 'tinyshop.db')

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('''
INSERT INTO users (email, password_hash, is_admin)
VALUES (?, ?, 1)
''', (
    'admin@example.com',
    bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
))

conn.commit()
conn.close()

print("✅ 관리자 계정 생성 완료")
