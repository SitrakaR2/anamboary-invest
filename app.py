from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ANAMBOARY_SECRET_KEY_RENDER_2025")

# Configuration Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'votre.email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'votre-mot-de-passe-app')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'votre.email@gmail.com')

mail = Mail(app)

# Configuration production
app.config.update(
    DEBUG=os.environ.get("DEBUG", "False").lower() == "true",
    SECRET_KEY=os.environ.get("SECRET_KEY", "ANAMBOARY_SECRET_KEY_RENDER_2025"),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'anamboary.db')

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
        email TEXT NOT NULL UNIQUE,
        phone_number TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
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
        reference TEXT UNIQUE,
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
        reference TEXT UNIQUE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
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

# Initialize database on startup
with app.app_context():
    init_db()

# ---------------- UTILITY FUNCTIONS ----------------
def generate_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def validate_phone(phone):
    return phone.strip().isdigit() and len(phone) >= 8

# ---------------- EMAIL FUNCTIONS ----------------
def send_welcome_email(email, full_name):
    """Envoyer un email de bienvenue réel"""
    try:
        subject = "🎉 Bienvenue sur Anamboary Invest!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                    color: #333;
                    line-height: 1.6;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(45deg, #ffc107, #ff8c00);
                    color: black;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .features {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #343a40;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Anamboary Invest</h1>
                    <p>Votre succès financier commence ici</p>
                </div>
                
                <div class="content">
                    <h2>Bonjour {full_name} !</h2>
                    <p>Nous sommes ravis de vous accueillir sur <strong>Anamboary Invest</strong>, la plateforme d'investissement la plus sécurisée de Madagascar.</p>
                    
                    <div class="features">
                        <p><strong>🎯 Ce que vous pouvez faire maintenant :</strong></p>
                        <ul>
                            <li>✅ Faire votre premier dépôt</li>
                            <li>✅ Investir avec 11.67% de profit quotidien</li>
                            <li>✅ Suivre vos performances en temps réel</li>
                            <li>✅ Retirer vos gains à tout moment</li>
                        </ul>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="https://votre-site.com/dashboard" class="button">
                            Commencer à Investir
                        </a>
                    </p>
                    
                    <p><strong>📞 Besoin d'aide ?</strong><br>
                    Notre équipe de support est disponible 24h/24 et 7j/7 pour vous accompagner.</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 Anamboary Invest. Tous droits réservés.</p>
                    <p>Cet email a été envoyé à {email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body
        )
        
        mail.send(msg)
        print(f"✅ Email de bienvenue envoyé à: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email à {email}: {str(e)}")
        return False

def send_transaction_email(email, full_name, transaction_type, amount, reference=None):
    """Envoyer un email pour les transactions"""
    try:
        if transaction_type == "dépôt":
            subject = "💰 Dépôt réussi - Anamboary Invest"
            action = "déposé"
            color = "#28a745"
            emoji = "💰"
        elif transaction_type == "retrait":
            subject = "💸 Retrait réussi - Anamboary Invest"
            action = "retiré"
            color = "#dc3545"
            emoji = "💸"
        else:
            subject = "📈 Investissement réussi - Anamboary Invest"
            action = "investi"
            color = "#ffc107"
            emoji = "📈"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: {color};
                    color: white;
                    padding: 25px;
                    text-align: center;
                }}
                .content {{
                    padding: 25px;
                    color: #333;
                    line-height: 1.6;
                }}
                .transaction-details {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #343a40;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{emoji} {subject}</h2>
                </div>
                
                <div class="content">
                    <p>Bonjour <strong>{full_name}</strong>,</p>
                    
                    <p>Votre transaction a été effectuée avec succès !</p>
                    
                    <div class="transaction-details">
                        <h3>Détails de la transaction :</h3>
                        <p><strong>Type :</strong> {transaction_type}</p>
                        <p><strong>Montant :</strong> {amount} Ar</p>
                        <p><strong>Statut :</strong> ✅ Réussi</p>
                        {f'<p><strong>Référence :</strong> {reference}</p>' if reference else ''}
                        <p><strong>Date :</strong> {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
                    </div>
                    
                    <p>Vous avez {action} <strong>{amount} Ar</strong> avec succès.</p>
                    
                    <p>Pour toute question, n'hésitez pas à contacter notre support.</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 Anamboary Invest - Plateforme sécurisée d'investissement</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body
        )
        
        mail.send(msg)
        print(f"✅ Email transaction envoyé à: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email transaction à {email}: {str(e)}")
        return False

def send_investment_email(email, full_name, amount, daily_profit):
    """Envoyer un email pour les investissements"""
    try:
        monthly_profit = daily_profit * 30
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .profit-card {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Investissement Réussi !</h1>
                    <p>Votre argent travaille pour vous</p>
                </div>
                
                <div class="content">
                    <p>Félicitations <strong>{full_name}</strong> !</p>
                    
                    <p>Votre investissement de <strong>{amount} Ar</strong> a été placé avec succès.</p>
                    
                    <div class="profit-card">
                        <h3>📈 Votre Profit Quotidien</h3>
                        <h2>{daily_profit} Ar</h2>
                        <p>Soit {monthly_profit} Ar par mois</p>
                    </div>
                    
                    <p><strong>Prochain profit :</strong> Dans 24 heures</p>
                    <p><strong>Disponibilité :</strong> Retrait possible à tout moment</p>
                    
                    <p>Merci de nous faire confiance pour faire fructifier votre capital.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject="📈 Investissement placé avec succès - Anamboary Invest",
            recipients=[email],
            html=html_body
        )
        
        mail.send(msg)
        print(f"✅ Email investissement envoyé à: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email investissement à {email}: {str(e)}")
        return False

# ---------------- SESSION MANAGEMENT ----------------
@app.before_request
def make_session_permanent():
    session.permanent = True

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect('/dashboard')
        
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        password = request.form['password'].strip()

        if not full_name or not email or not phone or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return render_template('register.html')

        if len(password) < 4:
            flash("Le mot de passe doit contenir au moins 4 caractères.", "error")
            return render_template('register.html')

        if not validate_phone(phone):
            flash("Numéro de téléphone invalide.", "error")
            return render_template('register.html')

        # Validation email simple
        if '@' not in email or '.' not in email:
            flash("Adresse email invalide.", "error")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Vérifier si l'email existe déjà
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            if cursor.fetchone():
                flash("Cet email est déjà enregistré.", "error")
                return render_template('register.html')

            # Vérifier si le numéro existe déjà
            cursor.execute("SELECT * FROM users WHERE phone_number=?", (phone,))
            if cursor.fetchone():
                flash("Ce numéro est déjà enregistré.", "error")
                return render_template('register.html')

            hashed = generate_password_hash(password)
            cursor.execute("INSERT INTO users(full_name, email, phone_number, password) VALUES (?, ?, ?, ?)",
                           (full_name, email, phone, hashed))
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO wallets(user_id, balance) VALUES (?, ?)", (user_id, 0))
            conn.commit()
            
            # Envoyer email de bienvenue
            send_welcome_email(email, full_name)
            
            flash("Inscription réussie ! Un email de bienvenue vous a été envoyé.", "success")
            return redirect('/login')
        except Exception as e:
            conn.rollback()
            flash("Erreur lors de l'inscription. Veuillez réessayer.", "error")
            return render_template('register.html')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/dashboard')
        
    if request.method == 'POST':
        login_input = request.form['login_input'].strip()
        password = request.form['password'].strip()

        if not login_input or not password:
            flash("Veuillez entrer votre email/téléphone et mot de passe.", "error")
            return render_template('login.html')

        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Essayer de trouver par email ou téléphone
            cursor.execute("SELECT * FROM users WHERE email=? OR phone_number=?", (login_input, login_input))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session.permanent = True
                session['user_id'] = user['id']
                session['full_name'] = user['full_name']
                session['phone'] = user['phone_number']
                session['email'] = user['email']
                
                cursor.execute(
                    "INSERT INTO user_logins (user_id, login_time, ip_address) VALUES (?, ?, ?)",
                    (user['id'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.remote_addr)
                )
                conn.commit()
                
                flash(f"Bienvenue {user['full_name']} !", "success")
                return redirect('/dashboard')
            else:
                flash("Email/téléphone ou mot de passe incorrect.", "error")
                return render_template('login.html')
        except Exception as e:
            flash("Erreur de connexion. Veuillez réessayer.", "error")
            return render_template('login.html')
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Veuillez vous connecter pour accéder au dashboard.", "error")
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Vérifier si l'utilisateur existe toujours
        cursor.execute("SELECT * FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            session.clear()
            flash("Session expirée. Veuillez vous reconnecter.", "error")
            return redirect('/login')

        cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
        wallet = cursor.fetchone()
        balance = wallet['balance'] if wallet else 0

        cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT 5", (session['user_id'],))
        transactions = cursor.fetchall()

        cursor.execute("SELECT * FROM investments WHERE user_id=? ORDER BY date DESC", (session['user_id'],))
        investments = cursor.fetchall()

        return render_template('dashboard.html', name=session['full_name'], balance=balance,
                               transactions=transactions, investments=investments)
                               
    except Exception as e:
        flash("Erreur de chargement des données.", "error")
        return redirect('/login')
    finally:
        conn.close()

@app.route('/invest', methods=['POST'])
def invest():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401

    try:
        amount = float(request.form['amount'])
    except:
        return jsonify({'success': False, 'message': 'Montant invalide'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
        wallet = cursor.fetchone()
        balance = wallet['balance'] if wallet else 0

        if amount <= 0 or amount > balance:
            return jsonify({'success': False, 'message': 'Solde insuffisant ou montant invalide'}), 400

        daily_profit = round(amount * 0.1167, 2)
        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id=?", (amount, session['user_id']))

        reference = generate_reference()
        cursor.execute("INSERT INTO investments (user_id, amount, date, profit, status, reference) VALUES (?, ?, ?, ?, ?, ?)",
                       (session['user_id'], amount, datetime.now().strftime("%Y-%m-%d"), daily_profit, "actif", reference))

        cursor.execute("INSERT INTO transactions (user_id, type, amount, reference, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (session['user_id'], "investissement", amount, reference, "réussi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        
        # Récupérer le nouveau solde
        cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
        new_wallet = cursor.fetchone()
        new_balance = new_wallet['balance'] if new_wallet else 0
        
        # Envoyer email d'investissement
        send_investment_email(session['email'], session['full_name'], amount, daily_profit)
        
        return jsonify({
            'success': True, 
            'message': f'Investissement de {amount} Ar réussi ! Profit quotidien: {daily_profit} Ar. Un email de confirmation vous a été envoyé.',
            'new_balance': new_balance
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': 'Erreur lors de l\'investissement'}), 500
    finally:
        conn.close()

@app.route('/depot', methods=['GET', 'POST'])
def depot():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except:
            flash("Montant invalide", "error")
            return redirect('/depot')

        if amount <= 0:
            flash("Le montant doit être positif.", "error")
            return redirect('/depot')

        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE wallets SET balance = balance + ? WHERE user_id=?", (amount, session['user_id']))

            reference = generate_reference()
            cursor.execute("INSERT INTO transactions (user_id, type, amount, reference, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                           (session['user_id'], "dépôt", amount, reference, "réussi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            
            # Envoyer email de confirmation
            send_transaction_email(session['email'], session['full_name'], "dépôt", amount, reference)
            
            flash(f"Dépôt de {amount} Ar effectué avec succès ! Un email de confirmation vous a été envoyé.", "success")
        except Exception as e:
            conn.rollback()
            flash("Erreur lors du dépôt", "error")
        finally:
            conn.close()
            
        return redirect('/dashboard')

    return render_template('depot.html')

@app.route('/retrait', methods=['GET', 'POST'])
def retrait():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT balance FROM wallets WHERE user_id=?", (session['user_id'],))
        wallet = cursor.fetchone()
        balance = wallet['balance'] if wallet else 0
    except:
        balance = 0
    finally:
        conn.close()

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except:
            flash("Montant invalide", "error")
            return redirect('/retrait')

        if amount <= 0 or amount > balance:
            flash("Montant invalide ou solde insuffisant.", "error")
            return redirect('/retrait')

        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id=?", (amount, session['user_id']))

            reference = generate_reference()
            cursor.execute("INSERT INTO transactions (user_id, type, amount, reference, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                           (session['user_id'], "retrait", amount, reference, "réussi", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            
            # Envoyer email de confirmation
            send_transaction_email(session['email'], session['full_name'], "retrait", amount, reference)
            
            flash(f"Retrait de {amount} Ar effectué avec succès ! Un email de confirmation vous a été envoyé.", "success")
        except Exception as e:
            conn.rollback()
            flash("Erreur lors du retrait", "error")
        finally:
            conn.close()
            
        return redirect('/dashboard')

    return render_template('retrait.html', balance=balance)

@app.route('/logout')
def logout():
    session.clear()
    flash("Déconnexion réussie", "info")
    return redirect('/')

# ---------------- ADMIN ----------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
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

    cursor.execute("SELECT id, full_name, email, phone_number, created_at FROM users")
    users = cursor.fetchall()

    cursor.execute("""
        SELECT u.full_name, l.login_time, l.ip_address
        FROM user_logins l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.login_time DESC
        LIMIT 50
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
    from waitress import serve
    port = int(os.environ.get("PORT", 10000))
    
    print("🚀 Anamboary Invest - Server Production")
    print(f"📍 Port: {port}")
    print("📧 Système d'emails activé")
    print("📊 Application efa mety mijery...")
    
    serve(app, host='0.0.0.0', port=port)