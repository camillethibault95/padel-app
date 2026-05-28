import csv
import json
import re
import shutil
import os


def date_iso(d):
    if not d or "/" not in d:
        return ""
    parts = d.split("/")
    if len(parts) != 3:
        return ""
    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"


def parser_epreuves(nom, epreuves_str):
    paires = []
    lettre_vers_genre = {"H": "Messieurs", "F": "Dames", "D": "Dames", "M": "Mixte"}
    
    pattern1 = re.findall(r"P(\d{2,4})([HFDM])\b", nom)
    for cat_num, lettre in pattern1:
        paires.append({"categorie": f"P{cat_num}", "genre": lettre_vers_genre[lettre]})
    
    pattern2 = re.findall(r"P(\d{2,4})\s+H/F", nom)
    for cat_num in pattern2:
        if not any(p["categorie"] == f"P{cat_num}" for p in paires):
            paires.append({"categorie": f"P{cat_num}", "genre": "Messieurs"})
            paires.append({"categorie": f"P{cat_num}", "genre": "Dames"})
    
    pattern3 = re.findall(
        r"P(\d{2,4})\s+(Hommes|Messieurs|Dames|Femmes|Mixte|mixte|hommes|messieurs|dames|femmes)",
        nom, re.IGNORECASE
    )
    for cat_num, mot in pattern3:
        ml = mot.lower()
        if ml in ("hommes", "messieurs"):
            genre = "Messieurs"
        elif ml in ("dames", "femmes"):
            genre = "Dames"
        else:
            genre = "Mixte"
        if not any(p["categorie"] == f"P{cat_num}" and p["genre"] == genre for p in paires):
            paires.append({"categorie": f"P{cat_num}", "genre": genre})
    
    pattern4 = re.findall(r"P(\d{2,4})\s+([HFDM])\b", nom)
    for cat_num, lettre in pattern4:
        genre = lettre_vers_genre[lettre]
        if not any(p["categorie"] == f"P{cat_num}" and p["genre"] == genre for p in paires):
            paires.append({"categorie": f"P{cat_num}", "genre": genre})
    
    if not paires:
        cats = re.findall(r"P(\d{2,4})", nom)
        genres = []
        if "Messieurs" in epreuves_str:
            genres.append("Messieurs")
        if "Dames" in epreuves_str:
            genres.append("Dames")
        if "Mixte" in epreuves_str:
            genres.append("Mixte")
        
        if len(cats) == 1 and len(genres) == 1:
            paires.append({"categorie": f"P{cats[0]}", "genre": genres[0]})
        else:
            for c in cats:
                for g in genres:
                    paires.append({"categorie": f"P{c}", "genre": g})
    
    return paires


def charger_tournois(chemin_csv):
    with open(chemin_csv, "r", encoding="utf-8") as f:
        tournois = list(csv.DictReader(f))
    return [t for t in tournois if t["latitude"] and t["longitude"]]


def construire_points(tournois):
    points = []
    for t in tournois:
        cats_list = [c.strip() for c in (t["categories_p"] or "").split("/") if c.strip()]
        nom = t["nom_tournoi"] or ""
        epreuves = t["epreuves"] or ""
        epreuves_detail = parser_epreuves(nom, epreuves)
        
        points.append({
            "lat": float(t["latitude"]),
            "lon": float(t["longitude"]),
            "club": t["club"],
            "nom": nom,
            "dates": t["date_debut"] + " -> " + t["date_fin"],
            "date_debut_iso": date_iso(t["date_debut"]),
            "date_fin_iso": date_iso(t["date_fin"]),
            "categories": cats_list,
            "categories_str": t["categories_p"] or "Non precisee",
            "epreuves_detail": epreuves_detail,
            "ville": t["ville"],
            "juge": t["juge_arbitre"] or "Non precise",
            "tel": t["telephone"] or "",
            "email": t["email"] or "",
            "epreuves": epreuves,
        })
    return points


def main():
    tournois = charger_tournois("tournois.csv")
    print(f"{len(tournois)} tournois geolocalises")
    
    points = construire_points(tournois)
    
    sans_paire = sum(1 for p in points if not p["epreuves_detail"])
    print(f"{sans_paire} tournois sans paire detectee (sur {len(points)})")
    
    with open("tournois.json", "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)
    print("tournois.json genere")
    
    for fichier in ["index.html", "styles.css", "app.js"]:
        src = os.path.join("templates", fichier)
        shutil.copy(src, fichier)
        print(f"{fichier} copie")


if __name__ == "__main__":
    main()
