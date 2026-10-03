#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genere le pack premium : 3 vrais fichiers Excel (formules, mise en forme, facture imprimable)."""
import os

def build_pack(dl_dir):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.worksheet.datavalidation import DataValidation

    os.makedirs(dl_dir, exist_ok=True)
    HDR = PatternFill("solid", fgColor="0F172A")
    HDRF = Font(bold=True, color="FFFFFF", size=11)
    ACC = PatternFill("solid", fgColor="FFD60A")
    EDIT = PatternFill("solid", fgColor="FFF8D6")
    thin = Side(style="thin", color="CBD5E1")
    BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # ---------- 1. BUDGET MENSUEL ----------
    wb = Workbook()
    ws = wb.active
    ws.title = "Budget 2026"
    mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    cats = [("Loyer", 800), ("Courses", 350), ("Transport", 75), ("Abonnements", 60),
            ("Santé", 50), ("Loisirs", 100), ("Shopping", 80), ("Épargne", 150)]
    headers = ["Mois", "Catégorie", "Prévu (€)", "Réel (€)", "Écart (€)"]
    ws.append(headers)
    for c in ws[1]:
        c.fill, c.font, c.border = HDR, HDRF, BOX
    r = 2
    first_data = r
    for mi, mm in enumerate(mois):
        for ci, (cat, prevu) in enumerate(cats):
            ws.cell(r, 1, mm)
            ws.cell(r, 2, cat)
            ws.cell(r, 3, prevu)
            ws.cell(r, 4, 0 if ci < 7 else prevu if cat == "Épargne" else 0)
            ws.cell(r, 5, f"=C{r}-D{r}")
            for col in range(1, 6):
                ws.cell(r, col).border = BOX
            r += 1
    last_data = r - 1
    ws.cell(r, 1, "TOTAL ANNÉE")
    ws.cell(r, 2, "")
    for col, letter in [(3, "C"), (4, "D"), (5, "E")]:
        ws.cell(r, col, f"=SUM({letter}{first_data}:{letter}{last_data})")
    for c in ws[r]:
        c.fill, c.font, c.border = ACC, Font(bold=True, size=11), BOX
    ws.conditional_formatting.add(f"E{first_data}:E{last_data}",
        CellIsRule(operator="lessThan", formula=["0"], font=Font(color="DC2626", bold=True)))
    ws.conditional_formatting.add(f"E{first_data}:E{last_data}",
        CellIsRule(operator="greaterThan", formula=["0"], font=Font(color="15803D", bold=True)))
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 16
    for col in "CDE":
        ws.column_dimensions[col].width = 13
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:E{last_data}"
    g = wb.create_sheet("Guide")
    g["A1"] = "Comment utiliser ce budget (2 min)"
    g["A1"].font = Font(bold=True, size=14)
    for i, t in enumerate([
        "1. Chaque mois, remplis la colonne Réel (€) avec ce que tu as vraiment dépensé.",
        "2. La colonne Écart se calcule seule : rouge = dépassement, vert = sous le budget.",
        "3. La ligne TOTAL ANNÉE additionne tout automatiquement.",
        "4. Adapte les montants Prévu à ta vie (colonne C).",
        "5. Objectif simple : Épargne réelle > 0 tous les mois.",
    ], start=3):
        g.cell(i, 1, t)
    g.column_dimensions["A"].width = 90
    # --- Onglet Tableau de bord : totaux par catégorie + graphique ---
    from openpyxl.chart import BarChart, Reference
    db = wb.create_sheet("Tableau de bord")
    db["A1"] = "Dépenses annuelles par catégorie (Réel)"
    db["A1"].font = Font(bold=True, size=14)
    db.append([])  # ligne 2 vide
    db.cell(3, 1, "Catégorie").fill = HDR
    db.cell(3, 1).font = HDRF
    db.cell(3, 2, "Prévu (€)").fill = HDR
    db.cell(3, 2).font = HDRF
    db.cell(3, 3, "Réel (€)").fill = HDR
    db.cell(3, 3).font = HDRF
    for i, (cat, _) in enumerate(cats, start=4):
        db.cell(i, 1, cat).border = BOX
        db.cell(i, 2, f"=SUMIF('Budget 2026'!B2:B97,A{i},'Budget 2026'!C2:C97)").border = BOX
        db.cell(i, 3, f"=SUMIF('Budget 2026'!B2:B97,A{i},'Budget 2026'!D2:D97)").border = BOX
    tot = 4 + len(cats)
    db.cell(tot, 1, "TOTAL").font = Font(bold=True)
    db.cell(tot, 2, f"=SUM(B4:B{tot-1})").font = Font(bold=True)
    db.cell(tot, 3, f"=SUM(C4:C{tot-1})").font = Font(bold=True)
    db.cell(tot + 2, 1, "Taux d'épargne réel").font = Font(bold=True, size=12)
    db.cell(tot + 2, 3, f"=SUMIF('Budget 2026'!B2:B97,\"Épargne\",'Budget 2026'!D2:D97)/C{tot}")
    db.cell(tot + 2, 3).number_format = "0%"
    chart = BarChart()
    chart.title = "Réel dépensé par catégorie"
    chart.data = Reference(db, min_col=3, min_row=3, max_row=tot - 1)
    chart.cats = Reference(db, min_col=1, min_row=4, max_row=tot - 1)
    chart.height, chart.width = 8, 15
    db.add_chart(chart, f"A{tot + 4}")
    for col, w in [("A", 16), ("B", 13), ("C", 13)]:
        db.column_dimensions[col].width = w
    # --- Onglet Abonnements : le tueur d'économies ---
    ab = wb.create_sheet("Abonnements")
    ab["A1"] = "Tous tes abonnements : garde ou résilie (l'économie se calcule seule)"
    ab["A1"].font = Font(bold=True, size=13)
    for col, h in enumerate(["Service", "€ / mois", "€ / an", "Je garde ? (Oui/Non)", "Économisé si résilié"], start=1):
        c = ab.cell(3, col, h)
        c.fill, c.font, c.border = HDR, HDRF, BOX
    exemples_ab = [("Netflix", 13.49), ("Spotify", 11.12), ("Salle de sport", 30), ("Stockage cloud", 2.99), ("À compléter", 0)]
    for i, (nom, prix) in enumerate(exemples_ab, start=4):
        ab.cell(i, 1, nom).border = BOX
        ab.cell(i, 2, prix).border = BOX
        ab.cell(i, 3, f"=B{i}*12").border = BOX
        ab.cell(i, 4, "Oui").border = BOX
        ab.cell(i, 5, f'=IF(D{i}="Non",C{i},0)').border = BOX
        ab.cell(i, 5).fill = EDIT
    ab.cell(10, 1, "ÉCONOMIE ANNUELLE SI RÉSILIATION").font = Font(bold=True, size=12)
    ab.cell(10, 5, "=SUM(E4:E9)").font = Font(bold=True, size=13)
    ab.cell(10, 5).fill = ACC
    dv2 = DataValidation(type="list", formula1='"Oui,Non"', allow_blank=True)
    ab.add_data_validation(dv2)
    dv2.add("D4:D9")
    for col, w in [("A", 22), ("B", 11), ("C", 11), ("D", 18), ("E", 22)]:
        ab.column_dimensions[col].width = w
    wb.save(os.path.join(dl_dir, "budget-mensuel.xlsx"))

    # ---------- 2. SUIVI FACTURES ----------
    wb = Workbook()
    ws = wb.active
    ws.title = "Factures"
    headers = ["N°", "Date", "Client", "Objet", "HT (€)", "TVA (%)", "TTC (€)", "Statut"]
    ws.append(headers)
    for c in ws[1]:
        c.fill, c.font, c.border = HDR, HDRF, BOX
    exemples = [
        ["2026-001", "02/10/2026", "Client Exemple", "Prestation design", 500, 20, None, "Payée"],
        ["2026-002", "", "À compléter", "À compléter", 0, 20, None, "Brouillon"],
    ]
    for ex in exemples:
        ws.append(ex)
    for r in range(2, 52):
        ws.cell(r, 7, f"=E{r}*(1+F{r}/100)")
        for col in range(1, 9):
            ws.cell(r, col).border = BOX
    dv = DataValidation(type="list", formula1='"Brouillon,Envoyée,Payée,En retard"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add("H2:H51")
    ws.conditional_formatting.add("H2:H51",
        CellIsRule(operator="equal", formula=['"En retard"'], font=Font(color="FFFFFF", bold=True), fill=PatternFill("solid", fgColor="DC2626")))
    ws.conditional_formatting.add("H2:H51",
        CellIsRule(operator="equal", formula=['"Payée"'], font=Font(color="15803D", bold=True)))
    ws.cell(53, 1, "TOTAL HT FACTURÉ").font = Font(bold=True)
    ws.cell(53, 5, "=SUM(E2:E51)")
    ws.cell(54, 1, "TOTAL TTC FACTURÉ").font = Font(bold=True)
    ws.cell(54, 7, "=SUM(G2:G51)")
    ws.cell(55, 1, "RESTE À ENCAISSER (non payé)").font = Font(bold=True)
    ws.cell(55, 7, '=SUMIF(H2:H51,"<>Payée",G2:G51)')
    widths = [12, 12, 20, 24, 10, 9, 11, 12]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:H51"
    wb.save(os.path.join(dl_dir, "suivi-factures.xlsx"))

    # ---------- 3. MODELE FACTURE IMPRIMABLE ----------
    wb = Workbook()
    ws = wb.active
    ws.title = "Facture"
    ws.sheet_properties.pageSetUpPr = None
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.print_area = "A1:D32"
    for col, w in [("A", 38), ("B", 14), ("C", 16), ("D", 18)]:
        ws.column_dimensions[col].width = w
    ws["A1"] = "FACTURE"
    ws["A1"].font = Font(bold=True, size=22, color="0F172A")
    ws["A2"] = "N° :"
    ws["B2"] = "2026-001"
    ws["B2"].fill = EDIT
    ws["A3"] = "Date :"
    ws["C3"] = "02/10/2026"
    ws["C3"].fill = EDIT
    ws["A5"] = "ÉMETTEUR (remplace par tes infos)"
    ws["A5"].font = Font(bold=True, color="FFFFFF")
    ws["A5"].fill = HDR
    for i, t in enumerate(["Mon Entreprise", "12 rue Exemple, 75000 Paris", "SIRET : 123 456 789 00000", "contact@monexemple.fr — 06 00 00 00 00"], start=6):
        ws.cell(i, 1, t).fill = EDIT
    ws["A10"] = "FACTURÉ À"
    ws["A10"].font = Font(bold=True, color="FFFFFF")
    ws["A10"].fill = HDR
    for i, t in enumerate(["Nom du client", "Adresse du client"], start=11):
        ws.cell(i, 1, t).fill = EDIT
    for col, h in enumerate(["Description", "Qté", "PU HT (€)", "Total HT (€)"], start=1):
        c = ws.cell(14, col, h)
        c.fill, c.font, c.border, c.alignment = HDR, HDRF, BOX, center
    lignes = [("Prestation design — maquette site", 1, 500), ("", 0, 0), ("", 0, 0), ("", 0, 0), ("", 0, 0)]
    for i, (desc, qte, pu) in enumerate(lignes, start=15):
        ws.cell(i, 1, desc).border = BOX
        ws.cell(i, 2, qte).border = BOX
        ws.cell(i, 3, pu).border = BOX
        ws.cell(i, 4, f"=B{i}*C{i}").border = BOX
    ws.cell(20, 3, "Sous-total HT").font = Font(bold=True)
    ws.cell(20, 4, "=SUM(D15:D19)").font = Font(bold=True)
    ws.cell(21, 3, "TVA 20 %")
    ws.cell(21, 4, "=D20*20/100")
    ws.cell(22, 3, "TOTAL TTC").font = Font(bold=True, size=13)
    ws.cell(22, 4, "=D20+D21").font = Font(bold=True, size=13)
    ws.cell(22, 4).fill = ACC
    for t in ["Conditions : paiement à 30 jours.", "Pénalités de retard : 3x le taux légal. Indemnité forfaitaire 40 €.",
              "TVA non applicable si auto-entrepreneur en franchise (art. 293 B du CGI) — supprime la ligne TVA dans ce cas."]:
        ws.cell(ws.max_row + 2, 1, t).font = Font(size=9, color="64748B")
    wb.save(os.path.join(dl_dir, "modele-facture.xlsx"))
    # ---------- 4. MODELE DEVIS (clone de la facture, mentions devis) ----------
    from openpyxl import load_workbook as _load
    wd = _load(os.path.join(dl_dir, "modele-facture.xlsx"))
    ws = wd["Facture"]
    ws["A1"] = "DEVIS"
    ws["B2"] = "2026-001-D"
    ws.title = "Devis"
    # Remplace les 3 lignes de mentions par des mentions devis
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for c in row:
            if c.value and isinstance(c.value, str) and c.value.startswith("Conditions"):
                c.value = "Devis valable 3 mois. Bon pour accord, date + signature du client :"
            if c.value and isinstance(c.value, str) and c.value.startswith("Pénalités"):
                c.value = "Signature du devis = commande ferme. Acompte de 30 % demandé à la commande."
    wd.save(os.path.join(dl_dir, "modele-devis.xlsx"))
    return ["budget-mensuel.xlsx", "suivi-factures.xlsx", "modele-facture.xlsx", "modele-devis.xlsx"]

if __name__ == "__main__":
    print(build_pack(os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "premium", "telechargement")))
