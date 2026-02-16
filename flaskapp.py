from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"   # Needed for flash messages

UPLOAD_FOLDER = '/var/www/flaskapp/uploads'
DATABASE = '/var/www/flaskapp/users.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        firstname TEXT,
        lastname TEXT,
        email TEXT,
        address TEXT,
        filename TEXT,
        wordcount INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()


@app.route('/')
def index():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        address = request.form['address']

        filename = ""
        wordcount = 0

        file = request.files.get('file')
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            
            # Add timestamp to avoid overwriting
            unique_name = str(datetime.now().timestamp()).replace('.', '') + "_" + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(filepath)

            with open(filepath, 'r', errors='ignore') as f:
                wordcount = len(f.read().split())

            filename = unique_name

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("""INSERT INTO users 
                     (username,password,firstname,lastname,email,address,filename,wordcount)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (username,password,firstname,lastname,email,address,filename,wordcount))
        conn.commit()
        conn.close()

        return redirect(url_for('profile', username=username))

    except sqlite3.IntegrityError:
        return "Username already exists!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            return redirect(url_for('profile', username=username))
        else:
            return "INVALID USERNAME OR PASSWORD"

    return render_template('login.html')


@app.route('/profile/<username>')
def profile(username):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        return render_template('profile.html', user=user)
    else:
        return "User not found"


@app.route('/upload/<username>', methods=['POST'])
def upload(username):
    file = request.files.get('file')

    if file and file.filename != "":
        filename = secure_filename(file.filename)

        unique_name = str(datetime.now().timestamp()).replace('.', '') + "_" + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(filepath)

        with open(filepath, 'r', errors='ignore') as f:
            wordcount = len(f.read().split())

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE users SET filename=?, wordcount=? WHERE username=?",
                  (unique_name, wordcount, username))
        conn.commit()
        conn.close()

    return redirect(url_for('profile', username=username))
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               secure_filename(filename),
                               as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
