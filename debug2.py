from playwright.sync_api import sync_playwright

URL = "https://tenup.fft.fr/recherche/tournois"
VILLE = "Montpellier"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    print("Ouverture + cookies...")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    try:
        page.get_by_role("button", name="TOUT ACCEPTER").click(timeout=10000)
    except:
        pass
    page.wait_for_timeout(2000)
    
    print("Saisie ville...")
    champ = page.locator('#autocomplete-custom-input')
    champ.click()
    page.keyboard.type(VILLE, delay=100)
    page.wait_for_timeout(2500)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    
    print("Recherche...")
    page.wait_for_selector('button#edit-submit:not([disabled])', timeout=10000)
    page.locator('button#edit-submit').click()
    page.wait_for_timeout(5000)
    
    print("\n=== TOUS LES BOUTONS VISIBLES SUR LA PAGE DE RESULTATS ===\n")
    boutons = page.locator('button').all()
    for i, b in enumerate(boutons):
        try:
            if b.is_visible():
                texte = (b.inner_text() or "").strip().replace("\n", " ")[:80]
                btn_id = b.get_attribute('id') or ""
                btn_class = (b.get_attribute('class') or "")[:50]
                print(f"   [{i}]  texte={texte!r}  id={btn_id}")
        except:
            pass
    
    print("\nChrome reste ouvert 30 secondes")
    page.wait_for_timeout(30000)
    browser.close()
    print("Fini.")
