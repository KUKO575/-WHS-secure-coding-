# 🛒 Tiny Second-hand Shopping Platform

A secure, minimal second-hand trading platform built with **Flask** and **WebSocket** (Socket.IO).  
Supports core features like user registration/login, product listing, admin panel, 1:1 chat, reporting, and point transfers.

---

## 📦 Features

- User registration & login with JWT authentication
- Product listing with image upload
- Product detail view and search functionality
- 1:1 real-time chat using WebSocket (Socket.IO)
- Reporting system for users and items
- Admin dashboard for managing users, items, and reports
- Point transfer between users
- SQLite-based lightweight DB
- Secure coding practices (e.g., XSS prevention, bcrypt hashing, token auth)

---

## 🔧 Requirements

- Python 3.10+
- pip
- WSL (for Windows users)

### Install Required Packages

```bash
pip install flask flask-socketio eventlet bcrypt pyjwt
|Or install from a requirements.txt file if included:

#pip install -r requirements.txt

🚀 Quickstart (WSL or Ubuntu)
1. Clone this repository
bash
git clone https://github.com/your-username/tiny-secondhand-shop.git
cd tiny-secondhand-shop/backend

2. Set up Python virtual environment
bash
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
bash
pip install flask flask-socketio eventlet bcrypt pyjwt

4. Initialize database
bash
python init_db.py

5. Run both servers
(1) Backend server with WebSocket

bash
python app.py

(2) UI Frontend server (in a new terminal tab/window)
bash
python ui_app.py

🌐 URLs
API Server (WebSocket): http://127.0.0.1:5000

UI App: http://127.0.0.1:5500

📁 Project Structure
bash
backend/
├── app.py              # WebSocket backend (API server)
├── ui_app.py           # Frontend Flask UI server
├── init_db.py          # SQLite DB initializer
├── tinyshop.db         # Auto-generated SQLite database
├── static/uploads/     # Uploaded item images
└── templates/          # HTML templates (chat, items, report, admin, etc.)
🔐 Security Considerations

Area	Technique/Implementation
Passwords	bcrypt hashing
Auth	JWT-based token authentication
XSS Prevention	HTML escaping on product/user inputs
Access Control	Admin-only API endpoints
Input Security	Validation on forms (e.g. price, recipient ID)
🧪 Sample Accounts (Optional)
You can create an admin account manually with:

bash
python create_admin.py
📝 License
This project is licensed under the MIT License.
Use it freely for educational, academic, or personal projects.

🤝 Contributions
Pull requests are welcome.
For major changes, please open an issue first to discuss what you would like to change.
