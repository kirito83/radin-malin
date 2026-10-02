# 💰 Radin Malin — machine à cash 100% auto (0 € de départ)

Site statique SEO : **10 outils gratuits** (trafic stable) + **1 comparatif affilié publié chaque jour en automatique**.
Monétisation : affiliation Amazon + pubs display + produit premium Stripe/PayPal.
Coût : 0 € (Python stdlib, GitHub Pages gratuit).

## 💸 Comment ça gagne (même des centimes, en auto)

1. **Outils gratuits** → trafic Google evergreen (ex: "calcul TVA", "mensualité prêt").
2. **Comparatifs auto** (`data/keywords.json` → 30 idées, `daily.py` en publie 1/jour) → pages "meilleur X" avec boutons **Voir le prix** affiliés.
3. **Pubs** → s'activent seules dès que tu colles ton ID AdSense ou Monetag dans `config.json`.
4. **Premium Stripe/PayPal** → tu as déjà Stripe/PayPal : vends le pack templates via Payment Link (encaissement + livraison auto).

Ordre de grandeur honnête : 0 € tant que pas indexé (2-4 semaines), premiers centimes vers 100-500 visites/jour, puis ça scale avec le nombre d'articles (déjà automatisé).

## 🚀 Lancer en local (vérifié)

```powershell
python build.py        # génère le site dans public/
python -m http.server 8000 --directory public
# ouvrir http://localhost:8000
python daily.py        # simule la tâche du jour : +1 article + rebuild
```

## 🌍 Mettre en ligne gratuit (obligatoire pour gagner)

**Option A — GitHub Pages (recommandé, 5 min) :**
1. `git init; git add -A; git commit -m "init";` pousse sur GitHub.
2. Modifie `config.json` → `site_url` avec ta vraie URL (`https://TON-PSEUDO.github.io/TON-REPO`).
3. Le workflow `.github/workflows/daily.yml` publie 1 article/jour + déploie tout seul.
4. Dans GitHub → Settings → Pages → Source : `gh-pages`.

**Option B — Cloudflare Pages :** connecte le repo, build command `python build.py`, output `public/`.

## 🔑 Activer les revenus (3 champs dans `config.json`)

| Revenu | Champ | Où l'obtenir (gratuit) |
|---|---|---|
| Amazon affiliation | `amazon_tag` | Amazon Partenaires → ton tag `xxx-21` (3 ventes/180j requises sinon) |
| Pubs Google | `adsense_client` | AdSense → `ca-pub-xxx` (accepte après ~20-30 pages) |
| Pubs faciles (en attendant AdSense) | `monetag_tag` | Monetag.com → tag JS (acceptation immédiate) |
| Vente premium auto | `stripe_pro_link` / `paypal_link` | Stripe Dashboard → Payment Links / PayPal.me |

Sans les IDs, les boutons pointent vers la recherche Amazon simple (0 commission) et les pubs sont masquées : le site tourne quand même et accumule le SEO.

## 🤖 Automatisation quotidienne

- `daily.py` : prend le prochain mot-clé de `data/keywords.json`, l'ajoute à `data/published.json`, rebuild (`sitemap.xml` + `rss.xml` inclus).
- GitHub Actions (`daily.yml`) : cron `7 6 * * *` → commit + deploy, zéro action manuelle.
- Stock actuel : 30 mots-clés = 30 jours d'autonomie. Pour scaler : ajoute des lignes dans `keywords.json` (même format).

## 📁 Fichiers

- `build.py` — générateur statique (stdlib only)
- `daily.py` — job quotidien auto
- `config.json` — URLs + IDs monétisation
- `data/tools.json` — 10 outils
- `data/keywords.json` — 30 comparatifs programmés
- `data/published.json` — auto-généré (historique)
- `public/` — site généré (ne pas éditer à la main)
- `.github/workflows/daily.yml` — cron + deploy Pages

## ⚠️ Honnêteté

Pas de magie : sans mise en ligne + indexation Google, gain = 0. Ce repo maximise les probas avec 0 € : SEO programmatic, contenu quotidien auto, 5 leviers de revenus cumulés. Prochaine étape après premiers centimes : Search Console + 100 articles + Pinterest auto.
