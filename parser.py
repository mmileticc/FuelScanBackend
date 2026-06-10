import re
from playwright.async_api import async_playwright


def parse_number(val):
    """
    Pretvara srpski format broja u čist float, a ako je već float, samo ga vrati.
    """
    if val is None:
        return None

    # Ako je vrednost već broj (npr. float ili int), nema potrebe za obradom
    if isinstance(val, (int, float)):
        return float(val)

    try:
        # Pretvaramo u string, čistimo razmake, i sređujemo decimale
        clean_val = str(val).strip().replace(".", "").replace(",", ".")
        return float(clean_val)
    except ValueError:
        return None

async def parse_taxcore_receipt(url: str):
    invoice_number = None
    date_time = None
    total_amount = None
    items = []

    # Pokrećemo Playwright asinhrono
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Dodajemo standardni User-Agent da nas server ne bi blokirao
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"➡️ Otvaram račun: {url}")
            await page.goto(url, wait_until="networkidle")

            # --- 1. VADJENJE META PODATAKA (iz HTML-a) ---
            html = await page.content()

            inv_match = re.search(r"([A-Z0-9]{8}-[A-Z0-9]{8}-\d+)", html)
            if inv_match:
                invoice_number = inv_match.group(1)

            date_match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4}\.\s\d{2}:\d{2}:\d{2})", html)
            if date_match:
                date_time = date_match.group(1)

            total_match = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", html)
            if total_match:
                total_amount = total_match.group(1)

            # --- 1.5. VADJENJE IMENA PRODAJNOG MESTA ---
            try:
                # Primarno: Gađamo element po ID-u koji TaxCore koristi
                if await page.locator('#shopFullNameLabel').count() > 0:
                    station = await page.locator('#shopFullNameLabel').inner_text()
                else:
                    # Fallback: Nađemo labelu po tekstu i uzmemo prvi sledeći DOM element
                    label = page.locator('text="Име продајног места"').first
                    if await label.count() > 0:
                        station = await label.evaluate(
                            "el => el.nextElementSibling ? el.nextElementSibling.innerText : ''")
            except Exception as e:
                print(f"⚠️ Nije pronađeno ime prodajnog mesta: {e}")

            # Čistimo prazna mesta i nove redove
            station = station.strip() if station else "Nepoznata pumpa"

            # --- 2. KLIK NA SPECIFIKACIJU I VADJENJE ARTIKALA ---
            print("➡️ Tražim panel 'Спецификација рачуна'...")

            # CSS Selektor za link koji otvara panel (sa tvoje slike: href="#collapse-specs")
            collapse_link_selector = 'a[href="#collapse-specs"]'

            if await page.locator(collapse_link_selector).count() > 0:
                print("➡️ Klikćem na panel da se učitaju artikli...")
                # Kliknemo da se tabela pojavi i trigerujemo učitavanje
                await page.click(collapse_link_selector)

                # KLJUČNO: Čekamo da se pojave redovi (tr) unutar tbody u specifikaciji.
                # Ovo garantuje da je JS odradio svoj posao i povukao podatke.
                await page.wait_for_selector('#collapse-specs tbody tr', timeout=10000)

                # Uzimamo sve redove iz tabele
                rows = await page.locator('#collapse-specs tbody tr').all()
                print(f"➡️ Pronađeno {len(rows)} artikala. Izvlačim podatke...")

                for row in rows:
                    # Izvlačimo sve kolone (td) u tom redu
                    cols = await row.locator('td').all()

                    if len(cols) >= 7:
                        name = await cols[0].inner_text()
                        quantity = await cols[1].inner_text()
                        unit_price = await cols[2].inner_text()
                        total = await cols[3].inner_text()
                        tax_base = await cols[4].inner_text()
                        vat = await cols[5].inner_text()
                        label = await cols[6].inner_text()

                        items.append({
                            "name": name.strip(),
                            "quantity": parse_number(quantity.strip()),
                            "unit_price": parse_number(unit_price.strip()),
                            "total": parse_number(total.strip()),
                            "tax_base": parse_number(tax_base.strip()),
                            "vat": parse_number(vat.strip()),
                            "label": label.strip()
                        })
            else:
                print("⚠️ Nije pronađeno dugme '#collapse-specs'. Moguće da je struktura drugačija.")

        except Exception as e:
            print(f"❌ Greška u Playwright parseru: {e}")
        finally:
            # Obavezno zatvaramo browser na kraju kako ne bismo napravili memory leak
            await browser.close()

    return {
        "invoice_number": invoice_number,
        "date": date_time,
        "total": total_amount,
        "station": station,
        "items": items
    }