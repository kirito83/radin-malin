#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Poste les nouveaux articles sur Bluesky (API gratuite). SKIP sans secrets. Stdlib."""
import datetime, json, os, urllib.request, urllib.error
from lib import read_json, write_json
from social_text import build_text, link_facet, pick_todo

ROOT = os.path.dirname(os.path.abspath(__file__))

def api(host, path, token=None, payload=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else None)
    headers = {"Content-Type": ctype}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(host + path, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r) if "json" in r.headers.get("Content-Type", "") else r.read()

def main():
    handle = os.environ.get("BSKY_HANDLE", "")
    password = os.environ.get("BSKY_APP_PASSWORD", "")
    if not handle or not password:
        print("SKIP : secrets Bluesky absents.")
        return
    host = os.environ.get("BSKY_HOST", "https://bsky.social")
    ses = api(host, "/xrpc/com.atproto.server.createSession",
              payload={"identifier": handle, "password": password})
    token, did = ses["accessJwt"], ses["did"]
    cfg = read_json(os.path.join(ROOT, "config.json"), {})
    kws = {k["slug"]: k for k in read_json(os.path.join(ROOT, "data", "keywords.json"), [])}
    pub = read_json(os.path.join(ROOT, "data", "published.json"), {})
    slugs = list(pub.keys()) if isinstance(pub, dict) else pub
    state = os.path.join(ROOT, "data", "posted_bsky.json")
    posted = read_json(state, [])
    base = cfg["site_url"].rstrip("/")
    todo, skipped = pick_todo(slugs, posted)
    posted = posted + [s for s in skipped if s in kws]
    write_json(state, posted)
    for slug in [s for s in todo if s in kws]:
        a = kws[slug]
        link = f"{base}/comparatifs/{slug}/"
        text = build_text(a["title"], link)
        facet = link_facet(text, link)
        img_path = os.path.join(ROOT, "public", "pins", slug + ".png")
        thumb = None
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                up = api(host, "/xrpc/com.atproto.repo.uploadBlob", token, raw=f.read(), ctype="image/png")
            thumb = up["blob"]
        external = {"uri": link, "title": a["title"][:100], "description": a["keyword"][:200]}
        if thumb:
            external["thumb"] = thumb
        record = {"$type": "app.bsky.feed.post", "text": text,
                  "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "langs": ["fr"],
                  "embed": {"$type": "app.bsky.embed.external", "external": external}}
        if facet:
            record["facets"] = [facet]
        try:
            r = api(host, "/xrpc/com.atproto.repo.createRecord", token,
                    payload={"repo": did, "collection": "app.bsky.feed.post", "record": record})
            posted.append(slug)
            write_json(state, posted)
            print(f"BSKY OK : {slug} -> {r.get('uri')}")
        except urllib.error.HTTPError as e:
            print(f"BSKY KO : {slug} -> {e.code}")
            break

if __name__ == "__main__":
    main()
