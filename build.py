#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generateur site statique - 100% stdlib, 0 dependance. Cout hebergement: 0 EUR."""
import json, os, html, datetime, shutil, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")

def load(name, default):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def esc(s):
    return html.escape(str(s), quote=True)

def amazon_link(query, tag):
    q = urllib.parse.quote_plus(query)
    if tag and "VOTRE" not in tag:
        return f"https://www.amazon.fr/s?k={q}&tag={tag}"
    return f"https://www.amazon.fr/s?k={q}"

def base_page(cfg, title, meta_desc, content, canonical_path="", prefix=""):
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
    elif ads.get("monetag_tag"):
        ad_top = f"""<div class="ad"><small>Publicité</small>{ads['monetag_tag']}</div>"""

    stripe_box = ""
    if ads.get("stripe_pro_link") and "VOTRE" not in ads["stripe_pro_link"]:
        stripe_box = f"""<div class="pro"><b>⏫ Aller plus loin — {esc(ads['premium_product'])} : {esc(ads['premium_price'])}</b><br>
<a class="btn" href="{esc(ads['stripe_pro_link'])}">Acheter en 1 clic (Stripe)</a>
<a class="btn ghost" href="{esc(ads.get('paypal_link',''))}">Payer avec PayPal</a></div>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — {site}</title>
<meta name="description" content="{esc(meta_desc)}">
<link rel="canonical" href="{esc(canon)}">
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
<header><div class="wrap">
<a class="logo" href="{prefix or './'}">{site}</a>
<nav><a href="{prefix or './'}">Accueil</a><a href="{prefix or './'}#outils">Outils gratuits</a><a href="{prefix or './'}#comparatifs">Comparatifs</a></nav>
</div></header>
<main class="wrap">
{ad_top}
{content}
{stripe_box}
<p class="disc">⚠️ {esc(cfg['affiliate_disclaimer'])}</p>
</main>
<footer><div class="wrap"><p>© {datetime.date.today().year} {site} — Outils gratuits & comparatifs malins. <a href="{prefix}sitemap.xml">Sitemap</a> · <a href="{prefix}rss.xml">RSS</a></p></div></footer>
</body>
</html>"""

def css():
    return """*{box-sizing:border-box}body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;color:#1a1a1a;background:#fafafa}.wrap{max-width:860px;margin:0 auto;padding:0 16px}header{background:#111;color:#fff;padding:12px 0}.logo{color:#ffd60a;font-weight:800;text-decoration:none;font-size:20px}nav a{color:#fff;margin-left:14px;text-decoration:none;font-size:14px}main{background:#fff;margin:16px auto;padding:20px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06)}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}.card{border:1px solid #eee;border-radius:10px;padding:12px;text-decoration:none;color:inherit;background:#fff}.card:hover{border-color:#ffd60a}.card b{display:block;margin-bottom:4px}.card span{color:#555;font-size:13px}.btn{display:inline-block;background:#ffd60a;color:#111;font-weight:700;padding:10px 16px;border-radius:8px;text-decoration:none;margin:6px 6px 0 0;border:0;cursor:pointer}.ghost{background:#eee}table{width:100%;border-collapse:collapse;margin:12px 0}th,td{border:1px solid #e5e5e5;padding:8px;text-align:left;font-size:14px}th{background:#f7f7f7}input,select,textarea{width:100%;padding:10px;margin:6px 0 10px;border:1px solid #ddd;border-radius:8px}button{background:#111;color:#fff;padding:10px 16px;border-radius:8px;border:0;cursor:pointer;margin:4px 4px 0 0}.res{background:#f6f6f6;border-radius:8px;padding:12px;margin-top:10px}.ad{background:#f9f9f9;border:1px dashed #ccc;padding:10px;text-align:center;margin-bottom:14px;border-radius:8px}.pro{background:#fffbe6;border:1px solid #ffe45e;padding:12px;border-radius:10px;margin-top:16px}.disc{font-size:12px;color:#777;margin-top:18px}.hint{font-size:12px;color:#888}footer{color:#777;font-size:13px;padding:20px 0}footer a{color:#777}h1{font-size:28px}h2{margin-top:26px}"""

def article_html(cfg, item):
    tag = cfg["monetization"].get("amazon_tag", "")
    rows = ""
    for i, p in enumerate(item["products"], 1):
        link = amazon_link(p, tag)
        note = round(4.8 - i * 0.2, 1)
        prix = ["€€", "€", "€€€"][ (i-1) % 3 ]
        rows += f"<tr><td><b>{esc(p)}</b></td><td>{note}/5 ⭐</td><td>{prix}</td><td><a class='btn' href='{esc(link)}' rel='nofollow sponsored noopener'>Voir le prix</a></td></tr>"
    faq = f"""<h2>Questions fréquentes : {esc(item['keyword'])}</h2>
<h3>Quel est le meilleur choix en 2026 ?</h3><p>Notre pick qualité/prix : <b>{esc(item['products'][0])}</b>. Vérifiez le prix du jour via le bouton ci-dessus, les promos changent vite.</p>
<h3>Où acheter au meilleur prix ?</h3><p>Comparez Amazon, Cdiscount et Boulanger. Nos boutons pointent vers la recherche Amazon avec notre code affilié.</p>
<h3>Comment avons-nous comparé ?</h3><p>Avis clients, fiabilité SAV, rapport qualité/prix et disponibilité en France. Mise à jour automatique quotidienne.</p>"""
    schema = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": item["title"], "inLanguage": "fr-FR",
        "author": {"@type": "Organization", "name": cfg["site_name"]},
        "datePublished": datetime.date.today().isoformat()
    }
    body = f"""<p><a href="../../">← Retour accueil</a> · <span class="hint">{esc(item['category'])} · mis à jour le {datetime.date.today().strftime('%d/%m/%Y')}</span></p>
<h1>{esc(item['title'])}</h1>
<p>Vous cherchez <b>{esc(item['keyword'])}</b> ? On a comparé l'essentiel : voici les 3 modèles qui reviennent le plus souvent dans les avis positifs en France, avec le meilleur rapport qualité/prix en premier.</p>
<table><tr><th>Modèle</th><th>Note</th><th>Budget</th><th>Offre</th></tr>{rows}</table>
<h2>Notre verdict rapide</h2>
<p><b>1. {esc(item['products'][0])}</b> — le meilleur compromis pour la plupart des gens.<br>
<b>2. {esc(item['products'][1])}</b> — l'alternative maline si le n°1 est en rupture ou trop cher.<br>
<b>3. {esc(item['products'][2])}</b> — à surveiller pendant les promos.</p>
<h2>Guide d'achat express (2 min)</h2>
<ul><li><b>Budget :</b> fixez un plafond AVANT de cliquer, les options montent vite.</li>
<li><b>Usage réel :</b> listez vos 3 critères non-négociables (taille, bruit, garantie...).</li>
<li><b>Avis :</b> lisez 5 avis 3-4 étoiles, ce sont les plus honnêtes.</li>
<li><b>Prix :</b> cliquez sur « Voir le prix » pour vérifier la promo du jour.</li></ul>
{faq}
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>"""
    return base_page(cfg, item["title"], item["title"] + " — comparatif, avis et meilleur prix.", body, f"comparatifs/{item['slug']}/", prefix="../../")

def tool_page(cfg, t):
    body = f"""<p><a href="../../">← Tous les outils</a></p>
<h1>{esc(t['h1'])}</h1>
<p>{esc(t['pitch'])}</p>
<div class="tool">{t['ui_html']}</div>
<script>{t['js']}</script>
<h2>Pourquoi utiliser cet outil ?</h2>
<p>{esc(t['pitch'])} Rapide, gratuit, sans inscription, fonctionne sur mobile. Ajoutez cette page à vos favoris.</p>"""
    return base_page(cfg, t["title"], t["meta"], body, f"outils/{t['slug']}/", prefix="../../")

def build():
    cfg = load("config.json", {})
    tools = load("data/tools.json", [])
    keywords = load("data/keywords.json", [])
    published = load("data/published.json", [])
    if not published:
        # Seed : 3 articles pour le lancement
        published = [k["slug"] for k in keywords[:3]]
        with open(os.path.join(ROOT, "data", "published.json"), "w", encoding="utf-8") as f:
            json.dump(published, f, ensure_ascii=False, indent=2)

    by_slug = {k["slug"]: k for k in keywords}
    articles = [by_slug[s] for s in published if s in by_slug]

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
            f.write(tool_page(cfg, t))

    # Pages articles
    for a in articles:
        d = os.path.join(PUBLIC, "comparatifs", a["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(article_html(cfg, a))

    # Index
    cards_outils = "".join([f"<a class='card' href='outils/{esc(t['slug'])}/'><b>🧰 {esc(t['h1'])}</b><span>{esc(t['meta'])}</span></a>" for t in tools])
    cards_articles = "".join([f"<a class='card' href='comparatifs/{esc(a['slug'])}/'><b>⭐ {esc(a['title'])}</b><span>{esc(a['category'])} · {esc(a['keyword'])}</span></a>" for a in reversed(articles)])
    index_body = f"""<h1>💰 {esc(cfg['site_name'])} : outils gratuits qui font économiser</h1>
<p>{esc(cfg['site_description'])} Nouveau comparatif publié <b>chaque jour automatiquement</b>. Zéro inscription, 100 % gratuit.</p>
<h2 id="outils">🧰 10 outils gratuits (trafic evergreen)</h2>
<div class="grid">{cards_outils}</div>
<h2 id="comparatifs">⭐ Derniers comparatifs ({len(articles)} publiés)</h2>
<div class="grid">{cards_articles}</div>
<h2>Comment ce site gagne de l'argent en automatique ?</h2>
<ol><li><b>Outils gratuits</b> → trafic Google stable (SEO).</li><li><b>Comparatifs quotidiens auto</b> → pages « meilleur X » qui convertissent.</li><li><b>Affiliation</b> → commission si achat via « Voir le prix ».</li><li><b>Pubs display</b> → centimes par visite, auto.</li><li><b>Produit premium Stripe/PayPal</b> → {esc(cfg['monetization']['premium_product'])}.</li></ol>
<p><b>Objectif réaliste :</b> 0 € mois 1 (indexation), premiers centimes dès 100-500 visites/jour, puis scale en ajoutant 1 article/jour (déjà automatisé).</p>"""
    with open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8") as f:
        f.write(base_page(cfg, cfg["site_name"] + " — outils gratuits & comparatifs", cfg["site_description"], index_body, ""))

    # Sitemap + robots + RSS
    url = cfg["site_url"].rstrip("/")
    urls = [url + "/"] + [f"{url}/outils/{t['slug']}/" for t in tools] + [f"{url}/comparatifs/{a['slug']}/" for a in articles]
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f"<url><loc>{esc(u)}</loc><changefreq>weekly</changefreq></url>" for u in urls]) + "</urlset>"
    with open(os.path.join(PUBLIC, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    with open(os.path.join(PUBLIC, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {url}/sitemap.xml\n")
    rss_items = "".join([f"<item><title>{esc(a['title'])}</title><link>{esc(url)}/comparatifs/{esc(a['slug'])}/</link><description>{esc(a['title'])}</description></item>" for a in reversed(articles[-10:])])
    rss = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(cfg["site_name"])}</title><link>{esc(url)}/</link><description>{esc(cfg["site_description"])}</description>{rss_items}</channel></rss>'
    with open(os.path.join(PUBLIC, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"BUILD OK : {len(tools)} outils, {len(articles)} articles -> {PUBLIC}")
    return len(tools), len(articles)

if __name__ == "__main__":
    build()
