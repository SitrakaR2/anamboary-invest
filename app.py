from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ANAMBOARY_SECRET_KEY"

DB_PATH = "anamboary.db"


# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone_number TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        balance REAL DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        reference TEXT,
        status TEXT,
        timestamp TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        profit REAL,
        status TEXT,
        reference TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_logins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login_time TEXT,
        ip_address TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# ---------------- PAGE ACCUEIL ----------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# ---------------- INSCRIPTION ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        phone = request.form['phone'].strip()
        password = request.form['password'].strip()

        # Validation des champs
        if not full_name or not phone or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return redirect('/register')

        if len(password) < 4:
            flash("Le mot de passe doit contenir au moins 4 caractères.", "error")
            return redirect('/register')

        conn = get_db()
        cursor = conn.cursor()

        # Vérifier si le numéro existe déjà
        cursor.execute("SELECT * FROM users WHERE phone_number=?", (phone,))
        if cursor.fetchone():
            flash("Ce numéro est déjà enregistré.", "error")
            conn.close()
            return redirect('/register')

        # Hasher le mot de passe
        hashed = generate_password_hash(password)

        # Enregistrement utilisateur
        cursor.execute("INSERT INTO users(full_name, phone_number, password) VALUES (?, ?, ?)",
                       (full_name, phone, hashed))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO wallets(user_id, balance) VALUES (?, ?)", (user_id, 0))
        conn.commit()
        conn.close()

        flash("Inscription réussie ! Veuillez vous connecter.", "success")
        return redirect('/login')

    return render_template('register.html')


# ---------------- CONNEXION ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone'].strip()
        password = request.form['password'].strip()

        if not phone or not password:
            flash("Veuillez entrer votre numéro et mot de passe.", "error")
            return redirect('/login')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone_number=?", (phone,))
        user = cursor.fetchone()

        if user is None:
            flash("Ce numéro n’est pas enregistré.", "error")
            conn.close()
            return redirect('/login')

        # Vérification du mot de passe hashé
        if not check_password_hash(user['password'], password):
            flash("Mot de passe incorrect.", "error")
            conn.close()
            return redirect('/login')

        # Connexion réussie
        session['user_id'] = user['id']
        session['full_name'] = user['full_name']

        # Enregistrement du login
        cursor.execute(
            "INSERT INTO user_logins (user_id, login_time, ip_address) VALUES (?, ?, ?)",
            (user['id'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.remote_addr)
        )
        conn.commit()
        conn.close()

        flash("Connexion réussie !", "success")
        return redirect('/dashboard')

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST' and 'amount' in request.form:
        try:
            amount = float(request.form['amount'])
        except ValueError:
            return "Montant invalide", 400

        cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
        wallet = cursor.fetchone()
        balance = wallet['balance'] if wallet else 0

        if amount <= 0 or amount > balance:
            return "Solde insuffisant", 400

        daily_profit = round(amount * 0.1167)
        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id=?", (amount, session['user_id']))

        reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        cursor.execute("INSERT INTO investments (user_id, amount, date, profit, status, reference) VALUES (?, ?, ?, ?, ?, ?)",
                       (session['user_id'], amount, datetime.now().strftime("%Y-%m-%d"), daily_profit, "actif", reference))

        cursor.execute("INSERT INTO transactions (user_id, type, amount, reference, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (session['user_id'], "investissement", amount, reference, "réussi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

        cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
        balance = cursor.fetchone()['balance']

        cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT 5", (session['user_id'],))
        transactions = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM investments WHERE user_id=? ORDER BY date DESC", (session['user_id'],))
        investments = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify(balance=balance, transactions=transactions, investments=investments)

    # Affichage normal
    cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
    wallet = cursor.fetchone()
    balance = wallet['balance'] if wallet else 0

    cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT 5", (session['user_id'],))
    transactions = cursor.fetchall()

    cursor.execute("SELECT * FROM investments WHERE user_id=? ORDER BY date DESC", (session['user_id'],))
    investments = cursor.fetchall()

    conn.close()
    return render_template('dashboard.html', name=session['full_name'], balance=balance,
                           transactions=transactions, investments=investments)


# ---------------- DEPOT ----------------
@app.route('/depot', methods=['GET', 'POST'])
def depot():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash("Montant invalide", "error")
            return redirect('/depot')

        if amount <= 0:
            flash("Montant invalide.", "error")
            return redirect('/depot')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE wallets SET balance = balance + ? WHERE user_id=?", (amount, session['user_id']))

        reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, reference, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (session['user_id'], "dépôt", amount, reference, "réussi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        flash(f"Dépôt de {amount} Ar effectué avec succès !", "success")
        return redirect('/dashboard')

    return render_template('depot.html')


# ---------------- RETRAIT ----------------
@app.route('/retrait', methods=['GET', 'POST'])
def retrait():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
    wallet = cursor.fetchone()
    balance = wallet['balance'] if wallet else 0

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash("Montant invalide", "error")
            return redirect('/retrait')

        if amount <= 0 or amount > balance:
            flash("Montant invalide ou solde insuffisant.", "error")
            return redirect('/retrait')

        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id=?", (amount, session['user_id']))

        reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, reference, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (session['user_id'], "retrait", amount, reference, "réussi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        flash(f"Retrait de {amount} Ar effectué avec succès !", "success")
        return redirect('/dashboard')

    conn.close()
    return render_template('retrait.html', balance=balance)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Déconnexion réussie", "info")
    return redirect('/')


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    # Login admin tsotra
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "anamboary@2025":
            session['is_admin'] = True
            return redirect('/admin/dashboard')
        else:
            flash("Identifiants incorrects", "error")
            return redirect('/admin')
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect('/admin')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, full_name, phone_number FROM users")
    users = cursor.fetchall()

    cursor.execute("""
        SELECT u.full_name, l.login_time, l.ip_address
        FROM user_logins l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.login_time DESC
    """)
    logs = cursor.fetchall()

    conn.close()
    return render_template('admin_dashboard.html', users=users, logs=logs)


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash("Déconnecté de l'administration", "info")
    return redirect('/')

# ---------------- LANCEMENT ----------------
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    init_db()
    app.run(debug=True)
