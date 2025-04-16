from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)
API_BASE_URL = 'http://127.0.0.1:5000'  # Flask 백엔드 주소

# 공통 토큰 검사 함수
def require_token():
    token = request.args.get('token')
    if not token:
        return redirect(url_for('login'))
    return token

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        res = requests.post(f'{API_BASE_URL}/login', json={'email': email, 'password': password})
        result = res.json()
        if result.get('success'):
            token = result.get('token')
            return redirect(url_for('item_list', token=token))
        else:
            error = result.get('error')
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        res = requests.post(f'{API_BASE_URL}/register', json={'email': email, 'password': password})
        result = res.json()
        if result.get('success'):
            message = '회원가입 성공! 로그인 해주세요.'
        else:
            message = result.get('error')
    return render_template('register.html', message=message)

@app.route('/items')
def item_list():
    token = require_token()
    if not isinstance(token, str): return token
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(f'{API_BASE_URL}/items', headers=headers)
    items = res.json()
    return render_template('items.html', items=items, request=request, token=token)

@app.route('/items/<int:item_id>')
def item_detail(item_id):
    token = require_token()
    if not isinstance(token, str): return token
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(f'{API_BASE_URL}/items/{item_id}', headers=headers)
    result = res.json()
    if result.get('success'):
        return render_template('item_detail.html', item=result['item'], token=token)
    else:
        return f"에러: {result.get('error')}", 404

@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    token = require_token()
    if not isinstance(token, str): return token
    headers = {'Authorization': f'Bearer {token}'}
    if request.method == 'POST':
        data = {
            'price': request.form['price']
        }
        requests.put(f'{API_BASE_URL}/items/{item_id}', headers=headers, json=data)
        return redirect(url_for('item_detail', item_id=item_id, token=token))
    res = requests.get(f'{API_BASE_URL}/items/{item_id}', headers=headers)
    item = res.json().get('item', {})
    return render_template('item_edit.html', item=item, token=token)

@app.route('/items/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    token = require_token()
    if not isinstance(token, str): return token
    headers = {'Authorization': f'Bearer {token}'}
    requests.delete(f'{API_BASE_URL}/items/{item_id}', headers=headers)
    return redirect(url_for('item_list', token=token))

@app.route('/items/new', methods=['GET', 'POST'])
def new_item():
    token = require_token()
    if not isinstance(token, str): return token
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'price': request.form['price']
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        requests.post(f'{API_BASE_URL}/items', headers=headers, json=data)
        return redirect(url_for('item_list', token=token))
    return render_template('item_form.html', token=token)

@app.route('/chat/<int:target_user_id>')
def chat(target_user_id):
    token = require_token()
    if not isinstance(token, str): return token

    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(f'{API_BASE_URL}/me', headers=headers)
    user = res.json().get('user')
    if not user:
        return "유저 정보 확인 실패", 401
    sender_id = user['id']
    return render_template('chat.html', sender_id=sender_id, receiver_id=target_user_id)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    token = require_token()
    if not isinstance(token, str): return token
    message = None
    if request.method == 'POST':
        recipient_id = int(request.form['recipient_id'])
        amount = int(request.form['amount'])
        headers = {'Authorization': f'Bearer {token}'}
        res = requests.post(f'{API_BASE_URL}/transfer', headers=headers, json={
            'recipient_id': recipient_id,
            'amount': amount
        })
        message = res.json().get('message', res.json().get('error'))
    return render_template('transfer.html', token=token, message=message)

@app.route('/report', methods=['GET', 'POST'])
def report():
    token = require_token()
    if not isinstance(token, str): return token
    message = None
    if request.method == 'POST':
        target_user_id = request.form.get('target_user_id')
        target_item_id = request.form.get('target_item_id')
        reason = request.form.get('reason')
        headers = {'Authorization': f'Bearer {token}'}
        res = requests.post(f'{API_BASE_URL}/report', headers=headers, json={
            'target_user_id': int(target_user_id) if target_user_id else None,
            'target_item_id': int(target_item_id) if target_item_id else None,
            'reason': reason
        })
        message = res.json().get('message', res.json().get('error'))
    return render_template('report.html', token=token, message=message)

@app.route('/admin/users')
def admin_users():
    token = require_token()
    if not isinstance(token, str): return token
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(f'{API_BASE_URL}/admin/users', headers=headers)
    if res.status_code == 403:
        return "관리자 권한이 필요합니다.", 403
    users = res.json()
    return render_template('admin_users.html', users=users, token=token)

@app.route('/transfer')
def transfer_form():
    token = require_token()
    if not isinstance(token, str):
        return token
    return render_template('transfer.html', token=token)


if __name__ == '__main__':
    app.run(port=5500, debug=True)
