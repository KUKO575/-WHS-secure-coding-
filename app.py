from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import sqlite3
import os
import bcrypt
import jwt
import datetime
import html

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SECRET_KEY = 'your-secret-key'
DB_PATH = os.path.join(os.path.dirname(__file__), 'tinyshop.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_token(user_id, is_admin):
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return None

@app.route('/')
def index():
    return jsonify({'message': 'Tiny Second-hand Shopping Platform is running!'})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'success': False, 'error': '이메일과 비밀번호는 필수입니다.'}), 400
    hashed = hash_password(password)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, hashed))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': '이미 등록된 이메일입니다.'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cur.fetchone()
    conn.close()
    if not user:
        return jsonify({'success': False, 'error': '등록되지 않은 이메일입니다.'}), 404
    if user['is_suspended']:
        return jsonify({'success': False, 'error': '정지된 계정입니다.'}), 403
    if not check_password(password, user['password_hash']):
        return jsonify({'success': False, 'error': '비밀번호가 일치하지 않습니다.'}), 401
    token = generate_token(user['id'], user['is_admin'])
    return jsonify({'success': True, 'token': token})

@app.route('/items', methods=['POST'])
def create_item():
    payload = verify_token(request)
    if not payload:
        return jsonify({'success': False, 'error': '인증되지 않았습니다.'}), 401

    title = description = price = image_url = None

    if request.content_type.startswith('application/json'):
        data = request.get_json()
        title = html.escape(data.get('title', ''))
        description = html.escape(data.get('description', ''))
        price = data.get('price')
    elif request.content_type.startswith('multipart/form-data'):
        title = html.escape(request.form.get('title', ''))
        description = html.escape(request.form.get('description', ''))
        price = request.form.get('price')
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            image_url = f"/static/uploads/{filename}"

    if not title or not price:
        return jsonify({'success': False, 'error': '상품명과 가격은 필수입니다.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''INSERT INTO items (title, description, price, seller_id, image_url) VALUES (?, ?, ?, ?, ?)''', (title, description, price, payload['user_id'], image_url))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/items', methods=['GET'])
def get_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM items')
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item_detail(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT items.*, users.email AS seller_email FROM items JOIN users ON items.seller_id = users.id WHERE items.id = ?''', (item_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'error': '해당 상품이 존재하지 않습니다.'}), 404
    return jsonify({'success': True, 'item': dict(row)})

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    payload = verify_token(request)
    if not payload:
        return jsonify({'success': False, 'error': '인증되지 않았습니다.'}), 401
    data = request.get_json()
    price = data.get('price')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT seller_id FROM items WHERE id = ?', (item_id,))
    row = cur.fetchone()
    if not row or row['seller_id'] != payload['user_id']:
        return jsonify({'success': False, 'error': '본인 상품만 수정할 수 있습니다.'}), 403
    cur.execute('UPDATE items SET price = ? WHERE id = ?', (price, item_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    payload = verify_token(request)
    if not payload:
        return jsonify({'success': False, 'error': '인증되지 않았습니다.'}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT seller_id FROM items WHERE id = ?', (item_id,))
    row = cur.fetchone()
    if not row or row['seller_id'] != payload['user_id']:
        return jsonify({'success': False, 'error': '본인 상품만 삭제할 수 있습니다.'}), 403
    cur.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    payload = verify_token(request)
    if not payload or not payload.get('is_admin'):
        return jsonify({'success': False, 'error': '관리자만 접근할 수 있습니다.'}), 403
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, email, is_admin, is_suspended FROM users')
    users = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/admin/suspend/<int:user_id>', methods=['POST'])
def suspend_user(user_id):
    payload = verify_token(request)
    if not payload or not payload.get('is_admin'):
        return jsonify({'success': False, 'error': '관리자만 수행할 수 있습니다.'}), 403
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET is_suspended = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'{user_id}번 유저가 정지되었습니다.'})

@app.route('/report', methods=['POST'])
def report():
    payload = verify_token(request)
    if not payload:
        return jsonify({'success': False, 'error': '인증되지 않았습니다.'}), 401
    data = request.get_json()
    reporter_id = payload['user_id']
    target_user_id = data.get('target_user_id')
    target_item_id = data.get('target_item_id')
    reason = data.get('reason', '').strip()
    if not reason or (not target_user_id and not target_item_id):
        return jsonify({'success': False, 'error': '신고 대상과 사유를 입력해주세요.'}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''INSERT INTO reports (reporter_id, target_user_id, target_item_id, reason) VALUES (?, ?, ?, ?)''', (reporter_id, target_user_id, target_item_id, reason))
    if target_user_id:
        cur.execute('SELECT COUNT(*) FROM reports WHERE target_user_id = ?', (target_user_id,))
        if cur.fetchone()[0] >= 3:
            cur.execute('UPDATE users SET is_suspended = 1 WHERE id = ?', (target_user_id,))
    if target_item_id:
        cur.execute('SELECT COUNT(*) FROM reports WHERE target_item_id = ?', (target_item_id,))
        if cur.fetchone()[0] >= 3:
            cur.execute('DELETE FROM items WHERE id = ?', (target_item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '신고가 접수되었습니다.'})

@app.route('/transfer', methods=['POST'])
def transfer_points():
    payload = verify_token(request)
    if not payload:
        return jsonify({'success': False, 'error': '인증되지 않았습니다.'}), 401
    sender_id = payload['user_id']
    data = request.get_json()
    recipient_id = int(data.get('recipient_id'))
    amount = int(data.get('amount'))
    if not recipient_id or not amount or amount <= 0:
        return jsonify({'success': False, 'error': '올바른 수신자와 금액을 입력해주세요.'}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT points FROM users WHERE id = ?', (sender_id,))
    sender_points = cur.fetchone()
    if not sender_points or sender_points['points'] < amount:
        return jsonify({'success': False, 'error': '포인트가 부족합니다.'}), 403
    cur.execute('SELECT id FROM users WHERE id = ?', (recipient_id,))
    if not cur.fetchone():
        return jsonify({'success': False, 'error': '수신자를 찾을 수 없습니다.'}), 404
    cur.execute('UPDATE users SET points = points - ? WHERE id = ?', (amount, sender_id))
    cur.execute('UPDATE users SET points = points + ? WHERE id = ?', (amount, recipient_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'{amount}포인트를 전송했습니다.'})

@socketio.on('join')
def handle_join(data):
    sender = data['sender_id']
    receiver = data['receiver_id']
    room = get_chat_room(sender, receiver)
    join_room(room)
    emit('status', {'msg': f'{sender}님이 입장했습니다.'}, room=room)

@socketio.on('message')
def handle_message(data):
    sender = data['sender_id']
    receiver = data['receiver_id']
    msg = data['message']
    room = get_chat_room(sender, receiver)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)', (sender, receiver, msg))
    conn.commit()
    conn.close()
    emit('message', {'sender_id': sender, 'message': msg}, room=room)

def get_chat_room(user1, user2):
    return f"room_{min(user1, user2)}_{max(user1, user2)}"

@app.route('/me', methods=['GET'])
def get_current_user():
    payload = verify_token(request)
    if not payload:
        return jsonify({'success': False, 'error': '인증되지 않았습니다.'}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, email, is_admin, is_suspended, points FROM users WHERE id = ?', (payload['user_id'],))
    user = cur.fetchone()
    conn.close()
    if not user:
        return jsonify({'success': False, 'error': '유저 정보를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'user': dict(user)})

if __name__ == '__main__':
    socketio.run(app, debug=True)