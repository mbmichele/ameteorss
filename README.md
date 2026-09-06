# maltempo-rss

Feed RSS **non ufficiale** delle previsioni PRETEMP (pretemp.it), generato via scraping
del loro archivio pubblico, perché PRETEMP non pubblica un feed proprio.

Il feed viene ricontrollato e rigenerato **ogni ora** tramite GitHub Actions.

⚠️ **Disclaimer**: PRETEMP non emette allerte, ma previsioni probabilistiche
sperimentali. Per l'allertamento ufficiale fare sempre riferimento al
Dipartimento di Protezione Civile Nazionale. Questo è un progetto amatoriale/civico,
non affiliato a PRETEMP: se usato in un bot pubblico, cita sempre la fonte
e valuta di linkare il sito originale.

## Come funziona

- `scraper.py` legge `https://www.pretemp.it/archivio/<anno>`, prende le previsioni
  più recenti e per ciascuna scarica la pagina di dettaglio (`/previsioni/<id>`),
  estraendo titolo, livello di pericolosità, previsore, testo breve e mappa.
- Genera un file RSS 2.0 in `docs/rss.xml`, con **massimo 50 elementi**. Se serve
  più di una pagina di archivio per raggiungerli, lo script le scorre in automatico.
- La `<pubDate>` di ogni elemento è quella di aggiornamento/pubblicazione riportata
  nella pagina originale (non l'orario in cui gira lo scraper), convertita nel
  fuso orario Europe/Rome.
- Una GitHub Action (`.github/workflows/build-feed.yml`) rigenera il file ogni
  ora e lo committa nel repo.
- Con GitHub Pages abilitato sulla cartella `docs/`, il feed diventa
  pubblicamente accessibile a un URL fisso.

## Setup (5 minuti)

1. Crea un nuovo repository GitHub (pubblico) e carica questi file.
2. Vai su **Settings → Pages** del repository:
   - Source: `Deploy from a branch`
   - Branch: `main`, cartella `/docs`
   - Salva.
3. Dopo il primo giro della Action (o eseguila subito da **Actions → Aggiorna
   feed RSS PRETEMP → Run workflow**), il feed sarà disponibile su:

   ```
   https://<tuo-utente>.github.io/maltempo-rss/rss.xml
   ```

4. Incolla quell'URL in qualsiasi lettore RSS, o usalo nel tuo bot Telegram
   civico per rilanciare gli aggiornamenti (es. con `feedparser` in Python).

## Uso locale

```bash
pip install -r requirements.txt
python scraper.py --year 2026 --limit 15 --output docs/rss.xml
```

## Manutenzione

Lo scraping si basa su pattern di testo visibili nella pagina (es. "Previsore:",
"Aggiornato il", "TESTO BREVE") invece che su classi CSS, per essere un po' più
resistente a piccoli redesign del sito. Se PRETEMP cambia sostanzialmente il
sito e il feed smette di popolarsi, aggiorna le funzioni `parse_archive_listing`
e `parse_forecast_detail` in `scraper.py` guardando il markup aggiornato.

## Licenza dei contenuti

I testi delle previsioni restano di proprietà di PRETEMP (molte pagine sono
distribuite con licenza Creative Commons Attribuzione 4.0 Internazionale, come
indicato nelle singole pagine). Questo repository distribuisce solo il codice
dello scraper, non i contenuti.
