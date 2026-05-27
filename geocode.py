import csv
import requests
import time

API_URL = "https://api-adresse.data.gouv.fr/search/"


def geocoder(adresse, code_postal, ville):
    """Convertit une adresse en (latitude, longitude, score)."""
    # On construit une requête propre
    query = f"{adresse} {code_postal} {ville}"
    
    try:
        response = requests.get(
            API_URL,
            params={"q": query, "limit": 1},
            timeout=5
        )
        data = response.json()
        
        if not data.get("features"):
            return None, None, 0.0, "Pas de résultat"
        
        feature = data["features"][0]
        lon, lat = feature["geometry"]["coordinates"]
        score = feature["properties"].get("score", 0)
        label = feature["properties"].get("label", "")
        
        return lat, lon, score, label
    
    except Exception as e:
        return None, None, 0.0, f"Erreur : {e}"


# Lire le CSV existant
with open("tournois.csv", "r", encoding="utf-8") as f:
    tournois = list(csv.DictReader(f))

print(f"Géocodage de {len(tournois)} tournois...")
print("(API data.gouv.fr, ~0.1s par adresse, donc ~10s au total)\n")

# Géocoder chaque tournoi
for i, t in enumerate(tournois, 1):
    if not t["adresse"]:
        t["latitude"] = ""
        t["longitude"] = ""
        t["score_geo"] = ""
        t["adresse_normalisee"] = ""
        print(f"  [{i:2}/{len(tournois)}] ⚠️  Pas d'adresse : {t['club'][:40]}")
        continue
    
    lat, lon, score, label = geocoder(t["adresse"], t["code_postal"], t["ville"])
    
    t["latitude"] = lat if lat else ""
    t["longitude"] = lon if lon else ""
    t["score_geo"] = round(score, 2)
    t["adresse_normalisee"] = label
    
    emoji = "✅" if score > 0.8 else "⚠️" if score > 0.4 else "❌"
    print(f"  [{i:2}/{len(tournois)}] {emoji} score={score:.2f}  {label[:60]}")
    
    # On respecte l'API : 0.1s entre chaque appel
    time.sleep(0.1)

# Sauver en CSV avec les nouvelles colonnes
fieldnames = list(tournois[0].keys())
with open("tournois.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(tournois)

# Stats finales
ok = sum(1 for t in tournois if t.get("score_geo") and float(t["score_geo"]) > 0.8)
moyen = sum(1 for t in tournois if t.get("score_geo") and 0.4 < float(t["score_geo"]) <= 0.8)
ko = sum(1 for t in tournois if not t.get("score_geo") or float(t["score_geo"]) <= 0.4)

print(f"\n📊 Résultats :")
print(f"   ✅ Bon score (>0.8)  : {ok}")
print(f"   ⚠️  Moyen (0.4-0.8) : {moyen}")
print(f"   ❌ À vérifier        : {ko}")
print(f"\n✅ CSV mis à jour avec latitude / longitude")
