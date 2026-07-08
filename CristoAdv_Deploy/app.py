from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cristo_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cristo_adv.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Processo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Ativo')

HTML_TEMPLATE = """
<DOCTYPE html>
<html lang='pt-br'>
<head>
    <meta charset='UTF-8'>
    <title>Cristo Advogados - Dashboard</title>
    <style>
        :root { --gold: #d4af37; --dark: #0a0a0a; --glass: rgba(255,255,255,0.1); }
        body { background: var(--dark); color: white; font-family: 'Segoe UI', sans-serif; margin: 0; overflow-x: hidden; }
        .navbar { background: rgba(0,0,0,0.8); padding: 20px; border-bottom: 1px solid var(--gold); display: flex; justify-content: space-between; }
        .container { padding: 40px; }
        .card { background: var(--glass); border-radius: 15px; padding: 20px; border: 1px solid rgba(212,175,55,0.3); margin-bottom: 20px; backdrop-filter: blur(10px); }
        h1, h2 { color: var(--gold); text-transform: uppercase; letter-spacing: 2px; }
        .btn { background: var(--gold); color: black; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        input { background: transparent; border: 1px solid var(--gold); color: white; padding: 10px; border-radius: 5px; width: 100%; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class='navbar'>
        <div style='font-size: 24px; font-weight: bold; color: var(--gold);'>CRISTO ADVOGADOS</div>
        <div><a href='/logout' style='color: white;'>Sair</a></div>
    </div>
    <div class='container'>
        <h1>Bem-vindo ao Sistema de Gestao</h1>
        <div class='grid'>
            <div class='card'><h2>Processos</h2><p>Total: {{ processos|length }}</p></div>
            <div class='card'><h2>Financeiro</h2><p>Status: Em dia</p></div>
            <div class='card'><h2>Agenda</h2><p>3 Audiencias hoje</p></div>
        </div>
        <div class='card'>
            <h2>Novo Processo</h2>
            <form method='POST' action='/api/processos'>
                <input name='numero' placeholder='Numero do Processo' required>
                <input name='cliente' placeholder='Nome do Cliente' required>
                <button type='submit' class='btn'>Cadastrar</button>
            </form>
        </div>
        <div class='card'>
            <h2>Lista de Processos</h2>
            <ul>
                {% for p in processos %}
                <li>{{ p.numero }} - {{ p.cliente }} ({{ p.status }})</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    procs = Processo.query.all()
    return render_template_string(HTML_TEMPLATE, processos=procs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['email'] == 'admin@cristo.adv.br' and request.form['password'] == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('index'))
    return """^<body style='background:#0a0a0a; color:white; display:flex; align-items:center; justify-content:center; height:100vh; font-family:sans-serif;'^>
           <form method='POST' style='background:rgba(255,255,255,0.1); padding:40px; border-radius:10px; border:1px solid #d4af37;'>
           <h2 style='color:#d4af37'>CRISTO ADVOGADOS</h2>
           <input name='email' placeholder='Email' style='display:block; margin-bottom:10px; padding:10px; width:200px;'>
           <input name='password' type='password' placeholder='Senha' style='display:block; margin-bottom:20px; padding:10px; width:200px;'>
           <button style='background:#d4af37; border:none; padding:10px; width:100%; cursor:pointer;'>Entrar</button>
           </form></body>"""

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/api/processos', methods=['POST'])
def add_processo():
    new_p = Processo(numero=request.form['numero'], cliente=request.form['cliente'])
    db.session.add(new_p)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
