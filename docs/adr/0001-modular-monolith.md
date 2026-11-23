# ADR-001 – Modularer Monolith für das Backend

Entscheidung vom 22.11.2026 · Überarbeitet am 23.11.2026 · Status: **Entschieden**

## Ausgangslage

Wir arbeiten zu zweit an einem lokalen MVP bis zum 09.12.2026. Anmeldung, Import, Profile und Empfehlungen gehören zu einem gemeinsamen Ablauf. Beim Löschen eines Kontos müssen auch laufende Imports berücksichtigt werden. Unabhängige Skalierung ist bisher keine Anforderung.

## Welche Möglichkeiten gibt es?

1. **Modularer Monolith:** Eine FastAPI-Anwendung mit getrennten Modulen und einer PostgreSQL-Datenbank. Die Module rufen sich direkt auf.
2. **Getrennte Dienste:** Eigene Dienste für Anmeldung/Bibliothek, Import und Empfehlungen, verbunden über APIs beziehungsweise Nachrichten.

## Unsere Entscheidung

Wir wählen den modularen Monolithen. Diese Wahl wurde im Architekturgespräch nach dem AI-gestützten Vergleich bestätigt. Weniger Infrastruktur und gemeinsame DB-Transaktionen helfen uns, den vollständigen Ablauf rechtzeitig umzusetzen.

Auth, Bibliothek, Import, Metadaten und Empfehlungen bleiben trotzdem getrennte Module. Die Rechenlogik darf keine direkten Anbieteraufrufe auslösen. Den Vergleich mit konkreten Import- und Löschbeispielen enthält [architecture.md, Abschnitt 2](../architecture.md#2-zwei-architekturvarianten).

## Was gewinnen und verlieren wir?

- Ein Backend ist leichter zu starten und zu untersuchen; wir brauchen keinen Broker.
- Module und Adapter können getrennt getestet werden.
- Ein Fehler kann die gesamte API treffen. Lange Imports dürfen die interaktiven Aufrufe nicht blockieren.
- Einzelne Module lassen sich nicht unabhängig deployen oder skalieren.

## AI-Vorschlag kritisch bewertet

Die AI empfahl den Monolithen wegen Teamgröße und Zeitrahmen. Wir behalten den Vorschlag, berücksichtigen aber den gemeinsamen Prozess als möglichen Engpass: Importarbeit wird begrenzt und die Leistung später gegen N-01/N-02 geprüft. Die einfachere Struktur allein beweist noch keine ausreichende Leistung.

Wenn Messungen einen Engpass zeigen oder unabhängiger Betrieb nötig wird, prüfen wir zuerst einen separaten Import-Worker.
