#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Toote les nouveaux articles sur Mastodon (API gratuite). SKIP sans secrets. Stdlib."""
import json, os, urllib.request, urllib.error
from lib import read_json, write_json
from social_text import build_text, pick_todo

ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    instance = os.environ.get("MASTO_INSTANCE", "")
    token = os.environ.get("MASTO_TOKEN", "")
    if not instance or not token:
        print("SKIP : secrets Mastodon absents.")
        return
    cfg = read_json(os.path.join(ROOT, "config.json"), {})
    kws = {k["slug"]: k for k in read_json(os.path.join(ROOT, "data", "keywords.json"), [])}
    pub = read_json(os.path.join(ROOT, "data", "published.json"), {})
    slugs = list(pub.keys()) if isinstance(pub, dict) else pub
    state = os.path.join(ROOT, "data", "posted_masto.json")
    posted = read_json(state, [])
    base = cfg["site_url"].rstrip("/")
    todo, skipped = pick_todo(slugs, posted)
    posted = posted + [s for s in skipped if s in kws]
    write_json(state, posted)
    for slug in [s for s in todo if s in kws]:
        a = kws[slug]
        link = f"{base}/comparatifs/{slug}/"
        text = build_text(a["title"], link, tags=["#bonplan"], max_len=480)
        data = json.dumps({"status": text, "visibility": "public"}).encode()
        req = urllib.request.Request(f"https://{instance}/api/v1/statuses", data=data, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                json.load(r)
            posted.append(slug)
            write_json(state, posted)
            print(f"MASTO OK : {slug}")
        except urllib.error.HTTPError as e:
            print(f"MASTO KO : {slug} -> {e.code}")
            break

if __name__ == "__main__":
    main()
