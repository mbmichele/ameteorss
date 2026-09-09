# Changelog

Tutte le modifiche rilevanti al progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.0.0/) e il
progetto adotta il [Semantic Versioning](https://semver.org/lang/it/)
(MAJOR.MINOR.PATCH).

## [1.7.0]
### Modificato
- Il limite massimo di elementi nel feed è stato ridotto da 50 a 20.

## [1.6.2]
### Corretto
- **Bug**: la Action falliva con `! [rejected] main -> main (fetch first)`
  quando due esecuzioni partivano quasi in contemporanea (es. due trigger
  ravvicinati da cron-job.org). Aggiunta `concurrency` al workflow per
  accodare le esecuzioni sovrapposte invece di farle girare in parallelo,
  più un retry con `git pull --rebase` come rete di sicurezza.

## [1.6.1]
### Modificato
- Selezione dell'immagine più precisa: ora preferisce l'`alt` contenente
  "mappa" o un nome file tipico di una mappa (mappa/tend/agg o un pattern
  data), per evitare di prendere per sbaglio un logo o l'avatar del
  previsore invece della mappa reale della previsione presente sulla
  pagina linkata.

## [1.6.0]
### Corretto
- **Bug**: il titolo dell'item risultava sempre la sola parola "Previsione"
  (presa da un elemento di navigazione generico della pagina, non
  dall'intestazione reale). Ora viene cercata la riga di testo che contiene
  sia la parola chiave (Previsione/Tendenza) sia un anno a 4 cifre, che è
  sempre l'intestazione vera (es. "Tendenza per il 9 settembre 2026").
  Rimosso l'uso di `og:title`/`<title>`, generici su tutto il sito.

## [1.5.1]
### Modificato
- Rinominato il progetto in "ameteorss" per allinearlo al nome reale del
  repository GitHub (`mbmichele/ameteorss`). Aggiornati README e generator
  tag del feed di conseguenza.

## [1.5.0]
### Modificato
- Rimosso lo `schedule` interno di GitHub Actions: la Action viene ora
  avviata ogni ora da un cron esterno (cron-job.org) tramite chiamata API
  a `workflow_dispatch`, per evitare esecuzioni doppie.

## [1.4.1]
### Modificato
- Il titolo dell'item RSS ora corrisponde al titolo reale della pagina
  linkata (`og:title`, poi tag `<title>` come ripiego), invece di essere
  ricostruito dal testo della pagina.

## [1.4.0]
### Aggiunto
- Versioning del progetto: costante `__version__` in `scraper.py`, flag
  `--version` da riga di comando, numero di versione riportato nel tag
  `<generator>` del feed.

## [1.3.0]
### Modificato
- La descrizione di ogni item è ora limitata a 25 parole, con link
  "Continua a leggere su pretemp.it →" verso la pagina originale per il
  testo completo.

## [1.2.0]
### Aggiunto
- Ordinamento esplicito degli item per data di pubblicazione decrescente:
  il primo elemento del feed è sempre garantito essere l'ultima previsione
  pubblicata, anche se l'ordine dell'archivio dovesse cambiare.
### Modificato
- Il feed è limitato a un massimo di 50 elementi; lo scraper scorre più
  pagine dell'archivio se necessario per raggiungerne 50.

## [1.1.0]
### Aggiunto
- Campo `<pubDate>` per ogni item, calcolato dalla data/ora di aggiornamento
  riportata nella pagina di dettaglio originale (fuso orario Europe/Rome),
  invece dell'orario in cui viene eseguito lo scraper.

## [1.0.1]
### Aggiunto
- Tag `<enclosure>` con il link diretto all'immagine della mappa di
  previsione, oltre a quella già incorporata nella descrizione.

## [1.0.0]
### Aggiunto
- Prima versione funzionante: scraping dell'archivio previsioni PRETEMP
  (`/archivio/<anno>`) e delle relative pagine di dettaglio
  (`/previsioni/<id>`), generazione di un feed RSS 2.0 in `docs/rss.xml`.
- GitHub Action programmata per rigenerare il feed periodicamente e
  pubblicarlo tramite GitHub Pages.
