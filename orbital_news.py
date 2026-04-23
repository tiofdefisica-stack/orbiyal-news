#!/usr/bin/env python3
"""
Orbital News — Script único
Genera noticias con Claude API + web search y construye el index.html
"""

import os, json, datetime, re, sys, urllib.request, urllib.error

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY no definida", file=sys.stderr)
    sys.exit(1)

TODAY = datetime.date.today()
DAYS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MONTHS = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
DATE_ES = f"{DAYS[TODAY.weekday()]}, {TODAY.day} de {MONTHS[TODAY.month-1]} de {TODAY.year}"

SYSTEM = """Eres el sistema de generación de Orbital News, un medio de divulgación científica en español.
Usa web_search para buscar noticias científicas REALES de hoy o ayer. No inventes noticias.
Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional ni bloques markdown.

Estructura exacta del JSON:
{
  "ticker": ["titular 1","titular 2","titular 3","titular 4","titular 5","titular 6"],
  "hero": {"categoria":"Astronomía","titulo":"Título principal","deck":"2-3 frases explicando la noticia.","minutos_lectura":3},
  "lateral": [
    {"categoria":"Física","titulo":"Título","resumen":"1-2 frases."},
    {"categoria":"Biología","titulo":"Título","resumen":"1-2 frases."},
    {"categoria":"Tecnología","titulo":"Título","resumen":"1-2 frases."}
  ],
  "columnas": [
    {"num":"01","categoria":"Clima","titulo":"Título","resumen":"2-3 frases."},
    {"num":"02","categoria":"Neurociencia","titulo":"Título","resumen":"2-3 frases."},
    {"num":"03","categoria":"Espacio","titulo":"Título","resumen":"2-3 frases."}
  ],
  "profundidad": {"categoria":"Mecánica Orbital","titulo":"Título análisis","resumen":"3-4 frases.","minutos_lectura":8},
  "mini": [
    {"categoria":"Química","titulo":"Título breve"},
    {"categoria":"Geofísica","titulo":"Título breve"},
    {"categoria":"Computación","titulo":"Título breve"},
    {"categoria":"Medicina","titulo":"Título breve"}
  ],
  "editorial": "Frase reflexiva sobre la ciencia de hoy, máx 25 palabras.",
  "stats": [
    {"valor":"4,812","label":"Artículos científicos publicados hoy"},
    {"valor":"1,247","label":"Satélites activos en órbita"},
    {"valor":"3.8 cm","label":"Distancia Luna-Tierra ganada este año"},
    {"valor":"7","label":"Exoplanetas descubiertos esta semana"}
  ]
}"""

USER = f"""Fecha de hoy: {DATE_ES} ({TODAY.isoformat()})
Busca las noticias científicas más importantes de hoy o ayer. Cubre física, astronomía, biología, neurociencia, clima, tecnología, medicina.
Responde SOLO con el JSON."""

def call_claude():
    payload = {
        "model": "claude-opus-4-5",
        "max_tokens": 4000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "system": SYSTEM,
        "messages": [{"role": "user", "content": USER}]
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "web-search-2025-03-05"
        }, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

def extract_json(resp):
    text = ""
    for block in resp.get("content", []):
        if block.get("type") == "text":
            text = block["text"]
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text).strip()
    return json.loads(text)

def esc(t):
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def build_html(n):
    hero = n["hero"]; lateral = n["lateral"]; cols = n["columnas"]
    prof = n["profundidad"]; mini = n["mini"]
    editorial = n.get("editorial",""); stats = n.get("stats",[])
    ticker_items = n.get("ticker",[])

    ticker_spans = "".join(f"<span>{esc(t)}</span>" for t in ticker_items*2)
    lat_html = "".join(f'<div class="side-card"><div class="kicker g">{esc(c["categoria"])}</div><h3>{esc(c["titulo"])}</h3><p>{esc(c.get("resumen",""))}</p></div>' for c in lateral[:3])
    col_html = "".join(f'<div class="col-card"><div class="num">{esc(c["num"])}</div><div class="kicker">{esc(c["categoria"])}</div><h3>{esc(c["titulo"])}</h3><p>{esc(c.get("resumen",""))}</p></div>' for c in cols[:3])
    mini_html = "".join(f'<div class="mini-card"><div class="kicker m">{esc(m["categoria"])}</div><h4>{esc(m["titulo"])}</h4></div>' for m in mini[:4])
    stat_html = "".join(f'<div class="stat"><div class="stat-val">{esc(s["valor"])}</div><div class="stat-label">{esc(s["label"])}</div></div>' for s in stats[:4])

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<meta name="description" content="Orbital News — {esc(hero['titulo'])}"/>
<title>Orbital News — {esc(DATE_ES)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=DM+Sans:wght@300;400;500&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--ink:#0a0a0f;--paper:#f4f0e8;--accent:#e8400a;--gold:#c9a84c;--muted:#6b6b7a;--rule:rgba(200,190,170,0.2)}}
body{{background:var(--ink);color:var(--paper);font-family:'DM Sans',sans-serif;font-weight:300;line-height:1.6;overflow-x:hidden}}
#stars{{position:fixed;inset:0;z-index:0;pointer-events:none}}
#starCanvas{{width:100%;height:100%}}
.orbit-deco{{position:fixed;top:-30vw;right:-20vw;width:70vw;height:70vw;border:1px solid rgba(201,168,76,0.08);border-radius:50%;pointer-events:none;z-index:0;animation:spin 120s linear infinite}}
.orbit-deco::after{{content:'';position:absolute;top:10%;left:10%;right:10%;bottom:10%;border:1px solid rgba(201,168,76,0.05);border-radius:50%}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.site{{position:relative;z-index:1;animation:fadeIn .6s ease both}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
header{{border-bottom:1px solid var(--rule);padding:0 clamp(1rem,5vw,4rem)}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:1rem 0 .5rem;border-bottom:1px solid var(--rule);flex-wrap:wrap;gap:.5rem}}
.date-line{{font-family:'Space Mono',monospace;font-size:.65rem;color:var(--gold);letter-spacing:.15em;text-transform:uppercase}}
.edition-badge{{font-family:'Space Mono',monospace;font-size:.6rem;color:var(--muted);letter-spacing:.1em}}
.masthead{{text-align:center;padding:2rem 0 1.5rem}}
.masthead-rule{{display:flex;align-items:center;gap:1rem;margin-bottom:1rem}}
.masthead-rule span{{flex:1;height:1px;background:var(--rule)}}
.masthead-rule em{{font-family:'Space Mono',monospace;font-size:.6rem;color:var(--gold);font-style:normal;letter-spacing:.2em;white-space:nowrap}}
.logo{{font-family:'Playfair Display',serif;font-weight:900;font-size:clamp(3rem,10vw,7rem);line-height:.9;letter-spacing:-.02em;display:inline-block}}
.logo .o{{color:transparent;-webkit-text-stroke:1.5px var(--gold)}}
.tagline{{font-size:.75rem;font-weight:400;color:var(--muted);letter-spacing:.25em;text-transform:uppercase;margin-top:.5rem}}
nav{{display:flex;justify-content:center;gap:2rem;padding:.75rem 0;border-top:1px solid var(--rule);flex-wrap:wrap}}
nav a{{font-family:'Space Mono',monospace;font-size:.65rem;color:var(--muted);text-decoration:none;letter-spacing:.12em;text-transform:uppercase;transition:color .2s}}
nav a:hover,nav a.active{{color:var(--paper)}}
.ticker-wrap{{background:var(--accent);overflow:hidden;padding:.4rem 0}}
.ticker-track{{display:flex;white-space:nowrap;animation:ticker 50s linear infinite}}
.ticker-track span{{font-family:'Space Mono',monospace;font-size:.65rem;letter-spacing:.08em;color:var(--paper);padding:0 3rem}}
.ticker-track span::before{{content:'◆  ';color:rgba(255,255,255,.5)}}
@keyframes ticker{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
main{{padding:clamp(1.5rem,4vw,3rem) clamp(1rem,5vw,4rem);max-width:1400px;margin:0 auto}}
.sec{{font-family:'Space Mono',monospace;font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);display:flex;align-items:center;gap:.75rem;margin-bottom:1.5rem}}
.sec::after{{content:'';flex:1;height:1px;background:var(--rule)}}
.sec-inline{{font-family:'Space Mono',monospace;font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);display:flex;align-items:center;gap:.75rem;padding:1.25rem 0 0}}
.sec-inline::after{{content:'';flex:1;height:1px;background:var(--rule)}}
.kicker{{font-family:'Space Mono',monospace;font-size:.6rem;color:var(--accent);letter-spacing:.15em;text-transform:uppercase;margin-bottom:.75rem}}
.kicker.g{{color:var(--gold)}}.kicker.m{{color:var(--muted);font-size:.5rem}}
.byline{{font-family:'Space Mono',monospace;font-size:.6rem;color:var(--muted);margin-top:1.25rem}}
.byline span{{color:var(--gold)}}
.hero-grid{{display:grid;grid-template-columns:1fr 1fr 320px;gap:0;border:1px solid var(--rule)}}
.hero-main{{grid-column:1/3;padding:2rem;border-right:1px solid var(--rule);cursor:pointer;transition:background .3s}}
.hero-main:hover{{background:rgba(255,255,255,.02)}}
.hero-art{{width:100%;aspect-ratio:16/9;margin-bottom:1.5rem;border-radius:2px;overflow:hidden}}
.hero-art svg{{width:100%;height:100%;display:block}}
.hero-main h2{{font-family:'Playfair Display',serif;font-size:clamp(1.5rem,3vw,2.2rem);font-weight:700;line-height:1.15;margin-bottom:1rem}}
.deck{{font-size:.88rem;color:rgba(244,240,232,.65);line-height:1.7;max-width:55ch}}
.hero-side{{display:flex;flex-direction:column}}
.side-card{{padding:1.25rem 1.5rem;border-bottom:1px solid var(--rule);cursor:pointer;transition:background .3s;flex:1}}
.side-card:last-child{{border-bottom:none}}
.side-card:hover{{background:rgba(255,255,255,.03)}}
.side-card h3{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;line-height:1.25;margin-bottom:.5rem}}
.side-card p{{font-size:.78rem;color:rgba(244,240,232,.55);line-height:1.6}}
.three-col{{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--rule);border-top:none;margin-bottom:3rem}}
.col-card{{padding:1.5rem;border-right:1px solid var(--rule);cursor:pointer;transition:background .3s}}
.col-card:last-child{{border-right:none}}
.col-card:hover{{background:rgba(255,255,255,.03)}}
.num{{font-family:'Playfair Display',serif;font-size:2.5rem;color:rgba(201,168,76,.15);font-weight:900;line-height:1;margin-bottom:.5rem}}
.col-card h3{{font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:700;line-height:1.3;margin-bottom:.5rem}}
.col-card p{{font-size:.78rem;color:rgba(244,240,232,.55);line-height:1.6}}
.feature-row{{display:grid;grid-template-columns:2fr 1fr;gap:0;border:1px solid var(--rule);margin-bottom:3rem}}
.feature-main{{display:flex;gap:1.5rem;padding:1.75rem;border-right:1px solid var(--rule);cursor:pointer;transition:background .3s}}
.feature-main:hover{{background:rgba(255,255,255,.02)}}
.feature-img{{width:160px;flex-shrink:0;border-radius:2px;overflow:hidden;align-self:flex-start}}
.feature-img svg{{width:100%;height:100%;display:block}}
.feature-text h3{{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;line-height:1.2;margin-bottom:.5rem}}
.feature-text p{{font-size:.8rem;color:rgba(244,240,232,.6);line-height:1.65}}
.sidebar-stack{{display:flex;flex-direction:column}}
.mini-card{{padding:1rem 1.25rem;border-bottom:1px solid var(--rule);cursor:pointer;transition:background .3s}}
.mini-card:last-child{{border-bottom:none}}
.mini-card:hover{{background:rgba(255,255,255,.03)}}
.mini-card h4{{font-family:'Playfair Display',serif;font-size:.88rem;font-weight:700;line-height:1.3}}
.opinion{{background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.15);border-radius:2px;padding:2rem;margin-bottom:3rem;display:flex;gap:2rem;align-items:center}}
.opinion-icon{{font-size:3rem;flex-shrink:0;line-height:1}}
.opinion-label{{font-family:'Space Mono',monospace;font-size:.6rem;color:var(--gold);letter-spacing:.2em;text-transform:uppercase;margin-bottom:.5rem}}
.opinion blockquote{{font-family:'Playfair Display',serif;font-size:1.1rem;font-style:italic;line-height:1.5}}
.opinion-attr{{font-size:.72rem;color:var(--muted);margin-top:.75rem}}
.stats-bar{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid var(--rule);margin-bottom:3rem}}
.stat{{padding:1.25rem 1.5rem;border-right:1px solid var(--rule);text-align:center}}
.stat:last-child{{border-right:none}}
.stat-val{{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;color:var(--gold);line-height:1}}
.stat-label{{font-family:'Space Mono',monospace;font-size:.55rem;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-top:.35rem}}
footer{{border-top:3px solid var(--paper);padding:clamp(1.5rem,4vw,3rem) clamp(1rem,5vw,4rem) 2rem}}
.footer-grid{{display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr;gap:2rem;margin-bottom:2rem}}
.logo-sm{{font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:900;margin-bottom:.5rem}}
.footer-brand p{{font-size:.78rem;color:var(--muted);line-height:1.6;max-width:28ch}}
.footer-col h5{{font-family:'Space Mono',monospace;font-size:.6rem;letter-spacing:.15em;text-transform:uppercase;color:var(--gold);margin-bottom:1rem}}
.footer-col ul{{list-style:none}}
.footer-col li{{font-size:.8rem;color:var(--muted);margin-bottom:.5rem;cursor:pointer;transition:color .2s}}
.footer-col li:hover{{color:var(--paper)}}
.footer-bottom{{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--rule);padding-top:1.5rem;flex-wrap:wrap;gap:1rem}}
.footer-bottom p{{font-family:'Space Mono',monospace;font-size:.58rem;color:var(--muted)}}
.ai-badge{{display:flex;align-items:center;gap:.5rem;font-family:'Space Mono',monospace;font-size:.58rem;color:var(--accent);letter-spacing:.08em}}
.ai-badge::before{{content:'';width:6px;height:6px;background:var(--accent);border-radius:50%;animation:pulse 2s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@media(max-width:900px){{
  .hero-grid{{grid-template-columns:1fr}}
  .hero-main{{grid-column:1;border-right:none;border-bottom:1px solid var(--rule)}}
  .three-col{{grid-template-columns:1fr}}
  .col-card{{border-right:none;border-bottom:1px solid var(--rule)}}
  .feature-row{{grid-template-columns:1fr}}
  .feature-main{{border-right:none;border-bottom:1px solid var(--rule)}}
  .stats-bar{{grid-template-columns:repeat(2,1fr)}}
  .stat:nth-child(2){{border-right:none}}
  .footer-grid{{grid-template-columns:1fr 1fr}}
}}
@media(max-width:600px){{
  .feature-main{{flex-direction:column}}
  .feature-img{{width:100%}}
  .footer-grid{{grid-template-columns:1fr}}
  .opinion{{flex-direction:column;text-align:center}}
}}
</style>
</head>
<body>
<div id="stars"><canvas id="starCanvas"></canvas></div>
<div class="orbit-deco"></div>
<div class="site">
<header>
  <div class="header-top">
    <span class="date-line">{esc(DATE_ES)}</span>
    <span class="edition-badge">Vol. I · Edición Nº {TODAY.strftime('%Y%m%d')} · Generado por IA</span>
  </div>
  <div class="masthead">
    <div class="masthead-rule"><span></span><em>Ciencia en órbita · Cada día · Gratis</em><span></span></div>
    <div class="logo"><span class="o">O</span>RBITAL<br>NEWS</div>
    <div class="tagline">El universo no para — nosotros tampoco</div>
  </div>
  <nav>
    <a href="#" class="active">Portada</a><a href="#">Espacio</a><a href="#">Física</a>
    <a href="#">Biología</a><a href="#">Tecnología</a><a href="#">Clima</a>
    <a href="#">Opinión</a><a href="#">Archivo</a>
  </nav>
</header>
<div class="ticker-wrap"><div class="ticker-track">{ticker_spans}</div></div>
<main>
  <div class="sec">Portada del día</div>
  <div class="hero-grid">
    <div class="hero-main">
      <div class="hero-art"><svg viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="bg" cx="60%" cy="40%" r="70%"><stop offset="0%" stop-color="#1a0a3e"/><stop offset="50%" stop-color="#0d1a3a"/><stop offset="100%" stop-color="#04060f"/></radialGradient>
          <radialGradient id="g1" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#6b3fa0" stop-opacity=".6"/><stop offset="100%" stop-color="#6b3fa0" stop-opacity="0"/></radialGradient>
          <radialGradient id="g2" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#c9a84c" stop-opacity=".35"/><stop offset="100%" stop-color="#c9a84c" stop-opacity="0"/></radialGradient>
          <filter id="b1"><feGaussianBlur stdDeviation="8"/></filter>
          <filter id="b2"><feGaussianBlur stdDeviation="22"/></filter>
        </defs>
        <rect width="800" height="450" fill="url(#bg)"/>
        <ellipse cx="480" cy="180" rx="200" ry="130" fill="url(#g1)" filter="url(#b2)"/>
        <ellipse cx="180" cy="310" rx="130" ry="90" fill="url(#g2)" filter="url(#b2)"/>
        <g fill="white" opacity=".75">
          <circle cx="50" cy="40" r=".9"/><circle cx="130" cy="18" r="1.3"/><circle cx="210" cy="65" r=".6"/>
          <circle cx="370" cy="28" r="1.0"/><circle cx="520" cy="22" r="1.2"/><circle cx="660" cy="55" r=".7"/>
          <circle cx="740" cy="95" r=".6"/><circle cx="790" cy="32" r="1.1"/><circle cx="28" cy="160" r=".7"/>
          <circle cx="95" cy="210" r=".9"/><circle cx="290" cy="108" r="1.1"/><circle cx="430" cy="85" r=".8"/>
          <circle cx="42" cy="325" r="1.0"/><circle cx="305" cy="395" r=".9"/><circle cx="560" cy="362" r="1.1"/>
        </g>
        <circle cx="520" cy="220" r="68" fill="#1a2a5e" filter="url(#b1)" opacity=".5"/>
        <circle cx="520" cy="220" r="62" fill="#1e3070"/>
        <ellipse cx="520" cy="220" rx="62" ry="19" fill="none" stroke="#c9a84c" stroke-width="1.5" opacity=".65"/>
        <ellipse cx="520" cy="220" rx="88" ry="27" fill="none" stroke="#c9a84c" stroke-width=".8" opacity=".3"/>
        <circle cx="632" cy="168" r="11" fill="#3a4060"/>
        <ellipse cx="520" cy="220" rx="120" ry="40" fill="none" stroke="white" stroke-width=".5" stroke-dasharray="3,5" opacity=".2"/>
        <g transform="translate(275,315) rotate(-22)">
          <rect x="-4" y="-12" width="8" height="24" rx="2" fill="#8a9bc0"/>
          <rect x="-22" y="-2" width="18" height="4" rx="1" fill="#c9a84c" opacity=".8"/>
          <rect x="4" y="-2" width="18" height="4" rx="1" fill="#c9a84c" opacity=".8"/>
          <circle cx="0" cy="0" r="4" fill="#e8400a"/>
        </g>
        <path d="M 175 362 Q 275 282 375 242" stroke="#e8400a" stroke-width=".8" fill="none" stroke-dasharray="4,6" opacity=".5"/>
      </svg></div>
      <div class="kicker">{esc(hero['categoria'])} · Destacado</div>
      <h2>{esc(hero['titulo'])}</h2>
      <p class="deck">{esc(hero.get('deck',''))}</p>
      <div class="byline">Por <span>Orbital News IA</span> · {esc(DATE_ES)} · {esc(str(hero.get('minutos_lectura',3)))} min</div>
    </div>
    <div class="hero-side">{lat_html}</div>
  </div>
  <div class="three-col">{col_html}</div>
  <div class="sec-inline">En profundidad</div>
  <div class="feature-row">
    <div class="feature-main">
      <div class="feature-img"><svg viewBox="0 0 160 120" xmlns="http://www.w3.org/2000/svg">
        <rect width="160" height="120" fill="#080d1a"/>
        <circle cx="80" cy="60" r="35" fill="#0d2040"/>
        <circle cx="80" cy="60" r="28" fill="#1a3560" opacity=".7"/>
        <ellipse cx="80" cy="60" rx="50" ry="12" fill="none" stroke="#e8400a" stroke-width="1" opacity=".6"/>
        <circle cx="130" cy="48" r="5" fill="#c9a84c" opacity=".9"/>
        <ellipse cx="80" cy="60" rx="70" ry="19" fill="none" stroke="#c9a84c" stroke-width=".5" opacity=".3"/>
        <circle cx="80" cy="60" r="8" fill="#2a5090"/>
      </svg></div>
      <div class="feature-text">
        <div class="kicker g">{esc(prof['categoria'])} · Análisis</div>
        <h3>{esc(prof['titulo'])}</h3>
        <p>{esc(prof.get('resumen',''))}</p>
        <div class="byline" style="margin-top:.75rem;">Por <span>Orbital News IA</span> · {esc(str(prof.get('minutos_lectura',8)))} min</div>
      </div>
    </div>
    <div class="sidebar-stack">{mini_html}</div>
  </div>
  <div class="opinion">
    <div class="opinion-icon">🔭</div>
    <div>
      <div class="opinion-label">Editorial del día</div>
      <blockquote>"{esc(editorial)}"</blockquote>
      <div class="opinion-attr">— Editorial Orbital News · {esc(DATE_ES)}</div>
    </div>
  </div>
  <div class="sec">La ciencia en números</div>
  <div class="stats-bar">{stat_html}</div>
</main>
<footer>
  <div class="footer-grid">
    <div class="footer-brand">
      <div class="logo-sm">Orbital News</div>
      <p>Periodismo científico autónomo generado por inteligencia artificial. Noticias reales, cada día.</p>
    </div>
    <div class="footer-col"><h5>Secciones</h5><ul><li>Espacio y Cosmología</li><li>Física Fundamental</li><li>Biología y Vida</li><li>Tecnología Científica</li><li>Clima y Tierra</li></ul></div>
    <div class="footer-col"><h5>Proyecto</h5><ul><li>Sobre Orbital News</li><li>Metodología IA</li><li>Fuentes y verificación</li><li>Con F de Física</li><li>Contacto</li></ul></div>
    <div class="footer-col"><h5>Síguenos</h5><ul><li>YouTube</li><li>Facebook</li><li>Twitter / X</li><li>RSS Feed</li><li>Newsletter</li></ul></div>
  </div>
  <div class="footer-bottom">
    <p>© {TODAY.year} Orbital News — Un proyecto de Con F de Física · confdefisica.space</p>
    <div class="ai-badge">Contenido generado por IA · Actualizado cada 24h</div>
  </div>
</footer>
</div>
<script>
  const canvas=document.getElementById('starCanvas'),ctx=canvas.getContext('2d');let stars=[];
  function resize(){{canvas.width=window.innerWidth;canvas.height=window.innerHeight;}}
  function initStars(){{stars=Array.from({{length:200}},()=>({{x:Math.random()*canvas.width,y:Math.random()*canvas.height,r:Math.random()*1.2+.2,o:Math.random()*.6+.1,speed:Math.random()*.012+.003,phase:Math.random()*Math.PI*2}}));}}
  function draw(t){{ctx.clearRect(0,0,canvas.width,canvas.height);stars.forEach(s=>{{ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fillStyle=`rgba(255,255,240,${{s.o*(0.6+0.4*Math.sin(t*s.speed+s.phase))}})`;ctx.fill();}});requestAnimationFrame(draw);}}
  resize();initStars();requestAnimationFrame(draw);
  window.addEventListener('resize',()=>{{resize();initStars();}});
</script>
</body>
</html>"""

def main():
    print(f"🔭 Orbital News — {DATE_ES}")
    print("📡 Llamando a Claude con web search...")
    try:
        resp = call_claude()
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    print("✍️  Extrayendo noticias...")
    try:
        news = extract_json(resp)
    except Exception as e:
        print(f"ERROR JSON: {e}", file=sys.stderr)
        for b in resp.get("content",[]):
            if b.get("type")=="text":
                print(b["text"][:300], file=sys.stderr)
        sys.exit(1)

    print("🏗️  Construyendo index.html...")
    html = build_html(news)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Listo — {len(html)//1024} KB")

if __name__=="__main__":
    main()
