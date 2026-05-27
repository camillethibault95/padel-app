import csv

with open("tournois.csv", "r", encoding="utf-8") as f:
    tournois = list(csv.DictReader(f))

print(f"Total : {len(tournois)} tournois\n")

# Afficher les 10 premiers avec leurs coordonnées
print("=== 10 premiers tournois ===\n")
for t in tournois[:10]:
    print(f"Club    : {t['club'][:50]}")
    print(f"Adresse : {t['adresse']}, {t['code_postal']} {t['ville']}")
    print(f"GPS     : lat={t['latitude']}  lon={t['longitude']}")
    print(f"Score   : {t['score_geo']}")
    print(f"Norm    : {t['adresse_normalisee']}")
    print()
