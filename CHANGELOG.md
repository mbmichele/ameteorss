# Changelog

Tutte le modifiche rilevanti al progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.0.0/) e il
progetto adotta il [Semantic Versioning](https://semver.org/lang/it/)
(MAJOR.MINOR.PATCH).

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
