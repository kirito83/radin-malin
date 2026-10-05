#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Code partage : chargement JSON + historique {slug: date de publication}."""
import json, os, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(name, default=None):
    return read_json(os.path.join(ROOT, name), default)

def today_iso():
    return datetime.date.today().isoformat()

def load_published():
    """Rend un dict slug -> date ISO. Migre l'ancien format liste en
    reconstituant ~2 publications/jour a rebours depuis aujourd'hui."""
    raw = load("data/published.json", [])
    if isinstance(raw, dict) and raw:
        return raw
    slugs = raw if isinstance(raw, list) else []
    if not slugs:
        return {}
    t = datetime.date.today()
    n = len(slugs)
    pub = {}
    for i, s in enumerate(slugs):
        back = (n - 1 - i + 1) // 2
        pub[s] = (t - datetime.timedelta(days=back)).isoformat()
    save_published(pub)
    return pub

def save_published(pub):
    write_json(os.path.join(ROOT, "data", "published.json"), pub)

def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
