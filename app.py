import os
from datetime import datetime, date
from functools import wraps
from flask import Flask, request, session, redirect, url_for, jsonify, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'cristo_adv.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'cristo-adv-secret-key-2024'
db = SQLAlchemy(app)

# ===================== MODELS =====================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    admin = db.Column(db.Boolean, default=False)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(2), default='pf')
    cpf_cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    endereco = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

class Processo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_cnj = db.Column(db.String(60), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    parte_contraria = db.Column(db.String(150))
    area = db.Column(db.String(80))
    status = db.Column(db.String(20), default='Ativo')
    advogado = db.Column(db.String(120))
    data_distribuicao = db.Column(db.Date)
    valor_causa = db.Column(db.Float, default=0.0)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    andamentos = db.relationship('Andamento', backref='processo', lazy=True, cascade='all, delete-orphan')

class Andamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey('processo.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    descricao = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

class ContaReceber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    cliente_nome = db.Column(db.String(150))
    valor = db.Column(db.Float, nullable=False, default=0.0)
    data_vencimento = db.Column(db.Date)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')

class ContaPagar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    fornecedor = db.Column(db.String(150))
    valor = db.Column(db.Float, nullable=False, default=0.0)
    data_vencimento = db.Column(db.Date)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')

class Colaborador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cargo = db.Column(db.String(80))
    salario = db.Column(db.Float, default=0.0)
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    status = db.Column(db.String(20), default='ativo')

# ===================== HELPERS =====================
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Não autenticado'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

def current_user():
    if 'user_id' in session:
        return Usuario.query.get(session['user_id'])
    return None

def fmt_date(d):
    if not d:
        return ''
    if isinstance(d, str):
        return d
    return d.strftime('%d/%m/%Y')

def fmt_money(v):
    if v is None:
        return 'R$ 0,00'
    return 'R$ ' + format(float(v), ',.2f').replace(',', 'X').replace('.', ',').replace('X', '.')

def init_db():
    db.create_all()
    if not Usuario.query.filter_by(email='admin@cristo.adv.br').first():
        u = Usuario(nome='Administrador', email='admin@cristo.adv.br',
                    senha_hash=generate_password_hash('admin'), admin=True)
        db.session.add(u)
        db.session.commit()

# ===================== SHARED CSS =====================
BASE_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root{
  --bg:#0a0a12; --bg2:#12121f; --gold:#d4af37; --gold-soft:#b8941f;
  --glass:rgba(255,255,255,0.04); --glass-border:rgba(212,175,55,0.25);
  --text:#e8e8f0; --muted:#8a8aa0; --green:#22c55e; --yellow:#eab308; --gray:#6b7280; --red:#ef4444;
}
body{
  font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text);
  min-height:100vh; overflow-x:hidden; position:relative;
}
body::before{
  content:''; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:linear-gradient(rgba(212,175,55,0.06) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(212,175,55,0.06) 1px,transparent 1px);
  background-size:40px 40px; animation:gridMove 20s linear infinite;
}
@keyframes gridMove{ from{background-position:0 0;} to{background-position:40px 40px;} }
body::after{
  content:''; position:fixed; top:-200px; left:50%; transform:translateX(-50%);
  width:600px; height:600px; background:radial-gradient(circle,rgba(212,175,55,0.12),transparent 70%);
  z-index:0; pointer-events:none; filter:blur(40px);
}
.glass{ background:var(--glass); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  border:1px solid var(--glass-border); border-radius:16px; }
.navbar{ position:fixed; top:0; left:0; right:0; z-index:100; padding:14px 28px;
  display:flex; align-items:center; justify-content:space-between;
  background:rgba(10,10,18,0.6); backdrop-filter:blur(16px); border-bottom:1px solid var(--glass-border); }
.navbar .brand{ font-size:20px; font-weight:700; color:var(--gold); letter-spacing:1px; }
.navbar .brand span{ color:var(--text); font-weight:300; }
.navbar .nav-links{ display:flex; gap:18px; align-items:center; }
.navbar a{ color:var(--text); text-decoration:none; font-size:14px; transition:.2s; }
.navbar a:hover{ color:var(--gold); }
.btn-gold{ background:linear-gradient(135deg,var(--gold),var(--gold-soft)); color:#0a0a12;
  border:none; padding:10px 20px; border-radius:10px; font-weight:600; cursor:pointer; transition:.2s; }
.btn-gold:hover{ box-shadow:0 0 20px rgba(212,175,55,0.5); transform:translateY(-1px); }
.btn-ghost{ background:transparent; color:var(--gold); border:1px solid var(--gold);
  padding:8px 16px; border-radius:10px; cursor:pointer; transition:.2s; }
.btn-ghost:hover{ background:rgba(212,175,55,0.1); }
.btn-danger{ background:transparent; color:var(--red); border:1px solid var(--red);
  padding:6px 12px; border-radius:8px; cursor:pointer; font-size:13px; transition:.2s; }
.btn-danger:hover{ background:rgba(239,68,68,0.15); }
.layout{ display:flex; min-height:100vh; padding-top:70px; position:relative; z-index:1; }
.sidebar{ width:240px; min-height:calc(100vh - 70px); padding:24px 16px; transition:.3s;
  background:rgba(18,18,31,0.5); backdrop-filter:blur(14px); border-right:1px solid var(--glass-border); }
.sidebar.collapsed{ width:64px; }
.sidebar.collapsed .menu-text{ display:none; }
.sidebar h3{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:2px; margin:18px 10px 8px; }
.sidebar a{ display:flex; align-items:center; gap:12px; padding:12px 14px; color:var(--text);
  text-decoration:none; border-radius:10px; margin-bottom:4px; transition:.2s; font-size:14px; }
.sidebar a:hover, .sidebar a.active{ background:rgba(212,175,55,0.12); color:var(--gold); border-left:3px solid var(--gold); }
.sidebar .icon{ font-size:18px; width:24px; text-align:center; }
.content{ flex:1; padding:28px; }
.card{ padding:22px; margin-bottom:20px; }
.page-title{ font-size:24px; color:var(--gold); margin-bottom:20px; font-weight:600; }
.grid{ display:grid; gap:18px; }
.grid-4{ grid-template-columns:repeat(4,1fr); }
.grid-3{ grid-template-columns:repeat(3,1fr); }
.grid-2{ grid-template-columns:repeat(2,1fr); }
@media(max-width:900px){ .grid-4{ grid-template-columns:repeat(2,1fr);} .grid-3,.grid-2{ grid-template-columns:1fr;} }
.stat-card{ padding:22px; }
.stat-card .label{ color:var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:1px; }
.stat-card .value{ font-size:32px; color:var(--gold); font-weight:700; margin-top:8px; }
.stat-card .icon{ font-size:28px; float:right; opacity:.5; }
table{ width:100%; border-collapse:collapse; }
th{ text-align:left; padding:12px 14px; color:var(--gold); font-size:12px; text-transform:uppercase; letter-spacing:1px; border-bottom:1px solid var(--glass-border); }
td{ padding:12px 14px; border-bottom:1px solid rgba(255,255,255,0.05); font-size:14px; }
tr:nth-child(even) td{ background:rgba(255,255,255,0.02); }
tr:hover td{ background:rgba(212,175,55,0.06); }
.badge{ padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600; text-transform:uppercase; }
.badge-green{ background:rgba(34,197,94,0.15); color:var(--green); border:1px solid var(--green); }
.badge-yellow{ background:rgba(234,179,8,0.15); color:var(--yellow); border:1px solid var(--yellow); }
.badge-gray{ background:rgba(107,114,128,0.15); color:var(--gray); border:1px solid var(--gray); }
.badge-red{ background:rgba(239,68,68,0.15); color:var(--red); border:1px solid var(--red); }
.form-group{ margin-bottom:16px; }
.form-group label{ display:block; color:var(--muted); font-size:13px; margin-bottom:6px; }
input,select,textarea{
  width:100%; padding:11px 14px; background:rgba(10,10,18,0.6); border:1px solid rgba(255,255,255,0.1);
  border-radius:10px; color:var(--text); font-size:14px; transition:.2s; }
input:focus,select:focus,textarea:focus{ outline:none; border-color:var(--gold); box-shadow:0 0 0 3px rgba(212,175,55,0.15); }
.modal-bg{ position:fixed; inset:0; background:rgba(0,0,0,0.7); backdrop-filter:blur(4px); z-index:200;
  display:none; align-items:center; justify-content:center; padding:20px; }
.modal-bg.show{ display:flex; }
.modal{ width:100%; max-width:560px; padding:28px; max-height:90vh; overflow-y:auto; }
.modal h2{ color:var(--gold); margin-bottom:18px; }
.modal-actions{ display:flex; gap:10px; justify-content:flex-end; margin-top:20px; }
.toast{ position:fixed; bottom:24px; right:24px; z-index:300; padding:14px 20px; border-radius:10px;
  background:rgba(18,18,31,0.95); border:1px solid var(--gold); color:var(--text); transform:translateX(120%); transition:.3s; }
.toast.show{ transform:translateX(0); }
.toast.success{ border-color:var(--green); }
.toast.error{ border-color:var(--red); }
.timeline{ list-style:none; }
.timeline li{ padding:12px 0 12px 24px; border-left:2px solid var(--glass-border); position:relative; }
.timeline li::before{ content:''; position:absolute; left:-6px; top:16px; width:10px; height:10px; border-radius:50%; background:var(--gold); box-shadow:0 0 8px var(--gold); }
.timeline .date{ color:var(--muted); font-size:12px; }
.timeline .desc{ color:var(--text); margin-top:4px; }
.menu-toggle{ background:transparent; border:none; color:var(--gold); font-size:22px; cursor:pointer; }
@media(max-width:768px){ .sidebar{ position:fixed; left:0; top:70px; z-index:90; width:240px; transform:translateX(-100%); } .sidebar.open{ transform:translateX(0);} .content{ padding:16px; } }
"""

# ===================== SHARED JS =====================
BASE_JS = """
function toast(msg, type='success'){
  let t=document.createElement('div'); t.className='toast '+type; t.textContent=msg; document.body.appendChild(t);
  setTimeout(()=>t.classList.add('show'),50); setTimeout(()=>{t.classList.remove('show'); setTimeout(()=>t.remove(),300);},3000);
}
function openModal(id){ document.getElementById(id).classList.add('show'); }
function closeModal(id){ document.getElementById(id).classList.remove('show'); }
async function api(url, method='GET', data=null){
  let opt={method, headers:{'Content-Type':'application/json'}};
  if(data) opt.body=JSON.stringify(data);
  let r=await fetch(url, opt);
  if(!r.ok){ let e=await r.json().catch(()=>({})); throw new Error(e.error||'Erro'); }
  return r.json();
}
function toggleSidebar(){ document.getElementById('sidebar').classList.toggle('open'); document.getElementById('sidebar').classList.toggle('collapsed'); }
"""

# ===================== LANDING =====================
LANDING = """
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cristo Advogados Associados</title>
<style>""" + BASE_CSS + """
.hero{ min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:40px; position:relative; z-index:1; }
.hero h1{ font-size:54px; color:var(--gold); margin-bottom:16px; letter-spacing:2px; }
.hero h1 span{ color:var(--text); font-weight:300; }
.hero p{ font-size:18px; color:var(--muted); max-width:600px; margin-bottom:32px; line-height:1.6; }
.hero .cta{ display:flex; gap:16px; }
.features{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px; max-width:1000px; margin:40px auto; padding:0 20px; position:relative; z-index:1; }
@media(max-width:768px){ .features{ grid-template-columns:1fr; } .hero h1{ font-size:36px; } }
.feature{ padding:28px; text-align:center; }
.feature .icon{ font-size:40px; color:var(--gold); margin-bottom:14px; }
.feature h3{ color:var(--text); margin-bottom:8px; }
.feature p{ color:var(--muted); font-size:14px; line-height:1.5; }
.footer{ text-align:center; padding:30px; color:var(--muted); font-size:13px; position:relative; z-index:1; border-top:1px solid var(--glass-border); }
</style></head><body>
<div class="navbar">
  <div class="brand">CRISTO <span>Advogados Associados</span></div>
  <div class="nav-links">
    <a href="#features">Serviços</a>
    <a href="#sobre">Sobre</a>
    <a href="{{ url_for('login') }}" class="btn-gold">Acessar Sistema</a>
  </div>
</div>
<section class="hero">
  <h1>CRISTO <span>Advogados Associados</span></h1>
  <p>Direito com excelência, tecnologia e dedicação. Gestão jurídica inteligente para resultados extraordinários.</p>
  <div class="cta">
    <a href="{{ url_for('login') }}" class="btn-gold">Entrar no Sistema</a>
    <a href="#features" class="btn-ghost">Nossos Serviços</a>
  </div>
</section>
<section class="features" id="features">
  <div class="feature glass">
    <div class="icon">⚖️</div><h3>Direito Civil</h3><p>Atuação em causas cíveis, contratos e responsabilidade civil.</p>
  </div>
  <div class="feature glass">
    <div class="icon">🏢</div><h3>Direito Empresarial</h3><p>Assessoria jurídica para empresas e sociedades.</p>
  </div>
  <div class="feature glass">
    <div class="icon">👨‍👩‍👧</div><h3>Direito de Família</h3><p>Suporte em divórcios, guarda e inventários com sensibilidade.</p>
  </div>
</section>
<div class="footer" id="sobre">
  © 2024 Cristo Advogados Associados · OAB/BR · Todos os direitos reservados
</div>
</body></html>
"""

# ===================== LOGIN =====================
LOGIN = """
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login · Cristo Advogados</title>
<style>""" + BASE_CSS + """
.login-wrap{ min-height:100vh; display:flex; align-items:center; justify-content:center; padding:20px; position:relative; z-index:1; }
.login-card{ width:100%; max-width:400px; padding:40px; }
.login-card h1{ color:var(--gold); text-align:center; font-size:24px; margin-bottom:6px; }
.login-card p{ color:var(--muted); text-align:center; margin-bottom:28px; font-size:14px; }
.login-card .logo{ text-align:center; font-size:40px; margin-bottom:10px; }
.error{ color:var(--red); text-align:center; margin-bottom:16px; font-size:14px; }
.hint{ margin-top:18px; padding:12px; background:rgba(212,175,55,0.08); border:1px dashed var(--gold); border-radius:8px; font-size:12px; color:var(--muted); text-align:center; }
</style></head><body>
<div class="login-wrap">
  <div class="login-card glass">
    <div class="logo">⚖️</div>
    <h1>CRISTO ADVOGADOS</h1>
    <p>Sistema de Gestão Jurídica</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST">
      <div class="form-group"><label>Email</label><input type="email" name="email" required value="admin@cristo.adv.br"></div>
      <div class="form-group"><label>Senha</label><input type="password" name="senha" required value="admin"></div>
      <button type="submit" class="btn-gold" style="width:100%">Entrar</button>
    </form>
    <div class="hint">Acesso padrão: admin@cristo.adv.br / admin</div>
  </div>
</div>
</body></html>
"""

# ===================== ADMIN LAYOUT =====================
def admin_page(title, active, content_html, extra_head='', extra_js=''):
    user = current_user()
    return f"""
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Cristo Advogados</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>{BASE_CSS}</style>
{extra_head}
</head><body>
<div class="navbar">
  <div style="display:flex;align-items:center;gap:14px;">
    <button class="menu-toggle" onclick="toggleSidebar()">☰</button>
    <div class="brand">CRISTO <span>Advogados</span></div>
  </div>
  <div class="nav-links">
    <span style="color:var(--muted);font-size:13px;">{user.nome if user else ''}</span>
    <a href="{{ url_for('logout') }}" class="btn-ghost">Sair</a>
  </div>
</div>
<div class="layout">
  <div class="sidebar" id="sidebar">
    <h3>Menu</h3>
    <a href="{{ url_for('admin') }}" class="{'active' if active=='dashboard' else ''}"><span class="icon">📊</span><span class="menu-text">Dashboard</span></a>
    <a href="{{ url_for('admin_clientes') }}" class="{'active' if active=='clientes' else ''}"><span class="icon">👥</span><span class="menu-text">Clientes</span></a>
    <a href="{{ url_for('admin_processos') }}" class="{'active' if active=='processos' else ''}"><span class="icon">⚖️</span><span class="menu-text">Processos</span></a>
    <a href="{{ url_for('admin_financeiro') }}" class="{'active' if active=='financeiro' else ''}"><span class="icon">💰</span><span class="menu-text">Financeiro</span></a>
    <a href="{{ url_for('admin_pessoal') }}" class="{'active' if active=='pessoal' else ''}"><span class="icon">🧑‍💼</span><span class="menu-text">Pessoal</span></a>
    <a href="{{ url_for('admin_config') }}" class="{'active' if active=='config' else ''}"><span class="icon">⚙️</span><span class="menu-text">Configurações</span></a>
  </div>
  <div class="content">
    {content_html}
  </div>
</div>
<script>{BASE_JS}</script>
{extra_js}
</body></html>
"""

# ===================== ROUTES - AUTH =====================
@app.route('/')
def index():
    return render_template_string(LANDING)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        senha = request.form.get('senha', '')
        u = Usuario.query.filter_by(email=email).first()
        if u and check_password_hash(u.senha_hash, senha):
            session['user_id'] = u.id
            return redirect(url_for('admin'))
        return render_template_string(LOGIN, error='Email ou senha inválidos')
    return render_template_string(LOGIN, error=None)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# ===================== ADMIN PAGES =====================
@app.route('/admin')
@login_required
def admin():
    content = """
    <h1 class="page-title">Dashboard</h1>
    <div class="grid grid-4">
      <div class="stat-card glass"><span class="icon">👥</span><div class="label">Total Clientes</div><div class="value" id="st-clientes">0</div></div>
      <div class="stat-card glass"><span class="icon">⚖️</span><div class="label">Processos Ativos</div><div class="value" id="st-ativos">0</div></div>
      <div class="stat-card glass"><span class="icon">📦</span><div class="label">Processos Arquivados</div><div class="value" id="st-arquivados">0</div></div>
      <div class="stat-card glass"><span class="icon">💰</span><div class="label">Receita do Mês</div><div class="value" id="st-receita">R$ 0,00</div></div>
    </div>
    <div class="grid grid-2" style="margin-top:20px;">
      <div class="card glass">
        <h3 style="color:var(--gold);margin-bottom:16px;">Processos por Status</h3>
        <canvas id="chartStatus" height="180"></canvas>
      </div>
      <div class="card glass">
        <h3 style="color:var(--gold);margin-bottom:16px;">Últimos Andamentos</h3>
        <ul class="timeline" id="timeline"></ul>
      </div>
    </div>
    <div class="card glass" style="margin-top:20px;">
      <h3 style="color:var(--gold);margin-bottom:16px;">Contas a Receber do Mês</h3>
      <table><thead><tr><th>Descrição</th><th>Cliente</th><th>Vencimento</th><th>Valor</th><th>Status</th></tr></thead>
      <tbody id="receber-mes"></tbody></table>
    </div>
    """
    js = """
    let chart;
    async function loadDashboard(){
      try{
        let d=await api('/api/dashboard');
        document.getElementById('st-clientes').textContent=d.total_clientes;
        document.getElementById('st-ativos').textContent=d.processos_ativos;
        document.getElementById('st-arquivados').textContent=d.processos_arquivados;
        document.getElementById('st-receita').textContent=d.receita_mes;
        const ctx=document.getElementById('chartStatus').getContext('2d');
        if(chart) chart.destroy();
        chart=new Chart(ctx,{type:'bar',data:{labels:Object.keys(d.por_status),datasets:[{label:'Processos',data:Object.values(d.por_status),backgroundColor:'#d4af37',borderColor:'#d4af37',borderRadius:8}]},options:{plugins:{legend:{labels:{color:'#e8e8f0'}}},scales:{x:{ticks:{color:'#8a8aa0'},grid:{color:'rgba(255,255,255,0.05)'}},y:{ticks:{color:'#8a8aa0'},grid:{color:'rgba(255,255,255,0.05)'},beginAtZero:true}}}});
        let tl=document.getElementById('timeline'); tl.innerHTML=d.andamentos.map(a=>`<li><div class="date">${a.data} · ${a.processo}</div><div class="desc">${a.descricao}</div></li>`).join('') || '<li style="border:none;color:var(--muted)">Nenhum andamento</li>';
        let rb=document.getElementById('receber-mes'); rb.innerHTML=d.receber_mes_lista.map(r=>`<tr><td>${r.descricao}</td><td>${r.cliente_nome||'-'}</td><td>${r.data_vencimento}</td><td>${r.valor}</td><td><span class="badge ${r.status=='recebido'?'badge-green':'badge-yellow'}">${r.status}</span></td></tr>`).join('') || '<tr><td colspan=5 style="color:var(--muted);text-align:center">Nenhuma conta</td></tr>';
      }catch(e){ toast(e.message,'error'); }
    }
    loadDashboard();
    """
    return render_template_string(admin_page('Dashboard', 'dashboard', content, extra_js=js))

@app.route('/admin/clientes')
@login_required
def admin_clientes():
    content = """
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h1 class="page-title" style="margin:0">Clientes</h1>
      <button class="btn-gold" onclick="openModal('modalCliente')">+ Novo Cliente</button>
    </div>
    <div class="card glass">
      <table><thead><tr><th>Nome</th><th>Tipo</th><th>CPF/CNPJ</th><th>Telefone</th><th>Email</th><th>Ações</th></tr></thead>
      <tbody id="tb-clientes"></tbody></table>
    </div>
    <div class="modal-bg" id="modalCliente">
      <div class="modal glass">
        <h2>Novo Cliente</h2>
        <input type="hidden" id="cl_id">
        <div class="form-group"><label>Nome</label><input id="cl_nome"></div>
        <div class="grid grid-2">
          <div class="form-group"><label>Tipo</label><select id="cl_tipo"><option value="pf">Pessoa Física</option><option value="pj">Pessoa Jurídica</option></select></div>
          <div class="form-group"><label>CPF/CNPJ</label><input id="cl_cpf"></div>
        </div>
        <div class="grid grid-2">
          <div class="form-group"><label>Telefone</label><input id="cl_tel"></div>
          <div class="form-group"><label>Email</label><input id="cl_email"></div>
        </div>
        <div class="form-group"><label>Endereço</label><textarea id="cl_end"></textarea></div>
        <div class="modal-actions"><button class="btn-ghost" onclick="closeModal('modalCliente')">Cancelar</button><button class="btn-gold" onclick="saveCliente()">Salvar</button></div>
      </div>
    </div>
    """
    js = """
    async function loadClientes(){
      try{ let d=await api('/api/clientes');
        document.getElementById('tb-clientes').innerHTML=d.map(c=>`<tr><td>${c.nome}</td><td>${c.tipo=='pf'?'PF':'PJ'}</td><td>${c.cpf_cnpj||'-'}</td><td>${c.telefone||'-'}</td><td>${c.email||'-'}</td><td><button class="btn-ghost" onclick="editCliente(${JSON.stringify(c).replace(/"/g,'&quot;')})">Editar</button> <button class="btn-danger" onclick="delCliente(${c.id})">Excluir</button></td></tr>`).join('')||'<tr><td colspan=6 style="color:var(--muted);text-align:center">Nenhum cliente</td></tr>';
      }catch(e){ toast(e.message,'error'); }
    }
    function editCliente(c){ document.getElementById('cl_id').value=c.id; document.getElementById('cl_nome').value=c.nome; document.getElementById('cl_tipo').value=c.tipo; document.getElementById('cl_cpf').value=c.cpf_cnpj||''; document.getElementById('cl_tel').value=c.telefone||''; document.getElementById('cl_email').value=c.email||''; document.getElementById('cl_end').value=c.endereco||''; openModal('modalCliente'); }
    async function saveCliente(){
      let id=document.getElementById('cl_id').value;
      let data={nome:cl_nome.value,tipo:cl_tipo.value,cpf_cnpj:cl_cpf.value,telefone:cl_tel.value,email:cl_email.value,endereco:cl_end.value};
      try{ if(id){ await api('/api/clientes','POST',{...data,id:parseInt(id)}); } else { await api('/api/clientes','POST',data); } closeModal('modalCliente'); toast('Cliente salvo!'); loadClientes(); resetForm(); }catch(e){ toast(e.message,'error'); }
    }
    function resetForm(){ ['cl_id','cl_nome','cl_cpf','cl_tel','cl_email','cl_end'].forEach(i=>document.getElementById(i).value=''); }
    async function delCliente(id){ if(!confirm('Excluir cliente?'))return; try{ await api('/api/clientes/'+id,'DELETE'); toast('Excluído!'); loadClientes(); }catch(e){ toast(e.message,'error'); } }
    loadClientes();
    """
    return render_template_string(admin_page('Clientes', 'clientes', content, extra_js=js))

@app.route('/admin/processos')
@login_required
def admin_processos():
    content = """
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h1 class="page-title" style="margin:0">Processos</h1>
      <button class="btn-gold" onclick="openModal('modalProc')">+ Novo Processo</button>
    </div>
    <div class="card glass">
      <table><thead><tr><th>Número CNJ</th><th>Cliente</th><th>Parte Contrária</th><th>Área</th><th>Status</th><th>Advogado</th><th>Valor</th><th>Ações</th></tr></thead>
      <tbody id="tb-proc"></tbody></table>
    </div>
    <div class="modal-bg" id="modalProc">
      <div class="modal glass">
        <h2>Novo Processo</h2>
        <input type="hidden" id="pr_id">
        <div class="form-group"><label>Número CNJ</label><input id="pr_cnj"></div>
        <div class="form-group"><label>Cliente</label><select id="pr_cliente"></select></div>
        <div class="grid grid-2">
          <div class="form-group"><label>Parte Contrária</label><input id="pr_parte"></div>
          <div class="form-group"><label>Área</label><input id="pr_area"></div>
        </div>
        <div class="grid grid-2">
          <div class="form-group"><label>Status</label><select id="pr_status"><option>Ativo</option><option>Suspenso</option><option>Arquivado</option></select></div>
          <div class="form-group"><label>Advogado</label><input id="pr_adv"></div>
        </div>
        <div class="grid grid-2">
          <div class="form-group"><label>Data Distribuição</label><input type="date" id="pr_data"></div>
          <div class="form-group"><label>Valor da Causa</label><input type="number" step="0.01" id="pr_valor"></div>
        </div>
        <div class="modal-actions"><button class="btn-ghost" onclick="closeModal('modalProc')">Cancelar</button><button class="btn-gold" onclick="saveProc()">Salvar</button></div>
      </div>
    </div>
    <div class="modal-bg" id="modalAnd">
      <div class="modal glass">
        <h2>Andamentos</h2>
        <input type="hidden" id="and_proc_id">
        <ul class="timeline" id="and-list" style="margin-bottom:16px;"></ul>
        <div class="form-group"><label>Novo Andamento</label><textarea id="and_desc"></textarea></div>
        <div class="modal-actions"><button class="btn-ghost" onclick="closeModal('modalAnd')">Fechar</button><button class="btn-gold" onclick="addAnd()">Adicionar</button></div>
      </div>
    </div>
    """
    js = """
    let clientesCache=[];
    async function loadProc(){
      try{ let d=await api('/api/processos'); clientesCache=d.clientes||[];
        let sel=document.getElementById('pr_cliente'); sel.innerHTML=clientesCache.map(c=>`<option value="${c.id}">${c.nome}</option>`).join('');
        document.getElementById('tb-proc').innerHTML=d.processos.map(p=>`<tr><td>${p.numero_cnj}</td><td>${p.cliente_nome||'-'}</td><td>${p.parte_contraria||'-'}</td><td>${p.area||'-'}</td><td><span class="badge ${p.status=='Ativo'?'badge-green':p.status=='Suspenso'?'badge-yellow':'badge-gray'}">${p.status}</span></td><td>${p.advogado||'-'}</td><td>${p.valor_causa}</td><td><button class="btn-ghost" onclick="editProc(${JSON.stringify(p).replace(/"/g,'&quot;')})">Editar</button> <button class="btn-ghost" onclick="openAnd(${p.id})">Andamentos</button> <button class="btn-danger" onclick="delProc(${p.id})">Excluir</button></td></tr>`).join('')||'<tr><td colspan=8 style="color:var(--muted);text-align:center">Nenhum processo</td></tr>';
      }catch(e){ toast(e.message,'error'); }
    }
    function editProc(p){ document.getElementById('pr_id').value=p.id; document.getElementById('pr_cnj').value=p.numero_cnj; document.getElementById('pr_cliente').value=p.cliente_id||''; document.getElementById('pr_parte').value=p.parte_contraria||''; document.getElementById('pr_area').value=p.area||''; document.getElementById('pr_status').value=p.status; document.getElementById('pr_adv').value=p.advogado||''; document.getElementById('pr_data').value=p.data_distribuicao||''; document.getElementById('pr_valor').value=p.valor_causa_num||''; openModal('modalProc'); }
    async function saveProc(){
      let id=document.getElementById('pr_id').value;
      let data={numero_cnj:pr_cnj.value,cliente_id:parseInt(pr_cliente.value)||null,parte_contraria:pr_parte.value,area:pr_area.value,status:pr_status.value,advogado:pr_adv.value,data_distribuicao:pr_data.value||null,valor_causa:parseFloat(pr_valor.value)||0};
      try{ if(id){ await api('/api/processos','POST',{...data,id:parseInt(id)}); } else { await api('/api/processos','POST',data); } closeModal('modalProc'); toast('Processo salvo!'); loadProc(); resetProc(); }catch(e){ toast(e.message,'error'); }
    }
    function resetProc(){ document.getElementById('pr_id').value=''; ['pr_cnj','pr_parte','pr_area','pr_adv','pr_data','pr_valor'].forEach(i=>document.getElementById(i).value=''); }
    async function delProc(id){ if(!confirm('Excluir processo?'))return; try{ await api('/api/processos/'+id,'DELETE'); toast('Excluído!'); loadProc(); }catch(e){ toast(e.message,'error'); } }
    async function openAnd(id){ document.getElementById('and_proc_id').value=id; try{ let d=await api('/api/processos'); let p=d.processos.find(x=>x.id==id); document.getElementById('and-list').innerHTML=(p.andamentos||[]).map(a=>`<li><div class="date">${a.data_hora}</div><div class="desc">${a.descricao}</div></li>`).join('')||'<li style="border:none;color:var(--muted)">Sem andamentos</li>'; }catch(e){} openModal('modalAnd'); }
    async function addAnd(){ let pid=document.getElementById('and_proc_id').value; let desc=document.getElementById('and_desc').value; if(!desc)return; try{ await api('/api/processos/'+pid+'/andamento','POST',{descricao:desc}); document.getElementById('and_desc').value=''; toast('Andamento adicionado!'); openAnd(pid); }catch(e){ toast(e.message,'error'); } }
    loadProc();
    """
    return render_template_string(admin_page('Processos', 'processos', content, extra_js=js))

@app.route('/admin/financeiro')
@login_required
def admin_financeiro():
    content = """
    <h1 class="page-title">Financeiro</h1>
    <div class="grid grid-2">
      <div class="card glass">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h3 style="color:var(--gold)">Contas a Receber</h3><button class="btn-gold" onclick="openModal('modalRec')">+ Nova</button></div>
        <table><thead><tr><th>Descrição</th><th>Cliente</th><th>Venc.</th><th>Valor</th><th>Status</th><th>Ações</th></tr></thead><tbody id="tb-rec"></tbody></table>
      </div>
      <div class="card glass">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h3 style="color:var(--gold)">Contas a Pagar</h3><button class="btn-gold" onclick="openModal('modalPag')">+ Nova</button></div>
        <table><thead><tr><th>Descrição</th><th>Fornecedor</th><th>Venc.</th><th>Valor</th><th>Status</th><th>Ações</th></tr></thead><tbody id="tb-pag"></tbody></table>
      </div>
    </div>
    <div class="modal-bg" id="modalRec">
      <div class="modal glass">
        <h2>Conta a Receber</h2><input type="hidden" id="rec_id">
        <div class="form-group"><label>Descrição</label><input id="rec_desc"></div>
        <div class="form-group"><label>Cliente</label><input id="rec_cli"></div>
        <div class="grid grid-2"><div class="form-group"><label>Valor</label><input type="number" step="0.01" id="rec_val"></div><div class="form-group"><label>Vencimento</label><input type="date" id="rec_venc"></div></div>
        <div class="form-group"><label>Status</label><select id="rec_status"><option value="pendente">Pendente</option><option value="recebido">Recebido</option></select></div>
        <div class="modal-actions"><button class="btn-ghost" onclick="closeModal('modalRec')">Cancelar</button><button class="btn-gold" onclick="saveRec()">Salvar</button></div>
      </div>
    </div>
    <div class="modal-bg" id="modalPag">
      <div class="modal glass">
        <h2>Conta a Pagar</h2><input type="hidden" id="pag_id">
        <div class="form-group"><label>Descrição</label><input id="pag_desc"></div>
        <div class="form-group"><label>Fornecedor</label><input id="pag_forn"></div>
        <div class="grid grid-2"><div class="form-group"><label>Valor</label><input type="number" step="0.01" id="pag_val"></div><div class="form-group"><label>Vencimento</label><input type="date" id="pag_venc"></div></div>
        <div class="form-group"><label>Status</label><select id="pag_status"><option value="pendente">Pendente</option><option value="pago">Pago</option></select></div>
        <div class="modal-actions"><button class="btn-ghost" onclick="closeModal('modalPag')">Cancelar</button><button class="btn-gold" onclick="savePag()">Salvar</button></div>
      </div>
    </div>
    """
    js = """
    async function loadFin(){
      try{ let r=await api('/api/financeiro/receber');
        document.getElementById('tb-rec').innerHTML=r.map(x=>`<tr><td>${x.descricao}</td><td>${x.cliente_nome||'-'}</td><td>${x.data_vencimento}</td><td>${x.valor}</td><td><span class="badge ${x.status=='recebido'?'badge-green':'badge-yellow'}">${x.status}</span></td><td><button class="btn-ghost" onclick="editRec(${JSON.stringify(x).replace(/"/g,'&quot;')})">Editar</button> <button class="btn-danger" onclick="delRec(${x.id})">Excluir</button></td></tr>`).join('')||'<tr><td colspan=6 style="color:var(--muted);text-align:center">Nenhuma conta</td></tr>';
        let p=await api('/api/financeiro/pagar');
        document.getElementById('tb-pag').innerHTML=p.map(x=>`<tr><td>${x.descricao}</td><td>${x.fornecedor||'-'}</td><td>${x.data_vencimento}</td><td>${x.valor}</td><td><span class="badge ${x.status=='pago'?'badge-green':'badge-yellow'}">${x.status}</span></td><td><button class="btn-ghost" onclick="editPag(${JSON.stringify(x).replace(/"/g,'&quot;')})">Editar</button> <button class="btn-danger" onclick="delPag(${x.id})">Excluir</button></td></tr>`).join('')||'<tr><td colspan=6 style="color:var(--muted);text-align:center">Nenhuma conta</td></tr>';
      }catch(e){ toast(e.message,'error'); }
    }
    function editRec(x){ document.getElementById('rec_id').value=x.id; document.getElementById('rec_desc').value=x.descricao; document.getElementById('rec_cli').value=x.cliente_nome||''; document.getElementById('rec_val').value=x.valor_num||''; document.getElementById('rec_venc').value=x.data_vencimento_iso||''; document.getElementById('rec_status').value=x.status; openModal('modalRec'); }
    async function saveRec(){ let id=document.getElementById('rec_id').value; let data={descricao:rec_desc.value,cliente_nome:rec_cli.value,valor:parseFloat(rec_val.value)||0,data_vencimento:rec_venc.value||null,status:rec_status.value}; try{ if(id){ await api('/api/financeiro/receber','POST',{...data,id:parseInt(id)}); } else { await api('/api/financeiro/receber','POST',data); } closeModal('modalRec'); toast('Salvo!'); loadFin(); resetRec(); }catch(e){ toast(e.message,'error'); } }
    function resetRec(){ document.getElementById('rec_id').value=''; ['rec_desc','rec_cli','rec_val','rec_venc'].forEach(i=>document.getElementById(i).value=''); document.getElementById('rec_status').value='pendente'; }
    async function delRec(id){ if(!confirm('Excluir?'))return; try{ await api('/api/financeiro/receber/'+id,'DELETE'); toast('Excluído!'); loadFin(); }catch(e){ toast(e.message,'error'); } }
    function editPag(x){ document.getElementById('pag_id').value=x.id; document.getElementById('pag_desc').value=x.descricao; document.getElementById('pag_forn').value=x.fornecedor||''; document.getElementById('pag_val').value=x.valor_num||''; document.getElementById('pag_venc').value=x.data_vencimento_iso||''; document.getElementById('pag_status').value=x.status; openModal('modalPag'); }
    async function savePag(){ let id=document.getElementById('pag_id').value; let data={descricao:pag_desc.value,fornecedor:pag_forn.value,valor:parseFloat(pag_val.value)||0,data_vencimento:pag_venc.value||null,status:pag_status.value}; try{ if(id){ await api('/api/financeiro/pagar','POST',{...data,id:parseInt(id)}); } else { await api('/api/financeiro/pagar','POST',data); } closeModal('modalPag'); toast('Salvo!'); loadFin(); resetPag(); }catch(e){ toast(e.message,'error'); } }
    function resetPag(){ document.getElementById('pag_id').value=''; ['pag_desc','pag_forn','pag_val','pag_venc'].forEach(i=>document.getElementById(i).value=''); document.getElementById('pag_status').value='pendente'; }
    async function delPag(id){ if(!confirm('Excluir?'))return; try{ await api('/api/financeiro/pagar/'+id,'DELETE'); toast('Excluído!'); loadFin(); }catch(e){ toast(e.message,'error'); } }
    loadFin();
    """
    return render_template_string(admin_page('Financeiro', 'financeiro', content, extra_js=js))

@app.route('/admin/pessoal')
@login_required
def admin_pessoal():
    content = """
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h1 class="page-title" style="margin:0">Pessoal</h1>
      <button class="btn-gold" onclick="openModal('modalCol')">+ Novo Colaborador</button>
    </div>
    <div class="card glass">
      <table><thead><tr><th>Nome</th><th>Cargo</th><th>Salário</th><th>Telefone</th><th>Email</th><th>Status</th><th>Ações</th></tr></thead><tbody id="tb-col"></tbody></table>
    </div>
    <div class="modal-bg" id="modalCol">
      <div class="modal glass">
        <h2>Colaborador</h2><input type="hidden" id="col_id">
        <div class="form-group"><label>Nome</label><input id="col_nome"></div>
        <div class="grid grid-2"><div class="form-group"><label>Cargo</label><input id="col_cargo"></div><div class="form-group"><label>Salário</label><input type="number" step="0.01" id="col_sal"></div></div>
        <div class="grid grid-2"><div class="form-group"><label>Telefone</label><input id="col_tel"></div><div class="form-group"><label>Email</label><input id="col_email"></div></div>
        <div class="form-group"><label>Status</label><select id="col_status"><option value="ativo">Ativo</option><option value="inativo">Inativo</option></select></div>
        <div class="modal-actions"><button class="btn-ghost" onclick="closeModal('modalCol')">Cancelar</button><button class="btn-gold" onclick="saveCol()">Salvar</button></div>
      </div>
    </div>
    """
    js = """
    async function loadCol(){ try{ let d=await api('/api/pessoal'); document.getElementById('tb-col').innerHTML=d.map(c=>`<tr><td>${c.nome}</td><td>${c.cargo||'-'}</td><td>${c.salario}</td><td>${c.telefone||'-'}</td><td>${c.email||'-'}</td><td><span class="badge ${c.status=='ativo'?'badge-green':'badge-gray'}">${c.status}</span></td><td><button class="btn-ghost" onclick="editCol(${JSON.stringify(c).replace(/"/g,'&quot;')})">Editar</button> <button class="btn-danger" onclick="delCol(${c.id})">Excluir</button></td></tr>`).join('')||'<tr><td colspan=7 style="color:var(--muted);text-align:center">Nenhum colaborador</td></tr>'; }catch(e){ toast(e.message,'error'); } }
    function editCol(c){ document.getElementById('col_id').value=c.id; document.getElementById('col_nome').value=c.nome; document.getElementById('col_cargo').value=c.cargo||''; document.getElementById('col_sal').value=c.salario_num||''; document.getElementById('col_tel').value=c.telefone||''; document.getElementById('col_email').value=c.email||''; document.getElementById('col_status').value=c.status; openModal('modalCol'); }
    async function saveCol(){ let id=document.getElementById('col_id').value; let data={nome:col_nome.value,cargo:col_cargo.value,salario:parseFloat(col_sal.value)||0,telefone:col_tel.value,email:col_email.value,status:col_status.value}; try{ if(id){ await api('/api/pessoal','POST',{...data,id:parseInt(id)}); } else { await api('/api/pessoal','POST',data); } closeModal('modalCol'); toast('Salvo!'); loadCol(); resetCol(); }catch(e){ toast(e.message,'error'); } }
    function resetCol(){ document.getElementById('col_id').value=''; ['col_nome','col_cargo','col_sal','col_tel','col_email'].forEach(i=>document.getElementById(i).value=''); document.getElementById('col_status').value='ativo'; }
    async function delCol(id){ if(!confirm('Excluir?'))return; try{ await api('/api/pessoal/'+id,'DELETE'); toast('Excluído!'); loadCol(); }catch(e){ toast(e.message,'error'); } }
    loadCol();
    """
    return render_template_string(admin_page('Pessoal', 'pessoal', content, extra_js=js))

@app.route('/admin/config')
@login_required
def admin_config():
    user = current_user()
    content = f"""
    <h1 class="page-title">Configurações</h1>
    <div class="grid grid-2">
      <div class="card glass">
        <h3 style="color:var(--gold);margin-bottom:16px;">Perfil do Usuário</h3>
        <div class="form-group"><label>Nome</label><input value="{user.nome}" disabled></div>
        <div class="form-group"><label>Email</label><input value="{user.email}" disabled></div>
        <div class="form-group"><label>Tipo</label><input value="{'Administrador' if user.admin else 'Usuário'}" disabled></div>
      </div>
      <div class="card glass">
        <h3 style="color:var(--gold);margin-bottom:16px;">Sistema</h3>
        <div class="form-group"><label>Empresa</label><input value="Cristo Advogados Associados" disabled></div>
        <div class="form-group"><label>Banco de Dados</label><input value="SQLite (cristo_adv.db)" disabled></div>
        <div class="form-group"><label>Versão</label><input value="1.0.0" disabled></div>
      </div>
    </div>
    <div class="card glass" style="margin-top:20px;">
      <h3 style="color:var(--gold);margin-bottom:16px;">Sobre</h3>
      <p style="color:var(--muted);line-height:1.6;">Sistema de gestão jurídica desenvolvido com Flask, SQLAlchemy e SQLite. Design futurístico com glassmorphism e neon dourado. Todos os dados são armazenados localmente.</p>
    </div>
    """
    return render_template_string(admin_page('Configurações', 'config', content))

# ===================== API - CLIENTES =====================
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def api_clientes():
    if request.method == 'GET':
        return jsonify([{ 'id':c.id,'nome':c.nome,'tipo':c.tipo,'cpf_cnpj':c.cpf_cnpj,
            'telefone':c.telefone,'email':c.email,'endereco':c.endereco,
            'data_cadastro':fmt_date(c.data_cadastro) } for c in Cliente.query.order_by(Cliente.nome).all()])
    data = request.get_json(force=True)
    cid = data.get('id')
    if cid:
        c = Cliente.query.get(cid)
        if not c: return jsonify({'error':'Cliente não encontrado'}), 404
    else:
        c = Cliente()
        c.data_cadastro = datetime.utcnow()
    c.nome = data.get('nome','')
    c.tipo = data.get('tipo','pf')
    c.cpf_cnpj = data.get('cpf_cnpj','')
    c.telefone = data.get('telefone','')
    c.email = data.get('email','')
    c.endereco = data.get('endereco','')
    c.usuario_id = session.get('user_id')
    db.session.add(c)
    db.session.commit()
    return jsonify({'id':c.id,'nome':c.nome})

@app.route('/api/clientes/<int:cid>', methods=['DELETE'])
@login_required
def api_del_cliente(cid):
    c = Cliente.query.get(cid)
    if not c: return jsonify({'error':'Não encontrado'}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok':True})

# ===================== API - PROCESSOS =====================
@app.route('/api/processos', methods=['GET', 'POST'])
@login_required
def api_processos():
    if request.method == 'GET':
        clientes = {c.id:c.nome for c in Cliente.query.all()}
        procs = Processo.query.order_by(Processo.id.desc()).all()
        return jsonify({
            'clientes':[{'id':c.id,'nome':c.nome} for c in Cliente.query.order_by(Cliente.nome).all()],
            'processos':[{ 'id':p.id,'numero_cnj':p.numero_cnj,'cliente_id':p.cliente_id,
                'cliente_nome':clientes.get(p.cliente_id,''),'parte_contraria':p.parte_contraria,
                'area':p.area,'status':p.status,'advogado':p.advogado,
                'data_distribuicao':fmt_date(p.data_distribuicao),'valor_causa':fmt_money(p.valor_causa),
                'valor_causa_num':p.valor_causa,
                'andamentos':[{'data_hora':fmt_date(a.data_hora),'descricao':a.descricao} for a in (p.andamentos or [])] } for p in procs]
        })
    data = request.get_json(force=True)
    pid = data.get('id')
    if pid:
        p = Processo.query.get(pid)
        if not p: return jsonify({'error':'Processo não encontrado'}), 404
    else:
        p = Processo()
    p.numero_cnj = data.get('numero_cnj','')
    p.cliente_id = data.get('cliente_id')
    p.parte_contraria = data.get('parte_contraria','')
    p.area = data.get('area','')
    p.status = data.get('status','Ativo')
    p.advogado = data.get('advogado','')
    dd = data.get('data_distribuicao')
    p.data_distribuicao = datetime.strptime(dd,'%Y-%m-%d').date() if dd else None
    p.valor_causa = float(data.get('valor_causa',0) or 0)
    p.usuario_id = session.get('user_id')
    db.session.add(p)
    db.session.commit()
    return jsonify({'id':p.id,'numero_cnj':p.numero_cnj})

@app.route('/api/processos/<int:pid>', methods=['DELETE'])
@login_required
def api_del_processo(pid):
    p = Processo.query.get(pid)
    if not p: return jsonify({'error':'Não encontrado'}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/processos/<int:pid>/andamento', methods=['POST'])
@login_required
def api_andamento(pid):
    p = Processo.query.get(pid)
    if not p: return jsonify({'error':'Processo não encontrado'}), 404
    data = request.get_json(force=True)
    a = Andamento(processo_id=pid, descricao=data.get('descricao',''), usuario_id=session.get('user_id'))
    db.session.add(a)
    db.session.commit()
    return jsonify({'id':a.id})

# ===================== API - FINANCEIRO =====================
@app.route('/api/financeiro/receber', methods=['GET', 'POST'])
@login_required
def api_rec():
    if request.method == 'GET':
        return jsonify([{ 'id':r.id,'descricao':r.descricao,'cliente_nome':r.cliente_nome,
            'valor':fmt_money(r.valor),'valor_num':r.valor,'data_vencimento':fmt_date(r.data_vencimento),
            'data_vencimento_iso':r.data_vencimento.isoformat() if r.data_vencimento else '',
            'status':r.status } for r in ContaReceber.query.order_by(ContaReceber.id.desc()).all()])
    data = request.get_json(force=True)
    rid = data.get('id')
    if rid:
        r = ContaReceber.query.get(rid)
        if not r: return jsonify({'error':'Não encontrado'}), 404
    else:
        r = ContaReceber()
    r.descricao = data.get('descricao','')
    r.cliente_nome = data.get('cliente_nome','')
    r.valor = float(data.get('valor',0) or 0)
    dv = data.get('data_vencimento')
    r.data_vencimento = datetime.strptime(dv,'%Y-%m-%d').date() if dv else None
    r.status = data.get('status','pendente')
    if r.status == 'recebido' and not r.data_pagamento:
        r.data_pagamento = date.today()
    db.session.add(r)
    db.session.commit()
    return jsonify({'id':r.id})

@app.route('/api/financeiro/receber/<int:rid>', methods=['DELETE'])
@login_required
def api_del_rec(rid):
    r = ContaReceber.query.get(rid)
    if not r: return jsonify({'error':'Não encontrado'}), 404
    db.session.delete(r); db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/financeiro/pagar', methods=['GET', 'POST'])
@login_required
def api_pag():
    if request.method == 'GET':
        return jsonify([{ 'id':p.id,'descricao':p.descricao,'fornecedor':p.fornecedor,
            'valor':fmt_money(p.valor),'valor_num':p.valor,'data_vencimento':fmt_date(p.data_vencimento),
            'data_vencimento_iso':p.data_vencimento.isoformat() if p.data_vencimento else '',
            'status':p.status } for p in ContaPagar.query.order_by(ContaPagar.id.desc()).all()])
    data = request.get_json(force=True)
    pid = data.get('id')
    if pid:
        p = ContaPagar.query.get(pid)
        if not p: return jsonify({'error':'Não encontrado'}), 404
    else:
        p = ContaPagar()
    p.descricao = data.get('descricao','')
    p.fornecedor = data.get('fornecedor','')
    p.valor = float(data.get('valor',0) or 0)
    dv = data.get('data_vencimento')
    p.data_vencimento = datetime.strptime(dv,'%Y-%m-%d').date() if dv else None
    p.status = data.get('status','pendente')
    if p.status == 'pago' and not p.data_pagamento:
        p.data_pagamento = date.today()
    db.session.add(p); db.session.commit()
    return jsonify({'id':p.id})

@app.route('/api/financeiro/pagar/<int:pid>', methods=['DELETE'])
@login_required
def api_del_pag(pid):
    p = ContaPagar.query.get(pid)
    if not p: return jsonify({'error':'Não encontrado'}), 404
    db.session.delete(p); db.session.commit()
    return jsonify({'ok':True})

# ===================== API - PESSOAL =====================
@app.route('/api/pessoal', methods=['GET', 'POST'])
@login_required
def api_pessoal():
    if request.method == 'GET':
        return jsonify([{ 'id':c.id,'nome':c.nome,'cargo':c.cargo,'salario':fmt_money(c.salario),
            'salario_num':c.salario,'telefone':c.telefone,'email':c.email,'status':c.status } for c in Colaborador.query.order_by(Colaborador.nome).all()])
    data = request.get_json(force=True)
    cid = data.get('id')
    if cid:
        c = Colaborador.query.get(cid)
        if not c: return jsonify({'error':'Não encontrado'}), 404
    else:
        c = Colaborador()
    c.nome = data.get('nome','')
    c.cargo = data.get('cargo','')
    c.salario = float(data.get('salario',0) or 0)
    c.telefone = data.get('telefone','')
    c.email = data.get('email','')
    c.status = data.get('status','ativo')
    db.session.add(c); db.session.commit()
    return jsonify({'id':c.id})

@app.route('/api/pessoal/<int:cid>', methods=['DELETE'])
@login_required
def api_del_pessoal(cid):
    c = Colaborador.query.get(cid)
    if not c: return jsonify({'error':'Não encontrado'}), 404
    db.session.delete(c); db.session.commit()
    return jsonify({'ok':True})

# ===================== API - DASHBOARD =====================
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    total_clientes = Cliente.query.count()
    ativos = Processo.query.filter_by(status='Ativo').count()
    arquivados = Processo.query.filter_by(status='Arquivado').count()
    suspensos = Processo.query.filter_by(status='Suspenso').count()
    por_status = {'Ativo':ativos,'Suspenso':suspensos,'Arquivado':arquivados}
    now = datetime.utcnow()
    receitas = ContaReceber.query.filter(
        ContaReceber.status=='recebido',
        db.extract('month',ContaReceber.data_pagamento)==now.month,
        db.extract('year',ContaReceber.data_pagamento)==now.year
    ).all()
    receita_mes = sum(r.valor for r in receitas)
    andamentos = Andamento.query.order_by(Andamento.data_hora.desc()).limit(5).all()
    and_list = []
    for a in andamentos:
        p = Processo.query.get(a.processo_id)
        and_list.append({'data':fmt_date(a.data_hora),'processo':p.numero_cnj if p else '','descricao':a.descricao})
    receber_mes = ContaReceber.query.filter(
        db.extract('month',ContaReceber.data_vencimento)==now.month,
        db.extract('year',ContaReceber.data_vencimento)==now.year
    ).all()
    rec_list = [{'descricao':r.descricao,'cliente_nome':r.cliente_nome,'data_vencimento':fmt_date(r.data_vencimento),'valor':fmt_money(r.valor),'status':r.status} for r in receber_mes]
    return jsonify({
        'total_clientes':total_clientes,'processos_ativos':ativos,'processos_arquivados':arquivados,
        'receita_mes':fmt_money(receita_mes),'por_status':por_status,
        'andamentos':and_list,'receber_mes_lista':rec_list
    })

# ===================== MAIN =====================
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)