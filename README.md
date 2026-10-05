# 💰 Radin Malin — machine à cash 100% auto (0 € de départ)

Site statique SEO : **15 outils gratuits** + **2 comparatifs/jour en automatique** + duels "X vs Y" + quiz + hubs catégories + page saisonnière.
Monétisation : Amazon affiliation + Monetag + Stripe 9,90€ + AdSense (demandé).
Diffusion auto : Telegram + Bluesky + Mastodon + Pinterest (RSS).
Coût : 0 € (Python, GitHub Pages gratuit).

## 💸 Comment ça gagne

1. **Outils gratuits** → trafic evergreen (TVA, brut/net, notaire, IMC…).
2. **Comparatifs + duels + quiz** → pages "meilleur X" avec boutons **Voir le prix** affiliés (`radinmalin-21`, cookie 24h sur tout achat).
3. **Pubs display** → Monetag actif (vignette 1x/24h), AdSense en examen.
4. **Premium 9,90€** → pack Excel (budget, factures, devis) vendu via Stripe, livré en auto sur `/premium/merci/`.

## 🚀 Lancer en local

```powershell
python -m unittest discover -s tests -v   # d'abord les tests (42)
python build.py                             # génère public/
python -m http.server 8000 --directory public
python daily.py        # simule la publication du jour (publie vraiment !)
python stats.py        # tableau de bord local et privé
```

## 🔑 Config (`config.json`)

| Champ | Rôle |
|---|---|
| `site_url`, `site_name`… | Identité du site |
| `monetization.amazon_tag` | Tag affiliation Amazon |
| `monetization.monetag_tag` / `adsense_client` | Tags pubs (vignette plafonnée auto 1x/24h) |
| `monetization.stripe_pro_link` / `paypal_link` | Liens de paiement (PayPal masqué si non configuré) |
| `telegram_channel`, `social_bsky`, `social_masto` | Liens footer + boutons (masqués si vides) |
| `analytics_script`, `head_extra` | GA4 + metas de vérification (ne jamais coller de code dans `build.py`) |
| `google_site_verification` | Search Console |

Ne jamais commiter de secret : clés API uniquement en Secrets GitHub ou variables d'environnement.

## 🤖 Automatisation (GitHub Actions)

- `daily.yml` : cron 6h + 18h → tests → publie 1 article (priorité saisonnière Noël/BF) → rebuild → commit → déploie `gh-pages`.
- `social.yml` : sur chaque publication → Telegram + Bluesky + Mastodon (3 max/run, anti-flood, skip sans secrets).

## 🔗 Liens toujours à jour (politique)

- **Prix** : aucun prix statique affiché (que des fourchettes € et des boutons "Voir le prix") → rien ne se périme, le prix réel est toujours celui du clic.
- **Affiliation** : URLs recherche Amazon + tag, vérifiées par tests à chaque build (format + tag sur 100+ boutons).
- **Internes** : test d'intégrité à chaque build (aucun lien mort toléré).
- **Externes** : pas de scraping Amazon (bloqué + interdit) ; l'API PA-API sera branchée après les 3 premières ventes si pertinent.

## 🧪 Tests (obligatoires, 42)

`test_tools` (JS de chaque outil : ids, handlers, syntaxe), `test_build` (pages, sitemap lastmod, RSS, packs, pins, quiz, duels, hubs, GA/pubs/tags), `TestLiens` (zéro lien mort, tags affiliés), `TestLib` (migration dates, sélection saisonnière), `test_social` (textes, facettes octets, anti-flood).

Règles : aucun push si échec (CI bloquante aussi). Toute feature arrive avec ses tests.

## 📁 Fichiers

- `build.py` — générateur (pages, SEO/GEO, packs, pins, sitemap, RSS, llms.txt)
- `lib.py` — JSON + historique `{slug: date}` partagés
- `daily.py` — sélection (saisonnier d'abord) + build
- `social_post.py`, `post_bsky.py`, `post_masto.py`, `social_text.py` — autoposts
- `premium_pack.py`, `pin_images.py`, `gen_icons.py` — générateurs d'assets
- `stats.py` — dashboard local privé (`STRIPE_SECRET_KEY` en env pour le CA)
- `config.json`, `data/{tools,keywords,quizzes,published}.json`, `static/` (fichiers racine : verifs, icones, ads.txt)
- `tests/` — suite unitaire - `.github/workflows/` — daily, social
- `root-site/` — repo séparé `kirito83.github.io` (racine : redirect, sw.js, robots, ads.txt)

## ⚠️ Honnêteté

Pas de magie : revenus proportionnels au trafic indexé. Le système maximise les probas à 0 € : contenu 2/jour, 5 canaux, 4 revenus, SEO/GEO à jour. Surveiller : indexation Search Console, 3 ventes Amazon/180j, examen AdSense.
