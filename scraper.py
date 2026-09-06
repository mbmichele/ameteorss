#!/usr/bin/env python3
"""
Scraper PRETEMP -> RSS
======================

Legge l'archivio previsioni pubblico di https://www.pretemp.it/archivio/<anno>
e genera un feed RSS 2.0 con le previsioni/tendenze piu' recenti.

Note tecniche:
- PRETEMP non pubblica un feed RSS ufficiale, quindi questo script fa scraping
  dell'HTML pubblico. Se il sito cambia struttura, le funzioni di parsing
  (parse_archive_listing / parse_forecast_detail) vanno aggiornate.
- Per essere piu' resiliente a piccoli cambi di markup, il parsing si basa
  soprattutto su pattern di TESTO visibile nella pagina (es. "Previsore:",
  "Aggiornato il", "Pericolosita'") piuttosto che su classi CSS specifiche.
- Rispetta il sito: 1 richiesta alla volta, con pausa tra le richieste e uno
  User-Agent identificativo.
"""

import re
import sys
import time
import argparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urljoin
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.pretemp.it"
ARCHIVE_URL = BASE_URL + "/archivio/{year}"
HEADERS = {
    "User-Agent": "pretemp-rss-bot/1.0 (+https://github.com/; uso non commerciale, progetto civico)"
}
REQUEST_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT = 20
MAX_ITEMS = 50  # limite massimo di elementi nel feed
ROME_TZ = ZoneInfo("Europe/Rome")

MESI_ITALIANI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


def parse_italian_datetime(text: str):
    """Converte una stringa tipo '5 settembre 2026, 14:39' in un datetime
    consapevole del fuso orario (Europe/Rome). Ritorna None se non riesce."""
    if not text:
        return None
    m = re.search(
        r"(\d{1,2})\s+(\w+)\s+(\d{4})(?:,?\s*(\d{1,2}):(\d{2}))?",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    day, month_name, year, hour, minute = m.groups()
    month = MESI_ITALIANI.get(month_name.lower())
    if not month:
        return None
    hour = int(hour) if hour else 0
    minute = int(minute) if minute else 0
    try:
        return datetime(int(year), month, int(day), hour, minute, tzinfo=ROME_TZ)
    except ValueError:
        return None


def to_rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_archive_listing(year: int, page: int = 1):
    """Ritorna una lista di dict {id, url, date_short, tipo, pericolosita, previsori}
    leggendo la pagina archivio di un dato anno/pagina."""
    url = ARCHIVE_URL.format(year=year)
    if page > 1:
        url += f"?page={page}"
    soup = get_soup(url)

    items = []
    # Ogni previsione e' un link <a href="/previsioni/ID">...</a> il cui testo
    # contiene data, tipo (Previsione/Tendenza), pericolosita' e previsori.
    for a in soup.find_all("a", href=re.compile(r"^/previsioni/\d+$")):
        href = a.get("href")
        forecast_id = re.search(r"\d+", href).group()
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            continue
        items.append({
            "id": forecast_id,
            "url": urljoin(BASE_URL, href),
            "raw_text": text,
        })

    # Rimuove duplicati mantenendo l'ordine (lo stesso link puo' comparire piu' volte)
    seen = set()
    unique_items = []
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        unique_items.append(it)
    return unique_items


def get_total_pages(year: int) -> int:
    """Legge 'Pagina X di Y' dalla prima pagina dell'archivio per un anno."""
    soup = get_soup(ARCHIVE_URL.format(year=year))
    text = soup.get_text(" ", strip=True)
    m = re.search(r"Pagina\s+\d+\s+di\s+(\d+)", text)
    if m:
        return int(m.group(1))
    return 1


def parse_forecast_detail(url: str) -> dict:
    """Estrae i dettagli da una pagina /previsioni/<id>."""
    soup = get_soup(url)
    text = soup.get_text("\n", strip=True)

    # Titolo: "Previsione per il ..." oppure "Tendenza per ..."
    title_match = re.search(r"(Previsione|Tendenza)[^\n]*", text)
    title = title_match.group(0).strip() if title_match else "Previsione PRETEMP"

    # Pericolosita': "Nessun pericolo" oppure "Pericolosita' N"
    danger_match = re.search(r"(Nessun pericolo|Pericolosit[aà]\s*\d+)", text)
    danger = danger_match.group(1).strip() if danger_match else None

    # Previsore/i
    forecaster_match = re.search(r"Previsor[ei]:\s*([^\n]+)", text)
    forecaster = forecaster_match.group(1).strip() if forecaster_match else None

    # Data di aggiornamento
    updated_match = re.search(r"Aggiornato il\s*([^\n]+)", text)
    updated = updated_match.group(1).strip() if updated_match else None
    pub_date = parse_italian_datetime(updated)

    # Testo breve: tra "TESTO BREVE" e il disclaimer standard "PRETEMP e' un gruppo di lavoro"
    body = ""
    if "TESTO BREVE" in text:
        after = text.split("TESTO BREVE", 1)[1]
        cut_markers = ["PRETEMP è un gruppo di lavoro", "PRETEMP e' un gruppo di lavoro"]
        for marker in cut_markers:
            if marker in after:
                after = after.split(marker, 1)[0]
                break
        body = after.strip()

    # Immagine mappa (se presente)
    img_url = None
    img_tag = soup.find("img", src=re.compile(r"active_storage|\.png|\.jpg"))
    if img_tag and img_tag.get("src"):
        img_url = urljoin(BASE_URL, img_tag["src"])

    return {
        "title": title,
        "danger": danger,
        "forecaster": forecaster,
        "updated": updated,
        "pub_date": pub_date,
        "body": body,
        "image": img_url,
    }


def build_rss(entries: list, feed_title: str, feed_link: str, feed_description: str) -> str:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

    items_xml = []
    for e in entries:
        title = escape(e["title"])
        link = escape(e["url"])
        guid = escape(e["url"])

        desc_parts = []
        if e.get("danger"):
            desc_parts.append(f"Pericolosità: {e['danger']}")
        if e.get("forecaster"):
            desc_parts.append(f"Previsore/i: {e['forecaster']}")
        if e.get("updated"):
            desc_parts.append(f"Aggiornato il: {e['updated']}")
        if e.get("body"):
            desc_parts.append(e["body"])
        description = escape("\n\n".join(desc_parts))

        if e.get("image"):
            description += "&lt;br/&gt;" + escape(f'<img src="{e["image"]}" />')

        enclosure_tag = ""
        if e.get("image"):
            img_ext = e["image"].rsplit(".", 1)[-1].lower()
            img_type = "image/png" if img_ext == "png" else "image/jpeg" if img_ext in ("jpg", "jpeg") else "image/*"
            enclosure_tag = f'\n      <enclosure url="{escape(e["image"])}" type="{img_type}" length="0"/>'

        pub_date_tag = ""
        if e.get("pub_date"):
            pub_date_tag = f"\n      <pubDate>{to_rfc822(e['pub_date'])}</pubDate>"

        items_xml.append(f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{guid}</guid>
      <description>{description}</description>{enclosure_tag}{pub_date_tag}
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(feed_title)}</title>
    <link>{escape(feed_link)}</link>
    <description>{escape(feed_description)}</description>
    <language>it-IT</language>
    <lastBuildDate>{now}</lastBuildDate>
    <generator>pretemp-rss (scraper non ufficiale)</generator>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
    return rss


def main():
    parser = argparse.ArgumentParser(description="Genera un feed RSS dall'archivio PRETEMP")
    parser.add_argument("--year", type=int, default=datetime.now().year,
                         help="Anno dell'archivio da leggere (default: anno corrente)")
    parser.add_argument("--limit", type=int, default=MAX_ITEMS,
                         help=f"Numero massimo di previsioni da includere nel feed (max {MAX_ITEMS})")
    parser.add_argument("--output", default="docs/rss.xml",
                         help="Percorso del file RSS da scrivere")
    args = parser.parse_args()
    args.limit = min(args.limit, MAX_ITEMS)

    print(f"Leggo archivio anno {args.year}...", file=sys.stderr)
    listing = []
    year = args.year
    page = 1
    while len(listing) < args.limit:
        time.sleep(REQUEST_DELAY_SECONDS if page > 1 else 0)
        page_items = parse_archive_listing(year, page=page)
        if not page_items:
            if page == 1 and year > 2015:
                # Anno senza previsioni (es. inizio gennaio): ripiega sull'anno precedente
                print(f"Nessuna previsione per il {year}, provo il {year - 1}...", file=sys.stderr)
                year -= 1
                page = 1
                continue
            break  # fine delle pagine disponibili
        listing.extend(page_items)
        page += 1

    listing = listing[: args.limit]

    entries = []
    for item in listing:
        time.sleep(REQUEST_DELAY_SECONDS)
        print(f"Leggo dettaglio {item['url']}...", file=sys.stderr)
        try:
            detail = parse_forecast_detail(item["url"])
        except requests.RequestException as exc:
            print(f"  Errore nel leggere {item['url']}: {exc}", file=sys.stderr)
            continue
        entries.append({
            "url": item["url"],
            **detail,
        })

    # Ordina per data di pubblicazione decrescente: garantisce che il primo
    # elemento del feed sia sempre l'ultima previsione pubblicata, indipendentemente
    # dall'ordine in cui compaiono nell'archivio. Gli elementi senza data valida
    # (parsing fallito) finiscono in fondo. Poi si applica di nuovo il tetto
    # massimo, scartando eventuali elementi piu' vecchi oltre il limite.
    oldest_possible = datetime.min.replace(tzinfo=ROME_TZ)
    entries.sort(key=lambda e: e.get("pub_date") or oldest_possible, reverse=True)
    entries = entries[:MAX_ITEMS]

    rss_xml = build_rss(
        entries,
        feed_title="PRETEMP – Previsioni temporali (feed non ufficiale)",
        feed_link=BASE_URL,
        feed_description=(
            "Feed RSS non ufficiale generato tramite scraping dell'archivio "
            "pubblico di pretemp.it. PRETEMP non emette allerte, ma previsioni "
            "probabilistiche sperimentali. Per l'allertamento ufficiale fare "
            "sempre riferimento al Dipartimento di Protezione Civile."
        ),
    )

    import os
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"Feed scritto in {args.output} con {len(entries)} elementi.", file=sys.stderr)


if __name__ == "__main__":
    main()
