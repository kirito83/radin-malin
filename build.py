#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generateur site statique - 100% stdlib, 0 dependance. Cout hebergement: 0 EUR."""
import json, os, html, re, datetime, shutil, urllib.parse, unicodedata
from lib import load, load_published, save_published, today_iso, active_promos, days_left, next_promo

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")

ICONS = {"calcul-tva-remise": "🧾", "calcul-pret-mensualite": "🏦", "calcul-imc": "⚖️", "convertisseur-devises": "💱", "generateur-mot-de-passe": "🔐", "compteur-mots-caracteres": "✍️", "generateur-qr-code": "📷", "convertisseur-unites": "📏", "calcul-age": "🎂", "generateur-facture": "🧮", "salaire-brut-net": "💶", "frais-notaire": "🏠", "jours-entre-deux-dates": "📅", "tirage-au-sort": "🎲", "calcul-ovulation-grossesse": "🌸", "simulateur-impot-revenu": "📊", "calcul-moyenne-notes": "🎓", "generateur-cv-gratuit": "📄", "compresseur-image": "🖼️", "calcul-calories": "🔥", "convertisseur-cups-grammes": "🥄", "semaines-grossesse": "🤰"}

def art_card(a, href_prefix=""):
    return f"<a class='art-card' href='{href_prefix}comparatifs/{esc(a['slug'])}/'><div class='art-top'><span class='cat'>{esc(a['category'])}</span><span class='fresh'>publié le {esc(fr_date(a.get('pub_date', '')))}</span></div><b class='t'>{esc(a['title'])}</b><span class='k'>{esc(a['keyword'])}</span><span class='art-cta'>Comparer les prix →</span></a>"

def fr_date(iso):
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except (ValueError, AttributeError):
        return iso

def slugify(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return t or "produit"

QUIZ_BANKS = {
    "maison": ("Ton logement ?", [("Petit appartement", [0, 2, 1]), ("Maison familiale", [2, 1, 0]), ("Grand espace exigeant", [1, 0, 2])]),
    "cuisine": ("Tu cuisines… ?", [("Rarement, simple et rapide", [0, 2, 1]), ("Tous les jours en famille", [2, 1, 0]), ("Comme un chef", [1, 0, 2])]),
    "tech": ("Ton usage ?", [("Occasionnel", [0, 2, 1]), ("Quotidien polyvalent", [2, 1, 0]), ("Intensif / pro", [1, 0, 2])]),
    "sante": ("Ton besoin ?", [("Découverte petit prix", [0, 2, 1]), ("Usage régulier fiable", [2, 1, 0]), ("Le plus performant", [1, 0, 2])]),
    "sport": ("Ton niveau ?", [("Débutant en douceur", [0, 2, 1]), ("Régulier motivé", [2, 1, 0]), ("Confirmé exigeant", [1, 0, 2])]),
    "voyage": ("Tes voyages ?", [("Week-ends légers", [0, 2, 1]), ("Vacances en famille", [2, 1, 0]), ("Grands voyages fréquents", [1, 0, 2])]),
}
QUIZ_BUDGET = ("Ton budget ?", [("Serré au maximum", [0, 2, 1]), ("Bon rapport qualité/prix", [2, 1, 0]), ("Le meilleur, peu importe le prix", [1, 0, 2])])
QUIZ_PRIO = ("Ta priorité ?", [("Efficacité maximale", [2, 0, 1]), ("Simplicité d'usage", [1, 2, 0]), ("Durable et premium", [1, 0, 2])])

def quiz_base_name(keyword):
    t = re.sub(r"^(meilleur|meilleure|top)\s+", "", keyword.strip(), flags=re.IGNORECASE)
    t = re.sub(r"\s*20\d{2}\s*$", "", t).strip()
    return t or keyword

def auto_quiz(article):
    base = quiz_base_name(article["keyword"])
    usage_q, usage_opts = QUIZ_BANKS.get(article["category"], QUIZ_BANKS["maison"])
    def mk(q, opts):
        return {"q": q, "options": [{"label": l, "scores": s} for l, s in opts]}
    return {"slug": article["slug"],
            "title": f"Quel {base} pour toi ? Quiz 30 secondes",
            "keyword": f"quel {base} choisir quiz",
            "parent": article["slug"],
            "intro": f"3 questions, 30 secondes : on te désigne le bon modèle parmi « {article['title']} ».",
            "questions": [mk(usage_q, usage_opts), mk(*QUIZ_BUDGET), mk(*QUIZ_PRIO)]}

def esc(s):
    return html.escape(str(s), quote=True)

def amazon_link(query, tag):
    q = urllib.parse.quote_plus(query)
    if tag and "VOTRE" not in tag:
        return f"https://www.amazon.fr/s?k={q}&tag={tag}"
    return f"https://www.amazon.fr/s?k={q}"

def vignette_loader(raw):
    """Extrait le script vignette et le plafonne a 1x/24h. "" si absent."""
    vign = ""
    for m in re.finditer(r"<script>\(function\(s\)\{s\.dataset\.zone='(\d+)',s\.src='([^']+)'\}\)\(\[document\.documentElement, document\.body\]\.filter\(Boolean\)\.pop\(\)\.appendChild\(document\.createElement\('script'\)\)\)</script>", raw or ""):
        if "vignette" in m.group(2):
            zone, src = m.group(1), m.group(2)
            vign = ("<script>(function(){try{var k='rm_vign',t=Date.now();"
                    "if(t-parseInt(localStorage.getItem(k)||'0',10)<864e5)return;"
                    "localStorage.setItem(k,String(t));var s=document.createElement('script');"
                    "s.dataset.zone='" + zone + "';s.src='" + src + "';"
                    "document.body.appendChild(s);}catch(e){}})();</script>")
    return vign

def base_page(cfg, title, meta_desc, content, canonical_path="", prefix="", robots="index, follow", image=""):
    site = esc(cfg["site_name"])
    url = cfg["site_url"].rstrip("/")
    canon = f"{url}/{canonical_path.lstrip('/')}" if canonical_path else url + "/"
    ads = cfg["monetization"]
    # Slots pubs : s'activent seuls quand les IDs sont renseignes
    ad_top = ""
    if ads.get("adsense_client") and "VOTRE" not in ads["adsense_client"]:
        ad_top = f"""<div class="ad"><small>Publicité</small>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(ads['adsense_client'])}" crossorigin="anonymous"></script>
<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(ads['adsense_client'])}" data-ad-slot="auto" data-ad-format="auto" data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div>"""
    elif ads.get("monetag_tag") or ads.get("monetag_inpage_enabled") or ads.get("monetag_vignette_enabled"):
        inpage = ads.get("monetag_inpage", "") if ads.get("monetag_inpage_enabled") else ""
        if not inpage and ads.get("monetag_tag") and "vignette" not in ads.get("monetag_tag"):
            inpage = ads["monetag_tag"]
        vign = vignette_loader(ads.get("monetag_vignette", "")) if ads.get("monetag_vignette_enabled") else ""
        ad_top = f"""<div class="ad"><small>Publicité</small>{inpage}{vign}</div>""" if (inpage or vign) else ""

    stripe_box = ""
    if ads.get("stripe_pro_link") and "VOTRE" not in ads["stripe_pro_link"]:
        paypal_btn = ""
        if ads.get("paypal_link") and "VOTRE" not in ads["paypal_link"]:
            paypal_btn = f"""<a class="btn ghost" href="{esc(ads.get('paypal_link',''))}">Payer avec PayPal</a>"""
        stripe_box = f"""<div class="pro"><b>⏫ Aller plus loin — {esc(ads['premium_product'])} : {esc(ads['premium_price'])}</b><br>
<a class="btn" href="{esc(ads['stripe_pro_link'])}">Acheter en 1 clic (Stripe)</a>
{paypal_btn}</div>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — {site}</title>
<meta name="description" content="{esc(meta_desc)}">
<meta name="robots" content="{esc(robots)}">
<meta name="theme-color" content="#0d1120">
<meta name="google-site-verification" content="{esc(cfg.get('google_site_verification',''))}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💰</text></svg>">
<link rel="icon" type="image/png" sizes="32x32" href="{prefix}icon-32.png">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<link rel="manifest" href="{prefix}site.webmanifest">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{site}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta_desc)}">
<meta property="og:url" content="{esc(canon)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(meta_desc)}">
{('<meta property="og:image" content="' + esc(image) + '"><meta name="twitter:image" content="' + esc(image) + '">') if image else ''}
<link rel="stylesheet" href="{prefix}style.css">
{cfg.get('analytics_script','')}
{cfg.get('head_extra','')}
</head>
<body>
<header class="site"><div class="wrap topbar">
<a class="logo" href="{prefix or './'}"><span class="logo-dot">💰</span><span>{site}<small>OUTILS GRATUITS • COMPARATIFS</small></span></a>
<nav class="main"><a href="{prefix or './'}">Accueil</a><a href="{prefix or './'}#outils">Outils</a><a href="{prefix or './'}#comparatifs">Comparatifs</a><a href="{prefix}premium/">Pack Excel</a><a class="cta" href="{prefix or './'}#comparatifs">Top promos →</a></nav>
</div></header>
<main class="wrap sheet">
<div style="height:14px"></div>
{ad_top}
{content}
{stripe_box}
<p class="disc">⚠️ {esc(cfg['affiliate_disclaimer'])}</p>
</main>
<footer class="site"><div class="wrap"><div class="foot-grid">
<div><h4>💰 {site}</h4><p style="margin:0;font-size:14px">Outils gratuits + 2 nouveaux comparatifs chaque jour. Le site est financé par l'affiliation et la pub, sans surcoût pour toi.</p></div>
<div><h4>Site</h4><a href="{prefix or './'}">Accueil</a><a href="{prefix or './'}#outils">Tous les outils</a><a href="{prefix or './'}#comparatifs">Comparatifs</a><a href="{prefix}premium/">Pack Excel {esc(cfg['monetization']['premium_price'])}</a>{'<a href="' + esc(cfg.get('telegram_channel','')) + '">✈️ Canal Telegram</a>' if cfg.get('telegram_channel') else ''}{'<a href="' + esc(cfg.get('social_bsky','')) + '">🦋 Bluesky</a>' if cfg.get('social_bsky') else ''}{'<a href="' + esc(cfg.get('social_masto','')) + '">🐘 Mastodon</a>' if cfg.get('social_masto') else ''}</div>
<div><h4>Technique</h4><a href="{prefix}sitemap.xml">Sitemap</a><a href="{prefix}rss.xml">Flux RSS</a><a href="{prefix or './'}#methode">Notre méthode</a></div>
<div><h4>Infos</h4><a href="{prefix}a-propos/">À propos</a><a href="{prefix}contact/">Contact</a><a href="{prefix}confidentialite/">Confidentialité</a><a href="{prefix}promos/">Promos en cours</a></div>
</div><p class="hint">© {datetime.date.today().year} {site} — Contenu indicatif, prix variables. Vérifie toujours l'offre du jour.</p></div></footer>
</body>
</html>"""

def css():
    return """:root{--bg:#f6f7fb;--card:#ffffff;--ink:#0f172a;--muted:#64748b;--line:#e8ecf3;--brand:#ffd60a;--brand-ink:#111;--accent:#6c5ce7;--accent2:#00d2a8;--radius:18px;--shadow:0 10px 30px rgba(15,23,42,.08);--shadow-sm:0 4px 14px rgba(15,23,42,.07)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{font-family:Inter,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;margin:0;color:var(--ink);background:var(--bg);line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden;overflow-x:clip}
a,button,input,select,textarea{-webkit-tap-highlight-color:transparent}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.site{position:sticky;top:0;z-index:50;background:rgba(13,17,28,.86);backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.08);color:#fff}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 0;gap:12px}
.logo{color:#fff;font-weight:900;text-decoration:none;font-size:21px;letter-spacing:-.5px;display:flex;align-items:center;gap:10px}
.logo-dot{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,var(--brand),#ff9d0a);display:inline-flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 4px 14px rgba(255,214,10,.4)}
.logo small{font-weight:600;color:#aeb8cc;font-size:12px;display:block;line-height:1;letter-spacing:.4px}
nav.main{display:flex;gap:8px;flex-wrap:wrap}
nav.main a{color:#dbe2ef;text-decoration:none;font-size:14px;font-weight:600;padding:8px 14px;border-radius:999px;border:1px solid transparent}
nav.main a:hover{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.12);color:#fff}
nav.main a.cta{background:var(--brand);color:#111}
main.sheet{background:transparent;margin:0 auto 28px;padding:0}
.hero{background:radial-gradient(900px 400px at 20% 0%,rgba(108,92,231,.28),transparent),radial-gradient(800px 380px at 90% 10%,rgba(0,210,168,.22),transparent),linear-gradient(180deg,#0d1120,#151b31);color:#fff;border-radius:0 0 28px 28px;padding:56px 0 40px;margin-bottom:22px;position:relative;overflow:hidden}
.hero h1{font-size:clamp(30px,4.5vw,48px);line-height:1.05;letter-spacing:-1.2px;margin:14px 0 12px}
.hero h1 span{background:linear-gradient(90deg,var(--brand),#ffb700);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p.lead{color:#c3cbdd;font-size:17px;max-width:640px;margin:0}
.badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,214,10,.14);border:1px solid rgba(255,214,10,.35);color:#ffe27a;font-size:13px;font-weight:700;padding:7px 12px;border-radius:999px}
.badge .pulse{width:8px;height:8px;border-radius:50%;background:#22ff9d;box-shadow:0 0 0 6px rgba(34,255,157,.15);animation:p 2s infinite}
@keyframes p{50%{box-shadow:0 0 0 2px rgba(34,255,157,.25)}}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
.stat{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:10px 14px;font-size:13px;color:#dbe2ef}
.stat b{color:#fff;font-size:16px;display:block;line-height:1}
.actions{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--brand);color:#111;font-weight:800;padding:12px 18px;border-radius:12px;text-decoration:none;border:0;cursor:pointer;font-size:15px;box-shadow:0 8px 20px rgba(255,214,10,.3);transition:.18s;min-height:44px}
.btn:hover{transform:translateY(-1px);box-shadow:0 12px 26px rgba(255,214,10,.38)}
.btn.ghost{background:rgba(255,255,255,.08);color:#fff;box-shadow:none;border:1px solid rgba(255,255,255,.16)}
.btn.small{padding:9px 14px;font-size:14px;border-radius:10px}
.card-section{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow-sm);padding:22px;margin:18px 0}
.card-section h2{font-size:22px;letter-spacing:-.5px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 14px;font-size:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.tool-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;text-decoration:none;color:inherit;display:flex;gap:12px;align-items:flex-start;transition:.18s;position:relative;overflow:hidden}
.tool-card:hover{transform:translateY(-3px);box-shadow:var(--shadow);border-color:#d9defa}
.tool-card .ico{width:44px;height:44px;flex:0 0 44px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px;background:linear-gradient(135deg,#eef2ff,#e6fff8);border:1px solid var(--line)}
.tool-card b{display:block;font-size:15.5px;line-height:1.3;margin-bottom:4px}
.tool-card span{color:var(--muted);font-size:13.5px;line-height:1.45;display:block}
.tool-card .go{margin-left:auto;color:var(--accent);font-weight:800}
.art-card{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;text-decoration:none;color:inherit;transition:.18s;display:flex;flex-direction:column}
.art-card:hover{transform:translateY(-3px);box-shadow:var(--shadow)}
.art-top{padding:14px 16px 0;display:flex;gap:8px;align-items:center}
.cat{font-size:11.5px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;background:#eef2ff;color:var(--accent);padding:5px 10px;border-radius:999px}
.fresh{font-size:12px;color:var(--muted);margin-left:auto}
.art-card b.t{padding:10px 16px 4px;font-size:16px;line-height:1.35;display:block}
.art-card span.k{padding:0 16px 14px;color:var(--muted);font-size:13px}
.art-cta{margin:0 16px 16px;background:#0f172a;color:#fff;border-radius:10px;text-align:center;font-weight:800;font-size:14px;padding:10px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:12px}
.step{background:linear-gradient(180deg,#fff,#f8faff);border:1px solid var(--line);border-radius:14px;padding:14px}
.step i{width:30px;height:30px;border-radius:9px;background:#0f172a;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-style:normal;font-weight:800;font-size:14px}
.breadcrumb{display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 13px;text-decoration:none;color:var(--muted);font-size:13.5px;font-weight:600}
.breadcrumb:hover{color:var(--ink)}
h1.page{font-size:clamp(26px,3.6vw,38px);letter-spacing:-.8px;line-height:1.12;margin:14px 0 10px}
.lead{color:#3b4763;font-size:16.5px}
.toolbox{background:linear-gradient(180deg,#fff,#fbfbff);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow-sm)}
.toolbox label{font-size:13.5px;font-weight:700;color:#33415e;display:block;margin-top:4px}
input,select,textarea{width:100%;padding:12px 13px;margin:6px 0 10px;border:1.5px solid var(--line);border-radius:12px;font-size:15px;background:#fff;transition:.15s}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 4px rgba(108,92,231,.13)}
button.action{background:#0f172a;color:#fff;padding:12px 18px;border-radius:12px;border:0;cursor:pointer;font-weight:800;font-size:15px;margin:4px 8px 0 0;transition:.15s}
button.action:hover{transform:translateY(-1px);background:#1e293b}
.res{background:linear-gradient(180deg,#0f172a,#1a2440);color:#fff;border-radius:14px;padding:16px;margin-top:12px;font-size:16px;border:1px solid #26314f}
.res b{color:var(--brand)}
.res a{color:var(--brand);font-weight:700}
table{width:100%;border-collapse:separate;border-spacing:0;margin:14px 0;border:1px solid var(--line);border-radius:14px;overflow:hidden;font-size:14.5px}
th,td{padding:12px;text-align:left}th{background:#0f172a;color:#fff;font-size:13px;letter-spacing:.3px}tr+tr td{border-top:1px solid var(--line)}tr:nth-child(even) td{background:#f8faff}
.podium{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0}
.pick{background:#fff;border:1.5px solid var(--line);border-radius:16px;padding:14px;position:relative}
.pick.first{border-color:var(--brand);box-shadow:0 10px 26px rgba(255,214,10,.22)}
.rank{position:absolute;top:-11px;left:12px;background:#0f172a;color:#fff;font-size:12px;font-weight:800;padding:3px 10px;border-radius:999px}
.rank.gold{background:linear-gradient(90deg,#ffd60a,#ff9d0a);color:#111}
.guide{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.guide div{background:#f8faff;border:1px solid var(--line);border-radius:12px;padding:12px;font-size:14px}
.cv-head{display:flex;gap:16px;align-items:center;background:linear-gradient(135deg,#0f172a,#3b4678);color:#fff;border-radius:14px;padding:18px;margin-bottom:12px}
.cv-head img{border:3px solid var(--brand);box-shadow:0 4px 12px rgba(0,0,0,.3)}
.cv-head h3{margin:0;font-size:24px;letter-spacing:-.5px}
.cv-title{margin:2px 0;color:var(--brand);font-weight:800;font-size:15px}
.cv-contact{margin:4px 0 0;font-size:13px;color:#c3cbdd}
.cv-h{font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);border-bottom:2px solid var(--accent);padding-bottom:4px;margin:16px 0 6px}
.cv-pill{display:inline-block;background:linear-gradient(180deg,#eef2ff,#e0e7ff);border:1px solid #c7d2fe;border-radius:999px;padding:4px 12px;margin:2px;font-size:13px;font-weight:600;color:#1e1b4b}
details{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:8px 0}
summary{font-weight:800;cursor:pointer}
.ad{background:#f9fafb;border:1.5px dashed #cbd5e1;padding:12px;text-align:center;margin-bottom:16px;border-radius:14px;color:var(--muted)}
.pro{background:linear-gradient(135deg,#fff8d6,#fff);border:1.5px solid #ffe45e;padding:16px;border-radius:16px;margin-top:18px;box-shadow:0 8px 22px rgba(255,214,10,.18)}
.disc{font-size:12.5px;color:#8a94a8;margin-top:18px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.hint{font-size:12.5px;color:var(--muted)}
footer.site{margin-top:26px;background:#0d1120;color:#aeb8cc;padding:28px 0;border-radius:28px 28px 0 0}
footer.site a{color:#dbe2ef}
.foot-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:16px}
.foot-grid h4{color:#fff;margin:0 0 8px;font-size:14px}
.foot-grid a{display:block;text-decoration:none;font-size:14px;margin:4px 0;color:#aeb8cc}
.search{position:relative;margin:12px 0 4px}
.search input{padding-left:44px;border-radius:999px}
.search span{position:absolute;left:15px;top:50%;transform:translateY(-50%);font-size:18px}
.sticky-cta{position:fixed;left:0;right:0;bottom:0;z-index:60;background:rgba(13,17,32,.94);backdrop-filter:blur(10px);border-top:1px solid rgba(255,255,255,.12);padding:10px 14px;display:flex;align-items:center;gap:10px;justify-content:center;flex-wrap:wrap}
.sticky-cta span{color:#dbe2ef;font-size:13px;font-weight:600}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:14px}
.tscroll table{margin:0;min-width:560px}
.inv-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;color:#111}
.inv-top{display:flex;justify-content:space-between;align-items:center;font-weight:900;font-size:18px;margin-bottom:10px}
.inv-cols{display:flex;gap:16px;margin-bottom:10px;font-size:14px}
.inv-table{width:100%;border-collapse:collapse;font-size:14px}
.inv-table th,.inv-table td{border:1px solid #ddd;padding:8px;text-align:left}
.inv-total td{font-weight:900;background:#fff8d6}
@page{size:A4;margin:11mm}
@media print{header.site,footer.site,.ad,.pro,.disc,.breadcrumb,h1.page,.lead,.card-section,.toolbox>label,.toolbox>button,.toolbox>h2,.toolbox>.hint{display:none!important}.toolbox{box-shadow:none!important;border:0!important;padding:0!important}.res{background:#fff!important;color:#000!important;border:0!important}#facture-print,#cv-print{position:static;width:100%;background:#fff;color:#000;font-size:13px}#facture-print .inv-card,#cv-print{border:0;padding:0}}
@media(max-width:640px){
.foot-grid{grid-template-columns:1fr 1fr}
.topbar{flex-direction:column;align-items:stretch;padding:10px 0}
nav.main{flex-wrap:nowrap;overflow-x:auto;padding-bottom:6px;scrollbar-width:none}
nav.main::-webkit-scrollbar{display:none}
nav.main a{white-space:nowrap;flex:0 0 auto;min-height:44px;display:inline-flex;align-items:center}
.hero{padding:34px 0 26px;border-radius:0 0 22px 22px}
.card-section{padding:16px;margin:14px 0}
.toolbox{padding:14px}
th,td{padding:9px 8px;font-size:13px}
.sticky-cta{padding:8px 10px;gap:8px}
.sticky-cta span{display:none}
.sticky-cta .btn{width:100%;justify-content:center}
.hero .actions .btn{width:100%;justify-content:center}
.pick{padding:12px}
h1.page{margin-top:10px}
}
@media(max-width:400px){.foot-grid{grid-template-columns:1fr}}
"""

def article_html(cfg, item, related=None, duel=None, quiz=None):
    tag = cfg["monetization"].get("amazon_tag", "")
    rows = ""
    podium = ""
    medals = ["🥇", "🥈", "🥉"]
    labels = ["Notre choix", "Alternative maline", "À surveiller en promo"]
    for i, p in enumerate(item["products"], 1):
        link = amazon_link(p, tag)
        note = round(4.8 - i * 0.2, 1)
        stars = "⭐" * (6 - i) + "☆" * (i - 1)
        prix = ["€€", "€", "€€€"][(i - 1) % 3]
        rows += f"<tr><td><b>{medals[i-1]} {esc(p)}</b></td><td>{note}/5</td><td>{prix}</td><td><a class='btn small' href='{esc(link)}' rel='nofollow sponsored noopener' target='_blank'>Voir le prix →</a></td></tr>"
        cls = "first" if i == 1 else ""
        rk = "gold" if i == 1 else ""
        podium += f"""<div class="pick {cls}"><span class="rank {rk}">{medals[i-1]} N°{i} — {labels[i-1]}</span><br><b style="font-size:16px">{esc(p)}</b><div class="hint">{stars} · {note}/5 · Budget {prix}</div><a class="btn small" href="{esc(link)}" rel="nofollow sponsored noopener" target="_blank">Voir le prix du jour →</a></div>"""
    faq = f"""<h2>Questions fréquentes</h2>
<details open><summary>Quel est le meilleur choix en 2026 ?</summary><p>Notre pick qualité/prix : <b>{esc(item['products'][0])}</b>. Les promos changent vite, clique sur « Voir le prix » pour le tarif du jour.</p></details>
<details><summary>Où acheter au meilleur prix ?</summary><p>Compare Amazon, Cdiscount et Boulanger. Nos boutons pointent vers la recherche Amazon (lien affilié, sans surcoût pour toi).</p></details>
<details><summary>Comment avons-nous comparé ?</summary><p>Avis clients, fiabilité SAV, rapport qualité/prix et dispo en France. Fiche révisée à chaque mise à jour des offres.</p></details>"""
    schema = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": item["title"], "inLanguage": "fr-FR",
        "author": {"@type": "Organization", "name": cfg["site_name"]},
        "datePublished": item.get("pub_date", today_iso())
    }
    body = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../../">← Retour accueil</a> <span class="cat">{esc(item['category'])}</span> <span class="hint">publié le {esc(fr_date(item.get('pub_date', '')))}</span></p>
<h1 class="page">{esc(item['title'])}</h1>
<p class="lead">Tu cherches <b>{esc(item['keyword'])}</b> ? Voici les 3 modèles qui reviennent le plus dans les avis positifs en France, classés par rapport qualité/prix.</p>
<div class="card-section"><h2>⚡ L'essentiel en 20 secondes</h2>
<ul style="margin:0"><li><b>Meilleur choix :</b> {esc(item['products'][0])} — le meilleur rapport qualité/prix.</li><li><b>Alternative :</b> {esc(item['products'][1])} si le n°1 est trop cher ou en rupture.</li><li><b>Promo :</b> les prix bougent chaque jour, clique « Voir le prix » pour le tarif actuel.</li></ul></div>
<div class="podium">{podium}</div>
<div class="card-section"><h2>⚡ Comparatif express</h2><p class="sub">Clique pour vérifier la promo du jour — les prix bougent vite. Fais défiler → sur mobile.</p>
<div class="tscroll"><table><tr><th>Modèle</th><th>Note</th><th>Budget</th><th>Offre</th></tr>{rows}</table></div></div>
<div class="card-section"><h2>🧭 Guide d'achat express (2 min)</h2>
<div class="guide"><div><b>1. Budget</b><br>Fixe un plafond AVANT de cliquer.</div><div><b>2. Usage réel</b><br>Liste tes 3 critères non-négociables.</div><div><b>3. Avis</b><br>Lis 5 avis 3-4 étoiles, les plus honnêtes.</div><div><b>4. Prix</b><br>Clique « Voir le prix » pour la promo du jour.</div></div></div>
{faq}
<div class="card-section"><h2>📉 Alerte baisse de prix</h2><p class="sub">Les promos sur ce produit partent vite. On les signale sur notre canal (quelques messages par jour max, zéro spam).</p>
<div class="actions">{'<a class="btn" href="' + esc(cfg.get('telegram_channel','')) + '">✈️ Recevoir les alertes prix →</a>' if cfg.get('telegram_channel') else '<a class="btn" href="../../#comparatifs">⭐ Voir les autres comparatifs →</a>'}</div></div>
<div class="card-section"><h2>🔗 Comparatifs similaires</h2><p class="sub">Pour continuer à comparer avant d'acheter.</p>
{('<p>🎯 30 secondes chrono : <a href="../../quiz/' + esc(quiz) + '/"><b>trouve ton modèle avec le quiz →</b></a></p>') if quiz else ''}
{('<p>⚔️ Hésitation entre les deux favoris ? Lis le duel : <a href="../../versus/' + esc(duel[0]) + '/"><b>' + esc(duel[1]) + ' vs ' + esc(duel[2]) + '</b> →</a></p>') if duel else ''}
<div class="grid">{"".join([art_card(r, "../../") for r in (related or [])[:3]])}</div></div>
<div class="sticky-cta"><span>🔥 {esc(item['products'][0])} — vérifie la promo du jour :</span><a class="btn small" href="{esc(amazon_link(item['products'][0], tag))}" rel="nofollow sponsored noopener" target="_blank">Voir le prix →</a></div>
<div style="height:64px"></div>
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": cfg['site_url'].rstrip('/') + "/"}, {"@type": "ListItem", "position": 2, "name": item["category"], "item": cfg['site_url'].rstrip('/') + f"/categorie/{item['category']}/"}, {"@type": "ListItem", "position": 3, "name": item["title"]}]}, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Quel est le meilleur choix en 2026 ?", "acceptedAnswer": {"@type": "Answer", "text": f"Notre pick qualité/prix : {item['products'][0]}. Vérifiez la promo du jour avant d'acheter."}}, {"@type": "Question", "name": "Où acheter au meilleur prix ?", "acceptedAnswer": {"@type": "Answer", "text": "Comparez Amazon, Cdiscount et Boulanger pour trouver la meilleure offre."}}, {"@type": "Question", "name": "Comment avons-nous comparé ?", "acceptedAnswer": {"@type": "Answer", "text": "Avis clients, fiabilité SAV et rapport qualité/prix."}}]}, ensure_ascii=False)}</script>"""
    return base_page(cfg, item["title"], item["title"] + " — comparatif, avis et meilleur prix.", body, f"comparatifs/{item['slug']}/", prefix="../../", image=f"{cfg['site_url'].rstrip('/')}/pins/{item['slug']}.png")

def versus_html(cfg, item):
    """Page duel P1 vs P2 : requetes 'X vs Y' a forte intention d'achat."""
    tag = cfg["monetization"].get("amazon_tag", "")
    p1, p2 = item["products"][0], item["products"][1]
    l1, l2 = amazon_link(p1, tag), amazon_link(p2, tag)
    dslug = f"{slugify(p1)}-vs-{slugify(p2)}"
    title = f"{p1} vs {p2} : lequel choisir en 2026 ?"
    body = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../../">← Retour accueil</a> <a class="breadcrumb" href="../../comparatifs/{esc(item['slug'])}/">Comparatif complet</a></p>
<h1 class="page">{esc(title)}</h1>
<p class="lead">Hésitation entre <b>{esc(p1)}</b> et <b>{esc(p2)}</b> ? Voici le duel en 1 minute, puis les prix du jour.</p>
<div class="card-section"><h2>⚡ Verdict en 20 secondes</h2>
<ul style="margin:0"><li><b>Choisis {esc(p1)}</b> si tu veux le meilleur compromis global.</li><li><b>Choisis {esc(p2)}</b> si ton budget est serré ou pour un usage simple.</li><li><b>Prix :</b> vérifie les deux boutons, l'écart change selon les promos.</li></ul></div>
<div class="podium"><div class="pick first"><span class="rank gold">🥇 {esc(p1)}</span><br><b style="font-size:16px">Le meilleur choix</b><div class="hint">Rapport qualité/prix n°1 du comparatif</div><a class="btn small" href="{esc(l1)}" rel="nofollow sponsored noopener" target="_blank">Voir le prix →</a></div><div class="pick"><span class="rank">🥈 {esc(p2)}</span><br><b style="font-size:16px">L'alternative maline</b><div class="hint">Souvent moins cher en promo</div><a class="btn small" href="{esc(l2)}" rel="nofollow sponsored noopener" target="_blank">Voir le prix →</a></div></div>
<div class="card-section"><h2>⚔️ Face à face</h2><p class="sub">Fais défiler → sur mobile.</p>
<div class="tscroll"><table><tr><th>Critère</th><th>{esc(p1)}</th><th>{esc(p2)}</th></tr>
<tr><td><b>Notre avis</b></td><td>🥇 Choix de la rédaction</td><td>🥈 Bon plan</td></tr>
<tr><td><b>Idéal pour</b></td><td>Usage exigeant et durable</td><td>Petit budget, usage simple</td></tr>
<tr><td><b>Prix du jour</b></td><td><a class='btn small' href='{esc(l1)}' rel='nofollow sponsored noopener' target='_blank'>Voir →</a></td><td><a class='btn small' href='{esc(l2)}' rel='nofollow sponsored noopener' target='_blank'>Voir →</a></td></tr></table></div></div>
<h2>Questions fréquentes</h2>
<details open><summary>Lequel choisir, {esc(p1)} ou {esc(p2)} ?</summary><p>{esc(p1)} pour le meilleur rapport qualité/prix, {esc(p2)} pour économiser. Compare les prix du jour via les boutons.</p></details>
<details><summary>Lequel est le moins cher ?</summary><p>En général {esc(p2)}, mais les promos inversent parfois l'écart : clique les deux boutons.</p></details>
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": cfg['site_url'].rstrip('/') + "/"}, {"@type": "ListItem", "position": 2, "name": item["title"], "item": cfg['site_url'].rstrip('/') + f"/comparatifs/{item['slug']}/"}, {"@type": "ListItem", "position": 3, "name": title}]}, ensure_ascii=False)}</script>"""
    return dslug, base_page(cfg, title, title + " Duel, avis et meilleurs prix.", body, f"versus/{dslug}/", prefix="../../")

def quiz_html(cfg, quiz, products, tag):
    data = json.dumps({"questions": quiz["questions"], "products": products}, ensure_ascii=False)
    body = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../../">← Retour accueil</a> <a class="breadcrumb" href="../../comparatifs/{esc(quiz['parent'])}/">Comparatif complet</a></p>
<h1 class="page">{esc(quiz['title'])}</h1>
<p class="lead">{esc(quiz['intro'])}</p>
<div class="toolbox"><div id="qbar" class="hint">Question 1/{len(quiz['questions'])}</div>
<div id="qbox"></div><div id="qres"></div></div>
<script>
var QUIZ={data};var TAG={json.dumps(tag)};
function amazonQ(p){{return "https://www.amazon.fr/s?k="+encodeURIComponent(p)+"&tag="+TAG;}}
var qi=0,sc=[0,0,0];
function showQ(){{var q=QUIZ.questions[qi];document.getElementById('qbar').textContent='Question '+(qi+1)+'/'+QUIZ.questions.length;
var h='<h2 style="margin-top:6px">'+q.q+'</h2>';q.options.forEach(function(o,i){{h+='<button class="action" style="display:block;width:100%;margin:8px 0" onclick="answer('+i+')">'+o.label+'</button>';}});
document.getElementById('qbox').innerHTML=h;document.getElementById('qres').innerHTML='';}}
function answer(i){{var o=QUIZ.questions[qi].options[i];o.scores.forEach(function(p,k){{sc[k]+=p;}});qi++;
if(qi<QUIZ.questions.length)showQ();else showR();}}
function showR(){{var w=sc.indexOf(Math.max.apply(null,sc));var p=QUIZ.products[w];
document.getElementById('qbar').textContent='Résultat 🎉';document.getElementById('qbox').innerHTML='';
document.getElementById('qres').innerHTML='<div class="res">Ton modèle : <b>'+p+'</b><br><br><a class="btn" href="'+amazonQ(p)+'" rel="nofollow sponsored noopener" target="_blank">Voir le prix →</a> <a class="btn ghost" style="color:#111;background:#fff;border:1px solid #ddd;box-shadow:none" href="https://t.me/share/url?url='+encodeURIComponent(location.href)+'&text='+encodeURIComponent('Ce quiz a trouvé mon modèle !')+'">Partager le quiz ✈️</a></div>';}}
showQ();</script>"""
    return base_page(cfg, quiz["title"], quiz["title"] + " : trouve ton modèle en 30 secondes.", body, f"quiz/{quiz['slug']}/", prefix="../../", image=f"{cfg['site_url'].rstrip('/')}/pins/{quiz['parent']}.png")

def tool_page(cfg, t, all_tools=None, top_articles=None):
    # Boutons avec la bonne classe moderne
    ui = t['ui_html'].replace('<button', '<button class="action"')
    others = [x for x in (all_tools or []) if x["slug"] != t["slug"]][:3]
    others_html = "".join([f"<a class='tool-card' href='../../outils/{esc(x['slug'])}/'><span class='ico'>{ICONS.get(x['slug'], '🧰')}</span><span><b>{esc(x['h1'])}</b><span>{esc(x['meta'])}</span></span><span class='go'>→</span></a>" for x in others])
    promos = "".join([art_card(a, "../../") for a in (top_articles or [])[:3]])
    promos_block = f"""<div class="card-section"><h2>⭐ Comparatifs du moment</h2><p class="sub">Les guides d'achat les plus lus cette semaine.</p><div class="grid">{promos}</div></div>""" if promos else ""
    body = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../../">← Tous les outils</a></p>
<h1 class="page">{esc(t['h1'])}</h1>
<p class="lead">{esc(t['pitch'])}</p>
<div class="toolbox">{ui}</div>
<script>{t['js']}</script>
<div class="card-section"><h2>Pourquoi utiliser cet outil ?</h2>
<div class="guide"><div><b>⚡ Instantané</b><br>Calcul direct dans ton navigateur.</div><div><b>🔒 Privé</b><br>Rien n'est envoyé ni stocké.</div><div><b>📱 Mobile</b><br>Fonctionne sur téléphone et PC.</div><div><b>🆓 Gratuit</b><br>Sans inscription, pour toujours.</div></div></div>
<div class="card-section"><h2>🧰 Autres outils gratuits</h2><div class="grid">{others_html}</div></div>
{promos_block}"""
    return base_page(cfg, t["title"], t["meta"], body, f"outils/{t['slug']}/", prefix="../../")

def build():
    cfg = load("config.json", {})
    tools = load("data/tools.json", [])
    keywords = load("data/keywords.json", [])
    published = load_published()
    if not published:
        # Seed : 3 articles pour le lancement
        published = {k["slug"]: today_iso() for k in keywords[:3]}
        save_published(published)

    by_slug = {k["slug"]: k for k in keywords}
    articles = []
    for s, d in published.items():
        if s in by_slug:
            a = dict(by_slug[s])
            a["pub_date"] = d
            articles.append(a)

    if os.path.exists(PUBLIC):
        shutil.rmtree(PUBLIC)
    os.makedirs(PUBLIC, exist_ok=True)
    os.makedirs(os.path.join(PUBLIC, "outils"), exist_ok=True)
    os.makedirs(os.path.join(PUBLIC, "comparatifs"), exist_ok=True)

    with open(os.path.join(PUBLIC, "style.css"), "w", encoding="utf-8") as f:
        f.write(css())
    with open(os.path.join(PUBLIC, ".nojekyll"), "w") as f:
        f.write("")

    # Pages outils
    for t in tools:
        d = os.path.join(PUBLIC, "outils", t["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(tool_page(cfg, t, tools, list(reversed(articles[-6:]))))

    # Pages articles + duels versus (X vs Y) + quiz (manuel prioritaire, auto sinon)
    duels = []
    quizzes = {q["parent"]: q for q in load("data/quizzes.json", [])}
    quiz_slugs = []
    for a in articles:
        rel = [x for x in articles if x["slug"] != a["slug"] and x["category"] == a["category"]]
        rel += [x for x in articles if x["slug"] != a["slug"] and x["category"] != a["category"]]
        dslug, dhtml = versus_html(cfg, a)
        duels.append((a, dslug))
        d = os.path.join(PUBLIC, "versus", dslug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(dhtml)
        qz = quizzes.get(a["slug"]) or auto_quiz(a)
        quiz_slugs.append(qz["slug"])
        qd = os.path.join(PUBLIC, "quiz", qz["slug"])
        os.makedirs(qd, exist_ok=True)
        with open(os.path.join(qd, "index.html"), "w", encoding="utf-8") as f:
            f.write(quiz_html(cfg, qz, a["products"][:3], cfg["monetization"].get("amazon_tag", "")))
        d = os.path.join(PUBLIC, "comparatifs", a["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(article_html(cfg, a, rel, (dslug, a["products"][0], a["products"][1]), qz["slug"]))

    # Page promos en cours (calendrier : ajout/retrait automatiques par dates)
    promos = active_promos(load("data/promos.json", []))
    by_slug = {k["slug"]: k for k in keywords}
    psections = ""
    for ev in promos:
        picks = [dict(by_slug[s], pub_date=published.get(s, today_iso()))
                 for s in ev.get("picks", []) if s in published and s in by_slug]
        if not picks:
            continue
        left = days_left(ev["end"])
        cards = "".join([art_card(a, "../") for a in picks])
        psections += f"""<div class="card-section"><h2>{esc(ev['emoji'])} {esc(ev['title'])}</h2><p class="sub">Jusqu'au {esc(fr_date(ev['end']))} — plus que {left} jour(s). {esc(ev['text'])}</p><div class="grid">{cards}</div></div>"""
    if not psections:
        nxt = next_promo(load("data/promos.json", []))
        suite = f"Prochaine vague : <b>{esc(nxt['emoji'])} {esc(nxt['title'])}</b> dès le {esc(fr_date(nxt['start']))}." if nxt else "De nouvelles promos arrivent très vite."
        psections = f"""<div class="card-section"><h2>😴 Aucune promo en ce moment</h2><p class="sub">{suite} En attendant, nos comparatifs affichent déjà les meilleurs prix du jour.</p></div>"""
    pbody = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">🔥 Promos en cours</h1>
<p class="lead">Les opérations du moment avec notre sélection au meilleur rapport qualité/prix. Page mise à jour chaque jour : les promos terminées disparaissent toutes seules.</p>
{psections}"""
    os.makedirs(os.path.join(PUBLIC, "promos"), exist_ok=True)
    with open(os.path.join(PUBLIC, "promos", "index.html"), "w", encoding="utf-8") as f:
        f.write(base_page(cfg, "Promos en cours", "Promotions du moment : sélection au meilleur rapport qualité/prix.", pbody, "promos/", prefix="../"))
    def is_gift(a):
        blob = (a["slug"] + " " + a["keyword"]).lower()
        return any(w in blob for w in ["noel", "cadeau", "avent", "black-friday"])
    gifts = [a for a in articles if is_gift(a)]
    if gifts:
        gcards = "".join([art_card(a, "../") for a in reversed(gifts)])
        gbody = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">🎄 Idées cadeaux & promos ({len(gifts)})</h1>
<p class="lead">Guides cadeaux de Noël, calendriers de l'Avent et bons plans Black Friday : le bon choix au meilleur prix.</p>
<div class="grid">{gcards}</div>"""
        gd = os.path.join(PUBLIC, "idees-cadeaux")
        os.makedirs(gd, exist_ok=True)
        with open(os.path.join(gd, "index.html"), "w", encoding="utf-8") as f:
            f.write(base_page(cfg, "Idées cadeaux Noël & Black Friday", "Guides cadeaux, calendriers de l'Avent et promos Black Friday.", gbody, "idees-cadeaux/", prefix="../"))

    # Pages catégories (hubs SEO : 1 page par univers)
    cat_labels = {"maison": "Maison", "cuisine": "Cuisine", "tech": "Tech", "sante": "Santé & bien-être", "sport": "Sport", "voyage": "Voyage"}
    hubs = sorted({a["category"] for a in articles})
    for cat in hubs:
        items = [a for a in articles if a["category"] == cat]
        label = cat_labels.get(cat, cat)
        cards = "".join([art_card(a, "../../") for a in reversed(items)])
        hbody = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../../">← Retour accueil</a></p>
<h1 class="page">Comparatifs {esc(label)} ({len(items)})</h1>
<p class="lead">Tous nos guides d'achat {esc(label.lower())} : {esc(', '.join([x['keyword'] for x in items[:5]]))}… mis à jour en continu.</p>
<div class="grid">{cards}</div>"""
        d = os.path.join(PUBLIC, "categorie", cat)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(base_page(cfg, f"Comparatifs {label}", f"Tous nos comparatifs {label.lower()} : guides d'achat et meilleurs prix.", hbody, f"categorie/{cat}/", prefix="../../"))

    # Index
    qmap = {q["parent"]: q["slug"] for q in load("data/quizzes.json", [])}
    cards_outils = "".join([f"<a class='tool-card' data-name='{esc(t['h1'] + ' ' + t['meta'])}' href='outils/{esc(t['slug'])}/'><span class='ico'>{ICONS.get(t['slug'], '🧰')}</span><span><b>{esc(t['h1'])}</b><span>{esc(t['meta'])}</span></span><span class='go'>→</span></a>" for t in tools])
    cards_articles = "".join([art_card(a) for a in reversed(articles)])
    index_body = f"""<div class="hero"><div class="wrap">
<span class="badge"><span class="pulse"></span> 2 nouveaux comparatifs chaque jour • 100% gratuit</span>
<h1>Économise chaque jour<br><span>sans y penser.</span></h1>
<p class="lead">{esc(cfg['site_description'])} Outils instantanés + comparatifs malins avec meilleur prix.</p>
<div class="actions"><a class="btn" href="#outils">🧰 Utiliser un outil gratuit</a><a class="btn ghost" href="#comparatifs">⭐ Voir les comparatifs</a>{'<a class="btn ghost" href="' + esc(cfg.get('telegram_channel','')) + '">✈️ Bons plans sur Telegram</a>' if cfg.get('telegram_channel') else ''}</div>
<div class="stats"><div class="stat"><b>{len(tools)}</b>outils gratuits</div><div class="stat"><b>{len(articles)}</b>comparatifs en ligne</div><div class="stat"><b>+2/jour</b>comparatifs frais</div><div class="stat"><b>0 €</b>sans inscription</div></div>
</div></div>
<div class="card-section"><h2 id="outils">🧰 Outils gratuits</h2><p class="sub">Les pages qui ramènent le trafic Google stable. Clique, utilise, repars.</p>
<div class="search"><span>🔎</span><input id="q" placeholder="Rechercher un outil : TVA, prêt, IMC, QR..." oninput="filtrer()"></div>
<div class="grid" id="tools-grid">{cards_outils}</div>
<script>function filtrer(){{var q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('#tools-grid .tool-card').forEach(function(c){{c.style.display=c.getAttribute('data-name').toLowerCase().includes(q)?'flex':'none';}});}}</script></div>
<div class="card-section"><h2 id="comparatifs">⭐ Derniers comparatifs ({len(articles)} publiés)</h2><p class="sub">Nos guides « meilleur X » : le bon choix au meilleur prix du jour.</p>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px"><a class='cat' style='text-decoration:none' href='promos/'>🔥 Promos en cours</a><a class='cat' style='text-decoration:none' href='idees-cadeaux/'>🎄 Idées cadeaux</a>{"".join([f"<a class='cat' style='text-decoration:none' href='categorie/{esc(c)}/'>{esc({'maison':'🏠 Maison','cuisine':'🍳 Cuisine','tech':'💻 Tech','sante':'💚 Santé','sport':'⚽ Sport','voyage':'✈️ Voyage'}.get(c, c))}</a>" for c in sorted({a['category'] for a in articles})])}</div>
<div class="grid">{cards_articles}</div></div>
<div class="card-section"><h2>🎯 Quiz 30 secondes</h2><p class="sub">3 questions et on te désigne le bon modèle. Rapide, gratuit, partageable.</p>
<div class="grid">{"".join([f"<a class='tool-card' href='quiz/{esc(qmap.get(a['slug'], a['slug']))}/'><span class='ico'>🎯</span><span><b>Quel {esc(quiz_base_name(a['keyword']))} pour toi ?</b><span>Trouve ton modèle en 30 secondes chrono.</span></span><span class='go'>→</span></a>" for a in reversed(articles[-3:])])}</div></div>
<div class="card-section" id="methode"><h2>⚙️ Notre méthode : simple et indépendante</h2><p class="sub">Des outils gratuits qui servent vraiment, des comparatifs mis à jour chaque jour.</p>
<div class="steps"><div class="step"><i>1</i><br><b>Outils gratuits</b><br><span class="hint">Calculs instantanés, sans inscription.</span></div><div class="step"><i>2</i><br><b>Comparatifs quotidiens</b><br><span class="hint">2 nouveaux guides d'achat chaque jour.</span></div><div class="step"><i>3</i><br><b>Avis indépendants</b><br><span class="hint">Classement par rapport qualité/prix, pas par sponsor.</span></div><div class="step"><i>4</i><br><b>100% gratuit pour toi</b><br><span class="hint">Le site vit de l'affiliation, sans surcoût sur tes achats.</span></div></div>
<p class="hint"><b>Ajoute-nous à tes favoris :</b> un nouvel outil ou comparatif t'attend chaque jour.</p></div>"""
    with open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8") as f:
        f.write(base_page(cfg, cfg["site_name"] + " — outils gratuits & comparatifs", cfg["site_description"], index_body, ""))

    # Page premium (Stripe/PayPal -> encaissement auto)
    m = cfg.get("monetization", {})
    prem_body = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">Pack Excel auto-entrepreneur — {esc(m.get('premium_price','9,90 €'))}</h1>
<p class="lead">Tu as aimé le générateur de facture gratuit ? Passe au pack complet : {esc(m.get('premium_product','pack Excel'))}. {'Paiement Stripe ou PayPal' if m.get('paypal_link') and 'VOTRE' not in m.get('paypal_link') else 'Paiement Stripe sécurisé'}, accès immédiat, sans abonnement.</p>
<div class="card-section"><h2>✅ Ce que tu reçois</h2>
<div class="guide"><div><b>📊 Budget 12 mois</b><br>96 lignes pré-remplies, écarts rouge/vert + tableau de bord graphique + traqueur d'abonnements.</div><div><b>🧾 Suivi 50 factures</b><br>TTC auto, statuts, reste à encaisser calculé seul.</div><div><b>🖨️ Facture + devis A4</b><br>Modèles pro prêts à imprimer, TVA auto, mentions légales.</div><div><b>⚡ Accès immédiat</b><br>Lien de téléchargement dès le paiement, sans abonnement.</div></div>
<div class="actions"><a class="btn" href="{esc(m.get('stripe_pro_link',''))}">💳 Acheter {esc(m.get('premium_price','9,90 €'))} avec Stripe →</a>{'<a class="btn ghost" style="color:#111;border-color:#ddd;background:#fff" href="' + esc(m.get('paypal_link','')) + '">Payer avec PayPal</a>' if m.get('paypal_link') and 'VOTRE' not in m.get('paypal_link') else ''}</div>
<p class="hint">🛡️ Garantie 14 jours : pack inutile ? Un simple email et tu es remboursé, sans question. Paiement sécurisé via Stripe ou PayPal, reçu fiscal fourni.</p></div>
<div class="card-section"><h2>❓ Questions</h2>
<details open><summary>Faut-il Excel payant ?</summary><p>Non. Les fichiers s'ouvrent dans Excel, LibreOffice (gratuit) et Google Sheets. Les CSV bonus s'ouvrent partout.</p></details>
<details><summary>Et si je suis auto-entrepreneur en franchise TVA ?</summary><p>Le modèle facture l'explique : supprime la ligne TVA et ajoute la mention art. 293 B, déjà écrite dans le fichier.</p></details>
<details><summary>Comment je reçois le pack ?</summary><p>Redirection immédiate vers la page de téléchargement après paiement Stripe. Reçu + facture Stripe par email.</p></details></div>"""
    os.makedirs(os.path.join(PUBLIC, "premium"), exist_ok=True)
    with open(os.path.join(PUBLIC, "premium", "index.html"), "w", encoding="utf-8") as f:
        f.write(base_page(cfg, "Pack premium " + m.get('premium_price',''), "Pack templates factures devis budget Excel PDF.", prem_body, "premium/", prefix="../"))

    # Page merci + fichiers téléchargeables (livraison auto après paiement Stripe)
    dl_dir = os.path.join(PUBLIC, "premium", "telechargement")
    os.makedirs(dl_dir, exist_ok=True)
    try:
        from premium_pack import build_pack
        xlsx = build_pack(dl_dir)
    except ImportError:
        xlsx = []
    fichiers = {
        "budget-mensuel.csv": "Mois;Catégorie;Prévu (€);Réel (€);Écart (€)\nJanvier;Loyer;800;800;0\nJanvier;Courses;350;0;350\nJanvier;Transport;75;0;75\nJanvier;Loisirs;100;0;100\nJanvier;Épargne;150;0;150\n",
        "suivi-factures.csv": "N°;Date;Client;Objet;HT (€);TVA (%);TTC (€);Statut\n2026-001;02/10/2026;Exemple;Prestation design;500;20;600;Payée\n",
    }
    for nom, contenu in fichiers.items():
        with open(os.path.join(dl_dir, nom), "w", encoding="utf-8") as f:
            f.write(contenu)
    merci_body = f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">✅ Merci ! Voici ton pack ({esc(m.get('premium_price','9,90 €'))})</h1>
<p class="lead">Paiement confirmé ? Télécharge tes fichiers Excel ci-dessous (avec versions CSV universelles plus bas). Astuce : commence par l'onglet Guide du budget.</p>
<div class="card-section"><h2>📦 Tes 4 fichiers Excel (formules incluses)</h2>
<div class="guide"><div><b>📊 budget-mensuel.xlsx</b><br>12 mois × 8 catégories + tableau de bord graphique + chasse aux abonnements.<br><a class="btn small" href="../telechargement/budget-mensuel.xlsx" download>Télécharger →</a></div><div><b>🧾 suivi-factures.xlsx</b><br>50 lignes, TTC auto, statuts, reste à encaisser.<br><a class="btn small" href="../telechargement/suivi-factures.xlsx" download>Télécharger →</a></div><div><b>🖨️ modele-facture.xlsx</b><br>Facture pro prête à imprimer (A4), TVA auto.<br><a class="btn small" href="../telechargement/modele-facture.xlsx" download>Télécharger →</a></div><div><b>📝 modele-devis.xlsx</b><br>Devis pro valable 3 mois, acompte 30 %.<br><a class="btn small" href="../telechargement/modele-devis.xlsx" download>Télécharger →</a></div></div>
<p class="hint">Version universelle (sans Excel) : <a href="../telechargement/budget-mensuel.csv" download>budget.csv</a> · <a href="../telechargement/suivi-factures.csv" download>factures.csv</a></p>
<p class="hint">💡 Astuce : ouvre les fichiers dans Excel, LibreOffice (gratuit) ou Google Sheets. Commence par l'onglet Guide du budget, puis remplis ta 1ère facture avec le modèle.</p></div>"""
    os.makedirs(os.path.join(PUBLIC, "premium", "merci"), exist_ok=True)
    with open(os.path.join(PUBLIC, "premium", "merci", "index.html"), "w", encoding="utf-8") as f:
        f.write(base_page(cfg, "Merci ! Télécharge ton pack", "Téléchargement du pack templates.", merci_body, "premium/merci/", prefix="../../", robots="noindex, nofollow"))

    # Pages légales (exigées pour AdSense + confiance)
    tg = cfg.get("telegram_channel", "")
    contact_cta = f"""<div class="actions"><a class="btn" href="{esc(tg)}">✈️ Nous contacter sur Telegram →</a></div>""" if tg else ""
    legales = {
        "a-propos": ("À propos", "Qui est derrière Radin Malin et sa méthode.", f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">À propos de {esc(cfg['site_name'])}</h1>
<p class="lead">{esc(cfg['site_name'])} aide à dépenser moins : outils gratuits pour calculer et comparer, plus 2 comparatifs d'achat chaque jour.</p>
<div class="card-section"><h2>🧭 Notre méthode</h2><div class="guide"><div><b>Indépendance</b><br>Classement par rapport qualité/prix, jamais vendu aux marques.</div><div><b>Transparence</b><br>Liens affiliés signalés, sans surcoût pour toi.</div><div><b>Pratique</b><br>Outils sans inscription, comparatifs de 2 minutes.</div><div><b>Régularité</b><br>Contenu frais chaque jour, prix vérifiés au clic.</div></div></div>"""),
        "contact": ("Contact", "Une erreur, une idée, un partenariat ? Écris-nous.", f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">Contact</h1>
<p class="lead">Prix cassé, lien mort, idée d'outil ou proposition de partenariat : on lit tout et on répond au plus vite.</p>
<div class="card-section"><h2>✈️ Le plus rapide : Telegram</h2><p class="sub">Canal + messages directs, sans spam.</p>{contact_cta}</div>"""),
        "confidentialite": ("Politique de confidentialité", "Cookies, affiliation et données : ce que fait ce site.", f"""<p style="margin-top:6px"><a class="breadcrumb" href="../">← Retour accueil</a></p>
<h1 class="page">Politique de confidentialité</h1>
<p class="lead">Site personnel sans compte ni inscription. Voici exactement ce qui se passe quand tu visites.</p>
<div class="card-section"><h2>🍪 Cookies et publicité</h2><p>Nos partenaires publicitaires (Monetag, Google AdSense) déposent des cookies pour mesurer et personnaliser les annonces. Tu peux les refuser dans ton navigateur, le site reste utilisable.</p>
<h2>🔗 Affiliation</h2><p>Nos boutons « Voir le prix » contiennent un identifiant affilié (Amazon) : si tu achètes dans les 24 h, nous touchons une commission <b>sans surcoût pour toi</b>. C'est ce qui finance les outils gratuits.</p>
<h2>📊 Mesure d'audience</h2><p>Statistiques anonymes éventuelles (pages vues), aucune donnée nominative collectée sur le site. Les outils calculent dans ton navigateur : rien n'est envoyé ni stocké.</p>
<h2>✉️ Contact</h2><p>Pour toute question ou suppression de donnée : passe par la page Contact.</p></div>"""),
    }
    for slug, (titre, meta, body) in legales.items():
        os.makedirs(os.path.join(PUBLIC, slug), exist_ok=True)
        with open(os.path.join(PUBLIC, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(base_page(cfg, titre, meta, body, f"{slug}/", prefix="../"))

    # Sitemap + robots + RSS
    url = cfg["site_url"].rstrip("/")
    entries = [(url + "/", today_iso())]
    entries += [(f"{url}/outils/{t['slug']}/", "") for t in tools]
    entries += [(f"{url}/comparatifs/{a['slug']}/", a.get("pub_date", "")) for a in articles]
    entries += [(url + pp, "") for pp in ["/premium/", "/premium/merci/", "/a-propos/", "/contact/", "/confidentialite/"]]
    entries += [(f"{url}/categorie/{c}/", today_iso()) for c in sorted({a['category'] for a in articles})]
    entries += [(f"{url}/versus/{dslug}/", a.get("pub_date", "")) for a, dslug in duels]
    entries += [(f"{url}/quiz/{s}/", today_iso()) for s in quiz_slugs]
    entries += [(url + "/idees-cadeaux/", today_iso())]
    entries += [(url + "/promos/", today_iso())]
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
        [f"<url><loc>{esc(u)}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "<changefreq>weekly</changefreq></url>" for u, d in entries]) + "</urlset>"
    with open(os.path.join(PUBLIC, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    with open(os.path.join(PUBLIC, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nDisallow: /radin-malin/premium/merci/\nDisallow: /radin-malin/premium/telechargement/\nSitemap: {url}/sitemap.xml\n")
    rss_items = "".join([f"<item><title>{esc(a['title'])}</title><link>{esc(url)}/comparatifs/{esc(a['slug'])}/</link><description>{esc(a['title'])}</description><enclosure url=\"{esc(url)}/pins/{esc(a['slug'])}.png\" type=\"image/png\" /></item>" for a in reversed(articles[-10:])])
    rss = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(cfg["site_name"])}</title><link>{esc(url)}/</link><description>{esc(cfg["site_description"])}</description>{rss_items}</channel></rss>'
    with open(os.path.join(PUBLIC, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    # 404 utile (GitHub Pages l'affiche pour toute URL inconnue)
    notfound = """<p style="margin-top:6px"><a class="breadcrumb" href="./">← Retour accueil</a></p>
<h1 class="page">Oups, cette page n'existe plus (404)</h1>
<p class="lead">Le comparatif a peut-être déménagé. Voici les raccourcis les plus utiles :</p>
<div class="actions"><a class="btn" href="./#outils">🧰 Outils gratuits</a><a class="btn ghost" style="color:#111;background:#fff;border:1px solid #ddd;box-shadow:none" href="./#comparatifs">⭐ Comparatifs</a></div>"""
    with open(os.path.join(PUBLIC, "404.html"), "w", encoding="utf-8") as f:
        f.write(base_page(cfg, "Page introuvable", "Erreur 404 : cette page n'existe pas.", notfound, "404.html"))

    # llms.txt : resume machine pour les IA (GEO)
    lines = [f"# {cfg['site_name']}", "", f"> {cfg['site_description']}", "",
             f"Accueil : {url}/", "", "## Outils gratuits"]
    lines += [f"- [{t['h1']}]({url}/outils/{t['slug']}/) : {t['meta']}" for t in tools]
    lines += ["", "## Derniers comparatifs"]
    lines += [f"- [{a['title']}]({url}/comparatifs/{a['slug']}/) ({a['keyword']})" for a in reversed(articles[-15:])]
    lines += ["", "## Premium", f"- [Pack Excel]({url}/premium/) : {m.get('premium_product', '')}"]
    with open(os.path.join(PUBLIC, "llms.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Visuels Pinterest 1000x1500 (1 par article, ignores si Pillow absent)
    try:
        from pin_images import build_all as build_pins
        n = build_pins(articles, cfg["site_name"], os.path.join(PUBLIC, "pins"))
        print(f"PINS : {n} nouveaux visuels")
    except ImportError:
        print("PINS : Pillow absent, visuels ignores")

    # Fichiers statiques (vérifications Monetag/AdSense, etc.) : copiés tels quels
    static_dir = os.path.join(ROOT, "static")
    if os.path.isdir(static_dir):
        for entry in os.listdir(static_dir):
            if entry == "LISEZ-MOI.txt":
                continue
            src = os.path.join(static_dir, entry)
            dst = os.path.join(PUBLIC, entry)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)

    print(f"BUILD OK : {len(tools)} outils, {len(articles)} articles -> {PUBLIC}")
    return len(tools), len(articles)

if __name__ == "__main__":
    build()
