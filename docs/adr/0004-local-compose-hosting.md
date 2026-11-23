# ADR-004 – Lokal mit Docker Compose, öffentlich über Cloudflare

Entscheidung vom 22.11.2026 · Überarbeitet am 23.11.2026 · Status: **Entschieden**

## Ausgangslage

Der MVP soll lokal laufen und keine zusätzlichen laufenden Dienstkosten verursachen. Persönliche Daten bleiben laut N-04 lokal. Beide Teammitglieder sollen denselben Aufbau starten können. Live-Funktionen brauchen Internet, die getrennte Demo nicht.

## Welche Möglichkeiten gibt es?

1. Webserver, FastAPI und PostgreSQL mit Docker Compose starten.
2. Nur PostgreSQL im Container, Frontend und Backend nativ installieren.
3. Alles nativ installieren.
4. Für einen öffentlichen Betrieb Cloudflare Pages und Containers, Render oder einen selbst verwalteten VPS nutzen.

## Unsere Entscheidung

Wir wählen Option 1; das wurde im Architekturgespräch bestätigt. Nginx liefert das Vue-Build und leitet `/api/*` an FastAPI weiter. Nur `127.0.0.1:8080` ist am Host erreichbar. API und Datenbank bleiben intern, PostgreSQL nutzt ein persistentes lokales Volume.

Für den Browser läuft alles unter derselben Adresse. Das vereinfacht Cookie-Sitzungen und erspart separate Cross-Origin-Aufrufe. Login-Rückleitung und erlaubte Adresse müssen zur Konfiguration passen. Für native Vite-Entwicklung ist ein entsprechender API-Proxy möglich.

## Zielarchitektur für eine spätere Veröffentlichung

Cloudflare Pages liefert Vue und ein Worker leitet API-Anfragen derselben Domain an FastAPI in Cloudflare Containers weiter. Neon stellt PostgreSQL in einer EU-Region bereit. So bleiben eine Browser-Adresse, reguläres Python mit Uvicorn und persistente Datenhaltung erhalten. Cloudflare übernimmt den Betrieb von Frontend, Routing und Container. Neon übernimmt den Datenbankbetrieb. Der [Hostingplan](../hosting.md#6-cloudflare-bereitstellungsplan) dokumentiert Kosten, Bereitstellung und Freigabebedingungen.

## Was gewinnen und verlieren wir?

- Einheitlicher Start und weniger Unterschiede zwischen unseren Rechnern.
- Daten bleiben bei normalen Containerneustarts erhalten.
- Docker und Virtualisierung müssen lokal funktionieren; Compose ist noch einzurichten und auf beiden Rechnern zu testen.
- Ohne laufenden Rechner keine Erreichbarkeit. Ein Volume ist keine Absicherung gegen Datenträgerverlust.
- Lokales HTTP verwendet sichere Sitzungsregeln mit der Ausnahme `Secure=false` auf Loopback. Bei späterem HTTPS muss `Secure=true` gesetzt werden.

## AI-Vorschlag kritisch bewertet

Die AI schlug Compose als gemeinsamen Start vor. Das spart Einrichtung pro Dienst, bringt aber eine zusätzliche lokale Laufzeit mit. Wir nehmen diesen Aufwand in Kauf, damit die Referenzumgebung für beide gleich ist.

Python Workers wurden als günstigere Cloudflare-Variante geprüft. Für den geplanten Produktivbetrieb passen Containers besser zum vorhandenen FastAPI-Entwurf und zur Importverarbeitung in einem normalen Python-Prozess. Der Container kann bei Leerlauf schlafen, daher muss die Behandlung unterbrochener Imports beim Neustart getestet werden. Die Veröffentlichung setzt eine Freigabe für Budget und gehostete personenbezogene Daten voraus.
