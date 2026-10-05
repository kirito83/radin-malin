#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests FONCTIONNELS : chaque outil est execute pour de vrai (dukpy + DOM simule)
et ses resultats calcules sont verifies. Requiert : pip install dukpy
Lancez : python -m unittest discover -s tests -v
"""
import json, os, unittest

try:
    import dukpy
except ImportError:
    dukpy = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUB = """
var __els = {}, __printed = false, __alerted = null, __copied = null;
function __el(id, val){ if(!(__els[id])) __els[id] = {value: "", innerHTML: "", textContent: "", checked: true, style: {}, scrollIntoView: function(){}, addEventListener: function(){}, appendChild: function(){}}; if(val !== undefined) __els[id].value = val; return __els[id]; }
var document = {
  getElementById: function(id){ if(!__els[id]) throw new Error("id introuvable: " + id); return __els[id]; },
  createElement: function(t){ return {href: "", download: "", click: function(){}, remove: function(){}, style: {}, setAttribute: function(){}}; },
  body: {appendChild: function(){}},
  addEventListener: function(){}
};
var window = {print: function(){ __printed = true; }, open: function(){ return null; }};
var location = {href: "http://test/"};
var navigator = {clipboard: {writeText: function(t){ __copied = t; return {then: function(f){ f(); }}; }}};
var crypto = {getRandomValues: function(a){ for(var i = 0; i < a.length; i++) a[i] = (i * 7919 + 13) % 4294967296; return a; }};
var URL = {createObjectURL: function(){ return "blob:test"; }, revokeObjectURL: function(){}};
function Blob(a, b){ this.a = a; }
function alert(m){ __alerted = m; }
function setTimeout(f){ f(); return 0; }
"""

JS_PDF_STUB = """
window.__lastPdf = null;
window.jspdf = {jsPDF: function(o){ window.__lastPdf = {texts: [], saved: null}; var S = window.__lastPdf;
  this.text = function(){ S.texts.push(Array.prototype.join.call(arguments, "|")); };
  this.setFontSize = function(){}; this.save = function(n){ S.saved = n; }; }};
"""


def build_prog(tool, presets=None, raw_lines=(), call="", tail='__els["res"].innerHTML'):
    import re as _re
    js = tool["js"]
    pre = [STUB]
    ids = set(_re.findall(r"id='([^']+)'", tool["ui_html"])) | set(_re.findall(r'id="([^"]+)"', tool["ui_html"]))
    given = presets or {}
    for i in sorted(ids):
        pre.append(f"__el({json.dumps(i)}, {json.dumps(given.get(i, ''))});")
    pre.extend(raw_lines)
    return "\n".join(pre) + "\n" + js + "\n" + (call + "\n" if call else "") + tail


def run_tool(tool, presets=None, raw_lines=(), call="", tail='__els["res"].innerHTML'):
    return dukpy.evaljs(build_prog(tool, presets, raw_lines, call, tail))


def load_tools():
    with open(os.path.join(ROOT, "data", "tools.json"), encoding="utf-8") as f:
        return {t["slug"]: t for t in json.load(f)}


@unittest.skipIf(dukpy is None, "dukpy non installe")
class TestFonctionnel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = load_tools()

    def test_tva(self):
        t = self.tools["calcul-tva-remise"]
        r = run_tool(t, {"prix": "200", "tva": "20", "remise": "10"}, call="calcTVA();")
        self.assertIn("180.00", r)
        self.assertIn("216.00", r)
        self.assertIn("20.00", r)

    def test_pret(self):
        t = self.tools["calcul-pret-mensualite"]
        r = run_tool(t, {"cap": "100000", "taux": "3", "duree": "20"}, call="calcPret();")
        self.assertRegex(r, r"55\d\.\d{2}")

    def test_imc(self):
        t = self.tools["calcul-imc"]
        r = run_tool(t, {"poids": "70", "taille": "175"}, call="calcIMC();")
        self.assertIn("22.9", r)
        self.assertIn("Poids normal", r)

    def test_devises(self):
        t = self.tools["convertisseur-devises"]
        r = run_tool(t, {"mnt": "100"}, raw_lines=['__el("de").value="EUR";', '__el("vers").value="USD";'], call="conv();")
        self.assertIn("108.00", r)

    def test_devises_note_suit_conversion(self):
        t = self.tools["convertisseur-devises"]
        r = run_tool(t, {"mnt": "100"}, raw_lines=['__el("de").value="EUR";', '__el("vers").value="GBP";'],
                     call="conv();", tail='__els["src"].textContent')
        self.assertIn("GBP", r)
        self.assertIn("0.85", r)

    def test_mot_de_passe_longueur(self):
        t = self.tools["generateur-mot-de-passe"]
        r = run_tool(t, {"len": "16"}, raw_lines=["__el(\"sym\").checked=true;"], call="genMDP();", tail="String(last.length)")
        self.assertEqual(r, "16")

    def test_compteur(self):
        t = self.tools["compteur-mots-caracteres"]
        r = run_tool(t, {"txt": "Bonjour le monde"}, call="compter();")
        self.assertIn("Mots : <b>3</b>", r)
        self.assertIn("16</b>", r)

    def test_qr(self):
        t = self.tools["generateur-qr-code"]
        r = run_tool(t, {"qrtext": "https://example.com"})
        self.assertIn("api.qrserver.com", r)
        self.assertIn("example.com", r)
        self.assertIn("dlQR()", r)

    def test_qr_telechargement_sans_fetch(self):
        t = self.tools["generateur-qr-code"]
        run_tool(t, {"qrtext": "https://example.com"}, call="dlQR();",
                 tail='"ok"')  # repli window.open, ne doit pas lever

    def test_unites(self):
        t = self.tools["convertisseur-unites"]
        r = run_tool(t, {"v": "1"}, raw_lines=['__el("c").value="kg-lb";'], call="convU();")
        self.assertIn("2.20", r)

    def test_age(self):
        t = self.tools["calcul-age"]
        r = run_tool(t, {"dn": "2000-01-01"}, call="calcAge();")
        self.assertIn("ans</b>", r)
        self.assertIn("Jours", r)

    def test_facture_apercu(self):
        t = self.tools["generateur-facture"]
        r = run_tool(t, {"f0": "2026-001", "f1": "Moi", "f2": "Client", "f3": "Design", "f4": "500", "f5": "20"}, call="fact();")
        self.assertIn("600.00", r)
        self.assertIn("facture-print", r)

    def test_facture_pdf(self):
        t = self.tools["generateur-facture"]
        presets = {"f0": "2026-001", "f1": "Moi", "f2": "C", "f3": "D", "f4": "500", "f5": "20"}
        prog = build_prog(t, presets, raw_lines=[JS_PDF_STUB.strip()], call="downloadFacture();",
                           tail="window.__lastPdf.saved")
        self.assertEqual(dukpy.evaljs(prog), "facture-2026-001.pdf")
        prog2 = build_prog(t, presets, raw_lines=[JS_PDF_STUB.strip()], call="downloadFacture();",
                            tail="window.__lastPdf.texts.join(' ')")
        self.assertIn("600.00", dukpy.evaljs(prog2))

    def test_facture_fallback_html(self):
        t = self.tools["generateur-facture"]
        r = run_tool(t, {"f4": "500", "f5": "20"}, call="var _r=downloadFacture();", tail="_r")
        self.assertEqual(r, "html")

    def test_salaire(self):
        t = self.tools["salaire-brut-net"]
        r = run_tool(t, {"sb": "3000"}, raw_lines=['__el("st").value="0.77";'])
        self.assertIn("2310", r)

    def test_notaire(self):
        t = self.tools["frais-notaire"]
        r = run_tool(t, {"px": "200000"}, raw_lines=['__el("tb").value="0.075";'])
        self.assertIn("15000", r)

    def test_jours_entre_dates(self):
        t = self.tools["jours-entre-deux-dates"]
        r = run_tool(t, {"d1": "2026-01-01", "d2": "2026-01-31"})
        self.assertIn("30 jours", r)

    def test_tirage(self):
        t = self.tools["tirage-au-sort"]
        r = run_tool(t, {"plist": "Alice\nBob\nCharlie", "nb": "1"}, call="tirage();")
        self.assertTrue(any(n in r for n in ["Alice", "Bob", "Charlie"]))

    def test_ovulation(self):
        t = self.tools["calcul-ovulation-grossesse"]
        r = run_tool(t, {"dr": "2026-01-01", "cy": "28"})
        self.assertIn("2026", r)
        self.assertIn("fertile", r)

    def test_impot(self):
        t = self.tools["simulateur-impot-revenu"]
        r = run_tool(t, {"ri": "35000"}, raw_lines=['__el("parts").value="2";'])
        # quotient 17500 : 11497 a 0% + (17500-11497)*11% = 660.33 x2 = 1320.66
        self.assertIn("1321", r)
        self.assertIn("Taux moyen", r)

    def test_impot_reduction(self):
        t = self.tools["simulateur-impot-revenu"]
        r = run_tool(t, {"ri": "35000", "pd": "0", "red": "1000", "cred": "0"},
                     raw_lines=['__el("parts").value="2";'])
        self.assertIn("321", r)

    def test_moyenne(self):
        t = self.tools["calcul-moyenne-notes"]
        r = run_tool(t, {"n1": "14", "c1": "3", "n2": "11", "c2": "2", "n3": "16", "c3": "1"})
        # (42+22+16)/6 = 13.33
        self.assertIn("13.33", r)
        self.assertIn("Assez bien", r)

    def test_moyenne_ajout_dynamique(self):
        t = self.tools["calcul-moyenne-notes"]
        r = run_tool(t, {"n1": "10", "c1": "1", "n2": "10", "c2": "1", "n3": "10", "c3": "1"},
                     raw_lines=['__el("n4","");', '__el("c4","1");', '__el("n5","");', '__el("c5","1");',
                                'addNote();', 'addNote();',
                                '__els["n4"].value="20";', '__els["n5"].value="20";'],
                     call="calcMoy();")
        # (10+10+10+20+20)/5 = 14.00
        self.assertIn("14.00", r)

    def test_cv_apercu(self):
        t = self.tools["generateur-cv-gratuit"]
        r = run_tool(t, {"cvn": "Jean Test", "cvt": "Dev", "cve": "j@t.fr", "cvp": "0600", "cvx": "X", "cvf": "F", "cvs": "S"},
                     call="cvUpdate();", tail='__els["cvprev"].innerHTML')
        self.assertIn("Jean Test", r)
        self.assertIn("cv-print", r)

    def test_cv_sections_conditionnelles(self):
        t = self.tools["generateur-cv-gratuit"]
        r = run_tool(t, {"cvn": "J", "cvt": "D", "cve": "e", "cvp": "p", "cvv": "V", "cvl": "", "cvr": "", "cvx": "X", "cvf": "F", "cvs": "A, B", "cvg": "", "cvh": ""},
                     call="cvUpdate();", tail='__els["cvprev"].innerHTML')
        self.assertIn("cv-pill", r)
        self.assertNotIn("Loisirs", r)
        self.assertNotIn("Langues", r)

    def test_calories(self):
        t = self.tools["calcul-calories"]
        r = run_tool(t, {"wp": "70", "wh": "175", "wa": "30"},
                     raw_lines=['__el("sx").value="h";', '__el("ac").value="1.55";'])
        # TMB = 700+1093.75-150+5 = 1648.75 ; maintien x1.55 = 2555.56
        self.assertIn("1649", r)
        self.assertIn("2556", r)

    def test_cups(self):
        t = self.tools["convertisseur-cups-grammes"]
        r = run_tool(t, {"qc": "2"}, raw_lines=['__el("sens").value="cg";', '__el("ing").value="120";'])
        self.assertIn("240", r)

    def test_grossesse(self):
        t = self.tools["semaines-grossesse"]
        r = run_tool(t, {"gd": "2020-01-01"})
        self.assertIn("SA</b>", r)
        self.assertIn("Trimestre", r)

    def test_qr_wifi(self):
        t = self.tools["generateur-qr-code"]
        r = run_tool(t, {"qrtext": "x"}, raw_lines=['__el("qtype").value="wifi";', '__el("ssid").value="MaBox";', '__el("wpass").value="secret";'])
        self.assertIn("WIFI", r)
        self.assertIn("MaBox", r)


if __name__ == "__main__":
    unittest.main()
