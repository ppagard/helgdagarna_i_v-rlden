#!/usr/bin/env python3
"""Generera en PDF med helgdagar för ett givet land och år."""

import json
import re
import sys
import urllib.request
from datetime import datetime, date, timedelta
from fpdf import FPDF

API = "https://date.nager.at/api/v3"
LANG = "sv"

# ── Hjälpfunktioner ──
DAYS = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
MONTHS = [
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
    return max((TYPE_RANK.get(t, 0) for t in holiday.get("types", [])), default=0)


def fetch_holidays(country_code, year):
    url = f"{API}/AvailableCountries"
    req = urllib.request.Request(url, headers={"User-Agent": "helgdagar/1.0"})
    countries = json.loads(urllib.request.urlopen(req).read())
    country_name = next(
        (c["name"] for c in countries if c["countryCode"] == country_code), country_code
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
    return country_name, sorted(seen.values(), key=lambda h: h["date"])


def compute_easter(year):
    """Beräkna påskdagen med Gauss algoritm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - (b - (b + 8) // 25 + 1) // 3 + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - c % 4) % 7
    month = 3 + (d + e + 114) // 31
    day = ((d + e + 114) % 31) + 1
    return date(year, month, day)


# ── Beskrivningssystem ──
def _desc(*lines):
    return " ".join(lines)


COUNTRY_SPECIFIC = {
    "SE": {
        "Nyårsdagen": _desc(
            "Nyårsdagen inleder det nya året och är en av de äldsta helgdagarna i den kristna kalendern.",
            "Traditionellt firas dagen med nyårslöften, fyrverkerier från natten innan och",
            "årets första nyårskonsert i Wien. I Sverige är dagen en allmän helgdag sedan 1785.",
        ),
        "Trettondedag jul": _desc(
            "Trettondedagen, eller Epifania, firar de tre vise männens ankomst till Betlehem",
            "för att hylla Jesusbarnet. Dagen markerar slutet på julsäsongen och är allmän helgdag sedan 1785.",
        ),
        "Långfredagen": _desc(
            "Långfredagen högtidlighåller Jesu korsfästelse och död på Golgata. Det är en stilla",
            "helgdag inom kristendomen som infaller på fredagen före påskdagen.",
        ),
        "Påskdagen": _desc(
            "Påskdagen är den viktigaste helgdagen inom kristendomen och firar Jesu uppståndelse",
            "från de döda. Dagen infaller första söndagen efter första fullmånen efter vårdagjämningen.",
        ),
        "Annandag påsk": _desc(
            "Annandag påsk är dagen efter påskdagen och fortsätter firandet av Jesu uppståndelse.",
            "I Sverige har dagen varit allmän helgdag sedan 1785.",
        ),
        "Första maj": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag och firas med",
            "demonstrationer och tal över hela världen. I Sverige blev dagen allmän helgdag 1939.",
        ),
        "Kristi himmelsfärdsdag": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk. Högtiden",
            "är en av de tidigaste kristna helgdagarna och infaller alltid på en torsdag.",
        ),
        "Pingstdagen": _desc(
            "Pingstdagen firar den Helige Andes utgjutelse över apostlarna 50 dagar efter påsk,",
            "vilket kallas 'kyrkans födelsedag'. Ordet 'pingst' kommer från grekiskans 'pentekoste'.",
        ),
        "Sveriges nationaldag": _desc(
            "Sveriges nationaldag firas den 6 juni till minne av Gustav Vasas kröning 1523 och",
            "1809 års regeringsform. Dagen blev allmän helgdag först 2005.",
        ),
        "Midsommarafton": _desc(
            "Midsommarafton är en av de mest älskade svenska högtiderna och firas på fredagen",
            "mellan den 19 och 25 juni. Traditioner inkluderar midsommarstång, folkdans, sill och nypotatis.",
        ),
        "Midsommardagen": _desc(
            "Midsommardagen infaller på lördagen mellan den 20 och 26 juni och är den kristna",
            "högtiden för Johannes Döparens födelse. Allmän helgdag i Sverige sedan 1953.",
        ),
        "Alla helgons dag": _desc(
            "Alla helgons dag är en kristen helgdag till minne av alla helgon och martyrer.",
            "I Sverige tänder man traditionellt ljus på gravarna.",
        ),
        "Julafton": _desc(
            "Julafton är den mest centrala dagen i svenskt julfirande med julmat, julklappar",
            "och Kalle Anka på TV. Officiellt inte allmän helgdag men i praktiken ledigt för de flesta.",
        ),
        "Juldagen": _desc(
            "Juldagen firar Jesu Kristi födelse i Betlehem och är en av de största kristna",
            "högtiderna. I Sverige firas med julotta och familjesammankomster.",
        ),
        "Annandag jul": _desc(
            "Annandag jul är dagen efter juldagen och allmän helgdag i Sverige. Traditionellt",
            "en dag för jakt och idrott, idag ofta för mellandagsrea och familjeumgänge.",
        ),
        "Nyårsafton": _desc(
            "Nyårsafton firas den 31 december, årets sista dag. Kvällen inleds med festmiddag",
            "och avslutas med fyrverkerier vid midnatt.",
        ),
    },
    "NO": {
        "Første nyttårsdag": _desc(
            "Nyårsdagen inleder det nya året och är en av de äldsta helgdagarna i den kristna",
            "kalendern. I Norge är dagen allmän helgdag.",
        ),
        "Skjærtorsdag": _desc(
            "Skärtorsdagen infaller på torsdagen före påsk och högtidlighåller Jesus sista måltid",
            "med lärjungarna. Dagen är en rörlig helgdag som inleder påskhelgen i Norge.",
        ),
        "Langfredag": _desc(
            "Långfredagen högtidlighåller Jesu korsfästelse och död på Golgata. Det är en stilla",
            "helgdag inom kristendomen som infaller på fredagen före påskdagen.",
        ),
        "Første påskedag": _desc(
            "Påskdagen är den viktigaste helgdagen inom kristendomen och firar Jesu uppståndelse",
            "från de döda. I Norge firas påsken ofta med skidåkning i fjällen.",
        ),
        "Andre påskedag": _desc(
            "Andra påskdagen är dagen efter påskdagen och fortsätter firandet av Jesu uppståndelse.",
            "I Norge är dagen en del av den långa påskhelgen.",
        ),
        "Første mai": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag. I Norge har dagen",
            "varit allmän helgdag sedan 1947.",
        ),
        "Kristi himmelfartsdag": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk. Högtiden",
            "har firats sedan 300-talet och infaller alltid på en torsdag.",
        ),
        "Syttende mai": _desc(
            "Syttende mai är Norges nationaldag som firar undertecknandet av Norges grundlag",
            "i Eidsvoll den 17 maj 1814. Dagen firas med barnens tåg, flaggning och fest över hela Norge.",
        ),
        "Første pinsedag": _desc(
            "Pingstdagen firar den Helige Andes utgjutelse över apostlarna 50 dagar efter påsk.",
            "Ordet 'pingst' kommer från grekiskans 'pentekoste' som betyder femtionde.",
        ),
        "Andre pinsedag": _desc(
            "Andra pingstdagen är dagen efter pingstdagen och fortsätter firandet av den Helige",
            "Andes utgjutelse.",
        ),
        "Første juledag": _desc(
            "Juldagen firar Jesu Kristi födelse i Betlehem. I Norge firas med julotta och",
            "traditionellt julbord med pinnekjøtt eller ribbe.",
        ),
        "Andre juledag": _desc(
            "Andra juldagen är dagen efter juldagen och är allmän helgdag i Norge. Dagen",
            "används traditionellt för vänbesök och festligheter.",
        ),
    },
    "DK": {
        "Nytårsdag": _desc(
            "Nyårsdagen inleder det nya året med festligheter, fyrverkerier och goda föresatser."
        ),
        "Skærtorsdag": _desc(
            "Skärtorsdagen infaller på torsdagen före påsk och högtidlighåller den sista nattvarden."
        ),
        "Langfredag": _desc(
            "Långfredagen högtidlighåller Jesu korsfästelse. Det är en stilla helgdag i Danmark."
        ),
        "Påskedag": _desc(
            "Påskdagen firar Jesu uppståndelse och är den viktigaste kristna helgdagen."
        ),
        "2. Påskedag": _desc(
            "Andra påskdagen fortsätter firandet av Jesu uppståndelse."
        ),
        "Kristi Himmelfartsdag": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk."
        ),
        "Banklukkedag": _desc(
            "Banklukkedag är en dansk helgdag då bankerna har stängt."
        ),
        "Pinsedag": _desc(
            "Pingstdagen firar den Helige Andes utgjutelse 50 dagar efter påsk."
        ),
        "2. Pinsedag": _desc("Andra pingstdagen fortsätter pingstfirandet."),
        "Grundlovsdag": _desc(
            "Grundlovsdagen den 5 juni firar Danmarks grundlag från 1849 och den reviderade grundlagen från 1953."
        ),
        "Juleaftensdag": _desc(
            "Julafton firas med familjemiddag, dans kring julgranen och julklappar."
        ),
        "Juledag / 1. juledag": _desc(
            "Juldagen firar Jesu Kristi födelse med gudstjänst och familjesammankomst."
        ),
        "2. juledag": _desc(
            "Andra juldagen är dagen efter juldagen och allmän helgdag i Danmark."
        ),
        "Nytårsaftensdag": _desc(
            "Nyårsafton firas med festmiddag och fyrverkerier vid midnatt."
        ),
    },
    "FI": {
        "Uudenvuodenpäivä": _desc("Nyårsdagen inleder det nya året."),
        "Loppiainen": _desc(
            "Trettondedagen firar de tre vise männens ankomst till Betlehem."
        ),
        "Pitkäperjantai": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Pääsiäispäivä": _desc("Påskdagen firar Jesu uppståndelse från de döda."),
        "Toinen pääsiäispäivä": _desc("Andra påskdagen fortsätter påskfirandet."),
        "Vappu": _desc(
            "Vappu är både arbetarrörelsens högtidsdag och studenternas vårfest med",
            "picknick, bubbel och studentmössor. En av Finlands mest älskade högtider.",
        ),
        "Helatorstai": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk."
        ),
        "Helluntaipäivä": _desc("Pingstdagen firar den Helige Andes utgjutelse."),
        "Juhannusaatto": _desc(
            "Midsommarafton firas med bastu, grillning och midsommarbrasor vid sjöar."
        ),
        "Juhannuspäivä": _desc(
            "Midsommardagen är den kristna högtiden för Johannes Döparen."
        ),
        "Pyhäinpäivä": _desc(
            "Alla helgons dag är en högtid till minne av alla helgon."
        ),
        "Itsenäisyyspäivä": _desc(
            "Självständighetsdagen den 6 december firar Finlands självständighet från Ryssland 1917.",
            "Dagen firas med blåvit ljuständning och högtidliga ceremonier.",
        ),
        "Jouluaatto": _desc("Julafton firas med julmat, julklappar och bastu."),
        "Joulupäivä": _desc("Juldagen firar Jesu Kristi födelse."),
        "Tapaninpäivä": _desc("Annandag jul (Stefansdagen) är dagen efter juldagen."),
    },
    "IS": {
        "Nýársdagur": _desc("Nyårsdagen inleder det nya året."),
        "Skírdagur": _desc(
            "Skärtorsdagen före påsk högtidlighåller den sista nattvarden."
        ),
        "Föstudagurinn langi": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Páskadagur": _desc("Påskdagen firar Jesu uppståndelse."),
        "Annar í páskum": _desc("Andra påskdagen fortsätter påskfirandet."),
        "Sumardagurinn fyrsti": _desc(
            "Första sommardagen firas i slutet av april och markerar den traditionella början på sommaren på Island."
        ),
        "Verkalýðsdagurinn": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag."
        ),
        "Uppstigningardagur": _desc("Kristi himmelsfärdsdag firar Jesu himmelsfärd."),
        "Hvítasunnudagur": _desc("Pingstdagen firar den Helige Andes utgjutelse."),
        "Annar í hvítasunnu": _desc("Andra pingstdagen fortsätter pingstfirandet."),
        "Þjóðhátíðardagurinn": _desc(
            "Islands nationaldag den 17 juni firar republikens grundande 1944",
            "och hyllar Jón Sigurðsson, ledaren för självständighetsrörelsen.",
        ),
        "Frídagur verslunarmanna": _desc(
            "Verslunarmannahelgi är en helg i början av augusti med familjeutflykter och festivaler."
        ),
        "Aðfangadagur": _desc("Julafton firas med familjemiddag och julklappar."),
        "Jóladagur": _desc("Juldagen firar Jesu Kristi födelse."),
        "Annar í jólum": _desc("Andra juldagen är dagen efter juldagen."),
        "Gamlársdagur": _desc("Nyårsafton firas med fyrverkerier och festligheter."),
    },
    "DE": {
        "Neujahr": _desc("Nyårsdagen inleder det nya året."),
        "Heilige Drei Könige": _desc(
            "Trettondedagen firar de tre vise männens ankomst till Betlehem."
        ),
        "Internationaler Frauentag": _desc(
            "Internationella kvinnodagen den 8 mars uppmärksammar kvinnors rättigheter och jämställdhet."
        ),
        "Karfreitag": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Ostersonntag": _desc("Påskdagen firar Jesu uppståndelse."),
        "Ostermontag": _desc("Annandag påsk fortsätter påskfirandet."),
        "Tag der Arbeit": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag."
        ),
        "Christi Himmelfahrt": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk."
        ),
        "Pfingstsonntag": _desc("Pingstdagen firar den Helige Andes utgjutelse."),
        "Pfingstmontag": _desc("Annandag pingst fortsätter pingstfirandet."),
        "Fronleichnam": _desc(
            "Kristi lekamens högtid är en katolsk helgdag som firar nattvardens instiftande."
        ),
        "Mariä Himmelfahrt": _desc(
            "Marie himmelsfärd firar Jungfru Marias upptagande till himlen."
        ),
        "Weltkindertag": _desc("Världsbarnsdagen uppmärksammar barns rättigheter."),
        "Tag der Deutschen Einheit": _desc(
            "Dagen för tysk enhet den 3 oktober firar Tysklands återförening 1990."
        ),
        "Reformationstag": _desc("Reformationsdagen firar Martin Luthers reformation."),
        "Allerheiligen": _desc(
            "Alla helgons dag är en katolsk helgdag till minne av alla helgon."
        ),
        "Buß- und Bettag": _desc(
            "Bot- och böndagen är en protestantisk helgdag med fokus på eftertanke."
        ),
        "Erster Weihnachtstag": _desc("Juldagen firar Jesu Kristi födelse."),
        "Zweiter Weihnachtstag": _desc("Andra juldagen är dagen efter juldagen."),
    },
    "FR": {
        "Jour de l'an": _desc("Nyårsdagen inleder det nya året."),
        "Lundi de Pâques": _desc(
            "Annandag påsk fortsätter firandet av Jesu uppståndelse."
        ),
        "Fête du Travail": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag."
        ),
        "Victoire 1945": _desc(
            "Segerdagen den 8 maj firar de allierades seger över Nazityskland 1945."
        ),
        "Ascension": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk."
        ),
        "Lundi de Pentecôte": _desc("Annandag pingst fortsätter pingstfirandet."),
        "Fête nationale": _desc(
            "Frankrikes nationaldag den 14 juli firar stormningen av Bastiljen 1789",
            "med parader, fyrverkerier och festligheter.",
        ),
        "Assomption": _desc(
            "Marie himmelsfärd firar Jungfru Marias upptagande till himlen."
        ),
        "Toussaint": _desc(
            "Alla helgons dag är en katolsk helgdag till minne av alla helgon."
        ),
        "Armistice 1918": _desc(
            "Vapenstilleståndsdagen den 11 november firar slutet på första världskriget 1918."
        ),
        "Noël": _desc("Juldagen firar Jesu Kristi födelse."),
    },
    "GB": {
        "New Year's Day": _desc("Nyårsdagen inleder det nya året."),
        "2 January": _desc("Andra januaridagen är en allmän helgdag i Skottland."),
        "Saint Patrick's Day": _desc(
            "S:t Patricks dag den 17 mars firar Irlands skyddshelgon med parader och fest."
        ),
        "Good Friday": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Easter Monday": _desc("Annandag påsk fortsätter påskfirandet."),
        "Early May Bank Holiday": _desc("Första måndagen i maj är en allmän helgdag."),
        "Spring Bank Holiday": _desc("Sista måndagen i maj är en allmän helgdag."),
        "World Cup Bank Holiday": _desc("Helgdag med anledning av ett sportevenemang."),
        "Battle of the Boyne": _desc(
            "Slaget vid Boyne den 12 juli firar Vilhelm III:s seger 1690, firas i Nordirland."
        ),
        "Summer Bank Holiday": _desc("Sista måndagen i augusti är en allmän helgdag."),
        "Saint Andrew's Day": _desc(
            "S:t Andreas dag den 30 november firar Skottlands skyddshelgon."
        ),
        "Christmas Day": _desc("Juldagen firar Jesu Kristi födelse."),
        "Boxing Day": _desc(
            "Annandag jul är dagen efter juldagen, traditionellt för jakt och sport."
        ),
    },
    "NL": {
        "Nieuwjaarsdag": _desc("Nyårsdagen inleder det nya året."),
        "Goede Vrijdag": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Eerste Paasdag": _desc("Påskdagen firar Jesu uppståndelse."),
        "Tweede Paasdag": _desc("Annandag påsk fortsätter påskfirandet."),
        "Koningsdag": _desc(
            "Kungens dag den 27 april firar kungens födelsedag med loppmarknader, musik och fest."
        ),
        "Bevrijdingsdag": _desc(
            "Befrielsedagen den 5 maj firar Nederländernas befrielse från Nazityskland 1945."
        ),
        "Hemelvaartsdag": _desc("Kristi himmelsfärdsdag firar Jesu himmelsfärd."),
        "Eerste Pinksterdag": _desc("Pingstdagen firar den Helige Andes utgjutelse."),
        "Tweede Pinksterdag": _desc("Annandag pingst fortsätter pingstfirandet."),
        "Eerste Kerstdag": _desc("Juldagen firar Jesu Kristi födelse."),
        "Tweede Kerstdag": _desc("Andra juldagen är dagen efter juldagen."),
    },
    "BE": {
        "Nieuwjaar": _desc("Nyårsdagen inleder det nya året."),
        "Goede Vrijdag": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Pasen": _desc("Påskdagen firar Jesu uppståndelse."),
        "Paasmaandag": _desc("Annandag påsk fortsätter påskfirandet."),
        "Dag van de arbeid": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag."
        ),
        "Onze Lieve Heer hemel": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd."
        ),
        "Day after Ascension Day": _desc(
            "Dagen efter Kristi himmelsfärdsdag är en allmän helgdag."
        ),
        "Pinkstermaandag": _desc("Annandag pingst fortsätter pingstfirandet."),
        "Nationale feestdag": _desc(
            "Belgiens nationaldag den 21 juli firar Leopold I:s ed som kung 1831."
        ),
        "Onze Lieve Vrouw hemelvaart": _desc(
            "Marie himmelsfärd firar Jungfru Marias upptagande."
        ),
        "Allerheiligen": _desc("Alla helgons dag är en katolsk helgdag."),
        "Wapenstilstand": _desc(
            "Vapenstilleståndsdagen den 11 november firar slutet på första världskriget."
        ),
        "Kerstdag": _desc("Juldagen firar Jesu Kristi födelse."),
        "Boxing Day": _desc("Andra juldagen är dagen efter juldagen."),
    },
    "AT": {
        "Neujahr": _desc("Nyårsdagen inleder det nya året."),
        "Heilige Drei Könige": _desc(
            "Trettondedagen firar de tre vise männens ankomst."
        ),
        "Josefstag": _desc("S:t Josefs dag den 19 mars är en katolsk helgdag."),
        "Ostersonntag": _desc("Påskdagen firar Jesu uppståndelse."),
        "Ostermontag": _desc("Annandag påsk fortsätter påskfirandet."),
        "Staatsfeiertag": _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag."
        ),
        "Florianitag": _desc(
            "S:t Florians dag den 4 maj är ett regionalt helgon i Österrike."
        ),
        "Christi Himmelfahrt": _desc("Kristi himmelsfärdsdag."),
        "Pfingstsonntag": _desc("Pingstdagen."),
        "Pfingstmontag": _desc("Annandag pingst."),
        "Fronleichnam": _desc("Kristi lekamens högtid är en katolsk helgdag."),
        "Maria Himmelfahrt": _desc("Marie himmelsfärd den 15 augusti."),
        "Rupertitag": _desc(
            "S:t Ruperts dag den 24 september är regional helgdag i Salzburg."
        ),
        "Nationalfeiertag": _desc(
            "Österrikes nationaldag den 26 oktober firar landets eviga neutralitet."
        ),
        "Allerheiligen": _desc("Alla helgons dag den 1 november."),
        "Martinstag": _desc(
            "S:t Martins dag den 11 november med laternenumzüge och gås."
        ),
        "Leopolditag": _desc("S:t Leopolds dag den 15 november är regional helgdag."),
        "Mariä Empfängnis": _desc("Jungfru Marie obefläckade avlelse den 8 december."),
        "Weihnachten": _desc("Juldagen firar Jesu Kristi födelse."),
        "Stefanitag": _desc("Annandag jul (Stefansdagen) den 26 december."),
    },
    "CH": {
        "Neujahr": _desc("Nyårsdagen inleder det nya året."),
        "Berchtoldstag": _desc(
            "Berchtoldsdagen den 2 januari är en gammal schweizisk tradition."
        ),
        "Heilige Drei Könige": _desc("Trettondedagen."),
        "Jahrestag der Ausrufung der Republik": _desc(
            "Årsdagen för republikens utropande den 1 mars är helgdag i kantonen Neuchâtel."
        ),
        "Josefstag": _desc("S:t Josefs dag är helgdag i flera katolska kantoner."),
        "Karfreitag": _desc("Långfredagen."),
        "Näfelser Fahrt": _desc(
            "Näfelsfärden den första torsdagen i april firar segern i slaget vid Näfels 1388."
        ),
        "Ostermontag": _desc("Annandag påsk."),
        "Tag der Arbeit": _desc("Första maj."),
        "Auffahrt": _desc("Kristi himmelsfärdsdag."),
        "Pfingstmontag": _desc("Annandag pingst."),
        "Fronleichnam": _desc("Kristi lekamens högtid i katolska kantoner."),
        "Peter und Paul": _desc("S:t Peter och Paulus dag den 29 juni."),
        "Bundesfeier": _desc(
            "Schweiz nationaldag den 1 augusti firar det schweiziska edsförbundets grundande 1291."
        ),
        "Maria Himmelfahrt": _desc("Marie himmelsfärd den 15 augusti."),
        "Jeûne genevois": _desc(
            "Genèves fasta är en årlig helgdag i kantonen Genève den första torsdagen i september."
        ),
        "Eidgenössischer Dank-, Buss- und Bettag": _desc(
            "Den schweiziska bot- och böndagen i mitten av september."
        ),
        "Bettagsmontag": _desc(
            "Måndagen efter bot- och böndagen är helgdag i flera kantoner."
        ),
        "Allerheiligen": _desc("Alla helgons dag."),
        "Mariä Empfängnis": _desc("Jungfru Marie obefläckade avlelse."),
        "Weihnachten": _desc("Juldagen."),
        "Stephanstag": _desc("Annandag jul (Stefansdagen)."),
        "Restauration de la République": _desc(
            "Republikens återställande den 31 december firas i kantonen Genève."
        ),
    },
    "IT": {
        "Capodanno": _desc("Nyårsdagen inleder det nya året."),
        "Epifania": _desc(
            "Trettondedagen den 6 januari med traditionen att la Befana kommer med godis."
        ),
        "Pasqua": _desc("Påskdagen firar Jesu uppståndelse."),
        "Lunedì dell'Angelo": _desc("Annandag påsk, kallas även 'Ängelns måndag'."),
        "Festa della Liberazione": _desc(
            "Befrielsedagen den 25 april firar Italiens befrielse från fascismen 1945."
        ),
        "Festa del Lavoro": _desc("Första maj är arbetarrörelsens högtidsdag."),
        "Lunedì di Pentecoste": _desc("Annandag pingst."),
        "Festa della Repubblica": _desc(
            "Republikens dag den 2 juni firar Italiens övergång till republik 1946."
        ),
        "Ferragosto o Assunzione": _desc(
            "Ferragosto den 15 augusti firar Marie himmelsfärd och sommarens höjdpunkt."
        ),
        "San Francesco d'Assisi": _desc(
            "S:t Franciskus av Assisi dag den 4 oktober är ett helgon."
        ),
        "Tutti i santi": _desc("Alla helgons dag den 1 november."),
        "Immacolata Concezione": _desc(
            "Jungfru Marie obefläckade avlelse den 8 december."
        ),
        "Natale": _desc("Juldagen firar Jesu Kristi födelse."),
        "Santo Stefano": _desc("Annandag jul (Stefansdagen) den 26 december."),
    },
    "ES": {
        "Año Nuevo": _desc("Nyårsdagen inleder det nya året."),
        "Día de Reyes / Epifanía del Señor": _desc(
            "Trettondedagen den 6 januari med de tre vise männens ankomst och stora parader."
        ),
        "Día de Andalucía": _desc(
            "Andalusiens dag den 28 februari firar regionens autonomi."
        ),
        "Dia de les Illes Balears": _desc("Balearernas dag den 1 mars."),
        "Jueves Santo": _desc("Skärtorsdagen före påsk."),
        "Viernes Santo": _desc("Långfredagen."),
        "Lunes de Pascua": _desc("Annandag påsk."),
        "Día de Castilla y León": _desc("Kastilien och Leóns dag den 23 april."),
        "San Jorge (Día de Aragón)": _desc(
            "S:t Georgs dag den 23 april är Aragoniens dag."
        ),
        "Fiesta del trabajo": _desc("Första maj."),
        "Fiesta de la Comunidad de Madrid": _desc("Madrids regiondag den 2 maj."),
        "Día das Letras Galegas": _desc("Galiciska litteraturens dag den 17 maj."),
        "Día de Canarias": _desc("Kanarieöarnas dag den 30 maj."),
        "Día de la Región Castilla-La Mancha": _desc(
            "Castilla-La Manchas dag den 31 maj."
        ),
        "Corpus Christi": _desc("Kristi lekamens högtid."),
        "Día de La Rioja": _desc("La Riojas dag den 9 juni."),
        "Día de la Región de Murcia": _desc("Murcias regiondag den 9 juni."),
        "Sant Joan": _desc(
            "S:t Johannes dag den 24 juni firas i Katalonien och andra regioner."
        ),
        "Santiago Apóstol": _desc(
            "S:t Jakob den äldres dag den 25 juli, Spaniens skyddshelgon."
        ),
        "Día de las Instituciones de Cantabria": _desc(
            "Kantabriens institutionsdag den 28 juli."
        ),
        "Asunción": _desc("Marie himmelsfärd den 15 augusti."),
        "Día de Asturias": _desc("Asturiens dag den 8 september."),
        "Día de Extremadura": _desc("Extremaduras dag den 8 september."),
        "Diada Nacional de Catalunya": _desc(
            "Kataloniens nationaldag den 11 september."
        ),
        "Festividad de la Bien Aparecida": _desc("Kantabriens regionalhelgdag."),
        "Dia de la Comunitat Valenciana": _desc("Valencias regiondag den 9 oktober."),
        "Fiesta Nacional de España": _desc(
            "Spaniens nationaldag den 12 oktober firar Christofer Columbus ankomst till Amerika 1492."
        ),
        "Día de todos los Santos": _desc("Alla helgons dag den 1 november."),
        "Día de la Constitución": _desc(
            "Konstitutionsdagen den 6 december firar 1978 års grundlag."
        ),
        "Inmaculada Concepción": _desc(
            "Jungfru Marie obefläckade avlelse den 8 december."
        ),
        "Navidad": _desc("Juldagen firar Jesu Kristi födelse."),
        "Feast of Saint Stephen": _desc("Annandag jul (Stefansdagen) den 26 december."),
    },
    "PT": {
        "Ano Novo": _desc("Nyårsdagen inleder det nya året."),
        "Carnaval": _desc(
            "Karnevalen i februari är en färgsprakande högtid med parader och fest."
        ),
        "Sexta-feira Santa": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Domingo de Páscoa": _desc("Påskdagen firar Jesu uppståndelse."),
        "Dia da Liberdade": _desc(
            "Frihetens dag den 25 april firar nejlikerevolutionen 1974 som störtade diktaturen."
        ),
        "Dia do Trabalhador": _desc("Första maj."),
        "Dia dos Açores": _desc("Azorernas dag den 20 maj."),
        "Corpo de Deus": _desc("Kristi lekamens högtid."),
        "Dia de Portugal, de Camões e das Comunidades Portuguesas": _desc(
            "Portugals nationaldag den 10 juni firar poeten Luís de Camões och portugisisk kultur."
        ),
        "Dia da Madeira": _desc("Madeiras dag den 1 juli."),
        "Assunção de Nossa Senhora": _desc("Marie himmelsfärd den 15 augusti."),
        "Implantação da República": _desc("Republikens införande den 5 oktober 1910."),
        "Dia de Todos-os-Santos": _desc("Alla helgons dag den 1 november."),
        "Restauração da Independência": _desc(
            "Självständighetens återställande den 1 december 1640 från Spanien."
        ),
        "Imaculada Conceição": _desc(
            "Jungfru Marie obefläckade avlelse den 8 december."
        ),
        "Natal": _desc("Juldagen firar Jesu Kristi födelse."),
        "Primeira Oitava": _desc("Annandag jul."),
    },
    "US": {
        "New Year's Day": _desc("Nyårsdagen inleder det nya året."),
        "Martin Luther King, Jr. Day": _desc(
            "Martin Luther King-dagen den tredje måndagen i januari firar medborgarrättsledarens födelsedag."
        ),
        "Lincoln's Birthday": _desc("Abraham Lincolns födelsedag den 12 februari."),
        "Washington's Birthday": _desc(
            "George Washingtons födelsedag tredje måndagen i februari, ofta kallad Presidents Day."
        ),
        "Good Friday": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Truman Day": _desc("Harry S. Trumans födelsedag den 8 maj firas i Missouri."),
        "Memorial Day": _desc(
            "Memorial Day sista måndagen i maj hedrar amerikanska soldater som stupat i krig."
        ),
        "Juneteenth National Independence Day": _desc(
            "Juneteenth den 19 juni firar slaveriets upphörande i USA 1865."
        ),
        "Independence Day": _desc(
            "Självständighetsdagen den 4 juli firar USA:s självständighetsförklaring 1776 med fyrverkerier och parader."
        ),
        "Labor Day": _desc(
            "Labor Day första måndagen i september firar arbetarrörelsen, skiljer sig från Europas 1 maj."
        ),
        "Columbus Day": _desc(
            "Columbus dagen den 12 oktober firar Christofer Columbus ankomst till Amerika."
        ),
        "Indigenous Peoples' Day": _desc(
            "Urbefolkningens dag uppmärksammar Amerikas ursprungsbefolkning."
        ),
        "Veterans Day": _desc(
            "Veterandagen den 11 november hedrar amerikanska krigsveteraner."
        ),
        "Thanksgiving Day": _desc(
            "Thanksgiving den fjärde torsdagen i november är en familjehögtid med kalkonmiddag och tacksägelse."
        ),
        "Christmas Day": _desc("Juldagen firar Jesu Kristi födelse."),
    },
    "CA": {
        "New Year's Day": _desc("Nyårsdagen inleder det nya året."),
        "Family Day": _desc(
            "Family Day tredje måndagen i februari är en dag för familjen."
        ),
        "Good Friday": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Easter Monday": _desc("Annandag påsk."),
        "Victoria Day": _desc(
            "Victoriadagen sista måndagen före 25 maj firar drottning Victorias födelsedag."
        ),
        "National Aboriginal Day": _desc(
            "Dagen för ursprungsbefolkningen den 21 juni."
        ),
        "Fête nationale du Québec": _desc(
            "Quebecs nationaldag den 24 juni, även kallad S:t Jean-Baptiste-dagen."
        ),
        "Canada Day": _desc(
            "Kanadadagen den 1 juli firar Kanadas konfederation 1867 med parader och fyrverkerier."
        ),
        "Civic Holiday": _desc(
            "Civic Holiday första måndagen i augusti är en allmän helgdag i flera provinser."
        ),
        "Labour Day": _desc("Labour Day första måndagen i september."),
        "National Day for Truth and Reconciliation": _desc(
            "Sannings- och försoningsdagen den 30 september hedrar ursprungsbefolkningen."
        ),
        "Thanksgiving": _desc(
            "Thanksgiving andra måndagen i oktober är en skördehögtid."
        ),
        "Remembrance Day": _desc(
            "Remembrance Day den 11 november hedrar krigsveteraner."
        ),
        "Christmas Day": _desc("Juldagen firar Jesu Kristi födelse."),
        "Boxing Day": _desc("Annandag jul den 26 december."),
    },
    "AU": {
        "New Year's Day": _desc("Nyårsdagen inleder det nya året."),
        "Australia Day": _desc(
            "Australiendagen den 26 januari firar den brittiska kolonisationens början 1788."
        ),
        "Good Friday": _desc("Långfredagen."),
        "Easter Eve": _desc("Påsknatten, dagen före påskdagen."),
        "Easter Sunday": _desc("Påskdagen firar Jesu uppståndelse."),
        "Easter Monday": _desc("Annandag påsk."),
        "Anzac Day": _desc(
            "Anzac Day den 25 april hedrar australiska och nyzeeländska soldater som stupat i krig, speciellt Gallipoli 1915."
        ),
        "King's Birthday": _desc(
            "Kungens födelsedag firas i juni (de flesta delstater)."
        ),
        "Christmas Day": _desc("Juldagen firar Jesu Kristi födelse."),
        "Boxing Day": _desc("Annandag jul den 26 december."),
    },
    "NZ": {
        "Waitangi Day": _desc(
            "Waitangidagen den 6 februari firar undertecknandet av Waitangifördraget 1840, Norges grunddokument."
        ),
        "Good Friday": _desc("Långfredagen."),
        "Easter Monday": _desc("Annandag påsk."),
        "Anzac Day": _desc("Anzac Day den 25 april hedrar stupade soldater."),
        "King's Birthday": _desc("Kungens födelsedag i juni."),
        "Matariki": _desc(
            "Matariki firar maoriernas nyår när stjärnhoparna Plejaderna syns på natthimlen i juni/juli."
        ),
        "Labour Day": _desc("Labour Day fjärde måndagen i oktober."),
        "Christmas Day": _desc("Juldagen."),
        "Boxing Day": _desc("Annandag jul."),
    },
    "JP": {
        "元日": _desc(
            "Nyårsdagen (Ganjitsu) är en av de viktigaste högtiderna i Japan med tempelbesök och familjemiddag."
        ),
        "成人の日": _desc(
            "Seijin no Hi (andra måndagen i januari) firar ungdomar som fyllt 20 år och blivit vuxna."
        ),
        "建国記念の日": _desc(
            "Kenkoku Kinen no Hi den 11 februari firar Japans grundande."
        ),
        "天皇誕生日": _desc("Kejsarens födelsedag den 23 februari."),
        "春分の日": _desc(
            "Shunbun no Hi (vårdagjämningen) är en dag för att hedra förfäder och naturen."
        ),
        "昭和の日": _desc("Shōwa no Hi den 29 april firar kejsar Shōwas födelsedag."),
        "憲法記念日": _desc(
            "Kenpō Kinenbi den 3 maj firar Japans konstitution från 1947."
        ),
        "みどりの日": _desc(
            "Midori no Hi den 4 maj är en dag för att uppskatta naturen."
        ),
        "こどもの日": _desc(
            "Kodomo no Hi den 5 maj är barnens högtid med karpoppflagg och samurajdockor."
        ),
        "海の日": _desc(
            "Umi no Hi (tredje måndagen i juli) firar havets betydelse för Japan."
        ),
        "山の日": _desc("Yama no Hi den 11 augusti firar bergens betydelse."),
        "敬老の日": _desc(
            "Keirō no Hi (tredje måndagen i september) hedrar äldre människor."
        ),
        "秋分の日": _desc(
            "Shūbun no Hi (höstdagjämningen) är en dag för att hedra förfäder."
        ),
        "スポーツの日": _desc(
            "Supōtsu no Hi (andra måndagen i oktober) främjar sport och motion."
        ),
        "文化の日": _desc(
            "Bunka no Hi den 3 november firar kultur, konst och akademi."
        ),
        "勤労感謝の日": _desc(
            "Kinrō Kansha no Hi den 23 november är en tacksägelsedag för arbete och produktion."
        ),
    },
    "BR": {
        "Confraternização Universal": _desc(
            "Nyårsdagen inleder det nya året och firas med festligheter."
        ),
        "Carnaval": _desc(
            "Karnevalen är Brasiliens mest kända högtid med parader, samba och färgsprakande kostymer."
        ),
        "Sexta-feira Santa": _desc("Långfredagen högtidlighåller Jesu korsfästelse."),
        "Domingo de Páscoa": _desc("Påskdagen firar Jesu uppståndelse."),
        "Dia de Tiradentes": _desc(
            "Tiradentes dag den 21 april firar nationalhjälten Joaquim José da Silva Xavier."
        ),
        "Dia do Trabalhador": _desc("Första maj är arbetarrörelsens högtidsdag."),
        "Corpus Christi": _desc("Kristi lekamens högtid."),
        "Revolução Constitucionalista de 1932": _desc(
            "Konstitutionalistrevolutionens dag den 9 juli i São Paulo."
        ),
        "Dia da Independência": _desc(
            "Självständighetsdagen den 7 september firar Brasiliens självständighet från Portugal 1822."
        ),
        "Nossa Senhora Aparecida": _desc(
            "Vår Fru av Aparecida den 12 oktober är Brasiliens skyddshelgon."
        ),
        "Dia de Finados": _desc("Alla själars dag den 2 november."),
        "Proclamação da República": _desc(
            "Republikens utropande den 15 november 1889."
        ),
        "Dia da Consciência Negra": _desc("Svart medvetenhets dag den 20 november."),
        "Natal": _desc("Juldagen firar Jesu Kristi födelse."),
    },
    "PL": {
        "Nowy Rok": _desc("Nyårsdagen inleder det nya året."),
        "Święto Trzech Króli": _desc("Trettondedagen den 6 januari."),
        "Wielkanoc": _desc("Påskdagen firar Jesu uppståndelse."),
        "Drugi Dzień Wielkanocy": _desc("Annandag påsk."),
        "Święto Pracy": _desc("Första maj."),
        "Święto Narodowe Trzeciego Maja": _desc(
            "Polska konstitutionsdagen den 3 maj firar 1791 års grundlag."
        ),
        "Zielone Świątki": _desc("Pingstdagen, även kallad 'Gröna högtiden' i Polen."),
        "Boże Ciało": _desc("Kristi lekamens högtid med traditionella processioner."),
        "Wniebowzięcie Najświętszej Maryi Panny": _desc(
            "Marie himmelsfärd den 15 augusti."
        ),
        "Wszystkich Świętych": _desc(
            "Alla helgons dag den 1 november med ljuständning på kyrkogårdarna."
        ),
        "Narodowe Święto Niepodległości": _desc(
            "Polens självständighetsdag den 11 november firar återfåendet av självständighet 1918."
        ),
        "Wolna Wigilia": _desc("Julafton, ledig dag före jul."),
        "Boże Narodzenie": _desc("Juldagen firar Jesu Kristi födelse."),
        "Drugi Dzień Bożego Narodzenia": _desc("Annandag jul."),
    },
    "IE": {
        "Lá Caille": _desc("Nyårsdagen inleder det nya året."),
        "Lá Fhéile Bríde": _desc(
            "S:t Brigids dag den 1 februari är en gammal keltisk högtid."
        ),
        "Lá Fhéile Pádraig": _desc(
            "S:t Patrick's Day den 17 mars är Irlands nationaldag med parader och fest."
        ),
        "Aoine an Chéasta": _desc("Långfredagen."),
        "Luan Cásca": _desc("Annandag påsk."),
        "Lá Bealtaine": _desc("Första maj är en gammal keltisk vårfest."),
        "Lá Saoire i mí an Mheithimh": _desc(
            "Junibankhelgdagen första måndagen i juni."
        ),
        "Lá Saoire i mí Lúnasa": _desc(
            "Augustibankhelgdagen första måndagen i augusti."
        ),
        "Lá Saoire i mí Dheireadh Fómhair": _desc(
            "Oktoberbankhelgdagen sista måndagen i oktober."
        ),
        "Lá Nollag": _desc("Juldagen firar Jesu Kristi födelse."),
        "Lá Fhéile Stiofáin": _desc("Annandag jul (Stefansdagen) den 26 december."),
    },
    "CZ": {
        "Den obnovy samostatného českého státu": _desc(
            "Dagen för återupprättandet av Tjeckien den 1 januari 1993."
        ),
        "Nový rok": _desc("Nyårsdagen."),
        "Velký pátek": _desc("Långfredagen."),
        "Velikonoční pondělí": _desc("Annandag påsk."),
        "Svátek práce": _desc("Första maj."),
        "Den vítězství": _desc(
            "Segerdagen den 8 maj firar slutet på andra världskriget."
        ),
        "Den slovanských věrozvěstů Cyrila a Metoděje": _desc(
            "Cyrillus och Methodius dag den 5 juli."
        ),
        "Den upálení mistra Jana Husa": _desc("Mäster Jan Hus dag den 6 juli."),
        "Den české státnosti": _desc("Tjeckiska statsdagen den 28 september."),
        "Den vzniku samostatného československého státu": _desc(
            "Självständighetsdagen den 28 oktober 1918."
        ),
        "Den boje za svobodu a demokracii a Mezinárodní den studentstva": _desc(
            "Kampen för frihet och demokrati den 17 november."
        ),
        "Štědrý den": _desc("Julafton den 24 december."),
        "1. svátek vánoční": _desc("Juldagen den 25 december."),
        "2. svátek vánoční": _desc("Annandag jul den 26 december."),
    },
    "HU": {
        "Újév": _desc("Nyårsdagen."),
        "Nemzeti ünnep": _desc(
            "Nationella helgdagen den 15 mars firar 1848 års revolution."
        ),
        "Nagypéntek": _desc("Långfredagen."),
        "Húsvétvasárnap": _desc("Påskdagen."),
        "Húsvéthétfő": _desc("Annandag påsk."),
        "A munka ünnepe": _desc("Första maj."),
        "Pünkösdvasárnap": _desc("Pingstdagen."),
        "Pünkösdhétfő": _desc("Annandag pingst."),
        "Az államalapítás ünnepe": _desc(
            "Statsgrundningsdagen den 20 augusti firar kung Stefan I."
        ),
        "Nemzeti ünnep": _desc(
            "Nationaldagen den 23 oktober firar 1956 års revolution."
        ),
        "Mindenszentek": _desc("Alla helgons dag den 1 november."),
        "Karácsony": _desc("Juldagen den 25 december."),
        "Karácsony másnapja": _desc("Annandag jul den 26 december."),
    },
    "EE": {
        "uusaasta": _desc("Nyårsdagen."),
        "iseseisvuspäev": _desc(
            "Självständighetsdagen den 24 februari firar Estlands självständighet 1918."
        ),
        "suur reede": _desc("Långfredagen."),
        "ülestõusmispühade 1. püha": _desc("Påskdagen."),
        "kevadpüha": _desc("Vårfesten den 1 maj."),
        "nelipühade 1. püha": _desc("Pingstdagen."),
        "võidupüha and jaanilaupäev": _desc(
            "Segerdagen den 23 juni firar segern i slaget vid Võnnu 1919."
        ),
        "jaanipäev": _desc("Midsommardagen den 24 juni."),
        "taasiseseisvumispäev": _desc(
            "Återupprättad självständighetsdag den 20 augusti 1991."
        ),
        "jõululaupäev": _desc("Julafton den 24 december."),
        "esimene jõulupüha": _desc("Juldagen den 25 december."),
        "teine jõulupüha": _desc("Annandag jul den 26 december."),
    },
    "LV": {
        "Jaungada diena": _desc("Nyårsdagen."),
        "Lielā Piektdiena": _desc("Långfredagen."),
        "Pirmās Lieldienas": _desc("Påskdagen."),
        "Otrās Lieldienas": _desc("Annandag påsk."),
        "Darba svētki": _desc("Första maj."),
        "Latvijas Republikas Satversmes sapulces sasaukšanas diena": _desc(
            "Konstitutionsförsamlingens dag den 1 maj."
        ),
        "Latvijas Republikas Neatkarības atjaunošanas diena": _desc(
            "Självständighetens återställande den 4 maj 1990."
        ),
        "Mātes diena": _desc("Mors dag andra söndagen i maj."),
        "Vasarsvētki": _desc("Pingstdagen."),
        "Līgo diena": _desc("Midsommarafton den 23 juni med sång och dans."),
        "Jāņu diena": _desc("Midsommardagen den 24 juni."),
        "Latvijas Republikas Proklamēšanas diena": _desc(
            "Republikens proklamering den 18 november 1918."
        ),
        "Ziemassvētku vakars": _desc("Julafton den 24 december."),
        "Pirmie Ziemassvētki": _desc("Juldagen den 25 december."),
        "Otrie Ziemassvētki": _desc("Annandag jul den 26 december."),
        "Vecgada diena": _desc("Nyårsafton den 31 december."),
    },
    "LT": {
        "Naujieji metai": _desc("Nyårsdagen."),
        "Lietuvos valstybės atkūrimo diena": _desc(
            "Statsåterupprättelsedagen den 16 februari 1918."
        ),
        "Lietuvos nepriklausomybės atkūrimo diena": _desc(
            "Självständighetens återställande den 11 mars 1990."
        ),
        "Velykos": _desc("Påskdagen."),
        "Antroji Velykų diena": _desc("Annandag påsk."),
        "Tarptautinė darbo diena": _desc("Första maj."),
        "Joninės, Rasos": _desc("Midsommardagen den 24 juni."),
        "Valstybės diena": _desc(
            "Statsdagen den 6 juli firar kung Mindaugas kröning 1253."
        ),
        "Žolinė": _desc("Marie himmelsfärd den 15 augusti."),
        "Visų šventųjų diena": _desc("Alla helgons dag den 1 november."),
        "Vėlinės": _desc("Alla själars dag den 2 november."),
        "Šv. Kūčios": _desc("Julafton den 24 december."),
        "Šv. Kalėdos": _desc("Juldagen den 25 december."),
        "Šv. Kalėdos": _desc("Annandag jul den 26 december."),
    },
    "HR": {
        "Novi godina": _desc("Nyårsdagen."),
        "Bogojavljenje": _desc("Trettondedagen den 6 januari."),
        "Uskrs": _desc("Påskdagen."),
        "Uskrsni ponedjeljak": _desc("Annandag påsk."),
        "Praznik rada": _desc("Första maj."),
        "Tijelovo": _desc("Kristi lekamens högtid."),
        "Dan državnosti": _desc("Statsdagen den 30 maj."),
        "Dan antifašističke borbe": _desc("Antifascistiska kampens dag den 22 juni."),
        "Dan pobjede i domovinske zahvalnosti": _desc(
            "Seger- och hemlandstacksägelsedagen den 5 augusti."
        ),
        "Velika Gospa": _desc("Marie himmelsfärd den 15 augusti."),
        "Dan neovisnosti": _desc("Självständighetsdagen den 8 oktober."),
        "Svi sveti": _desc("Alla helgons dag den 1 november."),
        "Božić": _desc("Juldagen den 25 december."),
        "Sveti Stjepan": _desc("Annandag jul den 26 december."),
    },
}


# ── Universella beskrivningar (matchas via datum och/eller nyckelord) ──


def _date_desc(month, day, fallback):
    """Skapa en beskrivning för ett givet datum om ingen landsspecifik finns."""
    fixed = {
        (1, 1): _desc(
            "Nyårsdagen inleder det nya året. Dagen firas med festligheter, fyrverkerier och nyårslöften över hela världen."
        ),
        (1, 6): _desc(
            "Trettondedagen, eller Epifania, firar de tre vise männens ankomst till Betlehem för att hylla Jesusbarnet."
        ),
        (5, 1): _desc(
            "Första maj är arbetarrörelsens internationella högtidsdag och firas med demonstrationer och tal över hela världen."
        ),
        (12, 25): _desc(
            "Juldagen firar Jesu Kristi födelse i Betlehem. Det är en av de största kristna högtiderna med en lång tradition."
        ),
        (12, 26): _desc(
            "Annandag jul är dagen efter juldagen och är en allmän helgdag som traditionellt används för vänbesök och festligheter."
        ),
        (12, 24): _desc(
            "Julafton är den mest centrala dagen i julfirandet med familjemiddag, julklappar och gemenskap."
        ),
        (12, 31): _desc(
            "Nyårsafton firas den sista dagen på året med festmiddag och fyrverkerier vid midnatt."
        ),
        (11, 1): _desc(
            "Alla helgons dag är en kristen helgdag till minne av alla helgon och martyrer."
        ),
        (8, 15): _desc(
            "Marie himmelsfärd firar Jungfru Marias upptagande till himlen."
        ),
        (3, 8): _desc(
            "Internationella kvinnodagen uppmärksammar kvinnors rättigheter och kampen för jämställdhet."
        ),
    }
    return fixed.get((month, day), fallback)


def _movable_desc(name, date, easter, fallback):
    """Skapa beskrivning för rörliga helgdagar baserat på relation till påsk."""
    diff = (date - easter).days
    movable = {
        "lang_fredag": _desc(
            "Långfredagen högtidlighåller Jesu korsfästelse och död på Golgata. Det är en stilla helgdag inom kristendomen."
        ),
        "skär_torsdag": _desc(
            "Skärtorsdagen högtidlighåller den sista nattvarden, Jesus sista måltid med lärjungarna."
        ),
        "påsk_dag": _desc(
            "Påskdagen är den viktigaste helgdagen inom kristendomen och firar Jesu uppståndelse från de döda."
        ),
        "annandag_påsk": _desc(
            "Annandag påsk är dagen efter påskdagen och fortsätter firandet av Jesu uppståndelse."
        ),
        "himmelsfärd": _desc(
            "Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk. Högtiden har firats sedan 300-talet."
        ),
        "pingst": _desc(
            "Pingstdagen firar den Helige Andes utgjutelse över apostlarna 50 dagar efter påsk."
        ),
        "annandag_pingst": _desc(
            "Annandag pingst fortsätter firandet av den Helige Andes utgjutelse."
        ),
        "corpus_christi": _desc(
            "Kristi lekamens högtid är en katolsk högtid som firar nattvardens instiftande, 60 dagar efter påsk."
        ),
    }
    if diff == -2:
        return movable["skär_torsdag"]
    if diff == -3:
        return movable["skär_torsdag"]
    elif diff == -1:
        return movable["lang_fredag"]
    elif diff == 0:
        return movable["påsk_dag"]
    elif diff == 1:
        return movable["annandag_påsk"]
    elif diff == 39:
        return movable["himmelsfärd"]
    elif diff == 49:
        return movable["pingst"]
    elif diff == 50:
        return movable["annandag_pingst"]
    elif diff == 60:
        return movable["corpus_christi"]
    return fallback


def get_description(holiday, country_code, country_name):
    """Hitta beskrivning för en helgdag."""
    date_str = holiday["date"]
    name = holiday["localName"]
    htype = holiday.get("types", [""])[0]
    d = datetime.strptime(date_str, "%Y-%m-%d")
    month, day = d.month, d.day

    # 1. Landsspecifik beskrivning
    country_descs = COUNTRY_SPECIFIC.get(country_code.upper(), {})
    if name in country_descs:
        return country_descs[name]

    # 2. Försök matcha via relation till påsk (rörliga helgdagar)
    easter = compute_easter(d.year)
    easter_diff = (
        (d.date() - easter).days
        if hasattr(d, "date")
        else (date(d.year, d.month, d.day) - easter).days
    )

    movable_descs = {
        -2: _desc("Skärtorsdagen högtidlighåller den sista nattvarden."),
        -1: _desc(
            "Långfredagen högtidlighåller Jesu korsfästelse och död. Det är en stilla helgdag inom kristendomen."
        ),
        0: _desc(
            "Påskdagen är den viktigaste helgdagen inom kristendomen och firar Jesu uppståndelse från de döda."
        ),
        1: _desc("Annandag påsk fortsätter firandet av Jesu uppståndelse."),
        39: _desc("Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk."),
        49: _desc(
            "Pingstdagen firar den Helige Andes utgjutelse över apostlarna 50 dagar efter påsk."
        ),
        50: _desc(
            "Annandag pingst fortsätter firandet av den Helige Andes utgjutelse."
        ),
        60: _desc("Kristi lekamens högtid firar nattvardens instiftande."),
    }
    if easter_diff in movable_descs:
        return movable_descs[easter_diff]

    # 3. Försök matcha via datum för kända fasta helgdagar
    fixed = {
        (1, 1): _desc(
            "Nyårsdagen inleder det nya året och firas med festligheter över hela världen."
        ),
        (1, 6): _desc(
            "Trettondedagen firar de tre vise männens ankomst till Betlehem."
        ),
        (2, 14): _desc(
            "Alla hjärtans dag (Valentine's Day) är en dag för kärlek och vänskap."
        ),
        (3, 8): _desc(
            "Internationella kvinnodagen uppmärksammar kvinnors rättigheter globalt."
        ),
        (5, 1): _desc("Första maj är arbetarrörelsens internationella högtidsdag."),
        (6, 6): _desc("Sveriges nationaldag."),
        (8, 15): _desc(
            "Marie himmelsfärd firar Jungfru Marias upptagande till himlen."
        ),
        (10, 3): _desc("Dagen för tysk enhet firar Tysklands återförening 1990."),
        (10, 12): _desc(
            "Spaniens nationaldag firar Christofer Columbus ankomst till Amerika 1492."
        ),
        (10, 31): _desc("Halloween har sina rötter i den keltiska högtiden Samhain."),
        (11, 1): _desc(
            "Alla helgons dag är en kristen helgdag till minne av alla helgon."
        ),
        (11, 2): _desc(
            "Alla själars dag är en dag för att minnas och be för de avlidna."
        ),
        (11, 11): _desc(
            "Vapenstilleståndsdagen firar slutet på första världskriget 1918."
        ),
        (12, 24): _desc("Julafton firas med familjemiddag och julklappar."),
        (12, 25): _desc("Juldagen firar Jesu Kristi födelse i Betlehem."),
        (12, 26): _desc("Annandag jul är dagen efter juldagen."),
        (12, 31): _desc("Nyårsafton firas med fest och fyrverkerier."),
    }
    if (month, day) in fixed:
        return fixed[(month, day)]

    # 4. Försök matcha via nyckelord i namnet
    name_lower = name.lower()
    keywords = [
        (
            r"national|independence|republi|freiheit|frei|frihet|självständ|grundlov|"
            r"fête nationale|festa nazionale|nationalfeier|federal|unabhängig|"
            r"constitu|patria|patrie|fädernes|iseseisv|neatkarības|nepriklausomybės|"
            r"státnosti|državnosti|államalapítás|suverenit|domovinske|"
            r"þjóðhátíðar|flaggdag|nationaldag",
            _desc(
                "Nationaldagen är en av landets viktigaste högtider och firas med patriotism och festligheter."
            ),
        ),
        (
            r"jul(e|en)?|christmas|weihnacht|noël?l?|natal|kerst|krismas|nollag|"
            r"boże narodzenie|karácsony|kalėd|vianoč|jõulu|joulu|božič|joł|crăciun|"
            r"roždestvo|крист|христ|coladă|kūčios|ziemassvētku",
            _desc(
                "Julen firar Jesu Kristi födelse och är en av de största högtiderna i den kristna världen."
            ),
        ),
        (
            r"påsk|påske|easter|paasch|pâqu|pasqua?|pascua|passah|pasen|"
            r"wielkanoc|velikono|páscoa|húsvét|pääsiäis|velyk|velika noč|pásk",
            _desc(
                "Påsken firar Jesu uppståndelse och är den viktigaste helgdagen inom kristendomen."
            ),
        ),
        (
            r"pingst|pinse|pentecost|pfingst|pinkster|pentecôte|helluntai|"
            r"pünkösd|nelipüh|vasarsvētki|binkoštna|zielone świątki|whitsun|hvítasunnu",
            _desc(
                "Pingst firar den Helige Andes utgjutelse över apostlarna 50 dagar efter påsk."
            ),
        ),
        (
            r"him(mel)?elsfärd|himmelfart|ascension|himmelfahrt|hemelvaart|"
            r"helatorstai|uppstigning|himmalsferð|himmal(s)?(i)? (ferðar)?dag",
            _desc("Kristi himmelsfärdsdag firar Jesu himmelsfärd 40 dagar efter påsk."),
        ),
        (
            r"arbet|arbeit|labo(u)?r|travail|lavoro|trabalhador|worker|"
            r"munka|praznik rada|dag van de arbeid",
            _desc(
                "Arbetarrörelsens högtidsdag firas till minne av arbetarnas kamp för bättre villkor."
            ),
        ),
        (
            r"ny(tt)?års|nyår|new year|neujahr|nouvel an|nytårs|"
            r"uudenvuoden|año nuevo|ano novo|capodanno|nieuwjaar|nowy rok|"
            r"novo leto|nýárs|naujieji|nový rok|újév|jaungada|"
            r"ganjitsu|ganj|confraternização",
            _desc("Nyårsdagen inleder det nya året och firas världen över."),
        ),
        (
            r"midsommar|midsummer|juhannus|jaani|jāņu|joninės|rasos|st john|"
            r"dia de são joão|san juan|jónsmessa|jóns",
            _desc(
                "Midsommar är en av de mest älskade högtiderna i Norden med traditioner som härrör från förkristen tid."
            ),
        ),
        (
            r"pentecoste|lunedì dell.?angelo|lundi de pentecôte|paasmaandag|"
            r"tweede pinksterdag|pfingstmontag|annan(dag)? påsk|2\. påskedag",
            _desc("Högtiden fortsätter firandet av påsken."),
        ),
    ]

    for pattern, fallback_desc in keywords:
        if re.search(pattern, name_lower):
            return fallback_desc

    # 5. Generisk fallback
    typ_label = TYPE_LABELS.get(htype, htype)
    if htype == "Public":
        return _desc(
            f"{name} är en allmän helgdag i {country_name} som firas med olika traditioner."
        )
    elif htype == "Observance":
        return _desc(f"{name} är en kulturell högtid i {country_name}.")
    return _desc(f"{name} är en {typ_label.lower()} i {country_name}.")


# ── PDF-generering ──
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


def generate_pdf(country_code, year, output_path=None, country_name=None):
    if country_name is None:
        country_name, raw = fetch_holidays(country_code, year)
    else:
        _, raw = fetch_holidays(country_code, year)

    # Deduplicera (säkerställ att det inte finns dubbletter)
    seen = {}
    for h in raw:
        r = best_type(h)
        if r > seen.get(h["date"], {}).get("_rank", 0):
            h["_rank"] = r
            seen[h["date"]] = h
    holidays = sorted(seen.values(), key=lambda h: h["date"])

    pdf = HolidayPDF()
    pdf._country = country_name
    pdf._year = year
    pdf.set_auto_page_break(auto=True, margin=25)

    cjk = country_code.upper() in ("JP", "CN", "KR", "HK", "TW")
    if cjk:
        font = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
        pdf.add_font("Arial", "", font)
        pdf.add_font("Arial", "B", font)
        pdf.add_font("Arial", "I", font)
        pdf.add_font("Arial", "BI", font)
    else:
        pdf.add_font("Arial", "", "/System/Library/Fonts/Supplemental/Arial.ttf")
        pdf.add_font("Arial", "B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
        pdf.add_font(
            "Arial", "I", "/System/Library/Fonts/Supplemental/Arial Italic.ttf"
        )
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
    pdf.cell(0, 7, f"{len(holidays)} helgdagar", align="C")
    pdf.ln(7)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 7, f"Genererad: {datetime.now().strftime('%B %Y').lower()}", align="C")

    # ── Innehållsförteckning ──
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 14, "Innehåll", align="L")
    pdf.ln(12)
    pdf.set_draw_color(99, 102, 241)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    for i, h in enumerate(holidays, 1):
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
        pdf.cell(25, 9, DAYS[d.weekday()], align="C")
        pdf.ln(9)
    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Arial", "I", 8)
    pdf.ln(12)
    pdf.multi_cell(
        0,
        5,
        "Not: Rörliga helgdagar (påsk, pingst, Kristi himmelsfärdsdag, "
        "Långfredagen, Alla helgons dag, midsommar) är beräknade utifrån "
        "det aktuella årets datum.",
    )

    # ── En sida per helgdag ──
    for idx, h in enumerate(holidays, 1):
        pdf.add_page()
        d = datetime.strptime(h["date"], "%Y-%m-%d")
        namn = h["localName"]
        t = h.get("types", [""])[0]
        typ_label = TYPE_LABELS.get(t, t)
        desc = get_description(h, country_code, country_name)

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
            f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1].capitalize()} {d.year}",
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
        pdf.cell(0, 7, f"Veckodag: {DAYS[d.weekday()]}")
        if h.get("global", True) and t == "Public":
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
    pdf.cell(0, 8, f"Helgdagar i {country_name} \u2013 {year}", align="C")

    if output_path is None:
        return pdf.output()
    pdf.output(output_path)
    return pdf.page_no()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generera PDF med helgdagar")
    parser.add_argument(
        "country", nargs="?", default="SE", help="Landskod (t.ex. SE, NO, DK, FI)"
    )
    parser.add_argument(
        "year", nargs="?", type=int, default=2026, help="År (1900\u20132100)"
    )
    parser.add_argument("-o", "--output", help="Sökväg för PDF-fil")
    args = parser.parse_args()
    out = args.output or f"helgdagar_{args.country}_{args.year}.pdf"
    try:
        pages = generate_pdf(args.country, args.year, out)
        print(f"PDF skapad: {out} ({pages} sidor)")
    except Exception as e:
        print(f"Fel: {e}", file=sys.stderr)
        sys.exit(1)
