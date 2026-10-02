#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tache quotidienne 100% auto : publie le prochain comparatif + rebuild. Utilise par GitHub Actions (cron)."""
import json, os
from build import build

ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    with open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8") as f:
        keywords = json.load(f)
    pub_path = os.path.join(ROOT, "data", "published.json")
    try:
        with open(pub_path, encoding="utf-8") as f:
            published = json.load(f)
    except FileNotFoundError:
        published = []
    remaining = [k for k in keywords if k["slug"] not in published]
    if not remaining:
        print("STOCK EPUISE : tous les mots-cles sont publies. Ajoutez-en dans data/keywords.json.")
    else:
        nxt = remaining[0]
        published.append(nxt["slug"])
        with open(pub_path, "w", encoding="utf-8") as f:
            json.dump(published, f, ensure_ascii=False, indent=2)
        print(f"NOUVEL ARTICLE PUBLIE : {nxt['slug']} ({len(published)}/{len(keywords)})")
    n_tools, n_articles = build()
    print(f"SITE REGENERE : {n_tools} outils, {n_articles} articles.")

if __name__ == "__main__":
    main()
