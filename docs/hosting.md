# QuestQueue – Hostingvergleich

Stand: 23.11.2026 · Phase 2

**Die Hochschulabgabe läuft lokal mit Docker Compose und 0 € zusätzlichen Dienstkosten.** Für einen späteren öffentlichen Betrieb ist **Cloudflare Pages und Cloudflare Containers mit Neon PostgreSQL** die vorgesehene Zielarchitektur. Die Entscheidung steht in [ADR-004](adr/0004-local-compose-hosting.md).

## 1. Was wir vergleichen

Zum Hosting gehören Frontend, Python-Backend und PostgreSQL. Ein kostenloses statisches Frontend allein reicht also nicht. Wir berücksichtigen Kosten, Datenspeicherung, Erreichbarkeit und den Aufwand für uns als Zweierteam.

Die 0 € beziehen sich auf zusätzliche Dienste. Vorhandener Rechner, Internet, Strom und unsere Arbeitszeit sind nicht eingerechnet. Live-Login und API-Import brauchen auch beim lokalen Betrieb Internet; nur die getrennte Demo funktioniert offline.

## 2. Möglichkeiten und Kosten

| Möglichkeit | Preisbasis | Vorteile | Nachteile für QuestQueue |
| --- | --- | --- | --- |
| **A: Eigener Rechner – Hochschulabgabe** | **0 € zusätzliche Dienstkosten** | Passt zu den Anforderungen; Compose bündelt Webserver, Backend und DB; lokale Demo möglich | Rechner muss laufen; Einrichtung und Updates bleiben bei uns; lokaler Datenträger kann ausfallen |
| **Cloudflare Pages + Containers + Neon – öffentlicher Betrieb** | **ab 5 US-$/Monat** bei geringem Verbrauch und Neon Free | Vue-Build, reguläres FastAPI mit Uvicorn und verwaltetes PostgreSQL | Mehrkosten bei überschrittenen Kontingenten, möglicher Kaltstart und gehostete personenbezogene Daten |
| **B: EU-VPS, z. B. Hetzner** | CX23: recherchierter Tarif von **5,49 €/Monat netto ohne IPv4**; aktuell nicht verfügbar | Compose-Konzept gut übertragbar; volle Kontrolle über alle Dienste | Serverpflege, TLS, Backups und Überwachung selbst übernehmen; Zusatzkosten und anderer Datenstandort |
| **C: Render Free** | **0 US-$ innerhalb der Free-Limits** | Einfacher Einstieg für einen zeitlich begrenzten Test | Webservice schläft nach 15 Minuten; Start dauert etwa eine Minute; kostenlose DB läuft nach 30 Tagen ab |
| **D: Render Paid** | Anbieterbeispiel vom **Juli 2026: etwa 13 US-$/Monat für Web + DB**, zuzüglich möglichem Mehrverbrauch | Weniger Serveradministration, verwaltete Datenbank | Laufende Gebühren, Anbieterbindung und externe persönliche Daten; aktueller Gesamttarif muss geprüft werden |

Quellen: [Hetzner-Preistabelle](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [Hetzner-Verfügbarkeit](https://www.hetzner.com/cloud/cost-optimized/), [Render Free](https://render.com/docs/free), [Render-Kostenbeispiel](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).

**Einordnung der Preise:** Die Hetzner-Tabelle war über den offiziellen Suchindex lesbar, der direkte Abruf lieferte 404. Die Produktseite nennt den CX23 derzeit nicht verfügbar. Der Betrag ist deshalb ein Tarifbeispiel, kein gerade buchbares Angebot. Die 13 US-$ bei Render sind ausdrücklich ein älteres Anbieterbeispiel, kein bestätigter November-Tarif. Vor einer Bestellung müssten wir den [Hetzner-Kalkulator](https://www.hetzner.com/cloud/) beziehungsweise die [Render-Preisliste](https://render.com/pricing) prüfen. Leistung und tatsächliche Rechnungen haben wir bei keinem Anbieter getestet.

## 3. Was noch auf die Rechnung kommen kann

Statische Anfragen an Cloudflare Pages sind kostenlos. Der Workers-Paid-Plan kostet mindestens 5 US-$/Monat und enthält für Containers 25 GiB-Stunden RAM, 375 vCPU-Minuten und 200 GB-Stunden Datenträger pro Monat. Bei laufendem Container zählen RAM und Datenträger nach bereitgestellter Größe, CPU nach aktiver Nutzung. Nach dem Einschlafen endet die laufzeitbezogene Abrechnung. Neon Free enthält 1 GB Speicher und 100 Compute-Unit-Stunden pro Projekt und Monat. 5 US-$ sind der Einstiegspreis bei passender Nutzung. Mehrverbrauch, ein späterer Datenbanktarif, Domain und Steuern kommen gegebenenfalls dazu. [Pages-Preise](https://developers.cloudflare.com/pages/functions/pricing/) · [Container-Preise](https://developers.cloudflare.com/containers/platform/pricing/) · [Neon-Preise](https://neon.com/pricing).

Beim VPS kommt zur VM gegebenenfalls eine öffentliche IPv4-Adresse, Backup-/Zusatzspeicher, Mehrtraffic, eine Domain und die anwendbare Steuer dazu. PostgreSQL läuft in dieser Variante auf derselben VM; eine zusätzlich gebuchte Managed-DB wäre ein weiterer Kostenpunkt.

Bei Render zählen Web-Compute, DB-Compute, Speicher und gegebenenfalls Mehrverbrauch bei Traffic und Builds. Der Anbieter nennt für DB-Speicher 0,30 US-$/GB im Monat. Ohne den genauen Tarif rechnen wir das ältere 13-US-$-Beispiel nicht zu einem scheinbar exakten Gesamtpreis hoch. Dollarpreise lassen wir ohne belegten Wechselkurs in Dollar. [Kostenmodell](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).

Render Free hat außerdem 750 Webservice-Stunden je Workspace/Monat und 1 GB DB-Speicher. Nach 30 Tagen ist die DB ohne Upgrade unzugänglich; nach weiteren 14 Tagen wird sie gelöscht. Free-DB-Backups gibt es nicht. Dateien im Webservice sind flüchtig und ersetzen keine persistente Datenbank. Überschrittene Nutzungslimits können Gebühren oder Sperren verursachen. [Offizielle Limits](https://render.com/docs/free).

Docker Desktop ist laut [Lizenzübersicht](https://docs.docker.com/subscription-billing/desktop-license/) für Bildung kostenlos; [Compose ist enthalten](https://docs.docker.com/compose/install/). Für unsere Live-Quellen gelten weiterhin die [Steam-API-Bedingungen](https://steamcommunity.com/dev/apiterms) und der [nichtkommerzielle IGDB-Zugang](https://api-docs.igdb.com/#account-creation). Erste Steam-/IGDB-Zugriffe sind durch die [API-Probe vom 23.11.2026](integration-spike.md) belegt; die Anwendungsintegration steht noch aus.

## 4. Unsere Entscheidung

Compose erfüllt das Dienstbudget und die lokale Speicherung nach N-04 für die Hochschulabgabe. Die öffentliche Zielarchitektur setzt eine eigene Freigabe für gehostete personenbezogene Daten und laufende Kosten voraus.

Cloudflare Containers erhält den FastAPI-Monolithen samt Uvicorn und den üblichen Python-Abhängigkeiten. Gegenüber einem VPS fällt weniger Serverpflege an. Python Workers unterstützen FastAPI im eigenen Runtime-Modell. Für QuestQueue müssten dabei insbesondere Bibliothekskompatibilität, Steam-Import und Hintergrundverarbeitung neu geprüft werden. [Python-Pakete in Workers](https://developers.cloudflare.com/workers/languages/python/packages/) · [Container-Bereitstellung](https://developers.cloudflare.com/containers/guides/deploy/).

## 5. Geplanter lokaler Start

```text
Browser → localhost:8080 → web (Nginx: Frontend + /api-Proxy)
                            └→ api:8000 (FastAPI, ein Worker)
                                 └→ db:5432 (PostgreSQL, lokales Volume)
```

Nur `web` veröffentlicht einen Port auf Loopback. API und DB bleiben im Compose-Netz. Das DB-Volume bleibt beim normalen Stoppen erhalten; sein Löschen würde alle Konten und den Katalog entfernen und ersetzt nicht die kontobezogene Löschfunktion.

Backend-Schlüssel stehen lokal in `.env`, nicht im Frontend oder Repository. Basis-URL und tatsächliches Speicherland werden konfiguriert. Vor API-Bereitschaft müssen Datenbank und Migrationen bereit sein; ein einfacher Startreihenfolge-Eintrag reicht dafür nicht.

In Phase 3 entstehen die Compose-Datei und Startanleitung. Anschließend prüfen wir Start auf beiden Rechnern, Persistenz nach Neustart, Kontolöschung und Offline-Demo.

## 6. Cloudflare-Bereitstellungsplan

| Baustein | Geplante Bereitstellung |
| --- | --- |
| Vue + TypeScript | Das Frontend aus dem Repository bauen und `dist/` über Cloudflare Pages auf einer eigenen HTTPS-Domain ausliefern. Das Frontend verwendet relative `/api/`-URLs. |
| Routing und FastAPI | Auf der von Cloudflare verwalteten Proxied-Domain das Muster `/api/*` einem Worker zuordnen. Er leitet den Pfad an FastAPI in Cloudflare Containers weiter. Das Docker-Image startet Uvicorn. |
| PostgreSQL | Neon in einer EU-Region, geplant in Frankfurt. Das Backend verbindet sich über TLS. Anwendung, Sitzungen, Importstatus und Metadaten-Cache verwenden die Datenbank. Die Migrationen laufen vor der Freigabe. |
| Konfiguration | Steam-API-Key, Twitch-/IGDB-Zugangsdaten und DB-Zugangsdaten serverseitig als Cloudflare-Secrets hinterlegen und gezielt an den Container weitergeben. Öffentliche Basis-URL, Steam-OpenID-Realm und Callback auf die HTTPS-Domain konfigurieren. |

[Vue auf Pages](https://developers.cloudflare.com/pages/framework-guides/deploy-a-vue-site/) · [Worker-Routen](https://developers.cloudflare.com/workers/configuration/routing/routes/) · [Container-Secrets](https://developers.cloudflare.com/containers/examples/env-vars-and-secrets/) · [Neon-Regionen](https://neon.com/docs/introduction/regions).

**Vor einer Veröffentlichung**

1. Datenhinweis und Löschkonzept für gehostete Daten, Speicherregion und Backups freigeben. Für eine kommerzielle Veröffentlichung den IGDB-Zugang vorab klären. [IGDB-Zugangsbedingungen](https://api-docs.igdb.com/#account-creation).
2. Steam-Login, CSRF-Schutz und Cookies mit `Secure`, `HttpOnly` und `SameSite=Lax` auf der öffentlichen Domain prüfen. Persönliche API-Antworten mit `Cache-Control: no-store` ausliefern und vom Cloudflare-Cache ausnehmen. Nur die statischen Frontenddateien werden über Pages gecacht.
3. Leerlauf-Timeout und Instanzgröße mit einem größeren Steam-Import testen. Bei Neustart muss der gespeicherte Importstatus einen abgebrochenen Lauf erkennbar machen und den letzten gültigen Bibliotheksstand erhalten. Für Backups einen Wiederherstellungstest vorsehen.

Der Plan beschreibt eine mögliche spätere Bereitstellung. Die Semesterabgabe und ihre Abnahme erfolgen lokal.
