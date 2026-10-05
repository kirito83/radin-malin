#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tache quotidienne 100% auto : publie le prochain comparatif + rebuild. Utilise par GitHub Actions (cron)."""
from lib import load, load_published, save_published, today_iso
from build import build

def select_next(keywords, published):
    """Rend le prochain mot-cle non publie (pur, testable)."""
    done = set(published.keys()) if isinstance(published, dict) else set(published)
    for k in keywords:
        if k["slug"] not in done:
            return k
    return None

def main():
    keywords = load("data/keywords.json", [])
    published = load_published()
    nxt = select_next(keywords, published)
    if not nxt:
        print("STOCK EPUISE : tous les mots-cles sont publies. Ajoutez-en dans data/keywords.json.")
    else:
        published[nxt["slug"]] = today_iso()
        save_published(published)
        print(f"NOUVEL ARTICLE PUBLIE : {nxt['slug']} ({len(published)}/{len(keywords)})")
    n_tools, n_articles = build()
    print(f"SITE REGENERE : {n_tools} outils, {n_articles} articles.")

if __name__ == "__main__":
    main()
