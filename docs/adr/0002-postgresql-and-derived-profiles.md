# ADR-002 – PostgreSQL und Profile bei Bedarf berechnen

Entwurf vom 22.11.2026 · Überarbeitet am 23.11.2026 · Status: **Für die Umsetzung vorgesehen**

## Ausgangslage

PostgreSQL ist bereits in Phase 1 festgelegt. Persönliche Daten müssen Neustarts überstehen, nach Konto getrennt bleiben und vollständig löschbar sein. Allgemeine Genres sollen dagegen gemeinsam im Cache bleiben. Current und All-Time verwenden dieselbe Bibliothek mit unterschiedlichen Minutenfeldern.

## Welche Möglichkeiten gibt es?

1. Bibliothek und Metadaten relational speichern, Profile und Ranglisten daraus berechnen.
2. Zusätzlich fertige Profile und Ranglisten speichern und bei jeder relevanten Änderung aktualisieren.
3. Auf SQLite oder Dateien wechseln; das würde den festgelegten Stack ändern.

## Unsere Entscheidung

Wir planen Option 1. Fremdschlüssel sichern die Beziehungen zwischen Konto, Import und Bibliothek. Eine Transaktion ersetzt den Bibliotheksstand zusammen mit seinem Status. Allgemeine Metadaten besitzen keinen Kontoinhaber und werden bei Kontolöschung nicht entfernt.

Profile entstehen aus einem gemeinsam geladenen Datenstand. Das Ergebnis nennt `import_id`, `catalog_revision` und `rules_version`. Unbekannte Minuten bleiben `NULL`, SteamIDs Zeichenfolgen. Beide Profile brauchen keine getrennten Kopien der Bibliothek.

## Was gewinnen und verlieren wir?

- Weniger doppelte Daten und weniger Regeln zum Aktualisieren alter Ergebnisse.
- Kontotrennung, Löschung und Beziehungen lassen sich in einer DB absichern.
- Jede Ergebnisanfrage braucht Berechnung; N-01 muss später gemessen werden.
- Ohne damalige Metadatenstände können wir historische Empfehlungen nicht exakt wiederherstellen.
- PostgreSQL braucht einen eigenen Dienst und Migrationen.

## AI-Vorschlag kritisch bewertet

Die Berechnung bei Bedarf stammt aus dem AI-gestützten Entwurf. Sie passt zum kleinen Mengenziel, ist aber noch kein Leistungsnachweis. Falls N-01 nach Abfrageoptimierung nicht erfüllt wird, prüfen wir einen Ergebnis-Cache mit vollständigem Versionsschlüssel.

Ein `account_id`-Feld allein genügt außerdem nicht als Zugriffsschutz: Wir brauchen Sitzungsprüfungen, kontobezogene Abfragen und passende Fremdschlüssel. Details stehen im [Datenmodell](../architecture.md#6-datenmodell).
