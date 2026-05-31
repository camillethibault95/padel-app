from playwright.sync_api import sync_playwright
import requests
import os
import unicodedata

URL = "https://tenup.fft.fr/recherche/tournois?pratique=PADEL"
DOSSIER_PROJET = os.path.expanduser("~/padel-app")
DOSSIER_PDFS = os.path.join(DOSSIER_PROJET, "pdfs")

VILLES = [
    "Montpellier",
]

HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


def slugify(ville):
    s = unicodedata.normalize("NFKD", ville).encode("ascii", "ignore").decode()
    return s.lower().replace(" ", "-")


def telecharger_pdf_depuis_url(url, chemin):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(chemin, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"     ERREUR requests : {e}")
        return False


def chercher_et_telecharger(context, page, ville):
    print(f"\n--- Ville : {ville} ---")
    
    print("  0. Rechargement de Ten'Up...")
    page.bring_to_front()
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    print("     OK")
    
    print(f"  1. Saisie : {ville}")
    champ = page.locator('#autocomplete-custom-input')
    champ.click()
    page.wait_for_timeout(300)
    page.keyboard.type(ville, delay=100)
    page.wait_for_timeout(3000)
    
    try:
        page.wait_for_selector('.ui-autocomplete li', timeout=10000, state="visible")
    except:
        print("     ATTENTION : Pas de liste d'autocompletion")
    
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)
    print("     OK")
    
    print("  2. Recherche...")
    page.wait_for_selector('button#edit-submit:not([disabled])', timeout=10000)
    page.locator('button#edit-submit').click()
    page.wait_for_timeout(8000)
    print("     OK")
    
    print(f"  3. Telechargement...")
    try:
        with context.expect_page(timeout=30000) as new_page_info:
            page.get_by_text("Télécharger", exact=False).first.click()
        
        nouvel_onglet = new_page_info.value
        nouvel_onglet.wait_for_load_state("domcontentloaded", timeout=20000)
        url_pdf = nouvel_onglet.url
        print(f"     URL PDF : {url_pdf[:80]}...")
        
        # Le fichier principal s'appelle tournois.pdf (compat avec clean_and_geocode.py)
        chemin_pdf = os.path.join(DOSSIER_PROJET, "tournois.pdf")
        
        if telecharger_pdf_depuis_url(url_pdf, chemin_pdf):
            print(f"     OK : tournois.pdf")
            nouvel_onglet.close()
            page.bring_to_front()
            return True
        else:
            nouvel_onglet.close()
            page.bring_to_front()
            return False
    
    except Exception as e:
        print(f"     ERREUR : {type(e).__name__}: {str(e)[:100]}")
        return False


def telecharger_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=0 if HEADLESS else 600
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("Ouverture de Ten'Up...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        
        print("Acceptation des cookies...")
        try:
            page.get_by_role("button", name="TOUT ACCEPTER").click(timeout=10000)
            print("  OK")
        except:
            print("  Pas de popup")
        page.wait_for_timeout(2000)
        
        for ville in VILLES:
            chercher_et_telecharger(context, page, ville)
        
        page.wait_for_timeout(3000)
        browser.close()
        print("\nFini.")


if __name__ == "__main__":
    telecharger_pdf()
