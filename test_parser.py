"""
Test du parser d'épreuves : essaye de transformer le nom + epreuves
en liste de paires {categorie, genre}.
"""
import re
import csv


def parser_epreuves(nom, epreuves_str):
    """
    Retourne une liste de dicts {categorie, genre}.
    
    Logique :
    1. Cherche les motifs P25H, P100F, P250M dans le nom (lettre collée)
    2. Si pas trouvé, cherche P25 H/F/Mixte avec un espace ou separateur
    3. Si toujours rien, utilise les categories + epreuves comme fallback
    """
    paires = []
    
    # Mapping des lettres vers genres
    lettre_vers_genre = {
        "H": "Messieurs",
        "F": "Dames",
        "D": "Dames",  # parfois D pour Dames (genre P100D)
        "M": "Mixte",
    }
    
    # Pattern 1 : Pxx suivi immédiatement d'une lettre H/F/D/M
    # Exemple : P25H, P100F, P250M, P100D
    pattern1 = re.findall(r"P(\d{2,4})([HFDM])\b", nom)
    for cat_num, lettre in pattern1:
        paires.append({
            "categorie": f"P{cat_num}",
            "genre": lettre_vers_genre[lettre]
        })
    
    # Pattern 2 : Pxx H/F (= deux épreuves pour la même catégorie)
    pattern2 = re.findall(r"P(\d{2,4})\s+H/F", nom)
    for cat_num in pattern2:
        # Eviter doublons si pattern1 a déjà capté
        if not any(p["categorie"] == f"P{cat_num}" for p in paires):
            paires.append({"categorie": f"P{cat_num}", "genre": "Messieurs"})
            paires.append({"categorie": f"P{cat_num}", "genre": "Dames"})
    
    # Pattern 3 : Pxx suivi d'un mot complet (Hommes/Messieurs/Dames/Femmes/Mixte)
    pattern3 = re.findall(
        r"P(\d{2,4})\s+(Hommes|Messieurs|Dames|Femmes|Mixte|mixte|hommes|messieurs|dames|femmes)",
        nom, re.IGNORECASE
    )
    for cat_num, mot in pattern3:
        mot_lower = mot.lower()
        if mot_lower in ("hommes", "messieurs"):
            genre = "Messieurs"
        elif mot_lower in ("dames", "femmes"):
            genre = "Dames"
        else:
            genre = "Mixte"
        if not any(p["categorie"] == f"P{cat_num}" and p["genre"] == genre for p in paires):
            paires.append({"categorie": f"P{cat_num}", "genre": genre})
    
    # Pattern 4 : Pxx suivi d'un espace puis H/F/D/M isolés
    # Exemple : "P50 H 04/06", "P250 H ASCH"
    pattern4 = re.findall(r"P(\d{2,4})\s+([HFDM])\b", nom)
    for cat_num, lettre in pattern4:
        genre = lettre_vers_genre[lettre]
        if not any(p["categorie"] == f"P{cat_num}" and p["genre"] == genre for p in paires):
            paires.append({"categorie": f"P{cat_num}", "genre": genre})
    
    # Fallback : si rien trouvé, on utilise les categories + epreuves
    if not paires:
        # Chercher les Pxx dans le nom
        cats = re.findall(r"P(\d{2,4})", nom)
        # Identifier les genres depuis epreuves
        genres = []
        if "Messieurs" in epreuves_str: genres.append("Messieurs")
        if "Dames" in epreuves_str: genres.append("Dames")
        if "Mixte" in epreuves_str: genres.append("Mixte")
        
        # Si on a 1 cat et 1 genre, on associe
        if len(cats) == 1 and len(genres) == 1:
            paires.append({"categorie": f"P{cats[0]}", "genre": genres[0]})
        else:
            # Cas dégradé : on fait toutes les combinaisons (incertain)
            for c in cats:
                for g in genres:
                    paires.append({"categorie": f"P{c}", "genre": g, "incertain": True})
    
    return paires


# Test sur les 30 premiers tournois
with open("tournois.csv") as f:
    rows = list(csv.DictReader(f))

print("Test du parser sur 30 tournois :\n")
for r in rows[:30]:
    nom = r["nom_tournoi"]
    epreuves = r["epreuves"]
    paires = parser_epreuves(nom, epreuves)
    
    # Format compact
    paires_str = " | ".join(
        f"{p['categorie']}+{p['genre']}" + ("?" if p.get("incertain") else "")
        for p in paires
    ) or "(aucune épreuve détectée)"
    
    print(f"  {nom[:55]:55}")
    print(f"    epreuves brutes : {epreuves}")
    print(f"    → {paires_str}")
    print()
