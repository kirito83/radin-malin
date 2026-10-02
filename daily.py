#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tache quotidienne 100% auto : publie le prochain comparatif + rebuild. Utilise par GitHub Actions (cron)."""
from lib import load, load_published, save_published, today_iso
from build import build

def main():
    keywords = load("data/keywords.json", [])
    published = load_published()
    remaining = [k for k in keywords if k["slug"] not in published]
    if not remaining:
        print("STOCK EPUISE : tous les mots-cles sont publies. Ajoutez-en dans data/keywords.json.")
    else:
        nxt = remaining[0]
        published[nxt["slug"]] = today_iso()
        save_published(published)
        print(f"NOUVEL ARTICLE PUBLIE : {nxt['slug']} ({len(published)}/{len(keywords)})")
    n_tools, n_articles = build()
    print(f"SITE REGENERE : {n_tools} outils, {n_articles} articles.")

if __name__ == "__main__":
    main()
