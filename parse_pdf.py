import pdfplumber

with pdfplumber.open("tournois.pdf") as pdf:
    texte_complet = ""
    for page in pdf.pages:
        texte_complet += page.extract_text() + "\n"

with open("pdf_texte.txt", "w", encoding="utf-8") as f:
    f.write(texte_complet)

print(f"PDF lu : {len(texte_complet)} caractères")
print(f"Nombre de fois où on voit 'JUGE-ARBITRE' : {texte_complet.count('JUGE-ARBITRE')}")
print(f"Nombre de fois où on voit 'CODE :' : {texte_complet.count('CODE :')}")
print("Texte sauvegardé dans pdf_texte.txt")
