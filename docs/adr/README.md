# Architecture Decision Records

Stand: 23.11.2026 · Phase 2

Ein ADR hält fest, welche Frage wir hatten, welche Möglichkeiten wir gesehen haben und warum wir uns entschieden haben. Nachteile gehören genauso dazu wie Vorteile.

| ADR | Thema | Stand |
| --- | --- | --- |
| [001](0001-modular-monolith.md) | Modularer Monolith | Im Architekturgespräch ausgewählt |
| [002](0002-postgresql-and-derived-profiles.md) | PostgreSQL und abgeleitete Profile | PostgreSQL aus Phase 1; weiteres Modell als technischer Entwurf |
| [003](0003-import-orchestration.md) | Import in zwei Schritten | Technischer Entwurf, Laufzeitprüfung folgt |
| [004](0004-local-compose-hosting.md) | Docker Compose für die Hochschulabgabe, Cloudflare für den öffentlichen Betrieb | Lokaler Aufbau bestätigt. Cloudflare als Zielarchitektur dokumentiert. |

Die beiden im Gespräch ausgewählten Entscheidungen sind ausdrücklich bestätigt. Weitere technische Details wurden mit AI-Unterstützung ausgearbeitet und sind vor der Umsetzung gemeinsam durchzugehen. Kein ADR behauptet bereits bestandene Anwendungstests.

Wenn wir eine Entscheidung später ändern, ergänzen wir einen neuen ADR und verlinken ihn im alten. Der Gesamtaufbau steht in [architecture.md](../architecture.md).
