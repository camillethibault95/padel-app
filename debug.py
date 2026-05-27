from playwright.sync_api import sync_playwright

URL = "https://tenup.fft.fr/recherche/tournois"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    print("1. Ouverture...")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    
    print("2. Acceptation cookies...")
    try:
        page.get_by_role("button", name="TOUT ACCEPTER").click(timeout=10000)
        print("   Cookies acceptes")
    except:
        print("   Pas de cookies a accepter")
    
    page.wait_for_timeout(3000)
    
    print("3. Liste de tous les champs input visibles :")
    inputs = page.locator('input').all()
    for i, inp in enumerate(inputs):
        try:
            is_visible = inp.is_visible()
            input_id = inp.get_attribute('id') or 'pas-d-id'
            placeholder = inp.get_attribute('placeholder') or ''
            input_type = inp.get_attribute('type') or 'text'
            if is_visible:
                print(f"   [{i}] VISIBLE  type={input_type}  id={input_id}")
                if placeholder:
                    print(f"        placeholder: {placeholder}")
        except:
            pass
    
    print("Chrome reste ouvert 20 secondes")
    page.wait_for_timeout(20000)
    
    browser.close()
    print("Fini.")
