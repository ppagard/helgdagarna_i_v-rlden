# Helgdagar

Bläddra bland helgdagar för olika länder och år.

## Webbplats (`index.html`)

En fristående HTML-sida som hämtar helgdagsdata från [Nager.Date API](https://date.nager.at) (gratis, ingen API-nyckel krävs).

- **122 länder** – från Sverige till Zimbabwe
- **Rörliga helgdagar** – påsk, pingst, Kristi himmelsfärd m.fl. beräknas automatiskt för valt år
- **Dedupiering** – samma datum visas bara en gång (prioritet: Public > Bank > Optional > School > Observance)
- **År: 1900–2100**
- **Mörkt tema** – responsiv design, fungerar på mobil och desktop

### Användning

Öppna `index.html` i valfri webbläsare. Välj land och år – helgdagarna laddas direkt.

## PDF (`helgdagar_sverige_2026.pdf`)

En snyggt formaterad PDF med alla 16 helgdagar för Sverige 2026:

- Omslag med titel
- Innehållsförteckning
- En sida per helgdag med datum, veckodag, typ och utförlig beskrivning

### Generera om PDF

PDF:en är skapad med Python och `fpdf2`. För att generera om för ett annat år:

```bash
# Installera beroenden
pip install fpdf2

# Ändra år i skriptet och kör
python3 generate_pdf.py
```

## API

Data från [Nager.Date](https://date.nager.at) – öppen källa för allmänna helgdagar globalt.

```
GET https://date.nager.at/api/v3/AvailableCountries
GET https://date.nager.at/api/v3/PublicHolidays/{år}/{landkod}
```

## Licens

MIT
