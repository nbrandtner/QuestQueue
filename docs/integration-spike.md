# QuestQueue – Steam und IGDB praktisch prüfen

Stand: 23.11.2026 · Status: **API-Zugriff, Probe-Cache und aktuelle Steam-Minuten belegt; Anwendungsintegration offen**

Das Team hat das Skript am 23.11.2026 mehrfach lokal ausgeführt. Die ersten Berichte `report-first.json` und `report-cached.json` belegen 46 eindeutige IGDB-Zuordnungen mit Genres und deren Cache-Wiederverwendung. Nach Diagnose und Erweiterung wurde der ganze importierte Bestand geprüft: 195 Spiele, 182 Zuordnungen, 180 mit Genres. Alle fünf Spiele mit aktuellen Minuten haben Genres. Zugangsdaten wurden nicht an die AI übergeben. Die Ergebnisse stammen aus den Team-Berichten, nicht aus neuen Live-Aufrufen durch die AI.

Der frühe Integrationscheck aus Phase 1 ist damit teilweise erledigt. Die Berechnung von Current Taste mit Live-Metadaten, der verifizierte Steam-Login und die Anwendung mit PostgreSQL bleiben noch zu prüfen. Deshalb führen wir den Integrationsstand getrennt von der [Checkliste für die schriftlichen Deliverables](architecture.md#13-phase-2-definition-of-done).

## 1. Was das Prüfskript leistet

[tools/phase2_spike.py](../tools/phase2_spike.py) braucht Python ab 3.10, aber keine zusätzlichen Pakete. Es liest immer die gesamte zurückgegebene Steam-Bibliothek und verfügbare aktuelle Aktivität. Für die anschließende IGDB-Prüfung gibt es eine Stichprobe mit bis zu 50 Spielen oder `--all-games` für den ganzen importierten Bestand. Dafür nutzt es `external_game_source` und exakte AppIDs; ähnliche Spielnamen reichen nicht als Zuordnung. Metadatenanfragen werden in Gruppen von höchstens 50 AppIDs aufgeteilt.

Der lokale Bericht enthält Anzahlen, Zuordnungszustände, Metadatenabdeckung und Hinweise auf verfügbare aktuelle Minuten/letzte Zeitpunkte. Er enthält keine SteamID, API-Schlüssel oder vollständigen Anbieterantworten. Die Stichproben-AppIDs und ihre Spielzeitklasse können trotzdem Rückschlüsse auf die Bibliothek erlauben; sie bleiben deshalb lokal in `.local/phase2-spike/` und gehören nicht ins Repository.

Der separate JSON-Probe-Cache speichert allgemeine Metadaten sieben Tage. Ein zweiter Skriptprozess kann sie wiederverwenden. Das prüft den **Probe-Cache**, nicht PostgreSQL oder das spätere Backend. Bei fehlenden/mehrdeutigen Matches kann ein weiterer Lauf erneut anfragen; nur erfolgreiche Metadatenstände werden frisch gecacht. Anfragen sind sequenziell, IGDB-Starts mindestens eine Sekunde auseinander. Nach 429 wird die IGDB-/Twitch-Sperre lokal gespeichert und nicht automatisch erneut versucht. Bei anderen Fehlern findet ebenfalls kein automatischer Retry statt.

**Nicht abgedeckt:** Verifizierter Steam-Browserlogin, PostgreSQL-Persistenz, kontogetrennte Anwendungssitzungen, echte vollständige Empfehlung, 30-Sekunden-Gesamtdeadline der geplanten Anwendung, Kontolöschung oder Produktionsleistung. Das Skript verwendet einzelne 30-Sekunden-Netzwerk-Timeouts und berichtet die Steam-Laufzeit; dies ist kein N-02-Abnahmenachweis.

## 2. Sicher lokal starten

Vom Repository-Verzeichnis in PowerShell:

```powershell
Copy-Item -LiteralPath .env.spike.example -Destination .env.spike
```

Die neue `.env.spike` **lokal** im Editor ausfüllen. Die Vorlage enthält diese Variablen:

| Variable | Inhalt |
| --- | --- |
| `STEAM_API_KEY` | Eigener Backend-Schlüssel für die Steam Web API |
| `STEAM_ID64` | 17-stellige ID des eigenen Testkontos mit zugänglichen Spieldaten |
| `IGDB_CLIENT_ID` | Twitch-Anwendungs-ID für IGDB |
| `IGDB_CLIENT_SECRET` | Zugehöriges Backend-Secret |

Keine Schlüssel in den Chat, in Kommandoargumente oder in Git einfügen. Das Skript liest alternativ diese vier Umgebungsvariablen. Eine ausdrücklich gewählte Datei hat Vorrang. Es führt keine Konfigurationszeilen als Code aus. Die Probe erhebt keine Steam-Passwörter und ist kein Steam-Login.

Vor dem Start sicherstellen, dass das eigene Konto für diesen Test verwendet werden darf und die Spieldaten zugänglich sind. Der folgende bewusste Aufruf ruft die persönlichen Daten ab, hält die Spielminuten nur während des Laufs im Speicher und speichert die Stichprobenzugehörigkeit/-klasse lokal. Die Daten bleiben auf dem ausführenden Rechner; dessen tatsächlichen Standort im Prüfprotokoll notieren.

```powershell
python tools/phase2_spike.py --env-file .env.spike --all-games --confirm-data-use
```

Damit werden alle von Steam zurückgegebenen Bibliotheksspiele geprüft, beim bisherigen Testkonto 195. Vorhandene frische Metadaten werden wiederverwendet. Für eine kleinere Stichprobe stattdessen `--sample-size 50` verwenden; `--all-games`, `--sample-size` und `--app-ids` lassen sich nicht miteinander kombinieren. Das Berichtsfeld `summary.sample_size` enthält aus Kompatibilitätsgründen weiterhin diesen Namen, zählt bei `--all-games` aber den gesamten geprüften Bestand.

Für eine bewusst ausgewählte Stichprobe können echte, zur eigenen importierten Bibliothek gehörende AppIDs angegeben werden:

```powershell
python tools/phase2_spike.py --env-file .env.spike --app-ids "<echte-AppID>,<weitere-AppID>" --confirm-data-use
```

Die Platzhalter zuerst ersetzen. Die gezielte Auswahl ist auf 50 eigene AppIDs begrenzt. Ohne Auswahloption bleibt eine deterministische 50er-Stichprobe der Standard. **Ältere Titel, kleine Spiele und abweichende Editionen sollten auch fachlich geprüft werden.** Eine automatische Stichprobe garantiert diese Abdeckung nicht; der Vollbestand-Modus umfasst alle importierten Titel, ersetzt aber keine Prüfung der Metadatenqualität.

Anschließend lokal öffnen:

```powershell
Get-Content -Raw .local/phase2-spike/report.json
```

Bei einem Fehler nur den sicheren `error_code` und eine bereinigte Zusammenfassung weitergeben. Keine Debug-Tracebacks, Request-URLs oder privaten Antwortdateien veröffentlichen. Ein `probe_completed` bedeutet, dass die Probe abgearbeitet wurde; geringe Abdeckung oder fehlende Mindesttitel müssen trotzdem bewertet werden.

## 3. Wiederverwendung und Auswertung

1. Den ersten `report.json` lokal unter einem zweiten Namen aufbewahren, damit der nächste Lauf ihn nicht ersetzt.
2. Dasselbe Kommando als neuen Python-Prozess erneut starten. Dieselbe Stichprobe und weniger als sieben Tage alte erfolgreiche Metadaten verwenden.
3. `summary.fresh_cache_hits` und `network_calls.igdb/twitch` vergleichen. Sind **alle** Stichprobentitel erfolgreich/frisch gecacht, müssen IGDB und Twitch jeweils 0 neue Aufrufe zeigen. Fehlende Matches dürfen erneut untersucht werden; dann ist 0 Gesamtaufrufe nicht zu erwarten. Steam wird in jedem Lauf neu gelesen.
4. `summary.uniquely_mapped`, `with_genres`, `ambiguous`, `missing_or_unavailable`, `played_with_genres` und `unplayed_with_genres` auswerten. Mindestens zwei gespielte und zwei ungespielte Titel mit Genres sind die Mindestbasis, noch keine vollständige Live-Empfehlung.
5. Prüfen, ob `positive_current_with_genres > 0` ist und der wirkliche Nutzer kürzliche Aktivität hat. Ein vollständig leeres aktuelles Profil kann ein korrekter Leerzustand sein. Aus fehlenden Feldern wird keine 0 erfunden.
6. Ergebnisse mit Datum, Stichprobengröße, Auswahl und Grenzen in das folgende Protokoll übernehmen. Bericht und Cache bleiben lokal und werden bei Bedarf lokal entfernt; keine Daten oder AppIDs ohne bewusste Prüfung veröffentlichen.

### Ergebnisprotokoll vom 23.11.2026

| Prüfpunkt | Ergebnis / Nachweis |
| --- | --- |
| Ausführungsdatum und tatsächliches Speicherland | 23.11.2026; Österreich, vom Team bestätigt |
| Steam-Zugriff erfolgreich, Bibliotheksgröße | Beide Läufe abgeschlossen; 195 Spiele, 0 verworfene Datensätze |
| Stichprobenumfang und Auswahlbegründung | Dieselben 50 deterministisch ausgewählten Spiele in beiden Läufen: 34 gespielt, 16 ungespielt; bekannte Gesamtminuten für alle 50 |
| Ältere/kleinere Titel und abweichende Editionen geprüft | Manuelle Auswahl-/Qualitätsprüfung noch offen |
| Eindeutig zugeordnet / Stichprobe | 46/50 = 92 % der Stichprobe; keine Aussage über alle 195 Spiele |
| Mit Genres / Stichprobe | 46/50 |
| Fehlend / mehrdeutig / nicht abrufbar | 4 fehlende Zuordnungen, 0 mehrdeutige; kein Laufabbruch |
| Mindestens 2 gespielte + 2 ungespielte Titel mit Genres | Erfüllt: 33 gespielte und 13 ungespielte Titel mit Genres |
| Positive aktuelle Minuten / letzte Spielzeitpunkte nachweisbar | Erste Stichprobe: 0 aktuelle Minutenfelder, 34 gültige letzte Spielzeitpunkte. Zusätzlicher Diagnoselauf: fünf Bibliotheksspiele mit positiven aktuellen Minuten; alle fünf außerhalb der Stichprobe. |
| Zweiter Prozess: Cachetreffer und IGDB-/Twitch-Aufrufe | 46 Cachetreffer; 1 IGDB- und 1 Twitch-Aufruf für die erneut geprüften vier Lücken. Erster Lauf: 0 Treffer, 3 IGDB- und 1 Twitch-Aufruf. |
| IGDB bleibt geeignet / konkrete Anpassung nötig | Für den geprüften Bibliotheks-/Metadatenablauf geeignet; vier Lücken sichtbar lassen. Live-Current-Berechnung und manuelle Metadatenqualität noch prüfen. |

Die Berichte enthalten keine widersprüchlichen Klassifikationen zwischen den beiden Läufen. Die 46 passenden Einträge sind im lokalen Probe-Cache vorhanden. Das belegt dessen Wiederverwendung in einem neuen Prozess, noch keinen PostgreSQL-Cache.

### Ergänzung: Vollbestand vom 23.11.2026

Der Lauf mit `--all-games` ist lokal als `report-all-games-20261123-141022.json` gesichert. Bericht und Probe-Cache wurden auf Konsistenz geprüft:

| Prüfpunkt | Ergebnis |
| --- | --- |
| Geprüfter Bestand | 195 von 195 zurückgegebenen Bibliotheksspielen; 179 gespielt, 16 ungespielt |
| Gesamtminuten verfügbar | Für alle 195 Spiele |
| Eindeutige IGDB-Zuordnung | 182/195 = 93,3 % |
| Genres verfügbar | 180/195 = 92,3 %; zwei zugeordnete Spiele ohne Genres |
| Zuordnungslücken | 13 fehlende, keine mehrdeutige Zuordnung |
| Referenzen / Kandidaten mit Genres | 167 gespielte und 13 ungespielte Titel |
| Aktuelle Minuten | Fünf Spiele mit positiven 14-Tage-Minuten; alle fünf mit Genres und im geprüften Bestand |
| Letzter Spielzeitpunkt | Für 179 Spiele verfügbar |
| Cache und Aufrufe | 46 frische Einträge wiederverwendet; 2 Steam-, 1 Twitch- und 6 IGDB-Aufrufe |

Damit sind positive aktuelle Eingabedaten und Metadaten vorhanden. Die Live-Berechnung beider Profile und eine vollständige Empfehlung wurden durch die Probe noch nicht ausgeführt. Der Bericht speichert Verfügbarkeit und Klassifikationen, **keine exakten Minutenwerte**; diese wurden beim Abruf verarbeitet und sind nicht nachträglich aus den Berichten rekonstruierbar. Die spätere Anwendung speichert die numerischen Werte gemäß Datenmodell.

### Warum die ersten Berichte keine aktuellen Minuten zeigten

Die Ursache ist durch den Diagnoselauf vom 23.11.2026 geklärt: Alle 195 Bibliotheksspiele haben bekannte Gesamtminuten. Fünf besitzen positive aktuelle Minuten, aber keines davon war in der 50er-Stichprobe. Der anschließende Vollbestand-Lauf enthält alle fünf. Die separate Recent-Antwort enthielt zehn Spiele mit positiven Minuten; fünf davon gehören zur importierten Bibliothek. Daraus wird keine Besitzannahme über die übrigen fünf Spiele abgeleitet.

Die Daten fehlten also in der ausgewählten Stichprobe, nicht in der gesamten Steam-Antwort. Die bisherige Auswahl berücksichtigte nur gespielt/ungespielt/unbekannt und garantierte keine aktuelle Referenz. `--all-games` verhindert diese Stichprobenlücke. Der vorherige Diagnoselauf bleibt zusätzlich lokal als `report-diagnostics-20261123-140550.json` erhalten.

Das Skript schreibt `steam_diagnostics` mit sicheren Anzahlen für Bibliothek und geprüfte Auswahl:

| Feld | Bedeutung |
| --- | --- |
| `library_games_with_positive_recent_minutes` | Spiele mit gültigen positiven aktuellen Minuten in der gesamten importierten Bibliothek |
| `sample_games_with_positive_recent_minutes` | Davon in der geprüften Auswahl enthalten; bei `--all-games` gleich dem Bibliothekswert |
| `sample_missed_all_positive_recent_games` | `true`: Aktuelle Daten existieren, die Stichprobe hat die betroffenen Spiele aber verfehlt |
| `recent_response_state` | Beispielsweise `games_returned`, `empty_response`, `explicit_zero_count` oder `request_failed`; beschreibt die Antwort, diagnostiziert keinen Privatstatus |
| `recent_returned_game_rows` / `recent_rows_with_positive_minutes` | Ob der separate Recent-Endpunkt Spiele beziehungsweise positive Minuten geliefert hat |

Die Diagnose enthält keine SteamID, Titel, AppID-Liste, Schlüssel oder Rohantwort. Der erneute Aufruf verwendet denselben Befehl wie oben und schreibt `report.json`; die beiden vorhandenen benannten Berichte bleiben erhalten. Ein fehlendes Feld bleibt unbekannt und wird nicht als 0 ausgegeben.

Es wird kein unbegründeter pauschaler Abdeckungsprozentsatz als Erfolgsschwelle gesetzt. Die Mindesttitel prüfen die Machbarkeit; die Breite der Stichprobe, passende Genres und verbleibende Lücken entscheiden über die Nutzbarkeit. SteamSpy wird erst bei relevanten Lücken und nach eigener Zugriffs-, Qualitäts- und Bedingungsprüfung ergänzt.

## 4. Zusätzliche Nachweise außerhalb des Skripts

| Prüfung | Durchführung und Soll |
| --- | --- |
| Steam OpenID | Konfigurierten lokalen Callback mit einer geeigneten OpenID-2.0-Bibliothek testen; echte Providerprüfung, Browserbindung und einmalige Nonce. Nur verifizierte Antwort erstellt eine Sitzung. Abbruch, Manipulation und Replay dürfen keinen Import erlauben. |
| Vollständiger Live-Kernfall | Verifizierte Sitzung → Datenhinweis → Bibliothek → IGDB-Genres → beide Profile, soweit Daten vorhanden → begründete Empfehlung. Mindestens zwei gespielte und zwei ungespielte bestätigte Titel verwenden. |
| PostgreSQL-Cache nach Neustart | Backend/DB regulär neu starten; bei unverändertem frischem Cache keine erneute IGDB-Abfrage derselben Daten; die Bibliothek bleibt vorhanden. JSON-Probe-Cache zählt hierfür nicht. |
| Fehlendes / mehrdeutiges Mapping | Kontrollierte Adapterantwort; Titel bleibt sichtbar, keine erfundenen Genres, Abdeckung sinkt sichtbar. |
| Steam-Fehler und Current-Teilfehler | Simulierte Timeouts/unlesbare Antworten; alter Bestand bleibt bei Bibliotheksfehler, gültiger neuer All-Time-Stand bei isoliertem Current-Fehler. |
| 429 | Per Simulation testen, **keine echte Rate-Limit-Überlastung erzeugen**. Retry-After mindestens 60 Sekunden; kein automatischer Retry und kein versteckter Seitenaufruf-Import. |
| Abmeldung / Löschung während Import | Zweiteilige Tests: Commit gewinnt vor Löschung / Löschung gewinnt vor Commit. Danach keine persönlichen Daten mehr; zweites Konto und allgemeiner Cache bleiben erhalten. |

Diese Anwendungstests sind für Phase 3/4 vorgesehen. Der frühe Check aus Phase 1 ist noch nicht abgeschlossen. Falls er erst nach Phase 2 stattfindet, nennen wir diese Abweichung beim Abgabestand ausdrücklich.

## 5. Offline-Prüfung des gelieferten Skripts

Die mitgelieferten Tests verwenden synthetische Antworten und keine Zugangsdaten:

```powershell
python -m unittest discover -s tools -p "test_phase2_spike.py" -v
```

Sie prüfen unter anderem unbekannte Minuten, ungültige aktuelle Werte, exakte/mehrdeutige Zuordnung, Cache-Grenzen, 429 ohne Wiederholung und das Unterdrücken von geheimen URLs in Fehlermeldungen. Ein bestandener Offline-Test beweist die Probe-Logik, keinen funktionierenden Anbieterzugang.

Prüfstand vom 22.11.2026: Die ursprünglichen zehn Offline-Tests bestanden; API-Datei, Dokumentverweise und Diagramm wurden geprüft. Am 23.11.2026 kamen fünf Tests zur Recent-Diagnose und vier für Vollbestand/Batching dazu. Alle 19 Tests bestehen. Sie prüfen unter anderem den CLI-Aufruf für 195 Spiele und die begrenzten Metadatenanfragen für 601 Spiele. Dafür wurden keine Live-Zugangsdaten verwendet.
