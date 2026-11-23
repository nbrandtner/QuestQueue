# QuestQueue – Hostingvergleich

Stand: 23.11.2026 · Phase 2

**Für den MVP bleiben wir beim lokalen Betrieb mit Docker Compose.** Das passt zum 0-€-Budget für zusätzliche Dienste und zu unserer Vorgabe, persönliche Daten lokal zu speichern. Hier vergleichen wir trotzdem Alternativen für einen möglichen späteren Ausbau. Die Entscheidung steht in [ADR-004](adr/0004-local-compose-hosting.md).

## 1. Was wir vergleichen

Zum Hosting gehören Frontend, Python-Backend und PostgreSQL. Ein kostenloses statisches Frontend allein reicht also nicht. Wir berücksichtigen Kosten, Datenspeicherung, Erreichbarkeit und den Aufwand für uns als Zweierteam.

Die 0 € beziehen sich auf zusätzliche Dienste. Vorhandener Rechner, Internet, Strom und unsere Arbeitszeit sind nicht eingerechnet. Live-Login und API-Import brauchen auch beim lokalen Betrieb Internet; nur die getrennte Demo funktioniert offline.

## 2. Möglichkeiten und Kosten

| Möglichkeit | Preisbasis | Vorteile | Nachteile für QuestQueue |
| --- | --- | --- | --- |
| **A: Eigener Rechner – gewählt** | **0 € zusätzliche Dienstkosten** | Passt zu den Anforderungen; Compose bündelt Webserver, Backend und DB; lokale Demo möglich | Rechner muss laufen; Einrichtung und Updates bleiben bei uns; lokaler Datenträger kann ausfallen |
| **B: EU-VPS, z. B. Hetzner** | CX23: recherchierter Tarif von **5,49 €/Monat netto ohne IPv4**; aktuell nicht verfügbar | Compose-Konzept gut übertragbar; volle Kontrolle über alle Dienste | Serverpflege, TLS, Backups und Überwachung selbst übernehmen; Zusatzkosten und anderer Datenstandort |
| **C: Render Free** | **0 US-$ innerhalb der Free-Limits** | Einfacher Einstieg für einen zeitlich begrenzten Test | Webservice schläft nach 15 Minuten; Start dauert etwa eine Minute; kostenlose DB läuft nach 30 Tagen ab |
| **D: Render Paid** | Anbieterbeispiel vom **Juli 2026: etwa 13 US-$/Monat für Web + DB**, zuzüglich möglichem Mehrverbrauch | Weniger Serveradministration, verwaltete Datenbank | Laufende Gebühren, Anbieterbindung und externe persönliche Daten; aktueller Gesamttarif muss geprüft werden |

Quellen: [Hetzner-Preistabelle](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [Hetzner-Verfügbarkeit](https://www.hetzner.com/cloud/cost-optimized/), [Render Free](https://render.com/docs/free), [Render-Kostenbeispiel](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).

**Einordnung der Preise:** Die Hetzner-Tabelle war über den offiziellen Suchindex lesbar, der direkte Abruf lieferte 404. Die Produktseite nennt den CX23 derzeit nicht verfügbar. Der Betrag ist deshalb ein Tarifbeispiel, kein gerade buchbares Angebot. Die 13 US-$ bei Render sind ausdrücklich ein älteres Anbieterbeispiel, kein bestätigter November-Tarif. Vor einer Bestellung müssten wir den [Hetzner-Kalkulator](https://www.hetzner.com/cloud/) beziehungsweise die [Render-Preisliste](https://render.com/pricing) prüfen. Leistung und tatsächliche Rechnungen haben wir bei keinem Anbieter getestet.

## 3. Was noch auf die Rechnung kommen kann

Beim VPS kommt zur VM gegebenenfalls eine öffentliche IPv4-Adresse, Backup-/Zusatzspeicher, Mehrtraffic, eine Domain und die anwendbare Steuer dazu. PostgreSQL läuft in dieser Variante auf derselben VM; eine zusätzlich gebuchte Managed-DB wäre ein weiterer Kostenpunkt.

Bei Render zählen Web-Compute, DB-Compute, Speicher und gegebenenfalls Mehrverbrauch bei Traffic und Builds. Der Anbieter nennt für DB-Speicher 0,30 US-$/GB im Monat. Ohne den genauen Tarif rechnen wir das ältere 13-US-$-Beispiel nicht zu einem scheinbar exakten Gesamtpreis hoch. Dollarpreise lassen wir ohne belegten Wechselkurs in Dollar. [Kostenmodell](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).

Render Free hat außerdem 750 Webservice-Stunden je Workspace/Monat und 1 GB DB-Speicher. Nach 30 Tagen ist die DB ohne Upgrade unzugänglich; nach weiteren 14 Tagen wird sie gelöscht. Free-DB-Backups gibt es nicht. Dateien im Webservice sind flüchtig und ersetzen keine persistente Datenbank. Überschrittene Nutzungslimits können Gebühren oder Sperren verursachen. [Offizielle Limits](https://render.com/docs/free).

Docker Desktop ist laut [Lizenzübersicht](https://docs.docker.com/subscription-billing/desktop-license/) für Bildung kostenlos; [Compose ist enthalten](https://docs.docker.com/compose/install/). Für unsere Live-Quellen gelten weiterhin die [Steam-API-Bedingungen](https://steamcommunity.com/dev/apiterms) und der [nichtkommerzielle IGDB-Zugang](https://api-docs.igdb.com/#account-creation). Erste Steam-/IGDB-Zugriffe sind durch die [API-Probe vom 23.11.2026](integration-spike.md) belegt; die Anwendungsintegration steht noch aus.

## 4. Unsere Entscheidung

A erfüllt den aktuellen Rahmen am besten. Ein günstiger VPS oder PaaS würde nicht nur Geld kosten: Persönliche Daten lägen dann außerhalb des lokalen Rechners, was N-04 widerspricht und eine geänderte Anforderung braucht.

Bei späterem öffentlichen Betrieb wäre ein VPS interessant, wenn wir die Administration übernehmen möchten. Ein bezahltes PaaS passt eher, wenn uns weniger Serverpflege wichtiger ist als der niedrigste Preis. Render Free eignet sich für einen kurzen Test mit verzichtbaren Daten, nicht als dauerhafter Bestand. Eine bestehende Compose-Datei lässt sich auf PaaS außerdem nicht automatisch unverändert starten; Dienste und gemeinsamer Browser-Zugang müssten angepasst werden.

## 5. Geplanter lokaler Start

```text
Browser → localhost:8080 → web (Nginx: Frontend + /api-Proxy)
                            └→ api:8000 (FastAPI, ein Worker)
                                 └→ db:5432 (PostgreSQL, lokales Volume)
```

Nur `web` veröffentlicht einen Port auf Loopback. API und DB bleiben im Compose-Netz. Das DB-Volume bleibt beim normalen Stoppen erhalten; sein Löschen würde alle Konten und den Katalog entfernen und ersetzt nicht die kontobezogene Löschfunktion.

Backend-Schlüssel stehen lokal in `.env`, nicht im Frontend oder Repository. Basis-URL und tatsächliches Speicherland werden konfiguriert. Vor API-Bereitschaft müssen Datenbank und Migrationen bereit sein; ein einfacher Startreihenfolge-Eintrag reicht dafür nicht.

In Phase 3 entstehen die Compose-Datei und Startanleitung. Anschließend prüfen wir Start auf beiden Rechnern, Persistenz nach Neustart, Kontolöschung und Offline-Demo.

## 6. Falls wir später veröffentlichen

Dann müssten wir Budget und Datenstandort neu festlegen und unter anderem HTTPS, sichere Cookies, Login-Rückleitung, Secrets und Backups einplanen. Erst mit einem aktuellen Gesamttarif und klaren Zuständigkeiten wäre die Wahl zwischen VPS und PaaS sinnvoll.
