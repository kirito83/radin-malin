#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests unitaires : logique de consentement cookies (dukpy + stubs DOM).
Prouve que 'Tout refuser' ne charge ni GA ni pubs, et 'Tout accepter' si.
"""
import os, sys, unittest

try:
    import dukpy
except ImportError:
    dukpy = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build

STUB = """
var __store = {}, __head = [], __body = [];
var __banner = {hidden: true};
var window = {};
var localStorage = {getItem: function(k){ return (__store[k] === undefined) ? null : __store[k]; },
                     setItem: function(k, v){ __store[k] = String(v); }};
function __mkEl(){ return {hidden: false, dataset: {}, checked: true,
  set async(v){}, appendChild: function(c){ (__body).push(c); return c; }}; }
var document = {
  getElementById: function(id){ if(id === "rm-consent") return __banner;
    if(id === "rm-c-an") return {checked: true}; if(id === "rm-c-ad") return {checked: true};
    return __mkEl(); },
  createElement: function(t){ return {tag: t, dataset: {}, async: false, src: "",
    set src(v){ this._src = v; }, get src(){ return this._src; }}; },
  head: {appendChild: function(c){ __head.push(c); return c; }},
  body: {appendChild: function(c){ __body.push(c); return c; }},
  addEventListener: function(){}
};
"""


def run(script):
    return dukpy.evaljs(STUB + "\n" + build.CONSENT_JS + "\nwindow.__rmc=" + script + "\n" + """
rmApply();
"banner=" + __banner.hidden + "|ga=" + __head.length + "|ads=" + __body.length;
""")


@unittest.skipIf(dukpy is None, "dukpy non installe")
class TestConsent(unittest.TestCase):
    CFG = '{"ga":"G-X","zones":[["1","https://x/y.js"]],"vign":null,"adsense":""}'

    def test_sans_choix_banniere_affichee_rien_charge(self):
        r = run(self.CFG)
        self.assertIn("banner=false", r)
        self.assertIn("ga=0", r)
        self.assertIn("ads=0", r)

    def test_tout_accepter_charge(self):
        prog = STUB + "\n" + build.CONSENT_JS + "\nwindow.__rmc=" + self.CFG + "\nrmConsent(1,1);\nrmApply();\n\"banner=\" + __banner.hidden + \"|ga=\" + __head.length + \"|ads=\" + __body.length;"
        r = dukpy.evaljs(prog)
        self.assertIn("banner=true", r)
        self.assertIn("ga=1", r)
        self.assertIn("ads=1", r)

    def test_tout_refuser_bloque(self):
        prog = STUB + "\n" + build.CONSENT_JS + "\nwindow.__rmc=" + self.CFG + "\nrmConsent(0,0);\nrmApply();\n\"banner=\" + __banner.hidden + \"|ga=\" + __head.length + \"|ads=\" + __body.length;"
        r = dukpy.evaljs(prog)
        self.assertIn("banner=true", r)
        self.assertIn("ga=0", r)
        self.assertIn("ads=0", r)

    def test_granulaire_que_analytics(self):
        prog = STUB + "\n" + build.CONSENT_JS + "\nwindow.__rmc=" + self.CFG + "\nrmConsent(1,0);\nrmApply();\n\"ga=\" + __head.length + \"|ads=\" + __body.length;"
        r = dukpy.evaljs(prog)
        self.assertIn("ga=1", r)
        self.assertIn("ads=0", r)


if __name__ == "__main__":
    unittest.main()
