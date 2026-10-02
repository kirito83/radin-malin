#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Autopost Telegram du dernier article. 0 action si secrets absents. 100% stdlib."""
import json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat or "VOTRE" in token:
        print("SKIP : secrets Telegram absents (normal tant que non configuré).")
        return
    cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    kws = {k["slug"]: k for k in json.load(open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8"))}
    pub = json.load(open(os.path.join(ROOT, "data", "published.json"), encoding="utf-8"))
    if not pub:
        print("SKIP : rien de publié.")
        return
    last = kws.get(pub[-1])
    if not last:
        print("SKIP : dernier slug introuvable.")
        return
    url = cfg["site_url"].rstrip("/") + f"/comparatifs/{last['slug']}/"
    text = f"⭐ Nouveau comparatif : {last['title']}\n\n👉 {url}\n\n#bonplan #comparatif"
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    req = urllib.request.Request(api, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        print("TELEGRAM OK :", r.status)

if __name__ == "__main__":
    main()
