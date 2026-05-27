from bs4 import BeautifulSoup

# Lire le fichier HTML qu'on a sauvegardé
with open("page_tournoi.html", "r", encoding="utf-8") as f:
    html = f.read()

# BeautifulSoup transforme le HTML en truc qu'on peut "interroger"
soup = BeautifulSoup(html, "html.parser")

# --- Le titre du tournoi (club + ville) ---
titre = soup.find("h1")
print("Titre H1 :", titre.get_text(strip=True) if titre else "non trouvé")

# --- Toutes les balises h2 et h3 (titres de sections) ---
print("\n--- Sections trouvées ---")
for h in soup.find_all(["h2", "h3"]):
    print(f"  [{h.name}] {h.get_text(strip=True)}")

# --- On cherche le mot "Juge arbitre" et ce qui suit ---
print("\n--- Juge arbitre ---")
texte_complet = soup.get_text()
if "Juge arbitre" in texte_complet:
    idx = texte_complet.find("Juge arbitre")
    print(texte_complet[idx:idx+100])

# --- On cherche l'adresse ---
print("\n--- Recherche P100/P250/etc dans la page ---")
import re
categories = re.findall(r"P\d+", texte_complet)
print("Catégories P trouvées :", set(categories))
