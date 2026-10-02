#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Epingle auto les nouveaux articles sur Pinterest. SKIP sans secrets. Stdlib only."""
import json, os, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
API = "https://api.pinterest.com/v5"

def api(method, path, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def url_ok(u):
    try:
        req = urllib.request.Request(u, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            return 200 <= r.status < 400
    except Exception:
        return False

def main():
    token = os.environ.get("PINTEREST_TOKEN", "")
    board = os.environ.get("PINTEREST_BOARD_ID", "")
    if not token or not board:
        print("SKIP : secrets Pinterest absents.")
        return
    cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    kws = {k["slug"]: k for k in json.load(open(os.path.join(ROOT, "data", "keywords.json"), encoding="utf-8"))}
    pub = json.load(open(os.path.join(ROOT, "data", "published.json"), encoding="utf-8"))
    slugs = list(pub.keys()) if isinstance(pub, dict) else pub
    pin_path = os.path.join(ROOT, "data", "pinned.json")
    pinned = json.load(open(pin_path, encoding="utf-8")) if os.path.exists(pin_path) else []
    base = cfg["site_url"].rstrip("/")
    todo = [s for s in slugs if s in kws and s not in pinned]
    print(f"{len(todo)} epingles a creer.")
    for slug in todo:
        a = kws[slug]
        link = f"{base}/comparatifs/{slug}/"
        img = f"{base}/pins/{slug}.png"
        for _ in range(10):
            if url_ok(img):
                break
            time.sleep(30)
        if not url_ok(img):
            print(f"SKIP image introuvable : {slug}")
            continue
        title = a["title"][:100]
        desc = (f"{a['title']} : top 3, avis et meilleur prix. {a['keyword']} — guide mis a jour. " + " ".join(a["products"]))[:480]
        try:
            r = api("POST", "/pins", token, {
                "board_id": board, "title": title, "description": desc,
                "link": link, "image_source": {"source_type": "image_url", "url": img}})
            pinned.append(slug)
            json.dump(pinned, open(pin_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"PIN OK : {slug} -> {r.get('id')}")
        except urllib.error.HTTPError as e:
            print(f"PIN KO : {slug} -> {e.code} {e.read()[:200]}")
            break

if __name__ == "__main__":
    main()
