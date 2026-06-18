import csv
import re
import time
import requests
import pdfplumber


def load_clubs(chemin="clubs.csv"):
    """Charge clubs.csv en dict : { nom_normalise : {methode, ios, android, web, tel, notes} }"""
    clubs = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nom = row["nom_club"].strip().upper()
                clubs[nom] = {
                    "methode": row.get("methode", "").strip(),
                    "ios": row.get("url_ios", "").strip(),
                    "android": row.get("url_android", "").strip(),
                    "web": row.get("url_web", "").strip(),
                    "tel": row.get("telephone", "").strip(),
                    "notes": row.get("notes", "").strip(),
                }
        print(f"   {len(clubs)} clubs charges depuis {chemin}")
    except FileNotFoundError:
        print(f"   ATTENTION : {chemin} introuvable, pas d'infos d'inscription")
    return clubs


def match_club(nom_tournoi_club, dict_clubs):
    """Cherche le club correspondant : exact, puis 'contient', puis None."""
    if not nom_tournoi_club:
        return None
    nom_norm = nom_tournoi_club.strip().upper()
    
    # 1. Match exact
    if nom_norm in dict_clubs:
        return dict_clubs[nom_norm]
    
    # 2. Match "contient" (le nom du tournoi contient le nom d'un club du CSV, ou inverse)
    for nom_csv, infos in dict_clubs.items():
        if nom_csv in nom_norm or nom_norm in nom_csv:
            return infos
    
    # 3. Match par mots-cles : si 2+ mots significatifs en commun
    mots_tournoi = set(m for m in nom_norm.split() if len(m) > 3)
    for nom_csv, infos in dict_clubs.items():
        mots_csv = set(m for m in nom_csv.split() if len(m) > 3)
        if len(mots_tournoi & mots_csv) >= 2:
            return infos
    
    return None


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
    
    # Filtre : tournois non passes ET dates valides (entre 2024 et 2030)
    from datetime import datetime, date
    today = datetime.now().date()
    date_min = date(2024, 1, 1)
    date_max = date(2030, 12, 31)
    tournois_a_venir = []
    retires_passe = 0
    retires_aberrants = 0
    for t in tournois:
        if not t.get("date_fin") or not t.get("date_debut"):
            retires_aberrants += 1
            continue
        try:
            date_debut = datetime.strptime(t["date_debut"], "%d/%m/%Y").date()
            date_fin = datetime.strptime(t["date_fin"], "%d/%m/%Y").date()
            
            # Date aberrante (avant 2024 ou apres 2030) ?
            if date_debut < date_min or date_debut > date_max:
                retires_aberrants += 1
                continue
            if date_fin < date_min or date_fin > date_max:
                retires_aberrants += 1
                continue
            
            # Tournoi deja passe ?
            if date_fin < today:
                retires_passe += 1
                continue
            
            # Tournoi trop long (> 30 jours) ? Probablement un tournoi interne club
            duree = (date_fin - date_debut).days
            if duree > 30:
                retires_aberrants += 1
                continue
            
            tournois_a_venir.append(t)
        except ValueError:
            retires_aberrants += 1
            continue
    
    print(f"   Tournois retires : {retires_passe} passes + {retires_aberrants} dates aberrantes")
    tournois = tournois_a_venir
    
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
# --- Enrichissement avec clubs.csv ---
print("\n🔗 Association tournois <-> clubs...")
dict_clubs = load_clubs()
matches = 0
for t in tournois:
    infos = match_club(t.get("club"), dict_clubs)
    if infos:
        matches += 1
        t["inscription_methode"] = infos["methode"]
        t["inscription_ios"] = infos["ios"]
        t["inscription_android"] = infos["android"]
        t["inscription_web"] = infos["web"]
        t["inscription_tel"] = infos["tel"]
    else:
        t["inscription_methode"] = ""
        t["inscription_ios"] = ""
        t["inscription_android"] = ""
        t["inscription_web"] = ""
        t["inscription_tel"] = ""
print(f"   {matches}/{len(tournois)} tournois associes a un club")

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
