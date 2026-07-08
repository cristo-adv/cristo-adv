@echo off
setlocal enabledelayedexpansion
title Deploy Cristo Advogados Associados
color 0B

echo ======================================================
echo    CRISTO ADVOGADOS ASSOCIADOS - DEPLOY AUTOMATICO
echo ======================================================
echo.
echo [!] Iniciando processo de preparacao do ambiente...
echo.

:: 1. Criar pasta do projeto
set PROJECT_DIR=CristoAdv_Deploy
if not exist %PROJECT_DIR% (
    mkdir %PROJECT_DIR%
    echo [+] Pasta %PROJECT_DIR% criada com sucesso.
) else (
    echo [!] Pasta %PROJECT_DIR% ja existe. Limpando arquivos antigos...
    del /q %PROJECT_DIR%\*
)
cd %PROJECT_DIR%

:: 2. Criar app.py (Versao Enxuta e Funcional)
echo [!] Gerando app.py (Flask + SQLite)...

(
echo from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
echo from flask_sqlalchemy import SQLAlchemy
echo from werkzeug.security import generate_password_hash, check_password_hash
echo import datetime
echo.
echo app = Flask(__name__^)
echo app.config['SECRET_KEY'] = 'cristo_secret_key_2024'
echo app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cristo_adv.db'
echo db = SQLAlchemy(app^)
echo.
echo class User(db.Model^):
echo     id = db.Column(db.Integer, primary_key=True^)
echo     email = db.Column(db.String(120^), unique=True, nullable=False^)
echo     password = db.Column(db.String(200^), nullable=False^)
echo.
echo class Processo(db.Model^):
echo     id = db.Column(db.Integer, primary_key=True^)
echo     numero = db.Column(db.String(50^), nullable=False^)
echo     cliente = db.Column(db.String(100^), nullable=False^)
echo     status = db.Column(db.String(50^), default='Ativo'^)
echo.
echo HTML_TEMPLATE = """
echo ^<!DOCTYPE html^>
echo ^<html lang='pt-br'^>
echo ^<head^>
echo     ^<meta charset='UTF-8'^>
echo     ^<title^>Cristo Advogados - Dashboard^</title^>
echo     ^<style^>
echo         :root { --gold: #d4af37; --dark: #0a0a0a; --glass: rgba(255,255,255,0.1^); }
echo         body { background: var(--dark^); color: white; font-family: 'Segoe UI', sans-serif; margin: 0; overflow-x: hidden; }
echo         .navbar { background: rgba(0,0,0,0.8^); padding: 20px; border-bottom: 1px solid var(--gold^); display: flex; justify-content: space-between; }
echo         .container { padding: 40px; }
echo         .card { background: var(--glass^); border-radius: 15px; padding: 20px; border: 1px solid rgba(212,175,55,0.3^); margin-bottom: 20px; backdrop-filter: blur(10px^); }
echo         h1, h2 { color: var(--gold^); text-transform: uppercase; letter-spacing: 2px; }
echo         .btn { background: var(--gold^); color: black; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; font-weight: bold; }
echo         .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr^)^); gap: 20px; }
echo         input { background: transparent; border: 1px solid var(--gold^); color: white; padding: 10px; border-radius: 5px; width: 100%%; margin-bottom: 10px; }
echo     ^</style^>
echo ^</head^>
echo ^<body^>
echo     ^<div class='navbar'^>
echo         ^<div style='font-size: 24px; font-weight: bold; color: var(--gold^);'^>CRISTO ADVOGADOS^</div^>
echo         ^<div^>^<a href='/logout' style='color: white;'^>Sair^</a^>^</div^>
echo     ^</div^>
echo     ^<div class='container'^>
echo         ^<h1^>Bem-vindo ao Sistema de Gestao^</h1^>
echo         ^<div class='grid'^>
echo             ^<div class='card'^>^<h2^>Processos^</h2^>^<p^>Total: {{ processos^|length }}^</p^>^</div^>
echo             ^<div class='card'^>^<h2^>Financeiro^</h2^>^<p^>Status: Em dia^</p^>^</div^>
echo             ^<div class='card'^>^<h2^>Agenda^</h2^>^<p^>3 Audiencias hoje^</p^>^</div^>
echo         ^</div^>
echo         ^<div class='card'^>
echo             ^<h2^>Novo Processo^</h2^>
echo             ^<form method='POST' action='/api/processos'^>
echo                 ^<input name='numero' placeholder='Numero do Processo' required^>
echo                 ^<input name='cliente' placeholder='Nome do Cliente' required^>
echo                 ^<button type='submit' class='btn'^>Cadastrar^</button^>
echo             ^</form^>
echo         ^</div^>
echo         ^<div class='card'^>
echo             ^<h2^>Lista de Processos^</h2^>
echo             ^<ul^>
echo                 {%% for p in processos %%^}
echo                 ^<li^>{{ p.numero }} - {{ p.cliente }} ({{ p.status }}^)^</li^>
echo                 {%% endfor %%^}
echo             ^</ul^>
echo         ^</div^>
echo     ^</div^>
echo ^</body^>
echo ^</html^>
echo """
echo.
echo @app.route('/'^)
echo def index(^):
echo     if 'user' not in session: return redirect(url_for('login'^)^)
echo     procs = Processo.query.all(^)
echo     return render_template_string(HTML_TEMPLATE, processos=procs^)
echo.
echo @app.route('/login', methods=['GET', 'POST']^)
echo def login(^):
echo     if request.method == 'POST':
echo         if request.form['email'] == 'admin@cristo.adv.br' and request.form['password'] == 'admin':
echo             session['user'] = 'admin'
echo             return redirect(url_for('index'^)^)
echo     return """^<body style='background:#0a0a0a; color:white; display:flex; align-items:center; justify-content:center; height:100vh; font-family:sans-serif;'^>
echo            ^<form method='POST' style='background:rgba(255,255,255,0.1^); padding:40px; border-radius:10px; border:1px solid #d4af37;'^>
echo            ^<h2 style='color:#d4af37'^>CRISTO ADVOGADOS^</h2^>
echo            ^<input name='email' placeholder='Email' style='display:block; margin-bottom:10px; padding:10px; width:200px;'^>
echo            ^<input name='password' type='password' placeholder='Senha' style='display:block; margin-bottom:20px; padding:10px; width:200px;'^>
echo            ^<button style='background:#d4af37; border:none; padding:10px; width:100%%; cursor:pointer;'^>Entrar^</button^>
echo            ^</form^>^</body^>"""
echo.
echo @app.route('/logout'^)
echo def logout(^):
echo     session.pop('user', None^)
echo     return redirect(url_for('login'^)^)
echo.
echo @app.route('/api/processos', methods=['POST']^)
echo def add_processo(^):
echo     new_p = Processo(numero=request.form['numero'], cliente=request.form['cliente']^)
echo     db.session.add(new_p^)
echo     db.session.commit(^)
echo     return redirect(url_for('index'^)^)
echo.
echo if __name__ == '__main__':
echo     with app.app_context(^):
echo         db.create_all(^)
echo     app.run(debug=True^)
) > app.py

:: 3. Criar requirements.txt
echo [!] Criando requirements.txt...
(
echo flask
echo flask-sqlalchemy
echo gunicorn
) > requirements.txt

:: 4. Criar Procfile
echo [!] Criando Procfile...
echo web: gunicorn app:app > Procfile

:: 5. Criar render.yaml
echo [!] Criando render.yaml...
(
echo services:
echo   - type: web
echo     name: cristo-adv-associados
echo     env: python
echo     buildCommand: pip install -r requirements.txt
echo     startCommand: gunicorn app:app
echo     envVars:
echo       - key: PYTHON_VERSION
echo         value: 3.10.0
) > render.yaml

echo.
echo [OK] Arquivos do projeto gerados com sucesso!
echo.

:: 6. Git Setup
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [X] Erro: Git nao encontrado no PATH. Por favor, instale o Git.
    pause
    exit
)

echo [!] Inicializando Git...
git init
git add .
git commit -m "Initial deploy Cristo Advogados"

echo.
echo ======================================================
echo    CONFIGURACAO DO GITHUB
echo ======================================================
set /p GITHUB_USER="Digite seu nome de usuario do GitHub: "
set /p REPO_NAME="Digite o nome do repositorio (ex: cristo-adv): "

echo.
echo [!] Para finalizar o deploy, siga estes passos:
echo 1. Va para: https://github.com/new
echo 2. Crie um repositorio chamado: %REPO_NAME%
echo 3. Execute os comandos abaixo no terminal:
echo.
echo    git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 4. Apos o push, va para https://render.com
echo 5. Crie um 'New Web Service' e conecte seu repo '%REPO_NAME%'
echo 6. O Render detectara o 'render.yaml' e fara tudo sozinho!
echo.
echo ======================================================
echo    PROCESSO CONCLUIDO COM SUCESSO! 
echo ======================================================
pause