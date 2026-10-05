#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Textes des posts reseaux (pur, teste). Limites : Bluesky 300 signes, Mastodon 500."""

def build_text(title, url, tags=(), max_len=260):
    base = f"⭐ {title}"
    suffix = f" 👉 {url}"
    room = max_len - len(suffix.encode("utf-8")) - len("⭐ ".encode("utf-8"))
    short = title
    while len(short.encode("utf-8")) > room and len(short) > 20:
        short = short[: len(short) - 2].rstrip()
    text = f"⭐ {short}{suffix}"
    if tags:
        extra = " " + " ".join(tags)
        if len((text + extra).encode("utf-8")) <= max_len:
            text += extra
    return text

def link_facet(text, url):
    """ Facet Bluesky : offsets en OCTETS utf-8 (pas en caracteres). """
    raw = text.encode("utf-8")
    start = raw.find(url.encode("utf-8"))
    if start == -1:
        return None
    return {"index": {"byteStart": start, "byteEnd": start + len(url.encode("utf-8"))},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]}

def pick_todo(slugs, posted, limit=3):
    """Les `limit` plus recents a publier + le vieux stock a ignorer (anti-flood)."""
    fresh = [s for s in slugs if s not in set(posted)]
    if len(fresh) <= limit:
        return fresh, []
    return fresh[-limit:], fresh[:-limit]
