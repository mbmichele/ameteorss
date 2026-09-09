# ameteorss

Feed RSS **non ufficiale** delle previsioni PRETEMP (pretemp.it), generato via scraping
del loro archivio pubblico, perché PRETEMP non pubblica un feed proprio.

Il feed viene ricontrollato e rigenerato **ogni ora**, tramite un cron esterno
(cron-job.org) che chiama l'API di GitHub per avviare la Action — non tramite
lo schedule interno di GitHub Actions (rimosso per evitare esecuzioni doppie).

⚠️ **Disclaimer**: PRETEMP non emette allerte, ma previsioni probabilistiche
sperimentali. Per l'allertamento ufficiale fare sempre riferimento al
Dipartimento di Protezione Civile Nazionale. Questo è un progetto amatoriale/civico,
non affiliato a PRETEMP: se usato in un bot pubblico, cita sempre la fonte
e valuta di linkare il sito originale.

## Come funziona

- `scraper.py` legge `https://www.pretemp.it/archivio/<anno>`, prende le previsioni
  più recenti e per ciascuna scarica la pagina di dettaglio (`/previsioni/<id>`),
  estraendo titolo, livello di pericolosità, previsore, testo breve e mappa.
- Genera un file RSS 2.0 in `docs/rss.xml`, con **massimo 20 elementi**. Se serve
  più di una pagina di archivio per raggiungerli, lo script le scorre in automatico.
- La `<pubDate>` di ogni elemento è quella di aggiornamento/pubblicazione riportata
  nella pagina originale (non l'orario in cui gira lo scraper), convertita nel
  fuso orario Europe/Rome.
- Una GitHub Action (`.github/workflows/build-feed.yml`) rigenera il file e lo
  committa nel repo ogni volta che viene avviata via API (`workflow_dispatch`)
  da un cron esterno su cron-job.org, impostato per chiamarla ogni ora.
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
   https://mbmichele.github.io/ameteorss/rss.xml
   ```

4. Incolla quell'URL in qualsiasi lettore RSS, o usalo nel tuo bot Telegram
   civico per rilanciare gli aggiornamenti (es. con `feedparser` in Python).
5. Configura il cron esterno seguendo la sezione qui sotto, altrimenti la
   Action non partirà mai da sola (lo schedule interno di GitHub è stato
   rimosso apposta).

## Impostare il cron esterno (cron-job.org)

Il workflow ha solo il trigger `workflow_dispatch`, quindi va avviato ogni
ora dall'esterno tramite una chiamata all'API di GitHub.

### 1. Crea un Personal Access Token

GitHub → icona profilo → **Settings → Developer settings → Personal access
tokens → Fine-grained tokens → Generate new token**.
- Repository access: "Only select repositories" → `ameteorss`
- Permissions → "Actions" → "Read and write"
- Genera e copia subito il token (non sarà più visibile dopo).

### 2. Crea un account su cron-job.org

Vai su [cron-job.org](https://cron-job.org) → "Sign up" (gratuito).

### 3. Crea il cronjob

Dashboard → **"Create cronjob"**.

- **Title**: `ameteorss hourly trigger`
- **Address (URL)**:
  ```
  https://api.github.com/repos/mbmichele/ameteorss/actions/workflows/build-feed.yml/dispatches
  ```

### 4. Schedule

Scegli **"Every hour"**, minuto `0` (oppure "Custom" → `0 * * * *`).

### 5. Impostazioni avanzate ("Advanced")

- **Request method**: `POST`
- **Request headers**:
  ```
  Accept: application/vnd.github+json
  Authorization: Bearer IL-TUO-PERSONAL-ACCESS-TOKEN
  X-GitHub-Api-Version: 2022-11-28
  ```
- **Request body**:
  ```json
  {"ref":"main"}
  ```

### 6. Salva e testa

"Create cronjob" / "Save", poi usa il pulsante "Run now" per testare subito
senza aspettare l'ora piena. Controlla nella tab **Actions** del repo GitHub
che sia partita una nuova esecuzione, e nello storico di cron-job.org che lo
status HTTP sia `204` (= successo per l'API dispatch di GitHub).

⚠️ Il token inserito nell'header `Authorization` resta salvato sui server di
cron-job.org per poter fare la richiesta. Il rischio è limitato dato lo scope
ridotto (solo "Actions: write" su un solo repo pubblico), ma è bene saperlo.

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

## Versionamento

Il progetto segue il [Semantic Versioning](https://semver.org/lang/it/)
(`MAJOR.MINOR.PATCH`). La versione corrente è definita nella costante
`__version__` in cima a `scraper.py` ed è riportata anche nel tag
`<generator>` di ogni feed generato. La cronologia delle modifiche è in
[`CHANGELOG.md`](CHANGELOG.md).

Per rilasciare una nuova versione in futuro:

1. Aggiorna `__version__` in `scraper.py`.
2. Aggiungi una nuova sezione in cima a `CHANGELOG.md` con le modifiche.
3. Fai commit e push, poi crea un tag Git e una Release su GitHub:

   ```bash
   git add scraper.py CHANGELOG.md
   git commit -m "Rilascio v1.5.0"
   git tag v1.5.0
   git push origin main --tags
   ```

   Su GitHub, vai su "Releases" → "Draft a new release", scegli il tag
   appena creato e descrivi le novità: resta uno storico consultabile anche
   da chi non legge il CHANGELOG.

## Licenza dei contenuti

I testi delle previsioni restano di proprietà di PRETEMP (molte pagine sono
distribuite con licenza Creative Commons Attribuzione 4.0 Internazionale, come
indicato nelle singole pagine). Questo repository distribuisce solo il codice
dello scraper, non i contenuti.
