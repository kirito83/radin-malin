#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests unitaires : generation du site (pages, sitemap, rss, monétisation, packs).
Lancez : python -m unittest discover -s tests -v
"""
import json, os, re, unittest, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public")

import sys
sys.path.insert(0, ROOT)
import build
import lib


def read_pub(path):
    with open(os.path.join(PUBLIC, path), encoding="utf-8") as f:
        return f.read()


class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        n_tools, n_articles = build.build()
        assert n_tools > 0 and n_articles > 0
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
            cls.cfg = json.load(f)
        with open(os.path.join(ROOT, "data", "tools.json"), encoding="utf-8") as f:
            cls.tools = json.load(f)
        cls.pub = lib.load_published()
        cls.slugs = list(cls.pub.keys()) if isinstance(cls.pub, dict) else cls.pub

    def test_pages_outils(self):
        import html as html_mod
        for t in self.tools:
            with self.subTest(outil=t["slug"]):
                html = read_pub(f"outils/{t['slug']}/index.html")
                self.assertIn(html_mod.escape(t["h1"], quote=True), html)
                self.assertIn("<script>", html)

    def test_pages_articles(self):
        for s in self.slugs:
            with self.subTest(article=s):
                html = read_pub(f"comparatifs/{s}/index.html")
                self.assertIn("Voir le prix", html)
                self.assertIn("FAQPage", html)
                self.assertIn("BreadcrumbList", html)

    def test_tag_affiliation_partout(self):
        tag = self.cfg["monetization"]["amazon_tag"]
        for s in self.slugs:
            with self.subTest(article=s):
                self.assertIn(f"tag={tag}", read_pub(f"comparatifs/{s}/index.html"))

    def test_sitemap_valide(self):
        root = ET.parse(os.path.join(PUBLIC, "sitemap.xml")).getroot()
        locs = [u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text for u in root]
        self.assertIn(self.cfg["site_url"].rstrip("/") + "/", locs)
        for s in self.slugs:
            self.assertIn(f"/comparatifs/{s}/", "".join(locs))

    def test_rss_valide(self):
        root = ET.parse(os.path.join(PUBLIC, "rss.xml")).getroot()
        items = root.find("channel").findall("item")
        self.assertGreater(len(items), 0)

    def test_pages_speciales(self):
        for p in ["index.html", "404.html", "llms.txt", "robots.txt", "sitemap.xml",
                  "premium/index.html", "premium/merci/index.html",
                  "a-propos/index.html", "contact/index.html", "confidentialite/index.html"]:
            with self.subTest(page=p):
                self.assertTrue(os.path.exists(os.path.join(PUBLIC, p)), f"manquant : {p}")

    def test_merci_noindex(self):
        self.assertIn("noindex", read_pub("premium/merci/index.html"))

    def test_pas_de_placeholders_visibles(self):
        for s in self.slugs:
            html = read_pub(f"comparatifs/{s}/index.html")
            self.assertNotIn("VOTRE-", html)
        self.assertNotIn("paypal.me/VOTRE", read_pub("premium/index.html"))

    def test_packs_telechargeables(self):
        dl = os.path.join(PUBLIC, "premium", "telechargement")
        for f in ["budget-mensuel.xlsx", "suivi-factures.xlsx",
                  "modele-facture.xlsx", "modele-devis.xlsx"]:
            with self.subTest(fichier=f):
                self.assertTrue(os.path.exists(os.path.join(dl, f)))
                self.assertGreater(os.path.getsize(os.path.join(dl, f)), 1000)

    def test_visuels_pins(self):
        for s in self.slugs:
            with self.subTest(article=s):
                p = os.path.join(PUBLIC, "pins", s + ".png")
                self.assertTrue(os.path.exists(p), f"visuel manquant : {s}")

    def test_tags_head(self):
        html = read_pub("index.html")
        self.assertIn("G-VHM284ZNV5", html)
        self.assertIn('name="monetag"', html)

    def test_routage_outils_vers_comparatifs(self):
        with open(os.path.join(ROOT, "data", "tools.json"), encoding="utf-8") as f:
            slugs = [t["slug"] for t in json.load(f)]
        for s in slugs[:3]:
            with self.subTest(outil=s):
                html = read_pub(f"outils/{s}/index.html")
                self.assertIn("Comparatifs du moment", html)
                self.assertIn("comparatifs/", html)


class TestLib(unittest.TestCase):
    def test_migration_liste_vers_dict(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "data"))
            with open(os.path.join(tmp, "data", "published.json"), "w", encoding="utf-8") as f:
                json.dump(["a", "b", "c", "d"], f)
            old_root, lib.ROOT = lib.ROOT, tmp
            try:
                pub = lib.load_published()
            finally:
                lib.ROOT = old_root
        self.assertEqual(set(pub.keys()), {"a", "b", "c", "d"})
        for d in pub.values():
            self.assertRegex(d, r"^\d{4}-\d{2}-\d{2}$")

    def test_select_next(self):
        import daily
        kws = [{"slug": "a"}, {"slug": "b"}, {"slug": "c"}]
        self.assertEqual(daily.select_next(kws, {"a": "2026-01-01"})["slug"], "b")
        self.assertEqual(daily.select_next(kws, ["a", "b"])["slug"], "c")
        self.assertIsNone(daily.select_next(kws, {"a": "x", "b": "x", "c": "x"}))

    def test_select_next_saisonnier_dabord(self):
        import daily
        kws = [{"slug": "a"}, {"slug": "idee-cadeau-x-noel"}, {"slug": "b"}]
        self.assertEqual(daily.select_next(kws, {})["slug"], "idee-cadeau-x-noel")

    def test_lien_telegram_trace(self):
        import social_post
        u = social_post.build_link("https://kirito83.github.io/radin-malin", "mon-article")
        self.assertIn("/comparatifs/mon-article/", u)
        self.assertIn("utm_source=telegram", u)


class TestVersus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build as bmod
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
            cls.cfg = json.load(f)
        with open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8") as f:
            cls.by_slug = {k["slug"]: k for k in json.load(f)}
        import lib as libmod
        pub = libmod.load_published()
        cls.slugs = list(pub.keys()) if isinstance(pub, dict) else pub
        cls.duels = [(s, bmod.slugify(cls.by_slug[s]["products"][0]) + "-vs-" + bmod.slugify(cls.by_slug[s]["products"][1])) for s in cls.slugs]

    def test_slugify_sain(self):
        import build as bmod
        self.assertEqual(bmod.slugify("Roborock Q7 Max"), "roborock-q7-max")
        self.assertRegex(bmod.slugify("L'Oréal Crème"), r"^[a-z0-9-]+$")

    def test_pages_duels(self):
        tag = self.cfg["monetization"]["amazon_tag"]
        for s, dslug in self.duels:
            with self.subTest(duel=dslug):
                html = read_pub(f"versus/{dslug}/index.html")
                p1, p2 = self.by_slug[s]["products"][:2]
                self.assertIn(p1, html)
                self.assertIn(p2, html)
                self.assertIn(f"tag={tag}", html)
                self.assertIn("BreadcrumbList", html)

    def test_lien_duel_depuis_article(self):
        for s, dslug in self.duels[:5]:
            with self.subTest(article=s):
                self.assertIn(f"versus/{dslug}/", read_pub(f"comparatifs/{s}/index.html"))

    def test_duels_dans_sitemap(self):
        with open(os.path.join(PUBLIC, "sitemap.xml"), encoding="utf-8") as f:
            sm = f.read()
        for _, dslug in self.duels:
            self.assertIn(f"/versus/{dslug}/", sm)


class TestQuiz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "quizzes.json"), encoding="utf-8") as f:
            cls.quizzes = json.load(f)
        with open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8") as f:
            cls.by_slug = {k["slug"]: k for k in json.load(f)}

    def test_quizzes_valides(self):
        for q in self.quizzes:
            with self.subTest(quiz=q["slug"]):
                self.assertIn(q["parent"], self.by_slug)
                prods = self.by_slug[q["parent"]]["products"]
                self.assertGreaterEqual(len(prods), 2)
                for qu in q["questions"]:
                    for opt in qu["options"]:
                        self.assertEqual(len(opt["scores"]), len(prods[:3]))

    def test_pages_quiz(self):
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
            tag = json.load(f)["monetization"]["amazon_tag"]
        for q in self.quizzes:
            with self.subTest(quiz=q["slug"]):
                html = read_pub(f"quiz/{q['slug']}/index.html")
                for p in self.by_slug[q["parent"]]["products"][:3]:
                    self.assertIn(p, html)
                self.assertIn(f'TAG="{tag}"', html)
                self.assertIn("showQ()", html)

    def test_hub_cadeaux(self):
        import lib as libmod
        pub = libmod.load_published()
        slugs = list(pub.keys()) if isinstance(pub, dict) else pub
        with open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8") as f:
            kws = {k["slug"]: k for k in json.load(f)}
        gifts_pub = [s for s in slugs if any(w in s for w in ["noel", "cadeau", "avent", "black-friday"])]
        gifts_stock = [s for s in kws if any(w in s for w in ["noel", "cadeau", "avent", "black-friday"])]
        self.assertGreater(len(gifts_stock), 0, "aucun contenu saisonnier en stock")
        if gifts_pub:
            html = read_pub("idees-cadeaux/index.html")
            self.assertIn(kws[gifts_pub[0]]["keyword"].lower(), html.lower())
            with open(os.path.join(PUBLIC, "sitemap.xml"), encoding="utf-8") as f:
                self.assertIn("/idees-cadeaux/", f.read())


if __name__ == "__main__":
    unittest.main()
