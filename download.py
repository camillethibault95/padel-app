from playwright.sync_api import sync_playwright
import os

URL = "https://tenup.fft.fr/recherche/tournois?pratique=PADEL"
VILLE = "Montpellier"
DOSSIER_PROJET = os.path.expanduser("~/padel-app")


def telecharger_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=600)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 1. Ouvrir avec le filtre Padel dans l'URL
        print("1. Ouverture de Ten'Up (filtre Padel)...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        
        # 2. Cookies
        print("2. Acceptation des cookies...")
        try:
            page.get_by_role("button", name="TOUT ACCEPTER").click(timeout=10000)
            print("   OK")
        except:
            print("   Pas de popup")
        page.wait_for_timeout(2000)
        
        # 3. Saisir la ville
        print(f"3. Saisie de la ville : {VILLE}")
        champ = page.locator('#autocomplete-custom-input')
        champ.click()
        page.wait_for_timeout(300)
        page.keyboard.type(VILLE, delay=100)
        page.wait_for_timeout(2500)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        print("   OK")
        
        # 4. Rechercher
        print("4. Clic sur RECHERCHER...")
        page.wait_for_selector('button#edit-submit:not([disabled])', timeout=10000)
        page.locator('button#edit-submit').click()
        page.wait_for_timeout(6000)
        print("   OK")
        
        # 5. Télécharger
        print("5. Clic sur Telecharger...")
        try:
            with page.expect_download(timeout=30000) as download_info:
                page.get_by_text("Télécharger", exact=False).first.click()
            download = download_info.value
            chemin_pdf = os.path.join(DOSSIER_PROJET, "tournois.pdf")
            download.save_as(chemin_pdf)
            print(f"   ✅ PDF telecharge : {chemin_pdf}")
        except Exception as e:
            print(f"   ERREUR : {e}")
        
        page.wait_for_timeout(3000)
        browser.close()
        print("\n🎉 Fini.")


telecharger_pdf()
