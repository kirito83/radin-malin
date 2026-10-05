#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Autopost Telegram du dernier article. 0 action si secrets absents. 100% stdlib."""
import json, os, urllib.parse, urllib.request
from lib import read_json

ROOT = os.path.dirname(os.path.abspath(__file__))

def build_link(site_url, slug, source="telegram"):
    return f"{site_url.rstrip('/')}/comparatifs/{slug}/?utm_source={source}&utm_medium=social"

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat or "VOTRE" in token:
        print("SKIP : secrets Telegram absents (normal tant que non configuré).")
        return
    cfg = read_json(os.path.join(ROOT, "config.json"), {})
    kws = {k["slug"]: k for k in read_json(os.path.join(ROOT, "data", "keywords.json"), [])}
    pub = read_json(os.path.join(ROOT, "data", "published.json"), {})
    slugs = list(pub.keys()) if isinstance(pub, dict) else pub
    if not slugs:
        print("SKIP : rien de publié.")
        return
    last = kws.get(slugs[-1])
    if not last:
        print("SKIP : dernier slug introuvable.")
        return
    url = build_link(cfg["site_url"], last['slug'])
    text = f"⭐ Nouveau comparatif : {last['title']}\n\n👉 {url}\n\n#bonplan #comparatif"
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    req = urllib.request.Request(api, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        print("TELEGRAM OK :", r.status)

if __name__ == "__main__":
    main()
