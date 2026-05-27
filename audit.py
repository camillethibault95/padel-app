import csv

with open("tournois.csv", "r", encoding="utf-8") as f:
    tournois = list(csv.DictReader(f))

print(f"Total : {len(tournois)} tournois\n")

# Compter les champs vides
champs = tournois[0].keys()
print("Champs vides par colonne :")
for champ in champs:
    vides = sum(1 for t in tournois if not t[champ])
    if vides > 0:
        print(f"  {champ:20} : {vides} vides sur {len(tournois)}")

# Quelques exemples par ville
print("\nRépartition par ville :")
villes = {}
for t in tournois:
    v = t["ville"] or "INCONNUE"
    villes[v] = villes.get(v, 0) + 1
for v, n in sorted(villes.items(), key=lambda x: -x[1]):
    print(f"  {v:30} : {n}")

# Catégories P
print("\nCatégories P trouvées :")
toutes_cats = {}
for t in tournois:
    if t["categories_p"]:
        for cat in t["categories_p"].split(" / "):
            toutes_cats[cat] = toutes_cats.get(cat, 0) + 1
for cat, n in sorted(toutes_cats.items()):
    print(f"  {cat:6} : {n} tournois")
