#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tableau de bord local et PRIVE (ne jamais publier ce fichier ni ses sorties).
Usage : python stats.py
Option : STRIPE_SECRET_KEY=rk_live_... python stats.py  -> inclut le CA Stripe reel.
"""
import datetime
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)

def stripe_revenue():
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return None, "cle absente (export STRIPE_SECRET_KEY pour activer)"
    try:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/charges?limit=100",
            headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        total, n = 0.0, 0
        for ch in data.get("data", []):
            if ch.get("paid") and not ch.get("refunded"):
                total += ch.get("amount", 0) / 100.0
                n += 1
        return (n, total), None
    except Exception as e:
        return None, f"erreur API Stripe : {e}"

def main():
    cfg = load("config.json")
    tools = load("data/tools.json")
    kws = load("data/keywords.json")
    pub = load("data/published.json")
    restants = len(kws) - len(pub)
    m = cfg["monetization"]
    print("=" * 58)
    print(f"  RADIN MALIN — {datetime.date.today().isoformat()}")
    print("=" * 58)
    print(f"  Contenu      : {len(tools)} outils + {len(pub)} comparatifs en ligne")
    print(f"  Autonomie    : {restants} articles restants (~{restants // 2} jours a 2/jour)")
    print(f"  Boutons affi : {len(pub) * 3} liens Amazon (tag {m['amazon_tag']})")
    print()
    print("  REVENUS (100 derniers paiements Stripe)")
    res, err = stripe_revenue()
    if res:
        print(f"    Ventes : {res[0]}  |  CA : {res[1]:.2f} EUR")
    else:
        print(f"    Stripe : {err}")
    print("    Amazon   : voir https://partenaires.amazon.fr > Rapports")
    print("    Monetag  : voir https://monetag.com > Statistics")
    print()
    print("  TRAFIC")
    print("    Google : https://search.google.com/search-console > Performances")
    print("    Bing   : https://www.bing.com/webmasters > Rapports")
    print()
    print("  CHECKLIST MONETISATION")
    for label, ok in [
        ("Amazon tag actif", "VOTRE" not in m["amazon_tag"]),
        ("Monetag actif", bool(m["monetag_tag"])),
        ("Stripe Live", "buy.stripe.com" in m["stripe_pro_link"] and "VOTRE" not in m["stripe_pro_link"]),
        ("PayPal actif", "VOTRE" not in m.get("paypal_link", "VOTRE")),
        ("AdSense depose", bool(m["adsense_client"])),
    ]:
        print(f"    [{'OK' if ok else '--'}] {label}")
    print("=" * 58)

if __name__ == "__main__":
    main()
