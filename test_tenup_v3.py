from playwright.sync_api import sync_playwright

url = "https://tenup.fft.fr/tournoi/82454966"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("Ouverture de la page...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    
    html = page.content()
    
    with open("page_tournoi.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Page sauvegardée : {len(html)} caractères dans page_tournoi.html")
    print("Titre :", page.title())
    
    print("Le navigateur reste ouvert 10 secondes, regarde bien la page...")
    page.wait_for_timeout(10000)
    
    browser.close()
    print("Fini !")
