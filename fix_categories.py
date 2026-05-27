import csv
import re
import pdfplumber


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
            "club": None, "nom_tournoi": None, "date_debut": None, "date_fin": None,
            "juge_arbitre": None, "code": None, "adresse": None, "code_postal": None,
            "ville": None, "telephone": None, "email": None,
            "categories_p": [], "epreuves": [],
        }
        
        lignes = bloc.strip().split("\n")
        if lignes:
            data["club"] = lignes[0].strip()
        if len(lignes) > 1:
            data["nom_tournoi"] = lignes[1].strip()
        
        match = re.search(r"(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})", bloc)
        if match:
            data["date_debut"] = match.group(1)
            data["date_fin"] = match.group(2)
        
        match = re.search(r"JUGE-ARBITRE\s*:\s*([^\n]+)", bloc)
        if match:
            ja = match.group(1).strip()
            data["juge_arbitre"] = ja if ja != "null null" else None
        
        match = re.search(r"CODE\s*:\s*(P\s+\d{4}\s+\d+\s+\d+\s+\d+\s+\d+)", bloc)
        if match:
            data["code"] = match.group(1).strip()
        
        match = re.search(r"INSTALLATIONS\s*:.*?\n(.*?)\n(\d{5})\s+([A-ZÀ-Ÿ][^\n]+)", bloc, re.DOTALL)
        if match:
            data["adresse"] = match.group(1).strip()
            data["code_postal"] = match.group(2).strip()
            data["ville"] = match.group(3).strip()
        
        match = re.search(r"(\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2})", bloc)
        if match:
            data["telephone"] = match.group(1)
        
        match = re.search(r"([\w.-]+@[\w.-]+\.\w+)", bloc)
        if match:
            data["email"] = match.group(1)
        
        # FIX V2 : on capture P suivi de chiffres, suivi éventuellement de H/F/M
        # On nettoie d'abord le code FFT pour pas le confondre
        bloc_clean = re.sub(r"P\s+\d{4}\s+\d+\s+\d+\s+\d+\s+\d+", "", bloc)
        # Trouve : P25, P100, P25H, P250M, P100F, etc.
        matches = re.findall(r"\bP(\d{2,4})[HFM]?\b", bloc_clean)
        # On garde juste le numéro (P25, P100, P250...)
        cats = sorted(set(f"P{n}" for n in matches), key=lambda x: int(x[1:]))
        data["categories_p"] = cats
        
        epreuves = re.findall(r"Double (?:Dames|Messieurs|Mixte)", bloc)
        data["epreuves"] = sorted(set(epreuves))
        
        tournois.append(data)
    
    # Dédoublonner sur le code
    vus = set()
    uniques = []
    for t in tournois:
        if t["code"] and t["code"] not in vus:
            vus.add(t["code"])
            uniques.append(t)
    return uniques


def sauver_csv(tournois, fichier):
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
sauver_csv(tournois, "tournois.csv")

# Audit immédiat
vides = sum(1 for t in tournois if not t["categories_p"])
print(f"✅ {len(tournois)} tournois sauvegardés")
print(f"📊 Catégories vides : {vides} (avant : 17)")
print(f"\nExemples :")
for t in tournois[:5]:
    print(f"  {t['nom_tournoi'][:50]:52} → {t['categories_p']}")
