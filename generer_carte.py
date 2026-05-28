"""
Generateur de la carte : 
- Lit le CSV des tournois
- Genere data/tournois.json
- Copie templates/* vers la racine pour Vercel
"""
import csv
import json
import shutil
import os


def date_iso(d):
    """Convertit JJ/MM/AAAA en AAAA-MM-JJ"""
    if not d or "/" not in d:
        return ""
    parts = d.split("/")
    if len(parts) != 3:
        return ""
    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"


def charger_tournois(chemin_csv):
    """Charge le CSV et retourne la liste des tournois geolocalises."""
    with open(chemin_csv, "r", encoding="utf-8") as f:
        tournois = list(csv.DictReader(f))
    return [t for t in tournois if t["latitude"] and t["longitude"]]


def construire_points(tournois):
    """Convertit les lignes CSV en dictionnaires propres pour le JS."""
    points = []
    for t in tournois:
        cats_list = [c.strip() for c in (t["categories_p"] or "").split("/") if c.strip()]
        points.append({
            "lat": float(t["latitude"]),
            "lon": float(t["longitude"]),
            "club": t["club"],
            "nom": t["nom_tournoi"],
            "dates": t["date_debut"] + " -> " + t["date_fin"],
            "date_debut_iso": date_iso(t["date_debut"]),
            "date_fin_iso": date_iso(t["date_fin"]),
            "categories": cats_list,
            "categories_str": t["categories_p"] or "Non precisee",
            "ville": t["ville"],
            "juge": t["juge_arbitre"] or "Non precise",
            "tel": t["telephone"] or "",
            "email": t["email"] or "",
            "epreuves": t["epreuves"] or "",
        })
    return points


def main():
    tournois = charger_tournois("tournois.csv")
    print(f"{len(tournois)} tournois geolocalises")
    
    points = construire_points(tournois)
    with open("tournois.json", "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)
    print("tournois.json genere")
    
    for fichier in ["index.html", "styles.css", "app.js"]:
        src = os.path.join("templates", fichier)
        dst = fichier
        shutil.copy(src, dst)
        print(f"{fichier} copie")


if __name__ == "__main__":
    main()
