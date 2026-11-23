# ADR-003 – Import in zwei Schritten ohne zusätzlichen Broker

Entwurf vom 22.11.2026 · Überarbeitet am 23.11.2026 · Status: **Für die Umsetzung vorgesehen**

## Ausgangslage

N-02 verlangt innerhalb von 30 Sekunden einen erfolgreichen Steam-Import, ein nutzbares Teilergebnis oder einen erklärten Abbruch. Die Suche nach Genres kann länger dauern. API-Fehler dürfen den letzten gültigen Bestand nicht zerstören. Nach Logout oder Löschung darf ein alter Import nichts Persönliches mehr speichern.

## Welche Möglichkeiten gibt es?

1. Steam und IGDB vollständig innerhalb einer HTTP-Anfrage abarbeiten.
2. Einen Job mit `202 Accepted` starten und im Backend bearbeiten; Steam und Metadaten trennen.
3. Einen eigenen Worker mit Nachrichtenwarteschlange und Wiederanlauf betreiben.

## Unsere Entscheidung

Wir planen Option 2. Der Steam-Teil hat insgesamt 30 Sekunden ab Annahme des Auftrags. Gültige Bibliotheksdaten und ihr Status werden gemeinsam gespeichert. Danach folgt die Metadatenphase mit sichtbarem Fortschritt; vorhandene Genres können schon vorher verwendet werden.

Je Konto läuft höchstens ein Job, mit mindestens 60 Sekunden zwischen Starts. Insgesamt sind zwei aktive Tasks erlaubt; weitere Starts erhalten vor Jobanlage `503 IMPORT_CAPACITY`. IGDB-Aufrufe erfolgen nacheinander mit mindestens einer Sekunde zwischen Starts.

Vor persönlichem Speichern und weiteren Anbieteraufrufen wird die Sitzung erneut geprüft. Nach 429 speichern wir die Sperre; später ist ein bewusster neuer Start nötig. Ein API-Neustart beendet offene Jobs mit `interrupted`, ohne automatischen Wiederanlauf. `metadata_only` erneuert nur Metadaten und lässt das Bibliotheksdatum unverändert.

## Was gewinnen und verlieren wir?

- Die HTTP-Antwort muss nicht auf die gesamte Genresuche warten.
- Kein zusätzlicher Broker, trotzdem nachvollziehbarer Status in PostgreSQL.
- Gültige Bibliotheksdaten bleiben bei späteren Metadatenfehlern erhalten.
- Neustarts unterbrechen Arbeit. Wir garantieren keine dauerhafte Jobzustellung.
- Genau eine API-Instanz/ein Uvicorn-Worker ist vorgesehen; mehrere Instanzen bräuchten gemeinsame Begrenzungen.

## AI-Vorschlag kritisch bewertet

Ein Hintergrund-Task allein löst weder Neustartverhalten noch sichere Löschung. Deshalb gehören Status, Abbruch und erneute Sitzungsprüfung zum Entwurf. Die [FastAPI-Dokumentation](https://fastapi.tiangolo.com/tutorial/background-tasks/#caveat) nennt externe Werkzeuge für größere Hintergrundaufgaben.

Wenn ein zuverlässiger Wiederanlauf oder mehrere API-Instanzen nötig werden, prüfen wir einen eigenen Worker. Für den aktuellen MVP überwiegt der zusätzliche Aufwand. Ablauf: [architecture.md, Abschnitt 7](../architecture.md#7-abläufe-und-fehlerbehandlung).
