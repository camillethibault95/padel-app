from playwright.sync_api import sync_playwright

# URL avec le filtre padel directement dans les paramètres
URLS_A_TESTER = [
    "https://tenup.fft.fr/recherche/tournois?pratique=PADEL",
    "https://tenup.fft.fr/recherche/tournois?pratique=padel",
    "https://tenup.fft.fr/recherche/tournois?sport=padel",
]

VILLE = "Montpellier"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    # On essaie la 1re URL
    url = URLS_A_TESTER[0]
    print(f"Test URL : {url}")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    
    try:
        page.get_by_role("button", name="TOUT ACCEPTER").click(timeout=10000)
    except:
        pass
    page.wait_for_timeout(2000)
    
    # Saisie ville
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
    page.wait_for_timeout(6000)
    
    page.screenshot(path="test_url_padel.png", full_page=True)
    print("Capture sauvegardee : test_url_padel.png")
    
    # On regarde ce qu'on a comme épreuves dans les résultats
    print("\nRecherche des codes d'epreuves (SM/SD = tennis, DM/DD/DX = padel) :")
    boutons = page.locator('button').all()
    codes_trouves = set()
    for b in boutons:
        try:
            if b.is_visible():
                txt = (b.inner_text() or "").strip()
                if txt in ["SM", "SD", "DM", "DD", "DX"] or "/" in txt and len(txt) < 25:
                    codes_trouves.add(txt)
        except:
            pass
    print(f"   Codes trouves : {codes_trouves}")
    
    print("\nChrome reste ouvert 30s pour observer")
    page.wait_for_timeout(30000)
    browser.close()
