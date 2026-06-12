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
    station = "Nepoznata pumpa"
    items = []

    async with async_playwright() as p:
        # Dodajemo argumente za smanjenje potrošnje memorije u Dockeru
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # Ključno za Docker kontejnere sa malo RAM-a
                "--disable-accelerated-2d-canvas",
                "--disable-gpu"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # OPTIMIZACIJA: Blokiramo slike, fontove i CSS da uštedimo protok i vreme
        await page.route("**/*", lambda route, request:
        route.abort() if request.resource_type in ["image", "media", "font", "stylesheet"]
        else route.continue_()
                         )

        try:
            print(f"➡️ Otvaram račun: {url}")
            # Smanjujemo timeout na 20 sekundi da ruter ne bi čekao večno ako pukne veza
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # --- 1. VADJENJE META PODATAKA ---
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
                # Koristimo kraći timeout za pojedinačne elemente
                shop_label = page.locator('#shopFullNameLabel')
                if await shop_label.count() > 0:
                    station = await shop_label.inner_text()
                else:
                    label = page.locator('text="Име продајног места"').first
                    if await label.count() > 0:
                        station = await label.evaluate(
                            "el => el.nextElementSibling ? el.nextElementSibling.innerText : ''")
            except Exception as e:
                print(f"⚠️ Nije pronađeno ime prodajnog mesta: {e}")

            station = station.strip() if station else "Nepoznata pumpa"

            # --- 2. KLIK NA SPECIFIKACIJU I VADJENJE ARTIKALA ---
            collapse_link_selector = 'a[href="#collapse-specs"]'

            if await page.locator(collapse_link_selector).count() > 0:
                await page.click(collapse_link_selector)

                # Čekamo samo tabelu, smanjen timeout na 5 sekundi jer je DOM već tu
                await page.wait_for_selector('#collapse-specs tbody tr', timeout=5000)

                rows = await page.locator('#collapse-specs tbody tr').all()

                for row in rows:
                    cols = await row.locator('td').all()
                    if len(cols) >= 7:
                        # Brže uzimanje teksta direktno preko evaluate ili inner_text
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
                print("⚠️ Nije pronađeno dugme '#collapse-specs'.")

        except Exception as e:
            print(f"❌ Greška u Playwright parseru: {e}")
        finally:
            # Eksplicitno zatvaranje klijenta i browsera
            await context.close()
            await browser.close()

    return {
        "invoice_number": invoice_number,
        "date": date_time,
        "total": total_amount,
        "station": station,
        "items": items
    }