from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3, os
from collections import Counter

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "results")

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            firstname TEXT,
            lastname TEXT,
            email TEXT,
            address TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ''
    if request.method == 'POST':
        data = (
            request.form['username'],
            request.form['password'],
            request.form['firstname'],
            request.form['lastname'],
            request.form['email'],
            request.form['address']
        )
        try:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, firstname, lastname, email, address) VALUES (?, ?, ?, ?, ?, ?)", data)
                conn.commit()
                session['user'] = data[0]
                return redirect(url_for('profile', username=data[0]))
        except sqlite3.IntegrityError:
            error = "Username or Email already exists."
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                session['user'] = username
                return redirect(url_for('profile', username=username))
            else:
                error = "Invalid username or password."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    if 'user' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
    word_count = None
    if os.path.exists(os.path.join(UPLOAD_FOLDER, 'Limerick.txt')):
        with open(os.path.join(UPLOAD_FOLDER, 'Limerick.txt'), 'r') as f:
            text = f.read()
            word_count = len(text.split())
    return render_template('profile.html', user=user, word_count=word_count)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and file.filename.endswith('.txt'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return redirect(url_for('profile', username=session.get('user')))
    return "Invalid file type", 400

@app.route('/download')
def download():
    fp = os.path.join(UPLOAD_FOLDER, "Limerick.txt")
    if os.path.exists(fp):
        return send_file(fp, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)
