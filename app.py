from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
import random
import string

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
        full_name = request.form['full_name']
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE phone_number=?", (phone,))
        if cursor.fetchone():
            flash("Numéro déjà enregistré", "error")
            return redirect('/register')

        cursor.execute("INSERT INTO users(full_name, phone_number, password) VALUES (?, ?, ?)",
                       (full_name, phone, password))
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
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone_number=? AND password=?", (phone, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            flash("Connexion réussie !", "success")
            return redirect('/dashboard')
        else:
            flash("Identifiants invalides", "error")

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    # --- POST (investissement) ---
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
        wallet = cursor.fetchone()
        balance = wallet['balance'] if wallet else 0

        cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT 5", (session['user_id'],))
        transactions = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM investments WHERE user_id=? ORDER BY date DESC", (session['user_id'],))
        investments = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify(balance=balance, transactions=transactions, investments=investments)

    # --- GET (affichage normal) ---
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

# ---------------- DÉPÔT ----------------
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

# ---------------- DÉCONNEXION ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Déconnexion réussie", "info")
    return redirect('/')

# ---------------- LANCER APP ----------------
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    init_db()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
