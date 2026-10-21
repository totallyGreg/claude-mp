#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "qrcode"]
# ///
"""Render a synthetic image set for the `see` tier eval, with ground truth.

    see_eval_images.py <out-dir>

Writes <out-dir>/*.png|jpg and <out-dir>/truth.json: one case per image with
its kind (text | pixels | code, the see.sh mode), JSON Schema, prompt, and
expected values.
"""
import json
import random
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
random.seed(7)
F = "/System/Library/Fonts/"
MONO = ImageFont.truetype(F + "Menlo.ttc", 26)
MONO_B = ImageFont.truetype(F + "Menlo.ttc", 30, index=1)
SANS = ImageFont.truetype(F + "Helvetica.ttc", 28)
SANS_B = ImageFont.truetype(F + "Helvetica.ttc", 40, index=1)
CJK = ImageFont.truetype(F + "Hiragino Sans GB.ttc", 28)
CJK_B = ImageFont.truetype(F + "Hiragino Sans GB.ttc", 36)

RECEIPT = {"type": "object", "properties": {
    "vendor": {"type": "string", "description": "Business name at the top"},
    "date": {"type": "string", "description": "Purchase date as YYYY-MM-DD"},
    "total": {"type": "number", "description": "The final total printed on the receipt"},
    "currency": {"type": "string", "description": "ISO 4217 code"}},
    "required": ["vendor", "date", "total", "currency"]}
cases = []


def page(lines: list[tuple[str, ImageFont.FreeTypeFont]], width: int = 640, pad: int = 40) -> Image.Image:
    height = pad * 2 + sum(f.size + 14 for _, f in lines)
    img = Image.new("RGB", (width, height), "white")
    d, y = ImageDraw.Draw(img), pad
    for text, font in lines:
        d.text((pad, y), text, fill="black", font=font)
        y += font.size + 14
    return img


def row(label: str, amount: str, width: int = 30) -> str:
    return f"{label}{amount.rjust(width - len(label))}"


def receipt(cid, vendor, date_printed, items, currency_sym, iso, date_iso, *, labels=("Subtotal", "Tax", "TOTAL"),
            tax_rate=0.08, printed_total=None, font=MONO, bold=MONO_B, photo=False, note=""):
    sub = round(sum(p for _, p in items), 2)
    tax = float(round(sub * tax_rate)) if iso == "JPY" else round(sub * tax_rate, 2)
    total = round(sub + tax, 2) if printed_total is None else printed_total
    fmt = (lambda v: f"{currency_sym}{v:,.0f}") if iso == "JPY" else (lambda v: f"{currency_sym}{v:,.2f}")
    lines = [(vendor, bold), (date_printed, font), ("-" * 30, font)]
    lines += [(row(n, fmt(p)), font) for n, p in items]
    lines += [("-" * 30, font), (row(labels[0], fmt(sub)), font), (row(labels[1], fmt(tax)), font),
              (row(labels[2], fmt(total)), bold)]
    img = page(lines)
    name = f"{cid}.png"
    if photo:
        img = img.rotate(4, expand=True, fillcolor=(214, 210, 200)).filter(ImageFilter.GaussianBlur(1.1))
        px = img.load()
        for _ in range(img.width * img.height // 12):
            x, y = random.randrange(img.width), random.randrange(img.height)
            v = random.randint(150, 255)
            px[x, y] = (v, v, v)
        name = f"{cid}.jpg"
        img.save(OUT / name, quality=35)
    else:
        img.save(OUT / name)
    cases.append({"id": cid, "file": name, "kind": "text", "schema": RECEIPT, "prompt": "Extract this receipt.",
                  "expect": {"vendor": vendor, "date": date_iso, "total": total, "currency": iso}, "note": note})


items = [("Oat latte", 5.25), ("Almond croissant", 4.50), ("Drip coffee", 3.10)]
receipt("receipt_cafe", "BLUE HERON CAFE", "10/14/2026 08:42", items, "$", "USD", "2026-10-14")
receipt("receipt_photo", "MAPLE ST HARDWARE", "09/30/2026 17:05",
        [("Wood screws 2in", 7.49), ("Hinge set", 12.99), ("Sandpaper 220", 5.25), ("Paint tray", 3.75)],
        "$", "USD", "2026-09-30", photo=True, note="rotated, blurred, noisy JPEG")
receipt("receipt_wrong_total", "CORNER MARKET", "10/02/2026 12:11",
        [("Apples 2lb", 4.38), ("Bread", 3.99), ("Milk 1gal", 4.29)], "$", "USD", "2026-10-02",
        printed_total=15.61, note="printed total is wrong (true sum 13.68); expect the printed value")
long_items = [(f"Item {i:02d} grocery", round(random.uniform(0.99, 14.99), 2)) for i in range(1, 29)]
receipt("receipt_long", "VALLEY FOODS", "10/11/2026 19:20", long_items, "$", "USD", "2026-10-11",
        note="28 line items, tall image")
receipt("receipt_german", "BÄCKEREI SONNENSCHEIN", "14.10.2026 07:55",
        [("Brezel", 1.20), ("Roggenbrot", 4.80), ("Kaffee groß", 3.40)], "€", "EUR", "2026-10-14",
        labels=("Zwischensumme", "MwSt 7%", "SUMME"), tax_rate=0.07, note="non-English")
receipt("receipt_spanish", "FERRETERÍA LA PALOMA", "03/10/2026 11:30",
        [("Tornillos", 3.95), ("Cinta métrica", 8.50), ("Pegamento", 4.25)], "€", "EUR", "2026-10-03",
        labels=("Subtotal", "IVA 21%", "TOTAL"), tax_rate=0.21, note="non-English, day-first date")
receipt("receipt_japanese", "さくら書店", "2026年10月12日 15:04",
        [("文庫本", 880.0), ("ノート", 330.0), ("ボールペン", 165.0)], "¥", "JPY", "2026-10-12",
        labels=("小計", "消費税", "合計"), tax_rate=0.10, font=CJK, bold=CJK_B, note="non-English, CJK")

page([("INVOICE", SANS_B), ("Harbor Light Design LLC", SANS), ("Invoice #: HLD-20417", SANS),
      ("Issued: October 1, 2026", SANS), ("Due: October 31, 2026", SANS), ("", SANS),
      ("Brand refresh — phase 2          $3,200.00", SANS), ("Revisions (4 h @ $95)               $380.00", SANS),
      ("", SANS), ("Amount due: $3,580.00", SANS_B)], width=760).save(OUT / "invoice.png")
cases.append({"id": "invoice", "file": "invoice.png", "kind": "text", "prompt": "Extract this invoice.",
              "schema": {"type": "object", "properties": {
                  "vendor": {"type": "string"}, "invoice_number": {"type": "string"},
                  "due_date": {"type": "string", "description": "YYYY-MM-DD"}, "amount_due": {"type": "number"}},
                  "required": ["vendor", "invoice_number", "due_date", "amount_due"]},
              "expect": {"vendor": "Harbor Light Design LLC", "invoice_number": "HLD-20417",
                         "due_date": "2026-10-31", "amount_due": 3580.00}, "note": ""})

page([("Form 1099-INT   Interest Income   2025", SANS_B), ("PAYER: Granite Federal Credit Union", SANS),
      ("RECIPIENT: Jordan A. Ellis", SANS), ("Recipient TIN: ***-**-4821", SANS), ("", SANS),
      ("1  Interest income                         $412.37", SANS),
      ("4  Federal income tax withheld               $0.00", SANS),
      ("8  Tax-exempt interest                          $0.00", SANS)], width=820).save(OUT / "tax_1099.png")
cases.append({"id": "tax_1099", "file": "tax_1099.png", "kind": "text", "prompt": "Extract this tax form.",
              "schema": {"type": "object", "properties": {
                  "payer": {"type": "string"}, "tax_year": {"type": "integer"},
                  "interest_income": {"type": "number"}, "federal_tax_withheld": {"type": "number"}},
                  "required": ["payer", "tax_year", "interest_income", "federal_tax_withheld"]},
              "expect": {"payer": "Granite Federal Credit Union", "tax_year": 2025,
                         "interest_income": 412.37, "federal_tax_withheld": 0.00}, "note": "tax note fm refused before"})

form = Image.new("RGB", (900, 420), (245, 246, 248))
d = ImageDraw.Draw(form)
d.text((40, 30), "Account settings", fill="black", font=SANS_B)
for i, (label, value) in enumerate([("Full name", "Priya Natarajan"), ("Email", "priya.n@lumen-labs.io"),
                                    ("Account ID", "ACC-7Q42-PX9")]):
    y = 110 + i * 95
    d.text((40, y), label, fill=(90, 90, 90), font=SANS)
    d.rectangle((300, y - 8, 860, y + 44), outline=(170, 170, 170), fill="white")
    d.text((316, y), value, fill="black", font=SANS)
form.save(OUT / "form_screenshot.png")
cases.append({"id": "form_screenshot", "file": "form_screenshot.png", "kind": "text", "prompt": "Read the form fields.",
              "schema": {"type": "object", "properties": {
                  "full_name": {"type": "string"}, "email": {"type": "string"}, "account_id": {"type": "string"}},
                  "required": ["full_name", "email", "account_id"]},
              "expect": {"full_name": "Priya Natarajan", "email": "priya.n@lumen-labs.io", "account_id": "ACC-7Q42-PX9"},
              "note": "UI screenshot"})

months = [("Jan", 42), ("Feb", 55), ("Mar", 38), ("Apr", 61), ("May", 74), ("Jun", 59)]
chart = Image.new("RGB", (800, 500), "white")
d = ImageDraw.Draw(chart)
d.text((40, 20), "Monthly signups", fill="black", font=SANS_B)
d.line((80, 440, 760, 440), fill="black", width=2)
for i, (m, v) in enumerate(months):
    x = 110 + i * 105
    d.rectangle((x, 440 - v * 4.5, x + 60, 440), fill=(70, 120, 200))
    d.text((x + 8, 450), m, fill="black", font=SANS)
chart.save(OUT / "chart.png")
cases.append({"id": "chart", "file": "chart.png", "kind": "pixels",
              "prompt": "Which month has the tallest bar? Give the month label exactly as written.",
              "schema": {"type": "object", "properties": {"month": {"type": "string"}}, "required": ["month"]},
              "expect": {"month": "May"}, "note": "no value labels; meaning in pixels"})

payload = "WIFI:T:WPA;S:HeronNet-5G;P:t7Kq-92xz!m;;"
qrcode.make(payload, box_size=10, border=4).save(OUT / "qr_wifi.png")
cases.append({"id": "qr_wifi", "file": "qr_wifi.png", "kind": "code", "prompt": "Print ONLY the exact payload.",
              "schema": None, "expect": {"payload": payload}, "note": "no text in image"})

(OUT / "truth.json").write_text(json.dumps(cases, indent=2, ensure_ascii=False))
print(f"{len(cases)} cases → {OUT}")
