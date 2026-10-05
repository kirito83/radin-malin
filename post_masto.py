#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Toote les nouveaux articles sur Mastodon (API gratuite). SKIP sans secrets. Stdlib."""
import json, os, urllib.request, urllib.error
from social_text import build_text

ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    instance = os.environ.get("MASTO_INSTANCE", "")
    token = os.environ.get("MASTO_TOKEN", "")
    if not instance or not token:
        print("SKIP : secrets Mastodon absents.")
        return
    cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    kws = {k["slug"]: k for k in json.load(open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8"))}
    pub = json.load(open(os.path.join(ROOT, "data", "published.json"), encoding="utf-8"))
    slugs = list(pub.keys()) if isinstance(pub, dict) else pub
    state = os.path.join(ROOT, "data", "posted_masto.json")
    posted = json.load(open(state, encoding="utf-8")) if os.path.exists(state) else []
    base = cfg["site_url"].rstrip("/")
    for slug in [s for s in slugs if s in kws and s not in posted]:
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
            json.dump(posted, open(state, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"MASTO OK : {slug}")
        except urllib.error.HTTPError as e:
            print(f"MASTO KO : {slug} -> {e.code}")
            break

if __name__ == "__main__":
    main()
