#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests unitaires : textes reseaux (longueurs, facettes, sans appel reseau)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from social_text import build_text, link_facet, pick_todo


class TestSocialText(unittest.TestCase):
    def test_contient_titre_et_lien(self):
        t = build_text("Mon super aspirateur robot", "https://example.com/a/")
        self.assertIn("Mon super aspirateur", t)
        self.assertIn("https://example.com/a/", t)

    def test_limite_bluesky(self):
        t = build_text("x" * 400, "https://example.com/" + "a" * 60)
        self.assertLessEqual(len(t.encode("utf-8")), 260)

    def test_titre_court_intact(self):
        t = build_text("Court", "https://e.com/")
        self.assertTrue(t.startswith("⭐ Court"))

    def test_facet_offsets_octets(self):
        url = "https://ex.com/éè"
        t = "Voir 👉 " + url
        f = link_facet(t, url)
        raw = t.encode("utf-8")
        self.assertIsNotNone(f)
        self.assertEqual(raw[f["index"]["byteStart"]:f["index"]["byteEnd"]].decode("utf-8"), url)

    def test_facet_absente_sans_lien(self):
        self.assertIsNone(link_facet("rien ici", "https://absent.com/"))

    def test_tags_optionnels(self):
        t = build_text("Titre", "https://e.com/", tags=["#bonplan"])
        self.assertIn("#bonplan", t)

    def test_pick_todo_anti_flood(self):
        slugs = [f"a{i}" for i in range(10)]
        todo, skipped = pick_todo(slugs, [], limit=3)
        self.assertEqual(todo, ["a7", "a8", "a9"])
        self.assertEqual(len(skipped), 7)
        todo2, skipped2 = pick_todo(slugs, ["a%d" % i for i in range(8)], limit=3)
        self.assertEqual(todo2, ["a8", "a9"])
        self.assertEqual(skipped2, [])


if __name__ == "__main__":
    unittest.main()
