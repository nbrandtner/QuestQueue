# QuestQueue

**Your Library, Your new Quest**

Stand: 23.11.2026 · Version 2.1 · Phase 2 – Architecture & Design

Phase 1 ist abgegeben. Für Phase 2 haben wir uns für ein modulares FastAPI-Backend und den lokalen Start mit Docker Compose entschieden. Variantenvergleich, Datenmodell und API stehen in [docs/architecture.md](docs/architecture.md), einschließlich Aufgabenabgleich und Fragen fürs Projektgespräch. Die Anwendung bauen wir in Phase 3. Die [API-Probe vom 23.11.2026](docs/integration-spike.md) prüft alle 195 importierten Spiele: 182 eindeutige IGDB-Zuordnungen, 180 mit Genres und fünf mit positiven aktuellen Minuten samt Genres. Die Wiederverwendung des Probe-Caches ist ebenfalls belegt. Die vollständige Anwendungsintegration bleibt offen.

QuestQueue unterstützt Steam-Spieler:innen bei der Frage **„Was soll ich als Nächstes spielen?“** Die Webanwendung analysiert die eigene Bibliothek und das bisherige Spielverhalten. Sie erstellt ein nachvollziehbares Präferenzprofil und empfiehlt passende ungespielte Titel aus dem eigenen Bestand. Zwei Profile unterscheiden aktuelle Interessen (**Current Taste**) von langfristigen Schwerpunkten (**All-Time Taste**).

## Problem und Motivation

Große Spielebibliotheken erschweren die Auswahl: Ungespielte Titel gehen unter, frühere Favoriten werden vergessen und Interessen verändern sich. Eine nach Gesamtspielzeit sortierte Liste zeigt weder aktuelle Vorlieben noch passende unentdeckte Spiele.

QuestQueue verbindet Spielübersichten, ein persönliches Präferenzprofil und begründete Vorschläge. Der Mehrwert liegt darin, vorhandene Spiele gezielter zu nutzen und die Entscheidung für das nächste Spiel zu erleichtern. Spielzeit dient dabei als Interessenssignal, nicht als Beweis für Zufriedenheit oder einen Spielabschluss.

## Zielgruppe und Projektziel

Die primäre Zielgruppe sind PC-Spieler:innen mit einer Steam-Bibliothek, mehreren ungespielten Titeln und dem Wunsch, ihren Bestand bewusster zu nutzen. Die spätere Produktentwicklung berücksichtigt außerdem das Entdecken neuer Spiele und die Wiederentdeckung früherer Favoriten.

Ein Team aus zwei Personen entwickelt QuestQueue im Wintersemester 2026/27. Projektziel ist ein lokal betreibbarer MVP mit einem vollständigen Ablauf von der Steam-Anmeldung bis zum begründeten Spielvorschlag. Die Implementierungsabgabe erfolgt am 09.12.2026; Qualitätssicherung und Evaluation folgen bis 22.12.2026.

## Wichtigste Anwendungsfälle

| Fall | Ablauf und Ergebnis | Anforderungen |
| --- | --- | --- |
| UC-01 · Eigenes Spiel auswählen | Über Steam anmelden, Daten importieren, Spielübersicht und Präferenzprofil prüfen und mit „What should I play?“ einen begründeten Vorschlag für ein eigenes ungespieltes Spiel erhalten. | US-01, US-02, US-03, US-05, US-09, US-13, US-14, US-19 |
| UC-02 · Aktuelle Interessen berücksichtigen | Zwischen All-Time Taste und Current Taste wechseln; Profil, Rangliste und Auswahl passen sich ohne erneuten Import an. Fehlende aktuelle Daten werden angezeigt. | US-03, US-05, US-09, US-13, US-15 |
| UC-03 · Eigene Daten kontrollieren | Den letzten gültigen Datenstand erkennen, die Sitzung durch Abmeldung beenden oder die eigenen gespeicherten Daten bestätigt löschen. | US-14, US-15, US-16 |

UC-01 bildet den vollständigen Hauptanwendungsfall. Ein getrennter Offline-Demomodus nach US-17 ermöglicht eine reproduzierbare Demonstration mit Beispieldaten.

## Funktionsübersicht

Die Produktvision enthält 13 Funktionen. Der MVP umfasst elf Must-Stories einschließlich Anmeldung, Datenversorgung und Datenkontrolle. Sieben Should-Stories und eine Could-Story bilden den Erweiterungsumfang.

| Funktion | User Story | Priorität / Umfang |
| --- | --- | --- |
| Last played games anzeigen | US-01 | Must / MVP |
| Most played games anzeigen | US-02 | Must / MVP |
| Preference Profile aufbauen | US-03 | Must / MVP |
| Dashboard, z. B. meistgespielte Genres | US-04 | Should / nach dem Kernablauf |
| Empfehlungen für eigene Spiele | US-05 | Must / MVP, zunächst ungespielte Titel |
| Empfehlungen für Spiele außerhalb der Bibliothek | US-06 | Should / Entdeckungsbereich |
| Like/Dislike für externe Empfehlungen | US-07 | Should / abhängig von US-06 |
| Spielzeit über die Zeit verfolgen | US-08 | Should / ab Beginn eigener Erfassung |
| Current Taste und All-Time Taste | US-09 | Must / MVP |
| Früher gern gespielte Titel wiederentdecken | US-10 | Should / eigener Empfehlungsbereich |
| Eigene Tags: Finished, Dropped, Loved It, Not Interested | US-11 | Should / beeinflussen Auswahl und Profil |
| Genres und andere Empfehlungseigenschaften ausschließen | US-12 | Should / zunächst Genre-Ausschluss |
| „What should I play?“ | US-13 | Must / MVP, konkrete Auswahl statt Zufall |

## MVP und Erweiterungen

Der MVP zeigt zuletzt und meistgespielte Titel, eine einfache Profilübersicht und bis zu fünf begründete Empfehlungen eigener ungespielter Spiele. Der Button „What should I play?“ wählt den bestgereihten Titel aus derselben Liste.

Current Taste nutzt verfügbare Spielminuten der letzten 14 Tage zum Importzeitpunkt, All-Time Taste die Gesamtspielzeit. Die inhaltsbasierte Empfehlungsmethode verteilt Referenzspielzeiten auf Genres und vergleicht die daraus entstehenden Profilgewichte mit den Genres der Kandidaten. Die Berechnungsregeln und ein festes Akzeptanzbeispiel stehen in [requirements.md, Abschnitt 5](docs/requirements.md#5-empfehlungsmethode-inhaltsbasierte-baseline-v1).

Dashboard, externe Empfehlungen, Feedback, eigener Spielzeitverlauf, Wiederentdeckung, persönliche Tags und Ausschlussfilter gehören zu späteren Erweiterungen. Der MVP beinhaltet keine periodische Hintergrundabfrage und keinen öffentlichen Hostingbetrieb.

## Technischer Rahmen und externe Abhängigkeiten

| Bereich | Festlegung |
| --- | --- |
| Plattform und Betrieb | Lokaler Hochschul-MVP mit Docker Compose. Für einen späteren öffentlichen Betrieb sind Cloudflare Pages, Cloudflare Containers und Neon PostgreSQL vorgesehen. |
| Anmeldung | Steam Sign-In über Steam OpenID |
| Backend | Python + FastAPI |
| Frontend | Vue + TypeScript |
| Datenhaltung | PostgreSQL; persönliche Daten je verifizierter SteamID getrennt |
| Persönliche Spieldaten | Steam Web API; Zugriff abhängig von der Sichtbarkeit der Spieldaten |
| Spielmetadaten | IGDB mit lokalem PostgreSQL-Cache |
| Empfehlung | Genrebasierte inhaltsbasierte Baseline v1 |
| Aktualisierung | Bewusst gestarteter Erstimport; danach manueller Refresh und Aktualisierung bei Anmeldung ab 24 Stunden Datenalter |

Steam-Anmeldung und externe Datenabrufe benötigen Internetzugang. IGDB-Metadaten werden sieben Tage als frisch behandelt. Bei fehlenden oder veralteten Einträgen erfolgt die Anreicherung während eines Imports; Lücken und ältere Daten bleiben erkennbar. API-Zugangsdaten verbleiben im Backend.

Der Integrationsnachweis in Phase 2 prüft Steam-Zugriff, IGDB-Zuordnung und Genreabdeckung anhand einer Bibliotheksstichprobe. SteamSpy ist eine technische Alternative bei relevanten Metadatenlücken. Für zusätzliche laufende Dienste ist ein Budget von 0 Euro vorgesehen; ein bestehender Entwicklungsrechner und Internetzugang werden vorausgesetzt.

## Name und Positionierung

QuestQueue verbindet die nächste spielerische „Quest“ mit einer geordneten Auswahl möglicher nächster Spiele. Der Claim **Your Library, Your new Quest** stellt den eigenen Bestand und das nächste Spielerlebnis in den Mittelpunkt. QuestQueue ist ein unabhängiges Studienprojekt.

## Dokumentation

| Datei | Inhalt |
| --- | --- |
| [docs/requirements.md](docs/requirements.md) | Begriffe, User Stories, funktionale und nichtfunktionale Anforderungen, Prioritäten, Akzeptanzkriterien und Datenregeln |
| [docs/mvp.md](docs/mvp.md) | MVP-Abgrenzung, Erweiterungen, Demonstrationsfall, Projektplan und Abnahmekriterien |
| [docs/ai-usage.md](docs/ai-usage.md) | AI-Anwendungen mit ausgewählten Prompts, Ergebnissen und kritischer Reflexion |
| [docs/architecture.md](docs/architecture.md) | Phase 2: Variantenvergleich, Technologieentscheidungen, C4-Sichten, Datenmodell, API und kritische AI-Reflexion |
| [docs/hosting.md](docs/hosting.md) | Lokale Hochschulumgebung, Cloudflare als Ziel für den öffentlichen Betrieb, Kostenvergleich und Bereitstellungsplan |
| [docs/adr/](docs/adr/README.md) | Vier Architecture Decision Records mit Kontext, Alternativen und Folgen |
| [Architekturdiagramm](docs/diagrams/c4-container.svg) | Eigenständig lesbares C4-Containerdiagramm; bearbeitbare Mermaid-Quellen im selben Ordner |
| [docs/api/openapi.json](docs/api/openapi.json) | OpenAPI-3.1-Entwurf der MVP-Schnittstellen |
| [docs/integration-spike.md](docs/integration-spike.md) | Anleitung zur API-Stichprobe, noch offene Nachweise und Ergebnisprotokoll |

Die AI-Unterstützung für Phase 2 ist in [architecture.md, Abschnitt 12](docs/architecture.md#12-ai-unterstützung-und-kritische-prüfung) dokumentiert. Die Phase-1-Anforderungen, der damalige MVP-Plan und das ursprüngliche AI-Protokoll bleiben als abgegebene Basis erhalten.
