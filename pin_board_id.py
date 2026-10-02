#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Affiche tes tableaux Pinterest + leurs IDs.
Usage : PINTEREST_TOKEN=xxxx python pin_board_id.py   (cle jamais dans le chat ni git)
"""
import json, os, urllib.request

token = os.environ.get("PINTEREST_TOKEN", "")
if not token:
    raise SystemExit("PINTEREST_TOKEN manquant.")
req = urllib.request.Request("https://api.pinterest.com/v5/boards?page_size=25",
    headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req, timeout=20) as r:
    data = json.load(r)
for b in data.get("items", []):
    print(b.get("id"), "->", b.get("name"))
