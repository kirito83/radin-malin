#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests unitaires : validite des donnees + chaque outil JS (references, syntaxe).
Lancez : python -m unittest discover -s tests -v
"""
import json, os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)

def strip_js(js):
    """Retire chaines et commentaires pour controler l'equilibre des symboles."""
    out, i, n = [], 0, len(js)
    while i < n:
        c = js[i]
        if c in "'\"`":
            q = c
            i += 1
            while i < n and js[i] != q:
                i += 2 if js[i] == "\\" else 1
            i += 1
        elif js.startswith("//", i):
            j = js.find("\n", i)
            i = n if j == -1 else j + 1
        elif js.startswith("/*", i):
            j = js.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)

def balanced(js):
    code = strip_js(js)
    pairs = {"}": "{", ")": "(", "]": "["}
    stack = []
    for c in code:
        if c in "{([":
            stack.append(c)
        elif c in pairs:
            if not stack or stack.pop() != pairs[c]:
                return False
    return not stack


class TestData(unittest.TestCase):
    def test_json_valides(self):
        for f in ["config.json", "data/tools.json", "data/keywords.json", "data/published.json"]:
            with self.subTest(fichier=f):
                load_json(f)

    def test_config_requise(self):
        cfg = load_json("config.json")
        self.assertTrue(cfg["site_url"].startswith("https://"))
        self.assertIn("monetization", cfg)

    def test_published_coherent(self):
        pub = load_json("data/published.json")
        slugs = set(pub.keys()) if isinstance(pub, dict) else set(pub)
        kws = {k["slug"] for k in load_json("data/keywords.json")}
        self.assertTrue(slugs <= kws, f"slugs inconnus : {slugs - kws}")
        if isinstance(pub, dict):
            for s, d in pub.items():
                self.assertRegex(d, r"^\d{4}-\d{2}-\d{2}$", f"date invalide pour {s}")


class TestTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = load_json("data/tools.json")

    def test_champs_requis(self):
        for t in self.tools:
            with self.subTest(outil=t.get("slug")):
                for champ in ["slug", "title", "meta", "h1", "pitch", "ui_html", "js"]:
                    self.assertTrue(t.get(champ), f"champ vide : {champ}")
                self.assertRegex(t["slug"], r"^[a-z0-9-]+$")

    def test_slugs_uniques(self):
        slugs = [t["slug"] for t in self.tools]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_ids_references_existent(self):
        for t in self.tools:
            with self.subTest(outil=t["slug"]):
                ids_ui = set(re.findall(r"id='([^']+)'", t["ui_html"]))
                ids_ui |= set(re.findall(r'id="([^"]+)"', t["ui_html"]))
                for ref in set(re.findall(r"getElementById\('([^']+)'\)", t["js"])):
                    self.assertIn(ref, ids_ui, f"id '{ref}' introuvable dans ui_html")
                for ref in set(re.findall(r'getElementById\("([^"]+)"\)', t["js"])):
                    self.assertIn(ref, ids_ui, f'id "{ref}" introuvable dans ui_html')

    def test_handlers_definis(self):
        for t in self.tools:
            with self.subTest(outil=t["slug"]):
                definies = set(re.findall(r"function\s+([A-Za-z_$][\w$]*)\s*\(", t["js"]))
                for h in set(re.findall(r"onclick='([A-Za-z_$][\w$]*)\(\)'", t["ui_html"])):
                    self.assertIn(h, definies, f"handler '{h}()' non defini")
                for h in set(re.findall(r'oninput="([A-Za-z_$][\w$]*)\(\)"', t["ui_html"])):
                    self.assertIn(h, definies, f"handler '{h}()' non defini")

    def test_js_equilibre(self):
        for t in self.tools:
            with self.subTest(outil=t["slug"]):
                self.assertTrue(balanced(t["js"]), "accolades/parentheses desequilibrees")

    def test_boutons_presents(self):
        for t in self.tools:
            with self.subTest(outil=t["slug"]):
                self.assertIn("<button", t["ui_html"])
                self.assertIn("id='res'", t["ui_html"].replace('"', "'"))


if __name__ == "__main__":
    unittest.main()
