# 💰 Radin Malin — outils gratuits & comparatifs

Site statique : **15 outils gratuits** + comparatifs d'achat + duels + quiz + hubs + promos en cours.
Publication automatique : 2 comparatifs par jour, priorité aux sujets saisonniers.
Diffusion automatique : Telegram, Bluesky, Mastodon, Pinterest.
Coût d'hébergement : 0 € (GitHub Pages).

## ⚙️ Fonctionnement

- **Outils** (`data/tools.json`) : calculatrices et convertisseurs 100% navigateur, sans inscription.
- **Comparatifs** (`data/keywords.json` → `data/published.json`) : `daily.py` publie le prochain sujet (saisonnier d'abord), avec boutons "Voir le prix", podium, FAQ, schemas Article/FAQ/Breadcrumb.
- **Duels** (`/versus/`) : 1 page "X vs Y" par comparatif, générée depuis les 2 premiers produits.
- **Quiz** (`data/quizzes.json`) : questionnaires 30 secondes avec recommandation + partage.
- **Hubs** : 6 catégories + `/idees-cadeaux/` (saisonniers) + `/promos/` (calendrier `data/promos.json` : seules les opérations en cours s'affichent, les terminées disparaissent seules).
- **Pages** : premium (`/premium/`, livraison `/premium/merci/` noindex), légales, 404, `llms.txt`, `sitemap.xml` (lastmod réelles), `rss.xml` (avec images), `static/` (fichiers racine : vérifications, icônes, ads.txt).

## 🚀 Lancer en local

```powershell
python -m unittest discover -s tests -v   # 44 tests d'abord
python build.py                             # génère public/
python -m http.server 8000 --directory public
python daily.py        # publie vraiment le prochain sujet !
python stats.py        # tableau de bord local et privé
```

## 🔑 Config (`config.json`)

Identité (`site_url`, `site_name`…), monétisation (`monetization.*` : tags Amazon/pubs, liens Stripe/PayPal — PayPal masqué si non configuré), liens sociaux (masqués si vides), `ga_id`, `head_extra`, `google_site_verification`.
Consentement : bandeau + cases mesure/pubs, GA et pubs chargés uniquement après acceptation (`rmShow()` rouvre le choix).
Jamais de code dans `build.py` pour un snippet : tout passe par `config.json`.
Jamais de secret commité : clés en Secrets GitHub ou variables d'environnement.

## 🤖 Automatisation (GitHub Actions)

- `daily.yml` (6h + 18h, et chaque push) : tests → publie → rebuild → commit → déploie `gh-pages`.
- `social.yml` (à chaque publication) : Telegram + Bluesky + Mastodon (3 max/run, skip sans secrets).

## 🔗 Fraîcheur des liens et promos

- Aucun prix statique affiché (fourchettes + boutons) : rien ne se périme.
- Test d'intégrité à chaque build : zéro lien interne mort, formats affiliés vérifiés.
- Promos pilotées par calendrier (`start`/`end`) : ajout et retrait automatiques au quotidien.
- Pas de scraping de prix (bloqué techniquement et interdit par les ToS).

## 🧪 Tests (44, obligatoires)

`test_tools`, `test_build` (pages, SEO, packs, quiz, duels, hubs, promos, cadeaux), `TestLiens`, `TestLib`, `test_social`.
Aucun push en échec (CI bloquante). Toute feature arrive avec ses tests.

## 📁 Fichiers

- `build.py`, `lib.py`, `daily.py`
- `social_post.py`, `post_bsky.py`, `post_masto.py`, `social_text.py`
- `premium_pack.py`, `pin_images.py`, `gen_icons.py`, `stats.py`
- `config.json`, `data/{tools,keywords,quizzes,promos,published,posted_*,pinned}.json`, `static/`, `tests/`
- `.github/workflows/` (daily, social) — `root-site/` = repo séparé `kirito83.github.io`
