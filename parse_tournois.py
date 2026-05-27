import pdfplumber
import re
import csv


def lire_pdf(chemin):
    with pdfplumber.open(chemin) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)


def extraire_tournois(texte):
    blocs = re.split(r"(?=^[A-ZÀ-Ÿ][^\n]*\n[^\n]+\n\d{2}/\d{2}/\d{4})", texte, flags=re.MULTILINE)
    
    tournois = []
    for bloc in blocs:
        if "JUGE-ARBITRE" not in bloc or "CODE :" not in bloc:
            continue
        
        data = {
            "club": None,
            "nom_tournoi": None,
            "date_debut": None,
            "date_fin": None,
            "juge_arbitre": None,
            "code": None,
            "adresse": None,
            "code_postal": None,
            "ville": None,
            "telephone": None,
            "email": None,
            "categories_p": [],
            "epreuves": [],
        }
        
        lignes = bloc.strip().split("\n")
        if lignes:
            data["club"] = lignes[0].strip()
        if len(lignes) > 1:
            data["nom_tournoi"] = lignes[1].strip()
        
        match_dates = re.search(r"(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})", bloc)
        if match_dates:
            data["date_debut"] = match_dates.group(1)
            data["date_fin"] = match_dates.group(2)
        
        match_ja = re.search(r"JUGE-ARBITRE\s*:\s*([^\n]+)", bloc)
        if match_ja:
            ja = match_ja.group(1).strip()
            data["juge_arbitre"] = ja if ja != "null null" else None
        
        match_code = re.search(r"CODE\s*:\s*(P\s+\d{4}\s+\d+\s+\d+\s+\d+\s+\d+)", bloc)
        if match_code:
            data["code"] = match_code.group(1).strip()
        
        match_install = re.search(
            r"INSTALLATIONS\s*:.*?\n(.*?)\n(\d{5})\s+([A-ZÀ-Ÿ][^\n]+)",
            bloc, re.DOTALL
        )
        if match_install:
            data["adresse"] = match_install.group(1).strip()
            data["code_postal"] = match_install.group(2).strip()
            data["ville"] = match_install.group(3).strip()
        
        match_tel = re.search(r"(\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2})", bloc)
        if match_tel:
            data["telephone"] = match_tel.group(1)
        
        match_mail = re.search(r"([\w.-]+@[\w.-]+\.\w+)", bloc)
        if match_mail:
            data["email"] = match_mail.group(1)
        
        # FIX : on cherche les P dans TOUT le bloc, pas juste le nom
        # On exclut "P 2026" qui apparait dans le CODE FFT
        bloc_sans_code = re.sub(r"P\s+\d{4}\s+\d+\s+\d+\s+\d+\s+\d+", "", bloc)
        categories = re.findall(r"\bP\d{2,4}\b", bloc_sans_code)
        data["categories_p"] = sorted(set(categories), key=lambda x: int(x[1:]))
        
        epreuves = re.findall(r"Double (?:Dames|Messieurs|Mixte)", bloc)
        data["epreuves"] = sorted(set(epreuves))
        
        tournois.append(data)
    
    vus = set()
    uniques = []
    for t in tournois:
        if t["code"] and t["code"] not in vus:
            vus.add(t["code"])
            uniques.append(t)
    
    return uniques


def sauver_csv(tournois, fichier):
    if not tournois:
        return
    rows = []
    for t in tournois:
        row = t.copy()
        row["categories_p"] = " / ".join(t["categories_p"]) if t["categories_p"] else ""
        row["epreuves"] = " / ".join(t["epreuves"]) if t["epreuves"] else ""
        rows.append(row)
    with open(fichier, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


texte = lire_pdf("tournois.pdf")
tournois = extraire_tournois(texte)

print(f"=== {len(tournois)} tournois uniques extraits ===\n")
for t in tournois[:3]:
    print("-" * 60)
    for cle, valeur in t.items():
        print(f"  {cle:15} : {valeur}")
    print()

sauver_csv(tournois, "tournois.csv")
print(f"\n✅ Sauvegardé dans tournois.csv")
