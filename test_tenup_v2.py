from playwright.sync_api import sync_playwright

url = "https://tenup.fft.fr/tournoi/82173545"

with sync_playwright() as p:
    # On lance un Chrome en arrière-plan (headless = invisible)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # On ouvre la page et on attend qu'elle soit prête
    print("Ouverture de la page...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    
    # On récupère le HTML final
    html = page.content()
    
    print("Taille de la page :", len(html), "caractères")
    print("---")
    print("Titre :", page.title())
    print("---")
    print("Aperçu (200 caractères au milieu) :")
    print(html[3000:3500])
    
    browser.close()
