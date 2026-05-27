import csv

with open("tournois.csv", "r", encoding="utf-8") as f:
    tournois = list(csv.DictReader(f))

print("Tournois en score bas (à vérifier) :\n")
for t in tournois:
    score = float(t["score_geo"]) if t["score_geo"] else 0
    if score <= 0.4:
        has_gps = "✅ GPS OK" if t["latitude"] else "❌ Pas de GPS"
        print(f"  {has_gps} | {t['club'][:35]:37} | {t['ville']:25} | lat={t['latitude']}")
