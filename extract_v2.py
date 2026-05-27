from bs4 import BeautifulSoup
import re


def extraire_tournoi(html):
    """
    Extrait les infos d'un tournoi depuis le HTML d'une page Ten'Up.
    Retourne un dictionnaire.
    """
    soup = BeautifulSoup(html, "html.parser")
    texte = soup.get_text()
    
    data = {
        "nom": None,
        "club_ville": None,
        "adresse": None,
        "code_postal": None,
        "ville": None,
        "dates": None,
        "juge_arbitre": None,
        "categories": [],
    }
    
    h1 = soup.find("h1")
    if h1:
        data["nom"] = h1.get_text(strip=True)
    
    h2 = soup.find("h2")
    if h2:
        data["club_ville"] = h2.get_text(strip=True)
    
    match = re.search(r"Juge arbitre\s+([A-Za-zÀ-ÿ' -]+?)\s*\n", texte)
    if match:
        data["juge_arbitre"] = match.group(1).strip()
    
    categories = re.findall(r"\bP\d+\b", texte)
    data["categories"] = sorted(set(categories))
    
    dates = re.findall(r"\d{2}/\d{2}/\d{2,4}", texte)
    if dates:
        data["dates"] = f"{dates[0]} - {dates[1]}" if len(dates) > 1 else dates[0]
    
    # Code postal et ville : on s'arrête au premier saut de ligne ou espace multiple
    match_cp = re.search(r"(\d{5})\s+([A-ZÀ-Ÿ][A-ZÀ-Ÿ' -]+?)(?:\s{2,}|\n)", texte)
    if match_cp:
        data["code_postal"] = match_cp.group(1)
        data["ville"] = match_cp.group(2).strip()
    
    match_adr = re.search(r"(\d+\s+(?:RUE|AVENUE|BOULEVARD|CHEMIN|ROUTE|PLACE|ALLEE|IMPASSE|QUAI)[^,\n]+)", texte)
    if match_adr:
        data["adresse"] = match_adr.group(1).strip()
    
    return data


with open("page_tournoi.html", "r", encoding="utf-8") as f:
    html = f.read()

infos = extraire_tournoi(html)

print("=" * 50)
print("Tournoi extrait :")
print("=" * 50)
for cle, valeur in infos.items():
    print(f"  {cle:15} : {valeur}")
