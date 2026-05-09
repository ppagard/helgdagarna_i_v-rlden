#!/usr/bin/env python3
"""Generera en PDF med helgdagar för ett givet land och år."""

import json
import sys
import urllib.request
from datetime import datetime
from fpdf import FPDF

API = "https://date.nager.at/api/v3"

# ── Beskrivningar ──
DESCRIPTIONS = {
    "Nyårsdagen": (
        "Nyårsdagen inleder det nya året och är en av de äldsta helgdagarna "
        "i den kristna kalendern. Traditionellt firas dagen med nyårslöften, "
        "fyrverkerier från natten innan och årets första nyårskonsert "
        "i Wien. I Sverige är dagen en allmän helgdag sedan 1785."
    ),
    "Trettondedag jul": (
        "Trettondedagen, eller Epifania, firar de tre vise männens ankomst "
        "till Betlehem för att hylla Jesusbarnet. Dagen kallas också "
        "'Trettondagen' och markerar slutet på julsäsongen. "
        "I Sverige är dagen allmän helgdag sedan 1785."
    ),
    "Långfredagen": (
        "Långfredagen högtidlighåller Jesu korsfästelse och död på Golgata. "
        "Det är en stilla helgdag inom kristendomen och infaller på "
        "fredagen före påskdagen. Långfredagen är en rörlig helgdag "
        "som bestäms utifrån påskens datum."
    ),
    "Påskdagen": (
        "Påskdagen är den viktigaste helgdagen inom kristendomen och "
        "firar Jesu uppståndelse från de döda. Dagen infaller första "
        "söndagen efter första fullmånen efter vårdagjämningen "
        "(mars/april). Påsken är därmed en rörlig högtid."
    ),
    "Annandag påsk": (
        "Annandag påsk är dagen efter påskdagen och fortsätter firandet "
        "av Jesu uppståndelse. I Sverige har dagen gamla traditioner och "
        "har varit allmän helgdag sedan 1785. Många passar på att vara "
        "utomhus och njuta av vårvädret."
    ),
    "Första maj": (
        "Första maj är arbetarrörelsens internationella högtidsdag och "
        "firas med demonstrationer och tal över hela världen. I Sverige "
        "blev dagen allmän helgdag 1939. Dagen har sitt ursprung i "
        "1889 års internationella arbetarkongress i Paris."
    ),
    "Kristi himmelsfärdsdag": (
        "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter "
        "påsk. Högtiden är en av de tidigaste kristna helgdagarna och "
        "har firats sedan 300-talet. Dagen infaller alltid på en "
        "torsdag och är en rörlig helgdag."
    ),
    "Pingstdagen": (
        "Pingstdagen firar den Helige Andes utgjutelse över apostlarna "
        "50 dagar efter påsk, vilket kallas 'kyrkans födelsedag'. "
        "Dagen markerar början på den kristna missionen och är en "
        "rörlig helgdag. Ordet 'pingst' kommer från grekiskans "
        "'pentekoste' som betyder femtionde."
    ),
    "Sveriges nationaldag": (
        "Sveriges nationaldag firas den 6 juni till minne av två "
        "historiska händelser: Gustav Vasas kröning 1523 och "
        "1809 års regeringsform. Dagen blev allmän helgdag först "
        "2005 och firas med flaggning, kungliga ceremonier och "
        "medborgarskapsceremonier runt om i landet."
    ),
    "Midsommarafton": (
        "Midsommarafton är en av de mest älskade svenska högtiderna "
        "och firas på fredagen mellan den 19 och 25 juni. Traditioner "
        "inkluderar midsommarstång (majstång), folkdans, sillunch "
        "med nypotatis och jordgubbar. Trots att dagen inte är "
        "officiellt allmän helgdag är den starkt förankrad i "
        "svensk kultur."
    ),
    "Midsommardagen": (
        "Midsommardagen infaller på lördagen mellan den 20 och 26 juni."
        " Den är den kristna högtiden för Johannes Döparens födelse "
        "och har varit allmän helgdag i Sverige sedan 1953. Dagen "
        "avslutar midsommarhelgen."
    ),
    "Alla helgons dag": (
        "Alla helgons dag är en kristen helgdag till minne av alla "
        "helgon och martyrer. I Sverige infaller den på lördagen "
        "mellan den 31 oktober och 6 november. Traditionellt tänder "
        "man ljus på gravarna, vilket skapar en stämningsfull syn "
        "över kyrkogårdarna i novembermörkret."
    ),
    "Julafton": (
        "Julafton är den mest centrala dagen i svenskt julfirande. "
        "De flesta firar med julmat (skinka, köttbullar, sill, "
        "lutfisk, risgrynsgröt), julklappar och Kalle Anka på TV "
        "klockan 15. Julafton är inte officiellt allmän helgdag "
        "men de flesta arbetsgivare ger ledigt."
    ),
    "Juldagen": (
        "Juldagen firar Jesu Kristi födelse i Betlehem och är en "
        "av de största kristna högtiderna. Dagen har firats sedan "
        "300-talet och är i Sverige en stilla helgdag med "
        "julotta (gudstjänst tidigt på morgonen) och "
        "familjesammankomster."
    ),
    "Annandag jul": (
        "Annandag jul är dagen efter juldagen och är allmän helgdag "
        "i Sverige. Traditionellt sett var det en dag för jakt, "
        "slädturer och idrottsevenemang. Idag används dagen ofta "
        "för att umgås med familj och vänner eller för att "
        "utnyttja mellandagsrean."
    ),
    "Nyårsafton": (
        "Nyårsafton firas den 31 december, årets sista dag. "
        "Kvällen inleds ofta med en festlig middag och avslutas "
        "med fyrverkerier vid midnatt. Dagen är inte officiellt "
        "en allmän helgdag men i praktiken har de flesta ledigt "
        "för att fira det nya årets ankomst."
    ),
}

DAYS_SV = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]

MONTHS_SV = [
    "januari",
    "februari",
    "mars",
    "april",
    "maj",
    "juni",
    "juli",
    "augusti",
    "september",
    "oktober",
    "november",
    "december",
]

TYPE_LABELS = {
    "Public": "Allmän helgdag",
    "Bank": "Bankdag",
    "Optional": "Frivillig",
    "School": "Skola",
    "Observance": "Kulturell högtid",
}

TYPE_RANK = {"Public": 5, "Bank": 4, "Optional": 3, "School": 2, "Observance": 1}


def best_type(holiday):
    types = holiday.get("types", [])
    return max((TYPE_RANK.get(t, 0) for t in types), default=0)


def fetch_holidays(country_code, year):
    url = f"{API}/AvailableCountries"
    req = urllib.request.Request(url, headers={"User-Agent": "helgdagar/1.0"})
    countries = json.loads(urllib.request.urlopen(req).read())
    country_name = next(
        (c["name"] for c in countries if c["countryCode"] == country_code),
        country_code,
    )

    url = f"{API}/PublicHolidays/{year}/{country_code}"
    req = urllib.request.Request(url, headers={"User-Agent": "helgdagar/1.0"})
    data = json.loads(urllib.request.urlopen(req).read())

    seen = {}
    for h in data:
        r = best_type(h)
        if r > seen.get(h["date"], {}).get("_rank", 0):
            h["_rank"] = r
            seen[h["date"]] = h

    holidays = sorted(seen.values(), key=lambda h: h["date"])
    return country_name, holidays


class HolidayPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 8)
            self.set_text_color(140, 140, 140)
            self.cell(0, 8, f"Helgdagar i {self._country} {self._year}", align="R")
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Sida {self.page_no()}", align="C")


def generate_pdf(country_code, year, output_path, descriptions=None, country_name=None):
    if descriptions is None:
        descriptions = DESCRIPTIONS

    if country_name is None:
        country_name, raw = fetch_holidays(country_code, year)
    else:
        _, raw = fetch_holidays(country_code, year)

    pdf = HolidayPDF()
    pdf._country = country_name
    pdf._year = year
    pdf.set_auto_page_break(auto=True, margin=25)

    pdf.add_font("Arial", "", "/System/Library/Fonts/Supplemental/Arial.ttf")
    pdf.add_font("Arial", "B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    pdf.add_font("Arial", "I", "/System/Library/Fonts/Supplemental/Arial Italic.ttf")
    pdf.add_font(
        "Arial", "BI", "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"
    )

    # ── Omslag ──
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_draw_color(99, 102, 241)
    pdf.set_line_width(0.6)
    pdf.line(25, 60, 185, 60)

    pdf.set_y(70)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(226, 232, 240)
    pdf.cell(0, 14, f"Helgdagar i {country_name}", align="C")
    pdf.ln(16)
    pdf.set_font("Arial", "", 16)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, str(year), align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "I", 11)
    pdf.cell(0, 10, "Allmänna helgdagar, högtider och märkesdagar", align="C")

    pdf.set_draw_color(99, 102, 241)
    pdf.line(25, 130, 185, 130)

    pdf.set_y(145)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 7, f"{len(raw)} helgdagar", align="C")
    pdf.ln(7)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 7, f"Genererad: {datetime.now().strftime('%B %Y').lower()}", align="C")

    # ── Innehållsförteckning ──
    pdf.add_page()
    pdf.set_fill_color(248, 250, 252)
    pdf.set_text_color(15, 23, 42)

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 14, "Innehåll", align="L")
    pdf.ln(12)

    pdf.set_draw_color(99, 102, 241)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    for i, h in enumerate(raw, 1):
        d = datetime.strptime(h["date"], "%Y-%m-%d")
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(12, 9, f"{i}.", align="R")
        pdf.set_text_color(99, 102, 241)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(60, 9, h["localName"])
        pdf.set_text_color(100, 116, 139)
        pdf.set_font("Arial", "", 10)
        pdf.cell(30, 9, f"{d.day}/{d.month}", align="C")
        pdf.cell(25, 9, DAYS_SV[d.weekday()], align="C")
        pdf.ln(9)

    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Arial", "I", 8)
    pdf.ln(12)
    pdf.multi_cell(
        0,
        5,
        "Not: Rörliga helgdagar (påsk, pingst, Kristi himmelsfärdsdag, Långfredagen, "
        "Alla helgons dag, Midsommardagen) är beräknade utifrån det aktuella årets datum. "
        "Midsommarafton, Julafton och Nyårsafton har en särskild status – de är inte "
        "officiellt allmänna helgdagar men ändå välfirade dagar då nästan alla har ledigt.",
    )

    # ── En sida per helgdag ──
    for idx, h in enumerate(raw, 1):
        pdf.add_page()
        d = datetime.strptime(h["date"], "%Y-%m-%d")
        namn = h["localName"]
        desc = descriptions.get(namn, "")
        t = h.get("types", [""])[0]
        typ_label = TYPE_LABELS.get(t, t)

        # Vänster färgstapel
        pdf.set_fill_color(99, 102, 241)
        pdf.rect(5, 10, 3, 270, "F")

        pdf.set_font("Arial", "B", 36)
        pdf.set_text_color(99, 102, 241)
        pdf.set_xy(18, 14)
        pdf.cell(20, 16, str(idx))

        pdf.set_xy(42, 14)
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 16, namn)

        pdf.set_xy(42, 32)
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(
            0,
            8,
            f"{DAYS_SV[d.weekday()]} {d.day} {MONTHS_SV[d.month - 1].capitalize()} {d.year}",
        )

        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.3)
        pdf.line(18, 48, 192, 48)

        pdf.set_xy(18, 55)
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 8, typ_label)

        pdf.set_xy(18, 72)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(172, 7, desc)

        pdf.set_xy(18, 130)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 7, "Detaljer")

        pdf.set_draw_color(226, 232, 240)
        pdf.line(18, 137, 192, 137)

        y = 144
        pdf.set_xy(18, y)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 7, f"Datum: {d.year}-{d.month:02d}-{d.day:02d}")

        pdf.set_xy(18, y + 8)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 7, f"Veckodag: {DAYS_SV[d.weekday()]}")

        if h.get("global", True):
            pdf.set_xy(18, y + 16)
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(0, 7, "Nationell helgdag")

        if h.get("counties"):
            pdf.set_xy(18, y + 24)
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(0, 7, f"Regioner: {', '.join(h['counties'])}")

    # ── Slutsida ──
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_y(120)
    pdf.set_font("Arial", "I", 14)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, "Genererad med data från Nager.Date API", align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "https://date.nager.at", align="C")
    pdf.ln(16)
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, f"Helgdagar i {country_name} – {year}", align="C")

    pdf.output(output_path)
    return pdf.page_no()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generera PDF med helgdagar")
    parser.add_argument(
        "country", nargs="?", default="SE", help="Landskod (t.ex. SE, NO, DK, FI)"
    )
    parser.add_argument(
        "year", nargs="?", type=int, default=2026, help="År (1900–2100)"
    )
    parser.add_argument("-o", "--output", help="Sökväg för PDF-fil")
    args = parser.parse_args()

    if args.output:
        out = args.output
    else:
        out = f"helgdagar_{args.country}_{args.year}.pdf"

    try:
        pages = generate_pdf(args.country, args.year, out)
        print(f"✅ PDF skapad: {out} ({pages} sidor)")
    except Exception as e:
        print(f"❌ Fel: {e}", file=sys.stderr)
        sys.exit(1)
