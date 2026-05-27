import subprocess
import sys
import os

# On veut être dans le bon dossier
os.chdir(os.path.expanduser("~/padel-app"))

ETAPES = [
    ("1️⃣  Téléchargement du PDF depuis Ten'Up", "download.py"),
    ("2️⃣  Parsing + géocodage", "clean_and_geocode.py"),
    ("3️⃣  Génération de la carte", "generer_carte.py"),
]

print("=" * 60)
print("  🎾 PADEL TOURNOIS — Mise à jour complète")
print("=" * 60)

for titre, script in ETAPES:
    print(f"\n{titre}")
    print("-" * 60)
    
    result = subprocess.run(
        [sys.executable, script],
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"\n❌ ERREUR sur {script}, arrêt du pipeline.")
        sys.exit(1)

print("\n" + "=" * 60)
print("  ✅ TERMINÉ — Ouverture de la carte...")
print("=" * 60)

# Ouvre la carte dans le navigateur
subprocess.run(["open", "carte.html"])
