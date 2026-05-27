import csv
import re
import time
import requests
import pdfplumber


def lire_pdf(chemin):
    with pdfplumber.open(chemin) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)


def nettoyer_adresse(adresse_brute):
    """Retire les pollutions comme 'INSCRIPTIONS / PAIEMENT...', 'CODE : P...'"""
    if not adresse_brute:
        return None
    
    lignes = adresse_brute.split("\n")
    lignes_propres = []
    for ligne in lignes:
        ligne = ligne.strip()
        # On garde uniquement les lignes qui ressemblent à une adresse
        if (ligne 
            and not ligne.startswith("INSCRIPTIONS") 
            and not ligne.startswith("CODE")
            and not ligne.startswith("PRIX")
            and not ligne.startswith("SURFACE")
            and not ligne.startswith("ENGAGEMENTS")
            and "@" not in ligne):
            lignes_propres.append(ligne)
    
    return " ".join(lignes_propres) if lignes_propres else None


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
        # Club = on prend la première ligne et on enlève la pollution après "ENGAGEMENTS"
        if lignes:
            club = lignes[0].split("ENGAGEMENTS")[0].strip()
            data["club"] = club
        
        # Nom du tournoi = on prend la 2e ligne, propre
        if len(lignes) > 1:
            nom = re.sub(r"\s+(?:Senior|Catégorie|ET TENNIS|ENGAGEMENTS).*$", "", lignes[1]).strip()
            # Et on coupe avant un numéro d'adresse (genre "250 rue", "816 av")
            nom = re.sub(r"\s+\d+\s+(rue|av|avenue|chemin|route|place|boulevard).*$", "", nom, flags=re.IGNORECASE).strip()
            data["nom_tournoi"] = nom
        
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
        
        # Extraction adresse : on cherche dans la section INSTALLATIONS
        # Pattern : trouve une ligne avec numéro + nom de rue, puis CP + ville
        # On extrait depuis INSTALLATIONS jusqu'au prochain bloc
        match_inst = re.search(r"INSTALLATIONS\s*:(.+?)(?:Catégorie|$)", bloc, re.DOTALL)
        if match_inst:
            zone_install = match_inst.group(1)
            # Trouver le code postal + ville
            match_cpv = re.search(r"(\d{5})\s+([A-ZÀ-Ÿ][A-ZÀ-Ÿ' -]+?)(?:\n|$)", zone_install)
            if match_cpv:
                data["code_postal"] = match_cpv.group(1)
                data["ville"] = match_cpv.group(2).strip()
                # L'adresse est avant le CP
                avant_cp = zone_install[:match_cpv.start()].strip()
                # Garde la dernière ligne avec des chiffres ou nom de rue
                lignes_adr = [l.strip() for l in avant_cp.split("\n") if l.strip()]
                # Prend la ligne qui a un numéro ou un mot de rue
                for ligne in reversed(lignes_adr):
                    if re.search(r"\d|rue|avenue|chemin|route|place|boulevard|impasse|allée|parc", ligne, re.IGNORECASE):
                        data["adresse"] = ligne
                        break
                if not data["adresse"] and lignes_adr:
                    data["adresse"] = lignes_adr[-1]
        
        match = re.search(r"(\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2})", bloc)
        if match:
            data["telephone"] = match.group(1)
        
        match = re.search(r"([\w.-]+@[\w.-]+\.\w+)", bloc)
        if match:
            data["email"] = match.group(1)
        
        bloc_clean = re.sub(r"P\s+\d{4}\s+\d+\s+\d+\s+\d+\s+\d+", "", bloc)
        matches = re.findall(r"\bP(\d{2,4})[HFM]?\b", bloc_clean)
        cats = sorted(set(f"P{n}" for n in matches), key=lambda x: int(x[1:]))
        data["categories_p"] = cats
        
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


def geocoder(adresse, code_postal, ville):
    query = f"{adresse} {code_postal} {ville}"
    try:
        r = requests.get("https://api-adresse.data.gouv.fr/search/",
                        params={"q": query, "limit": 1}, timeout=5)
        data = r.json()
        if not data.get("features"):
            return None, None, 0.0, "Pas de résultat"
        feat = data["features"][0]
        lon, lat = feat["geometry"]["coordinates"]
        score = feat["properties"].get("score", 0)
        label = feat["properties"].get("label", "")
        return lat, lon, score, label
    except Exception as e:
        return None, None, 0.0, f"Erreur : {e}"


# --- Programme ---
print("📄 Lecture du PDF...")
texte = lire_pdf("tournois.pdf")

print("🔍 Extraction des tournois...")
tournois = extraire_tournois(texte)
print(f"   → {len(tournois)} tournois uniques\n")

print("🌍 Géocodage en cours...")
for i, t in enumerate(tournois, 1):
    if not t["adresse"]:
        t["latitude"] = ""
        t["longitude"] = ""
        t["score_geo"] = 0
        t["adresse_normalisee"] = ""
        continue
    
    lat, lon, score, label = geocoder(t["adresse"], t["code_postal"], t["ville"])
    t["latitude"] = lat if lat else ""
    t["longitude"] = lon if lon else ""
    t["score_geo"] = round(score, 2)
    t["adresse_normalisee"] = label
    
    emoji = "✅" if score > 0.8 else "⚠️" if score > 0.4 else "❌"
    print(f"  [{i:2}/{len(tournois)}] {emoji} {score:.2f}  {t['club'][:30]:32} → {label[:50]}")
    time.sleep(0.1)

# Sauver
fieldnames = list(tournois[0].keys())
for t in tournois:
    if isinstance(t.get("categories_p"), list):
        t["categories_p"] = " / ".join(t["categories_p"])
    if isinstance(t.get("epreuves"), list):
        t["epreuves"] = " / ".join(t["epreuves"])

with open("tournois.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(tournois)

ok = sum(1 for t in tournois if t["score_geo"] and float(t["score_geo"]) > 0.8)
moyen = sum(1 for t in tournois if t["score_geo"] and 0.4 < float(t["score_geo"]) <= 0.8)
ko = sum(1 for t in tournois if not t["score_geo"] or float(t["score_geo"]) <= 0.4)

print(f"\n📊 Résultats :")
print(f"   ✅ Bon (>0.8)   : {ok}")
print(f"   ⚠️  Moyen (0.4-0.8) : {moyen}")
print(f"   ❌ À vérifier   : {ko}")
