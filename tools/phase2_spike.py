"""Read-only Steam/IGDB feasibility probe. Python standard library only.

No browser login, application database or background scheduler is implemented here.
Results and the public-metadata probe cache stay in ignored .local/phase2-spike/.
Never print keys, Steam IDs, request URLs or raw provider responses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local' / 'phase2-spike'
CACHE_VERSION = 'igdb-genres-probe-v1'
MAX_AGE = 7 * 24 * 60 * 60
METADATA_BATCH_SIZE = 50
SETTING_NAMES = ('STEAM_API_KEY', 'STEAM_ID64', 'IGDB_CLIENT_ID', 'IGDB_CLIENT_SECRET')


class ProbeError(Exception):
    """Only fixed, safe messages may be exposed to the console/report."""

    def __init__(self, code, message, blocked_until=None):
        super().__init__(message)
        self.code = code
        self.blocked_until = blocked_until


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def retry_time(value, now=None):
    now = time.time() if now is None else now
    try:
        seconds = int(value)
        provider = now + max(0, seconds)
    except (ValueError, TypeError):
        try:
            provider = parsedate_to_datetime(value).timestamp()
        except (ValueError, TypeError, OverflowError):
            provider = now
    return max(now + 60, provider)


def settings_from(env_file):
    values = {}
    if env_file:
        try:
            lines = Path(env_file).read_text(encoding='utf-8-sig').splitlines()
        except OSError:
            raise ProbeError('ENV_FILE_UNREADABLE', 'Konfigurationsdatei nicht lesbar.') from None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, separator, value = line.partition('=')
            if not separator:
                raise ProbeError('ENV_FORMAT', 'Konfiguration muss KEY=VALUE-Zeilen enthalten.')
            key = key.strip()
            if key in SETTING_NAMES:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key] = value
    # An explicitly selected file takes precedence over inherited environment.
    values = {key: values.get(key, os.environ.get(key, '')) for key in SETTING_NAMES}
    if any(not values[key] or values[key].startswith('replace_') for key in SETTING_NAMES):
        raise ProbeError('SETTINGS_MISSING', 'Vier lokale Konfigurationswerte erforderlich; siehe .env.spike.example.')
    if not values['STEAM_ID64'].isdigit() or len(values['STEAM_ID64']) != 17:
        raise ProbeError('STEAM_ID_INVALID', 'STEAM_ID64 muss die 17-stellige ID des eigenen Testkontos enthalten.')
    return values


def read_cache():
    path = OUTPUT / 'metadata-cache.json'
    if not path.exists():
        return {'version': CACHE_VERSION, 'entries': {}, 'steam_source_id': None, 'blocked_until': 0}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ProbeError('CACHE_UNREADABLE', 'Lokaler Probe-Cache unlesbar; bitte vor erneutem Start untersuchen.') from None
    if data.get('version') != CACHE_VERSION:
        raise ProbeError('CACHE_VERSION', 'Probe-Cache besitzt eine andere Version; bitte separat archivieren.')
    if not isinstance(data.get('entries'), dict):
        raise ProbeError('CACHE_FORMAT', 'Probe-Cache besitzt ein ungueltiges Format.')
    return data


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def fresh(entry, now=None):
    now = time.time() if now is None else now
    return (isinstance(entry, dict)
            and entry.get('version') == CACHE_VERSION
            and isinstance(entry.get('fetched_epoch'), (int, float))
            and 0 <= now - entry['fetched_epoch'] < MAX_AGE
            and entry.get('mapping_status') == 'mapped')


class Client:
    def __init__(self, settings, cache):
        self.settings = settings
        self.cache = cache
        self.calls = {'steam': 0, 'twitch': 0, 'igdb': 0}
        self.token = None
        self.last_igdb_start = 0.0

    def request_json(self, request, provider):
        self.calls[provider] += 1
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read(5_000_001).decode('utf-8'))
        except HTTPError as error:
            if error.code == 429:
                blocked_until = retry_time(error.headers.get('Retry-After'))
                if provider in ('igdb', 'twitch'):
                    self.cache['blocked_until'] = blocked_until
                raise ProbeError('HTTP_429_' + provider.upper(), 'Anbietersperre; keine automatische Wiederholung.', blocked_until) from None
            raise ProbeError('HTTP_ERROR_' + provider.upper(), f'{provider}: HTTP-Fehler {error.code}; keine Wiederholung.') from None
        except (URLError, TimeoutError, OSError):
            raise ProbeError('NETWORK_ERROR_' + provider.upper(), f'{provider}: Netzwerkfehler oder Timeout; keine Wiederholung.') from None
        except (ValueError, UnicodeError):
            raise ProbeError('INVALID_JSON_' + provider.upper(), f'{provider}: Antwort ist kein lesbares JSON.') from None

    def steam(self, method, extra=None):
        params = {'key': self.settings['STEAM_API_KEY'], 'steamid': self.settings['STEAM_ID64'], 'format': 'json'}
        params.update(extra or {})
        request = Request('https://api.steampowered.com/IPlayerService/' + method + '/v0001/?' + urlencode(params))
        data = self.request_json(request, 'steam')
        response = data.get('response') if isinstance(data, dict) else None
        if not isinstance(response, dict):
            raise ProbeError('STEAM_RESPONSE_INVALID', 'Steam-Antwort besitzt keinen gueltigen Response-Block.')
        return response

    def igdb(self, endpoint, query):
        if self.cache.get('blocked_until', 0) > time.time():
            raise ProbeError('IGDB_BLOCKED', 'Gespeicherte Anbietersperre noch aktiv; spaeter manuell starten.', self.cache['blocked_until'])
        if not self.token:
            body = urlencode({'client_id': self.settings['IGDB_CLIENT_ID'], 'client_secret': self.settings['IGDB_CLIENT_SECRET'], 'grant_type': 'client_credentials'}).encode()
            token = self.request_json(Request('https://id.twitch.tv/oauth2/token', data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'}), 'twitch')
            if not isinstance(token, dict) or not isinstance(token.get('access_token'), str) or not token['access_token']:
                raise ProbeError('TWITCH_TOKEN_INVALID', 'Kein gueltiger Anwendungstoken erhalten.')
            self.token = token['access_token']
        delay = 1.0 - (time.monotonic() - self.last_igdb_start)
        if delay > 0:
            time.sleep(delay)
        self.last_igdb_start = time.monotonic()
        request = Request('https://api.igdb.com/v4/' + endpoint, data=query.encode(), headers={'Client-ID': self.settings['IGDB_CLIENT_ID'], 'Authorization': 'Bearer ' + self.token, 'Accept': 'application/json', 'Content-Type': 'text/plain'})
        result = self.request_json(request, 'igdb')
        if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
            raise ProbeError('IGDB_RESPONSE_INVALID', 'IGDB-Antwort ist keine Liste gueltiger Datensaetze.')
        return result


def known_minutes(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def normalize_library(owned, recent):
    raw = owned.get('games', [])
    count = owned.get('game_count')
    if not isinstance(raw, list) or not isinstance(count, int) or isinstance(count, bool) or count != len(raw):
        raise ProbeError('LIBRARY_UNAVAILABLE', 'Keine eindeutig lesbare Bibliothek; Sichtbarkeit und Antwort pruefen. Kein sicherer Privatstatus.')
    recent_rows = recent.get('games', []) if recent is not None else []
    if not isinstance(recent_rows, list):
        recent_rows = []
    recent_by_id = {row.get('appid'): row for row in recent_rows if isinstance(row, dict) and isinstance(row.get('appid'), int)}
    entries, discarded = {}, 0
    for row in raw:
        if not isinstance(row, dict):
            discarded += 1
            continue
        app = row.get('appid')
        if not isinstance(app, int) or isinstance(app, bool) or not 0 < app <= 4294967295 or app in entries:
            discarded += 1
            continue
        total = known_minutes(row.get('playtime_forever'))
        current = known_minutes(row.get('playtime_2weeks'))
        if current is None:
            current = known_minutes(recent_by_id.get(app, {}).get('playtime_2weeks'))
        if total is not None and current is not None and current > total:
            current = None
        last = row.get('rtime_last_played')
        last_known = isinstance(last, int) and not isinstance(last, bool) and 0 < last <= time.time()
        entries[app] = {'app_id': app, 'total_minutes': total, 'recent_minutes': current, 'last_played_available': last_known}
    return list(entries.values()), discarded


def playtime_diagnostics(owned, recent, entries, sample):
    """Expose response shape and counts, never IDs, minutes or raw payloads."""
    owned_rows = owned.get('games', []) if isinstance(owned, dict) else []
    if not isinstance(owned_rows, list):
        owned_rows = []
    owned_rows = [row for row in owned_rows if isinstance(row, dict)]
    count = known_minutes(recent.get('total_count')) if isinstance(recent, dict) else None
    raw_recent_rows = recent.get('games') if isinstance(recent, dict) else None
    recent_rows = [row for row in raw_recent_rows if isinstance(row, dict)] if isinstance(raw_recent_rows, list) else []
    if recent is None:
        state = 'request_failed'
    elif not isinstance(recent, dict):
        state = 'invalid_response'
    elif not recent:
        state = 'empty_response'
    elif 'games' in recent and not isinstance(raw_recent_rows, list):
        state = 'invalid_games_field'
    elif count == 0 and not recent_rows:
        state = 'explicit_zero_count'
    elif recent_rows:
        state = 'games_returned'
    else:
        state = 'no_game_rows_without_confirmed_zero'

    library_ids = {row['app_id'] for row in entries}
    sample_ids = {row['app_id'] for row in sample}
    recent_ids = {row['appid'] for row in recent_rows if isinstance(row.get('appid'), int) and not isinstance(row['appid'], bool) and row['appid'] > 0}
    library_positive = sum(row['recent_minutes'] is not None and row['recent_minutes'] > 0 for row in entries)
    sample_positive = sum(row['recent_minutes'] is not None and row['recent_minutes'] > 0 for row in sample)
    return {
        'owned_games_with_lifetime_minutes': sum(known_minutes(row.get('playtime_forever')) is not None for row in owned_rows),
        'owned_games_with_recent_minutes_field': sum(known_minutes(row.get('playtime_2weeks')) is not None for row in owned_rows),
        'recent_response_state': state,
        'recent_reported_total_count': count,
        'recent_returned_game_rows': len(recent_rows),
        'recent_rows_with_minutes': sum(known_minutes(row.get('playtime_2weeks')) is not None for row in recent_rows),
        'recent_rows_with_positive_minutes': sum((known_minutes(row.get('playtime_2weeks')) or 0) > 0 for row in recent_rows),
        'recent_unique_games_in_library': len(recent_ids & library_ids),
        'recent_unique_games_in_sample': len(recent_ids & sample_ids),
        'library_games_with_recent_minutes': sum(row['recent_minutes'] is not None for row in entries),
        'library_games_with_positive_recent_minutes': library_positive,
        'sample_games_with_recent_minutes': sum(row['recent_minutes'] is not None for row in sample),
        'sample_games_with_positive_recent_minutes': sample_positive,
        'positive_recent_games_outside_sample': library_positive - sample_positive,
        'sample_missed_all_positive_recent_games': library_positive > 0 and sample_positive == 0,
    }


def select_sample(entries, size, explicit, all_games=False):
    if all_games:
        return sorted(entries, key=lambda row: row['app_id'])
    by_id = {row['app_id']: row for row in entries}
    if explicit:
        try:
            ids = list(dict.fromkeys(int(value.strip()) for value in explicit.split(',')))
        except ValueError:
            raise ProbeError('SAMPLE_INVALID', '--app-ids muss kommaseparierte numerische AppIDs enthalten.') from None
        if not ids or len(ids) > 50 or any(app not in by_id for app in ids):
            raise ProbeError('SAMPLE_INVALID', '1 bis 50 AppIDs aus der tatsaechlichen Bibliothek erforderlich.')
        return [by_id[app] for app in ids]
    # Deterministic, distributed sample, balancing played/unplayed/unknown.
    ordered = sorted(entries, key=lambda row: hashlib.sha256(str(row['app_id']).encode()).digest())
    buckets = [[row for row in ordered if row['total_minutes'] == 0], [row for row in ordered if row['total_minutes'] is not None and row['total_minutes'] > 0], [row for row in ordered if row['total_minutes'] is None]]
    sample = []
    while len(sample) < size and any(buckets):
        for bucket in buckets:
            if bucket and len(sample) < size:
                sample.append(bucket.pop(0))
    return sample


def resolve_metadata(client, sample, cache):
    results, missing = {}, []
    for row in sample:
        app = row['app_id']
        cached = cache['entries'].get(str(app))
        if fresh(cached):
            results[app] = {**cached, 'source': 'fresh_cache'}
        else:
            missing.append(app)
    if not missing:
        return results
    source = cache.get('steam_source_id')
    if not isinstance(source, int) or isinstance(source, bool) or source <= 0:
        sources = client.igdb('external_game_sources', 'fields id,name; limit 500;')
        matches = {row['id'] for row in sources if isinstance(row.get('id'), int) and str(row.get('name', '')).casefold() == 'steam'}
        if len(matches) != 1:
            raise ProbeError('STEAM_SOURCE_AMBIGUOUS', 'Steam-Quelle in IGDB nicht eindeutig nachgewiesen.')
        source = cache['steam_source_id'] = matches.pop()
    for start in range(0, len(missing), METADATA_BATCH_SIZE):
        batch = missing[start:start + METADATA_BATCH_SIZE]
        results.update(resolve_metadata_batch(client, batch, cache, source))
    return results


def resolve_metadata_batch(client, app_ids, cache, source):
    """Keep full-library requests within bounded provider query sizes."""
    app_values = ','.join('"' + str(app) + '"' for app in app_ids)
    mapping, offset = {app: set() for app in app_ids}, 0
    while True:
        rows = client.igdb('external_games', f'fields uid,game; where external_game_source = {source} & uid = ({app_values}); limit 500; offset {offset};')
        for row in rows:
            uid, game = row.get('uid'), row.get('game')
            if isinstance(uid, str) and uid.isdigit() and int(uid) in mapping and isinstance(game, int) and not isinstance(game, bool) and game > 0:
                mapping[int(uid)].add(game)
        if len(rows) < 500:
            break
        offset += 500
        if offset > 5000:
            raise ProbeError('MAPPING_TOO_LARGE', 'Unerwartet viele Mappingzeilen; manuelle Pruefung erforderlich.')
    ids = sorted({next(iter(values)) for values in mapping.values() if len(values) == 1})
    games = {}
    if ids:
        rows = client.igdb('games', 'fields id,name,genres.id,genres.name; where id = (' + ','.join(map(str, ids)) + '); limit 500;')
        games = {row['id']: row for row in rows if isinstance(row.get('id'), int)}
    results = {}
    for app, matches in mapping.items():
        state = 'missing' if not matches else 'ambiguous' if len(matches) > 1 else 'mapped'
        game_id = next(iter(matches)) if len(matches) == 1 else None
        game = games.get(game_id)
        if state == 'mapped' and not isinstance(game, dict):
            state = 'game_unavailable'
        genre_rows = game.get('genres', []) if game else []
        if not isinstance(genre_rows, list):
            genre_rows = []
        genres = {row['id']: row['name'] for row in genre_rows if isinstance(row, dict) and isinstance(row.get('id'), int) and not isinstance(row['id'], bool) and row['id'] > 0 and isinstance(row.get('name'), str) and row['name'].strip()}
        result = {'version': CACHE_VERSION, 'mapping_status': state, 'igdb_id': game_id, 'public_title': game.get('name') if game else None, 'genres': [{'id': key, 'name': genres[key]} for key in sorted(genres)], 'fetched_at': utc_now(), 'fetched_epoch': time.time()}
        if state == 'mapped':
            cache['entries'][str(app)] = result
        results[app] = {**result, 'source': 'live'}
    return results


def build_report(sample, metadata):
    rows = []
    for game in sample:
        meta = metadata.get(game['app_id'], {})
        total = game['total_minutes']
        rows.append({'app_id': game['app_id'], 'playtime_class': 'unknown' if total is None else 'unplayed' if total == 0 else 'played', 'current_minutes_available': game['recent_minutes'] is not None, 'current_minutes_positive': (game['recent_minutes'] or 0) > 0, 'last_played_available': game['last_played_available'], 'mapping_status': meta.get('mapping_status', 'not_checked'), 'genre_count': len(meta.get('genres', [])), 'source': meta.get('source', 'not_checked')})
    usable = [row for row in rows if row['mapping_status'] == 'mapped' and row['genre_count'] > 0]
    summary = {'sample_size': len(rows), 'uniquely_mapped': sum(row['mapping_status'] == 'mapped' for row in rows), 'with_genres': len(usable), 'ambiguous': sum(row['mapping_status'] == 'ambiguous' for row in rows), 'missing_or_unavailable': sum(row['mapping_status'] in ('missing', 'game_unavailable') for row in rows), 'fresh_cache_hits': sum(row['source'] == 'fresh_cache' for row in rows), 'played_with_genres': sum(row['playtime_class'] == 'played' for row in usable), 'unplayed_with_genres': sum(row['playtime_class'] == 'unplayed' for row in usable), 'positive_current_with_genres': sum(row['current_minutes_positive'] for row in usable), 'known_last_played': sum(row['last_played_available'] for row in rows)}
    summary['minimum_two_played_two_unplayed'] = summary['played_with_genres'] >= 2 and summary['unplayed_with_genres'] >= 2
    return {'summary': summary, 'entries': rows}


def main():
    parser = argparse.ArgumentParser(description='Read-only Steam/IGDB-Probe fuer Stichprobe oder ganze Bibliothek; kein OpenID-Login. Ergebnisse nur lokal.')
    parser.add_argument('--env-file', help='Lokale KEY=VALUE-Datei; nicht im Repository speichern.')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--sample-size', type=int, choices=range(1, 51), default=50, metavar='1..50', help='Stichprobe; ohne andere Auswahl standardmaessig 50 Spiele.')
    selection.add_argument('--app-ids', help='Optional: 1 bis 50 tatsaechliche Bibliotheks-AppIDs, kommasepariert.')
    selection.add_argument('--all-games', action='store_true', help='Alle von Steam zurueckgegebenen Bibliotheksspiele pruefen; frischen Metadaten-Cache weiterverwenden.')
    parser.add_argument('--confirm-data-use', action='store_true', help='Bewusster Abruf eigener Steam-Daten und lokale Speicherung der Stichprobenzugehoerigkeit.')
    args = parser.parse_args()
    if not args.confirm_data_use:
        parser.error('Live-Abruf nur mit --confirm-data-use nach Lesen von docs/integration-spike.md.')
    report = {'created_at': utc_now(), 'kind': 'provider_probe_only', 'status': 'not_started', 'limitations': ['Kein verifizierter Steam-OpenID-Login.', 'Keine PostgreSQL-/Anwendungs-Cachepruefung.', 'Keine vollstaendige Live-Empfehlung oder Performance-Abnahme.']}
    cache, client, metadata, sample = None, None, {}, []
    try:
        settings = settings_from(args.env_file)
        cache = read_cache()
        client = Client(settings, cache)
        started = time.monotonic()
        owned = client.steam('GetOwnedGames', {'include_appinfo': 'true', 'include_played_free_games': 'true'})
        try:
            recent = client.steam('GetRecentlyPlayedGames')
            report['recent_source'] = 'response_received_not_automatically_complete'
        except ProbeError as error:
            recent = None
            report['recent_source'] = error.code
        entries, discarded = normalize_library(owned, recent)
        report['steam_elapsed_seconds'] = round(time.monotonic() - started, 3)
        report['library_size'] = len(entries)
        report['discarded_records'] = discarded
        sample = select_sample(entries, args.sample_size, args.app_ids, args.all_games)
        report['selection'] = 'all_library_games' if args.all_games else 'explicit_library_app_ids' if args.app_ids else 'deterministic_stratified_sample_manual_edition_review_needed'
        report['steam_diagnostics'] = playtime_diagnostics(owned, recent, entries, sample)
        metadata = resolve_metadata(client, sample, cache)
        report['status'] = 'probe_completed'
    except ProbeError as error:
        report.update(status='probe_failed', error_code=error.code, message=str(error))
        if error.blocked_until:
            report['retry_after_at'] = datetime.fromtimestamp(error.blocked_until, timezone.utc).isoformat()
    except Exception as error:
        # Never expose repr/str(error), which can contain request URLs and secrets.
        report.update(status='probe_failed', error_code='LOCAL_ERROR', message='Lokaler Fehler vom Typ ' + type(error).__name__ + '; keine Rohdetails ausgegeben.')
    report.update(build_report(sample, metadata))
    if client:
        report['network_calls'] = client.calls
    if cache is not None:
        write_json(OUTPUT / 'metadata-cache.json', cache)
    write_json(OUTPUT / 'report.json', report)
    print('Status:', report['status'])
    print('Lokaler Bericht: .local/phase2-spike/report.json (nicht committen)')
    print('Lokaler Probe-Cache: .local/phase2-spike/metadata-cache.json (kein PostgreSQL-Nachweis)')
    if 'error_code' in report:
        print('Fehlercode:', report['error_code'])
    else:
        print('Gepruefte Spiele:', report['summary']['sample_size'], 'von', report['library_size'], '| mit Genres:', report['summary']['with_genres'])
    return 0 if report['status'] == 'probe_completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
