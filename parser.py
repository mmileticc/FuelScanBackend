import requests
from bs4 import BeautifulSoup
import re

def parse_taxcore_receipt(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # 1. ukupna cena (NAJPOUZDANIJE)
    total = soup.select_one("#totalAmountLabel")
    total_amount = total.text.strip() if total else None

    # 2. broj računa
    invoice_number = soup.select_one("#invoiceNumberLabel")
    invoice_number = invoice_number.text.strip() if invoice_number else None

    # 3. PFR vreme
    time_label = soup.select_one("#sdcDateTimeLabel")
    date_time = time_label.text.strip() if time_label else None

    # 4. parsing "jurnal" (ključni deo)
    pre = soup.find("pre")
    items = []

    if pre:
        lines = pre.get_text("\n").split("\n")

        for line in lines:
            # heuristika: hvata linije sa cenama
            match = re.search(r"(.+?)\s+(\d+[.,]\d{2})\s+(\d+(?:[.,]\d+)?)\s+(\d+[.,]\d{2})$", line)
            if match:
                name = match.group(1).strip()
                qty = match.group(2).replace(",", ".")
                unit_price = match.group(3).replace(",", ".")
                total_price = match.group(4).replace(",", ".")

                items.append({
                    "name": name,
                    "quantity": float(qty),
                    "unit_price": float(unit_price),
                    "total": float(total_price)
                })

    return {
        "invoice_number": invoice_number,
        "date": date_time,
        "total": total_amount,
        "items": items
    }

def parse_number(val: str):
    if not val:
        return None
    return float(val.replace(".", "").replace(",", "."))