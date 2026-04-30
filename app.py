#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template_string, request
from collections import Counter
from datetime import datetime
import os

app = Flask(__name__)

# ================== ГЕНЕТИЧНІ РОЗРАХУНКИ ==================

def eye_color_probabilities(mother_color, father_color):
    genotypes = {'brown': ['BB', 'BG', 'Bb'], 'green': ['GG', 'Gb'], 'blue': ['bb']}
    mother_genos = genotypes.get(mother_color, [])
    father_genos = genotypes.get(father_color, [])
    if not mother_genos or not father_genos:
        return {}
    child_colors = Counter()
    total = len(mother_genos) * len(father_genos) * 4
    for mg in mother_genos:
        for fg in father_genos:
            for ma in mg:
                for fa in fg:
                    alleles = [ma, fa]
                    if 'B' in alleles: child_colors['Коричневий'] += 1
                    elif 'G' in alleles: child_colors['Зелений'] += 1
                    else: child_colors['Блакитний'] += 1
    return {c: round(n/total*100, 2) for c, n in child_colors.items()}

def hair_color_probabilities(mother_hair, father_hair):
    def get_genos(hair):
        if hair == 'red': return ['dd'], ['rr']
        elif hair == 'dark': return ['DD', 'Dd'], ['RR', 'Rr']
        else: return ['dd'], ['RR', 'Rr']
    md, mr = get_genos(mother_hair)
    fd, fr = get_genos(father_hair)
    child_hair = Counter()
    total = len(md)*len(fd)*len(mr)*len(fr) * 16
    for mda in md:
        for fda in fd:
            for mra in mr:
                for fra in fr:
                    for ma in mda:
                        for fa in fda:
                            d_alleles = ma + fa
                            for m_ra in mra:
                                for f_ra in fra:
                                    r_alleles = m_ra + f_ra
                                    if 'D' in d_alleles: child_hair['Темний'] += 1
                                    else:
                                        if r_alleles.count('r') == 2: child_hair['Рудий'] += 1
                                        else: child_hair['Світлий'] += 1
    return {h: round(n/total*100, 2) for h, n in child_hair.items()}

def blood_type_probabilities(m_abo, f_abo, m_rh, f_rh):
    alleles = {'A': ['AA', 'AO'], 'B': ['BB', 'BO'], 'AB': ['AB'], 'O': ['OO']}
    ma = alleles.get(m_abo, [])
    fa = alleles.get(f_abo, [])
    if not ma or not fa:
        return {}, {}
    child_types = Counter()
    total_ab0 = len(ma) * len(fa) * 4
    for m in ma:
        for f in fa:
            for x in m:
                for y in f:
                    combo = x + y
                    if 'A' in combo and 'B' in combo: t = 'AB (IV)'
                    elif 'A' in combo: t = 'A (II)'
                    elif 'B' in combo: t = 'B (III)'
                    else: t = 'O (I)'
                    child_types[t] += 1
    ab0_probs = {bt: round(n / total_ab0 * 100, 2) for bt, n in child_types.items()}

    rh_alleles = {'+': ['DD', 'Dd'], '-': ['dd']}
    mrh = rh_alleles.get(m_rh, [])
    frh = rh_alleles.get(f_rh, [])
    child_rh = Counter()
    total_rh = len(mrh) * len(frh) * 4
    for m in mrh:
        for f in frh:
            for x in m:
                for y in f:
                    child_rh['Rh+' if ('D' in x or 'D' in y) else 'Rh-'] += 1
    rh_probs = {rh: round(n / total_rh * 100, 2) for rh, n in child_rh.items()}
    return ab0_probs, rh_probs

def handedness_probabilities(m_hand, f_hand):
    mg = {'right': ['RR', 'Rr'], 'left': ['rr']}.get(m_hand, ['RR', 'Rr'])
    fg = {'right': ['RR', 'Rr'], 'left': ['rr']}.get(f_hand, ['RR', 'Rr'])
    child = Counter()
    total = len(mg) * len(fg) * 4
    for m in mg:
        for f in fg:
            for x in m:
                for y in f: child['Правша' if ('R' in x or 'R' in y) else 'Шульга'] += 1
    return {h: round(n/total*100, 2) for h, n in child.items()}

def x_linked_prob(m_status, f_status, child_sex):
    mx = {'normal': ['D', 'D'], 'carrier': ['D', 'd'], 'affected': ['d', 'd']}.get(m_status, ['D', 'D'])
    fx = 'D' if f_status == 'normal' else 'd'
    if child_sex == 'male':
        probs = Counter()
        for x in mx: probs['Хворий' if x == 'd' else 'Норма'] += 1
        total = len(mx)
    elif child_sex == 'female':
        probs = Counter()
        for x in mx:
            if x == 'd' and fx == 'd': probs['Хвора'] += 1
            elif x == 'd' or fx == 'd': probs['Носій'] += 1
            else: probs['Норма'] += 1
        total = len(mx)
    else:
        m = x_linked_prob(m_status, f_status, 'male')
        f = x_linked_prob(m_status, f_status, 'female')
        probs = Counter()
        for k, v in m.items(): probs[f'{k} (чол.)'] = v * 0.5
        for k, v in f.items(): probs[f'{k} (жін.)'] = v * 0.5
        return {k: round(v, 2) for k, v in probs.items()}
    return {k: round(v/total*100, 2) for k, v in probs.items()}

def baldness_risk(m_family, f_bald, child_sex):
    if child_sex == 'male':
        if m_family == 'mother_bald': return {'Лисий': 75.0, 'Не лисий': 25.0}
        elif m_family == 'maternal_uncles': return {'Лисий': 50.0, 'Не лисий': 50.0}
        else: return {'Лисий': 10.0, 'Не лисий': 90.0}
    else:
        if m_family == 'mother_bald' and f_bald: return {'Можливе порідіння': 50.0, 'Норма': 50.0}
        elif m_family == 'mother_bald' or f_bald: return {'Можливе порідіння': 25.0, 'Норма': 75.0}
        else: return {'Можливе порідіння': 5.0, 'Норма': 95.0}

def migraine_risk(m, f):
    if m and f: risk = 70
    elif m or f: risk = 40
    else: risk = 15
    if risk >= 60: level = 'Високий ризик'
    elif risk >= 30: level = 'Середній ризик'
    else: level = 'Низький ризик'
    return {
        'Спадковий ризик мігрені': f'{risk}%',
        'Рівень ризику': level
    }

def twins_probability(mother_history):
    base_dizygotic = 1.2
    if mother_history == 'mother_twin':
        dizygotic = base_dizygotic * 4
    elif mother_history == 'maternal_relatives':
        dizygotic = base_dizygotic * 2
    else:
        dizygotic = base_dizygotic
    return {
        'Дизиготні (різнояйцеві) близнюки': f'{dizygotic:.2f}%',
        'Монозиготні (однояйцеві) близнюки': '0.4% (випадково)',
        'Загальний ризик двійні': f'{dizygotic + 0.4:.2f}%'
    }

GENETIC_CODE_DNA = {
    'ATA':'I','ATC':'I','ATT':'I','ATG':'M','ACA':'T','ACC':'T','ACG':'T','ACT':'T',
    'AAC':'N','AAT':'N','AAA':'K','AAG':'K','AGC':'S','AGT':'S','AGA':'R','AGG':'R',
    'CTA':'L','CTC':'L','CTG':'L','CTT':'L','CCA':'P','CCC':'P','CCG':'P','CCT':'P',
    'CAC':'H','CAT':'H','CAA':'Q','CAG':'Q','CGA':'R','CGC':'R','CGG':'R','CGT':'R',
    'GTA':'V','GTC':'V','GTG':'V','GTT':'V','GCA':'A','GCC':'A','GCG':'A','GCT':'A',
    'GAC':'D','GAT':'D','GAA':'E','GAG':'E','GGA':'G','GGC':'G','GGG':'G','GGT':'G',
    'TCA':'S','TCC':'S','TCG':'S','TCT':'S','TTC':'F','TTT':'F','TTA':'L','TTG':'L',
    'TAC':'Y','TAT':'Y','TAA':'*','TAG':'*','TGC':'C','TGT':'C','TGA':'*','TGG':'W',
}
COMP_DNA = {'A':'T','T':'A','G':'C','C':'G'}
COMP_RNA = {'A':'U','U':'A','G':'C','C':'G'}

# ================== HTML ШАБЛОН (з білими заголовками карток) ==================

MAIN_TEMPLATE = '''<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}🧬 Генетичний калькулятор{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --bg: #0f0f1a; --card: #1a1a2e; --accent: #e94560; --text: #eee; --muted: #adb5bd; }
        body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; }
        .navbar { background: var(--card) !important; border-bottom: 2px solid var(--accent); }
        .navbar-brand { color: var(--accent) !important; font-weight: bold; }
        .nav-link { color: orange !important; padding: 0.5rem 1rem !important; }
        .nav-link:hover { color: #ffaa00 !important; }
        .card { background: var(--card); border: 1px solid #2a2a4a; border-radius: 12px; transition: 0.3s; }
        .card:hover { border-color: var(--accent); transform: translateY(-3px); }
        .card-text { color: var(--muted) !important; }
        /* Заголовки карток – білі */
        .card h5 { color: #fff !important; }
        .btn-primary, .btn-calculate {
            background: red !important;
            border: none !important;
            color: black !important;
            font-weight: bold;
        }
        .btn-primary:hover, .btn-calculate:hover {
            background: darkred !important;
            color: black !important;
        }
        .btn-outline-primary { color: var(--accent); border-color: var(--accent); }
        .btn-outline-primary:hover { background: var(--accent); color: white; }
        .form-select, .form-control { background: #0a0a1a; color: var(--text); border: 1px solid #2a2a4a; }
        .form-select:focus, .form-control:focus { border-color: var(--accent); box-shadow: none; background: #0a0a1a; }
        .form-label { color: #fff !important; font-weight: 500; }
        .form-select { min-height: 44px; }
        .result-box { 
            background: var(--card); border-radius: 12px; padding: 20px; margin-top: 20px;
            animation: fadeIn 0.4s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .probability-bar { height: 24px; border-radius: 12px; }
        footer { background: var(--card); color: var(--muted); }
        h2 { color: var(--accent); }
        a { text-decoration: none; }
        .table-dark td, .table-dark th { color: #fff !important; }
        .result-box .note-text { color: #adb5bd !important; }
        .result-box p { word-break: break-word; overflow-wrap: break-word; }

        @media (max-width: 576px) {
            .table td, .table th { padding: 0.6rem 0.4rem; }
            h2 { font-size: 1.5rem; }
            .btn { padding: 0.6rem 1rem; font-size: 0.9rem; }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">🧬 ГенКальк</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="nav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/">🏠 Головна</a></li>
                    <li class="nav-item"><a class="nav-link" href="/twins">👯 Близнюки</a></li>
                    <li class="nav-item"><a class="nav-link" href="/dna-tools">🔬 ДНК</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <main class="container my-4">
        {% block content %}{% endblock %}
    </main>
    <footer class="text-center py-3 mt-5">
        <small>© {{ current_year }} Генетичний калькулятор | Для освітніх цілей</small>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

# ================== ДОПОМІЖНІ ФУНКЦІЇ ==================

def render_page(title, form_html, result_html=''):
    content = f'''
    <h2>{title}</h2>
    {form_html}
    {result_html}
    <a href="/" class="btn btn-outline-light mt-3">← На головну</a>
    '''
    return render_template_string(MAIN_TEMPLATE.replace('{% block content %}{% endblock %}', content))

def result_box(probs, colors=None, note=None):
    if not probs:
        return ''
    rows = ''
    for k, v in probs.items():
        color = colors.get(k, 'var(--accent)') if colors else 'var(--accent)'
        if isinstance(v, str):
            rows += f'<tr><td>{k}</td><td><b>{v}</b></td><td></td></tr>'
        else:
            rows += f'<tr><td>{k}</td><td><b>{v}%</b></td><td><div class="probability-bar" style="width:{v}%; background-color:{color};"></div></td></tr>'
    note_html = f'<p class="note-text mt-3">{note}</p>' if note else ''
    return f'''
    <div class="result-box">
        <h4>📊 Результат</h4>
        <table class="table table-dark table-sm mt-3">
            <thead><tr><th>Ознака</th><th>Ймовірність</th><th></th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        {note_html}
    </div>'''

# ================== МАРШРУТИ ==================

@app.route('/')
def index():
    cards = [
        ('/eye-color', '👁️ Колір очей', 'Коричневий, зелений, блакитний'),
        ('/hair-color', '💇 Колір волосся', 'Темний, світлий, рудий'),
        ('/blood-type', '🩸 Група крові та резус', 'AB0 / Rh'),
        ('/handedness', '✋ Правша чи шульга', 'Генетика рукості'),
        ('/baldness', '🧑‍🦲 Облисіння', 'Ризик алопеції'),
        ('/colorblindness', '🎨 Дальтонізм', 'Зчеплений з Х'),
        ('/hemophilia', '🩸 Гемофілія', 'Зчеплена з Х'),
        ('/migraine', '🤕 Мігрень', 'Спадкова схильність'),
        ('/dna-tools', '🔬 ДНК-інструменти', 'Транскрипція, трансляція'),
    ]
    cards_html = ''.join([
        f'''<div class="col-md-4 mb-4">
            <div class="card p-3 h-100">
                <h5>{title}</h5>
                <p class="card-text">{desc}</p>
                <a href="{url}" class="btn btn-primary mt-auto">Розрахувати →</a>
            </div>
        </div>''' for url, title, desc in cards
    ])
    return render_template_string(MAIN_TEMPLATE.replace('{% block content %}{% endblock %}',
        f'<h1 class="text-center mb-5">🧬 Генетичний калькулятор</h1><div class="row">{cards_html}</div>'))

@app.route('/eye-color', methods=['GET', 'POST'])
def eye_color_route():
    res = ''
    mother = father = ''
    if request.method == 'POST':
        mother = request.form.get('mother', '')
        father = request.form.get('father', '')
        probs = eye_color_probabilities(mother, father)
        bar_colors = {'Коричневий': '#8B4513', 'Зелений': '#2E8B57', 'Блакитний': '#4682B4'}
        res = result_box(probs, bar_colors) if probs else '<div class="alert alert-warning">Оберіть колір очей обох батьків.</div>'
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-5"><label class="form-label">Мати</label>
            <select name="mother" class="form-select"><option value="" disabled {"selected" if not mother else ""}>Оберіть колір</option><option value="brown" {"selected" if mother=="brown" else ""}>Коричневий</option><option value="green" {"selected" if mother=="green" else ""}>Зелений</option><option value="blue" {"selected" if mother=="blue" else ""}>Блакитний</option></select></div>
        <div class="col-md-5"><label class="form-label">Батько</label>
            <select name="father" class="form-select"><option value="" disabled {"selected" if not father else ""}>Оберіть колір</option><option value="brown" {"selected" if father=="brown" else ""}>Коричневий</option><option value="green" {"selected" if father=="green" else ""}>Зелений</option><option value="blue" {"selected" if father=="blue" else ""}>Блакитний</option></select></div>
        <div class="col-md-2 d-flex align-items-end"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    return render_page('👁️ Колір очей дитини', form, res)

@app.route('/hair-color', methods=['GET', 'POST'])
def hair_color_route():
    res = ''
    mother = father = ''
    if request.method == 'POST':
        mother = request.form.get('mother', '')
        father = request.form.get('father', '')
        probs = hair_color_probabilities(mother, father)
        bar_colors = {'Темний': '#3E2723', 'Світлий': '#F5DEB3', 'Рудий': '#D2691E'}
        res = result_box(probs, bar_colors) if probs else '<div class="alert alert-warning">Оберіть параметри.</div>'
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-5"><label class="form-label">Мати</label>
            <select name="mother" class="form-select"><option value="" disabled {"selected" if not mother else ""}>Оберіть колір</option><option value="dark" {"selected" if mother=="dark" else ""}>Темний</option><option value="blond" {"selected" if mother=="blond" else ""}>Світлий</option><option value="red" {"selected" if mother=="red" else ""}>Рудий</option></select></div>
        <div class="col-md-5"><label class="form-label">Батько</label>
            <select name="father" class="form-select"><option value="" disabled {"selected" if not father else ""}>Оберіть колір</option><option value="dark" {"selected" if father=="dark" else ""}>Темний</option><option value="blond" {"selected" if father=="blond" else ""}>Світлий</option><option value="red" {"selected" if father=="red" else ""}>Рудий</option></select></div>
        <div class="col-md-2 d-flex align-items-end"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    return render_page('💇 Колір волосся', form, res)

@app.route('/blood-type', methods=['GET', 'POST'])
def blood_type_route():
    ab0_html = rh_html = ''
    m_abo = f_abo = m_rh = f_rh = ''
    if request.method == 'POST':
        m_abo = request.form.get('mother_abo', '')
        f_abo = request.form.get('father_abo', '')
        m_rh = request.form.get('mother_rh', '')
        f_rh = request.form.get('father_rh', '')
        ab0, rh = blood_type_probabilities(m_abo, f_abo, m_rh, f_rh)
        ab0_colors = {'A (II)': '#d32f2f', 'B (III)': '#f57c00', 'AB (IV)': '#7b1fa2', 'O (I)': '#1976d2'}
        rh_colors = {'Rh+': '#388e3c', 'Rh-': '#757575'}
        if ab0: ab0_html = '<h5>Група крові AB0</h5>' + result_box(ab0, ab0_colors)
        if rh: rh_html = '<h5>Резус-фактор</h5>' + result_box(rh, rh_colors)
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-3"><label class="form-label">Група матері</label>
            <select name="mother_abo" class="form-select"><option value="" disabled {"selected" if not m_abo else ""}>Оберіть</option><option value="A" {"selected" if m_abo=="A" else ""}>A</option><option value="B" {"selected" if m_abo=="B" else ""}>B</option><option value="AB" {"selected" if m_abo=="AB" else ""}>AB</option><option value="O" {"selected" if m_abo=="O" else ""}>O</option></select></div>
        <div class="col-md-3"><label class="form-label">Резус матері</label>
            <select name="mother_rh" class="form-select"><option value="" disabled {"selected" if not m_rh else ""}>Оберіть</option><option value="+" {"selected" if m_rh=="+" else ""}>Rh+</option><option value="-" {"selected" if m_rh=="-" else ""}>Rh-</option></select></div>
        <div class="col-md-3"><label class="form-label">Група батька</label>
            <select name="father_abo" class="form-select"><option value="" disabled {"selected" if not f_abo else ""}>Оберіть</option><option value="A" {"selected" if f_abo=="A" else ""}>A</option><option value="B" {"selected" if f_abo=="B" else ""}>B</option><option value="AB" {"selected" if f_abo=="AB" else ""}>AB</option><option value="O" {"selected" if f_abo=="O" else ""}>O</option></select></div>
        <div class="col-md-3"><label class="form-label">Резус батька</label>
            <select name="father_rh" class="form-select"><option value="" disabled {"selected" if not f_rh else ""}>Оберіть</option><option value="+" {"selected" if f_rh=="+" else ""}>Rh+</option><option value="-" {"selected" if f_rh=="-" else ""}>Rh-</option></select></div>
        <div class="col-12"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    res = ab0_html + rh_html if (ab0_html or rh_html) else ''
    return render_page('🩸 Група крові та резус-фактор', form, res)

@app.route('/handedness', methods=['GET', 'POST'])
def handedness_route():
    res = ''
    mother = father = ''
    if request.method == 'POST':
        mother = request.form.get('mother', '')
        father = request.form.get('father', '')
        probs = handedness_probabilities(mother, father)
        note = "Цікавий факт: лише близько 10% населення світу є шульгами. Генетика відіграє в цьому лише часткову роль — важливі також внутрішньоутробні та соціальні фактори."
        res = result_box(probs, note=note)
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-5"><label class="form-label">Мати</label>
            <select name="mother" class="form-select"><option value="" disabled {"selected" if not mother else ""}>Оберіть</option><option value="right" {"selected" if mother=="right" else ""}>Правша</option><option value="left" {"selected" if mother=="left" else ""}>Шульга</option></select></div>
        <div class="col-md-5"><label class="form-label">Батько</label>
            <select name="father" class="form-select"><option value="" disabled {"selected" if not father else ""}>Оберіть</option><option value="right" {"selected" if father=="right" else ""}>Правша</option><option value="left" {"selected" if father=="left" else ""}>Шульга</option></select></div>
        <div class="col-md-2 d-flex align-items-end"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    return render_page('✋ Правша чи шульга', form, res)

@app.route('/baldness', methods=['GET', 'POST'])
def baldness_route():
    res = ''
    mother_family = father_bald = child_sex = ''
    if request.method == 'POST':
        mother_family = request.form.get('mother_family', '')
        father_bald = request.form.get('father_bald', '')
        child_sex = request.form.get('child_sex', '')
        probs = baldness_risk(mother_family, father_bald == 'yes', child_sex)
        note = "Ген облисіння часто передається по материнській лінії (через X-хромосому), але гени батька також мають значний вплив."
        res = result_box(probs, note=note)
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-4"><label class="form-label">Сімейна історія матері</label>
            <select name="mother_family" class="form-select"><option value="" disabled {"selected" if not mother_family else ""}>Оберіть</option><option value="none" {"selected" if mother_family=="none" else ""}>Немає облисіння</option><option value="maternal_uncles" {"selected" if mother_family=="maternal_uncles" else ""}>Лисі брати матері</option><option value="mother_bald" {"selected" if mother_family=="mother_bald" else ""}>Мати має облисіння</option></select></div>
        <div class="col-md-4"><label class="form-label">Батько лисий?</label>
            <select name="father_bald" class="form-select"><option value="" disabled {"selected" if not father_bald else ""}>Оберіть</option><option value="no" {"selected" if father_bald=="no" else ""}>Ні</option><option value="yes" {"selected" if father_bald=="yes" else ""}>Так</option></select></div>
        <div class="col-md-4"><label class="form-label">Стать дитини</label>
            <select name="child_sex" class="form-select"><option value="" disabled {"selected" if not child_sex else ""}>Оберіть</option><option value="male" {"selected" if child_sex=="male" else ""}>Хлопчик</option><option value="female" {"selected" if child_sex=="female" else ""}>Дівчинка</option></select></div>
        <div class="col-12"><button class="btn btn-primary">Розрахувати ризик →</button></div>
    </form>'''
    return render_page('🧑‍🦲 Ризик облисіння', form, res)

@app.route('/colorblindness', methods=['GET', 'POST'])
def colorblindness_route():
    res = ''
    mother_status = father_status = child_sex = ''
    if request.method == 'POST':
        mother_status = request.form.get('mother_status', '')
        father_status = request.form.get('father_status', '')
        child_sex = request.form.get('child_sex', '')
        probs = x_linked_prob(mother_status, father_status, child_sex)
        colors = {'Норма (чол.)': '#27ae60', 'Норма (жін.)': '#27ae60',
                  'Хворий (чол.)': '#e74c3c', 'Хвора (жін.)': '#e74c3c',
                  'Носій (жін.)': '#f39c12'}
        note = "Дальтонізм значно частіше зустрічається у чоловіків, оскільки вони мають лише одну X-хромосому. Жінки зазвичай є носіями гена без прояву ознаки."
        res = result_box(probs, colors, note)
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-4"><label class="form-label">Статус матері</label>
            <select name="mother_status" class="form-select"><option value="" disabled {"selected" if not mother_status else ""}>Оберіть</option><option value="normal" {"selected" if mother_status=="normal" else ""}>Норма</option><option value="carrier" {"selected" if mother_status=="carrier" else ""}>Носій</option><option value="affected" {"selected" if mother_status=="affected" else ""}>Хвора</option></select></div>
        <div class="col-md-4"><label class="form-label">Статус батька</label>
            <select name="father_status" class="form-select"><option value="" disabled {"selected" if not father_status else ""}>Оберіть</option><option value="normal" {"selected" if father_status=="normal" else ""}>Норма</option><option value="affected" {"selected" if father_status=="affected" else ""}>Хворий</option></select></div>
        <div class="col-md-4"><label class="form-label">Стать дитини</label>
            <select name="child_sex" class="form-select"><option value="" disabled {"selected" if not child_sex else ""}>Оберіть</option><option value="any" {"selected" if child_sex=="any" else ""}>Будь-яка</option><option value="male" {"selected" if child_sex=="male" else ""}>Хлопчик</option><option value="female" {"selected" if child_sex=="female" else ""}>Дівчинка</option></select></div>
        <div class="col-12"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    return render_page('🎨 Дальтонізм', form, res)

@app.route('/hemophilia', methods=['GET', 'POST'])
def hemophilia_route():
    res = ''
    mother_status = father_status = child_sex = ''
    if request.method == 'POST':
        mother_status = request.form.get('mother_status', '')
        father_status = request.form.get('father_status', '')
        child_sex = request.form.get('child_sex', '')
        probs = x_linked_prob(mother_status, father_status, child_sex)
        colors = {'Хворий (чол.)': '#c0392b', 'Хвора (жін.)': '#c0392b',
                  'Носій (жін.)': '#e67e22', 'Носій (чол.)': '#e67e22',
                  'Норма (чол.)': '#27ae60', 'Норма (жін.)': '#27ae60'}
        note = "Гемофілія — класичний приклад X-зчепленого рецесивного успадкування. Жінки-носії передають ген половині синів (які будуть хворі) та половині дочок (які стануть носіями)."
        res = result_box(probs, colors, note)
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-4"><label class="form-label">Статус матері</label>
            <select name="mother_status" class="form-select"><option value="" disabled {"selected" if not mother_status else ""}>Оберіть</option><option value="normal" {"selected" if mother_status=="normal" else ""}>Норма</option><option value="carrier" {"selected" if mother_status=="carrier" else ""}>Носій</option><option value="affected" {"selected" if mother_status=="affected" else ""}>Хвора</option></select></div>
        <div class="col-md-4"><label class="form-label">Статус батька</label>
            <select name="father_status" class="form-select"><option value="" disabled {"selected" if not father_status else ""}>Оберіть</option><option value="normal" {"selected" if father_status=="normal" else ""}>Норма</option><option value="affected" {"selected" if father_status=="affected" else ""}>Хворий</option></select></div>
        <div class="col-md-4"><label class="form-label">Стать дитини</label>
            <select name="child_sex" class="form-select"><option value="" disabled {"selected" if not child_sex else ""}>Оберіть</option><option value="any" {"selected" if child_sex=="any" else ""}>Будь-яка</option><option value="male" {"selected" if child_sex=="male" else ""}>Хлопчик</option><option value="female" {"selected" if child_sex=="female" else ""}>Дівчинка</option></select></div>
        <div class="col-12"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    return render_page('🩸 Гемофілія', form, res)

@app.route('/migraine', methods=['GET', 'POST'])
def migraine_route():
    res = ''
    mother_migr = father_migr = ''
    if request.method == 'POST':
        mother_migr = request.form.get('mother_migraine', '')
        father_migr = request.form.get('father_migraine', '')
        probs = migraine_risk(mother_migr == 'yes', father_migr == 'yes')
        risk_percent = float(probs['Спадковий ризик мігрені'].replace('%', ''))
        bar_color = '#27ae60' if risk_percent < 30 else ('#f39c12' if risk_percent < 60 else '#e74c3c')
        colors = {'Спадковий ризик мігрені': bar_color}
        note = "Спадковість відіграє роль у 50% випадків мігрені, але спосіб життя та фактори довкілля також мають велике значення."
        res = result_box(probs, colors, note)
    form = f'''
    <form method="post" class="row g-3">
        <div class="col-md-5"><label class="form-label">Мати має мігрень?</label>
            <select name="mother_migraine" class="form-select"><option value="" disabled {"selected" if not mother_migr else ""}>Оберіть</option><option value="no" {"selected" if mother_migr=="no" else ""}>Ні</option><option value="yes" {"selected" if mother_migr=="yes" else ""}>Так</option></select></div>
        <div class="col-md-5"><label class="form-label">Батько має мігрень?</label>
            <select name="father_migraine" class="form-select"><option value="" disabled {"selected" if not father_migr else ""}>Оберіть</option><option value="no" {"selected" if father_migr=="no" else ""}>Ні</option><option value="yes" {"selected" if father_migr=="yes" else ""}>Так</option></select></div>
        <div class="col-md-2 d-flex align-items-end"><button class="btn btn-primary">Розрахувати →</button></div>
    </form>'''
    return render_page('🤕 Спадкова схильність до мігрені', form, res)

@app.route('/twins', methods=['GET', 'POST'])
def twins_route():
    res = ''
    history = ''
    if request.method == 'POST':
        history = request.form.get('history', '')
        probs = twins_probability(history)
        rows = ''.join([f'<tr><td>{k}</td><td><b>{v}</b></td></tr>' for k, v in probs.items()])
        res = f'<div class="result-box"><h4>📊 Імовірність народження близнюків</h4><table class="table table-dark table-sm">{rows}</table></div>'
    form = f'''
    <form method="post" class="mt-4">
        <div class="mb-3">
            <label class="form-label">Чи є близнюки у вашій родині по материнській лінії?</label>
            <select name="history" class="form-select" required>
                <option value="" disabled {"selected" if not history else ""}>Оберіть варіант</option>
                <option value="none" {"selected" if history=="none" else ""}>Немає</option>
                <option value="maternal_relatives" {"selected" if history=="maternal_relatives" else ""}>Близнюки у близьких родичів матері (сестри, бабусі)</option>
                <option value="mother_twin" {"selected" if history=="mother_twin" else ""}>Мати – близнюк або вже народжувала близнюків</option>
            </select>
        </div>
        <button class="btn btn-primary">Розрахувати →</button>
    </form>
    '''
    info = '''
    <div class="result-box mt-4">
        <h5>📚 Як це працює</h5>
        <p>• Схильність до дизиготних (різнояйцевих) близнюків успадковується по жіночій лінії (ген гіперовуляції).</p>
        <p>• Монозиготні (однояйцеві) близнюки виникають випадково (~0.4% вагітностей).</p>
        <p>• Якщо у родині матері були близнюки – імовірність підвищується вдвічі (а в деяких випадках учетверо).</p>
    </div>'''
    return render_page('👯 Близнюки: ймовірність народження', form, res + info)

@app.route('/dna-tools', methods=['GET', 'POST'])
def dna_tools_route():
    res = seq = ''
    error = ''
    if request.method == 'POST':
        seq = request.form.get('sequence', '').upper().strip()
        action = request.form.get('action')
        if seq:
            is_rna = 'U' in seq
            valid_chars = 'AUGC' if is_rna else 'ATGC'
            if any(c not in valid_chars for c in seq):
                error = '<div class="alert alert-danger">Помилка: введено некоректні нуклеотиди. Дозволено лише A, T, G, C (для ДНК) або A, U, G, C (для РНК).</div>'
            else:
                try:
                    if action == 'transcribe':
                        if 'U' in seq:
                            raise ValueError("Для транскрипції потрібна ДНК-послідовність")
                        res = f'<span class="text-success fw-bold">РНК:</span> {seq.replace("T", "U")}'
                    elif action == 'reverse_transcribe':
                        if 'T' in seq and 'U' not in seq:
                            raise ValueError("Для зворотної транскрипції потрібна РНК-послідовність")
                        res = f'<span class="text-success fw-bold">ДНК:</span> {seq.replace("U", "T")}'
                    elif action == 'complement':
                        comp_map = COMP_RNA if is_rna else COMP_DNA
                        res = f"<span class=\"text-success fw-bold\">5'→3' комплементарна:</span> {''.join(comp_map[c] for c in seq)}"
                    elif action == 'reverse_complement':
                        comp_map = COMP_RNA if is_rna else COMP_DNA
                        res = f"<span class=\"text-success fw-bold\">3'→5' зворотня комплементарна:</span> {''.join(comp_map[c] for c in seq)[::-1]}"
                    elif action == 'gc_content':
                        gc = (seq.count('G') + seq.count('C')) / len(seq) * 100
                        res = f'<span class="text-success fw-bold">GC-склад:</span> <span class="fs-5 fw-bold text-info">{gc:.2f}%</span>'
                    elif action == 'translate':
                        protein = []
                        stop_found = False
                        for i in range(0, len(seq)-2, 3):
                            codon = seq[i:i+3]
                            aa = GENETIC_CODE_DNA.get(codon, '?')
                            if aa == '*':
                                stop_found = True
                                break
                            if aa != '?':
                                protein.append(aa)
                            else:
                                protein.append('X')
                        result_protein = ''.join(protein)
                        if not result_protein:
                            res = '<span class="text-warning">Не знайдено кодуючої послідовності</span>'
                        else:
                            note = ' (трансляція зупинена на стоп-кодоні)' if stop_found else ''
                            res = f'<span class="text-success fw-bold">Білок:</span> {result_protein}{note}'
                except ValueError as e:
                    error = f'<div class="alert alert-warning">{str(e)}</div>'
                except Exception as e:
                    error = f'<div class="alert alert-danger">Сталася помилка: {str(e)}</div>'
        else:
            if request.form.get('action'):
                error = '<div class="alert alert-warning">Введіть послідовність перед виконанням операції.</div>'

    form = f'''
    <form method="post">
        <textarea name="sequence" class="form-control mb-3" rows="4" 
            placeholder="Введіть послідовність ДНК/РНК (ATGC...)" style="font-family: 'Courier New', monospace;">{seq}</textarea>
        <div class="d-flex flex-wrap gap-2">
            <button name="action" value="transcribe" class="btn btn-outline-primary">Транскрипція</button>
            <button name="action" value="reverse_transcribe" class="btn btn-outline-primary">Зворотна транскрипція</button>
            <button name="action" value="complement" class="btn btn-outline-primary">Комплемент</button>
            <button name="action" value="reverse_complement" class="btn btn-outline-primary">Зворотній комплемент</button>
            <button name="action" value="gc_content" class="btn btn-outline-primary">GC-склад</button>
            <button name="action" value="translate" class="btn btn-outline-primary">Трансляція</button>
        </div>
    </form>'''
    
    if res and not error:
        res = f'<div class="result-box"><h4>📊 Результат</h4><p class="fs-5" style="word-break: break-all; color: #ffffff;">{res}</p></div>'
    elif error:
        res = error
    
    return render_page('🔬 ДНК-інструменти', form, res)

if __name__ == '__main__':
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        import webbrowser
        print("=" * 60)
        print("🧬 Генетичний калькулятор запущено!")
        print("Відкриваємо http://127.0.0.1:5000 у браузері...")
        print("=" * 60)
        webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=True)