"""Offline safety and data-quality checks for the architecture feasibility probe."""

import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

import phase2_spike as probe


class ProbeTests(unittest.TestCase):
    def test_missing_minutes_are_not_unplayed(self):
        rows, discarded = probe.normalize_library({'game_count': 2, 'games': [{'appid': 1}, {'appid': 2, 'playtime_forever': 0}]}, None)
        self.assertIsNone(rows[0]['total_minutes'])
        self.assertIsNone(rows[0]['recent_minutes'])
        self.assertEqual(rows[1]['total_minutes'], 0)
        self.assertEqual(discarded, 0)

    def test_invalid_current_does_not_destroy_total(self):
        rows, _ = probe.normalize_library({'game_count': 1, 'games': [{'appid': 1, 'playtime_forever': 20, 'playtime_2weeks': 21, 'rtime_last_played': 99999999999}]}, None)
        self.assertEqual(rows[0]['total_minutes'], 20)
        self.assertIsNone(rows[0]['recent_minutes'])
        self.assertFalse(rows[0]['last_played_available'])

    def test_ambiguous_empty_library_is_rejected(self):
        with self.assertRaises(probe.ProbeError):
            probe.normalize_library({}, None)
        self.assertEqual(probe.normalize_library({'game_count': 0}, None), ([], 0))

    def test_cache_expires_at_exactly_seven_days(self):
        entry = {'version': probe.CACHE_VERSION, 'fetched_epoch': 100, 'mapping_status': 'mapped'}
        self.assertTrue(probe.fresh(entry, 100 + probe.MAX_AGE - 0.01))
        self.assertFalse(probe.fresh(entry, 100 + probe.MAX_AGE))
        self.assertFalse(probe.fresh(entry, 99))

    def test_fresh_cache_performs_no_provider_calls(self):
        entry = {'version': probe.CACHE_VERSION, 'fetched_epoch': probe.time.time(), 'mapping_status': 'mapped', 'genres': []}
        class NoNetwork:
            def igdb(self, *_):
                raise AssertionError('Fresh cache must not request IGDB or Twitch')
        result = probe.resolve_metadata(NoNetwork(), [{'app_id': 1}], {'entries': {'1': entry}})
        self.assertEqual(result[1]['source'], 'fresh_cache')

    def test_mapping_requires_exact_appid_and_one_distinct_igdb_id(self):
        class FakeClient:
            def __init__(self):
                self.queries = []
            def igdb(self, endpoint, query):
                self.queries.append((endpoint, query))
                if endpoint == 'external_game_sources':
                    return [{'id': 42, 'name': 'Steam'}]
                if endpoint == 'external_games':
                    return [{'uid': '1', 'game': 10}, {'uid': '1', 'game': 10}, {'uid': '2', 'game': 20}, {'uid': '2', 'game': 21}, {'uid': '999', 'game': 99}]
                return [{'id': 10, 'name': 'Public game', 'genres': [{'id': 5, 'name': 'RPG'}, {'id': 5, 'name': 'RPG'}]}]
        client = FakeClient()
        cache = {'entries': {}}
        result = probe.resolve_metadata(client, [{'app_id': 1}, {'app_id': 2}, {'app_id': 3}], cache)
        self.assertEqual(result[1]['mapping_status'], 'mapped')
        self.assertEqual(len(result[1]['genres']), 1)
        self.assertEqual(result[2]['mapping_status'], 'ambiguous')
        self.assertEqual(result[3]['mapping_status'], 'missing')
        self.assertEqual(set(cache['entries']), {'1'})
        self.assertIn('external_game_source = 42', client.queries[1][1])
        self.assertNotIn('category', client.queries[1][1])

    def test_http_error_does_not_expose_secret_url_or_body_and_does_not_retry(self):
        secret_url = 'https://example.invalid/?key=SECRET_VALUE&steamid=PRIVATE_ID'
        client = probe.Client({}, {})
        error = HTTPError(secret_url, 429, 'SECRET_VALUE', {'Retry-After': '120'}, io.BytesIO(b'SECRET_RESPONSE'))
        with patch.object(probe, 'urlopen', side_effect=error) as network:
            with self.assertRaises(probe.ProbeError) as context:
                client.request_json(Request(secret_url), 'igdb')
        self.assertEqual(network.call_count, 1)
        self.assertNotIn('SECRET', str(context.exception))
        self.assertNotIn('PRIVATE_ID', str(context.exception))
        self.assertGreaterEqual(context.exception.blocked_until, probe.time.time() + 119)
        self.assertEqual(client.cache['blocked_until'], context.exception.blocked_until)

    def test_network_error_does_not_expose_credentials(self):
        with patch.object(probe, 'urlopen', side_effect=URLError('key=SECRET_VALUE')):
            with self.assertRaises(probe.ProbeError) as context:
                probe.Client({}, {}).request_json(Request('https://example.invalid/'), 'steam')
        self.assertNotIn('SECRET', str(context.exception))

    def test_sample_cannot_import_non_library_appid(self):
        with self.assertRaises(probe.ProbeError):
            probe.select_sample([{'app_id': 1}], 50, '1,2')

    def test_config_is_parsed_without_executing_shell_expressions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'env'
            path.write_text('STEAM_API_KEY=$(do_not_execute)\nSTEAM_ID64=76561198000000000\nIGDB_CLIENT_ID="dummy"\nIGDB_CLIENT_SECRET=unit-test\n', encoding='utf-8')
            settings = probe.settings_from(path)
            self.assertEqual(settings['STEAM_API_KEY'], '$(do_not_execute)')
            self.assertEqual(settings['IGDB_CLIENT_ID'], 'dummy')

    def test_recent_activity_outside_sample_is_identified_without_exposing_payload(self):
        owned = {'game_count': 2, 'games': [{'appid': 1, 'name': 'PRIVATE_TITLE', 'playtime_forever': 30}, {'appid': 2, 'playtime_forever': 20}]}
        recent = {'total_count': 1, 'games': [{'appid': 1, 'playtime_2weeks': 15}]}
        entries, _ = probe.normalize_library(owned, recent)
        result = probe.playtime_diagnostics(owned, recent, entries, [entries[1]])
        self.assertTrue(result['sample_missed_all_positive_recent_games'])
        self.assertEqual(result['library_games_with_positive_recent_minutes'], 1)
        self.assertEqual(result['recent_unique_games_in_sample'], 0)
        self.assertEqual(result['recent_response_state'], 'games_returned')
        self.assertNotIn('PRIVATE_TITLE', str(result))
        self.assertNotIn('appid', str(result))
        self.assertNotIn('steamid', str(result))

    def test_empty_recent_response_does_not_claim_no_activity(self):
        result = probe.playtime_diagnostics({}, {}, [], [])
        self.assertEqual(result['recent_response_state'], 'empty_response')
        self.assertIsNone(result['recent_reported_total_count'])
        self.assertFalse(result['sample_missed_all_positive_recent_games'])

    def test_explicit_zero_recent_count_is_distinct_from_missing_data(self):
        result = probe.playtime_diagnostics({}, {'total_count': 0}, [], [])
        self.assertEqual(result['recent_response_state'], 'explicit_zero_count')
        self.assertEqual(result['recent_reported_total_count'], 0)
        failed = probe.playtime_diagnostics({}, None, [], [])
        self.assertEqual(failed['recent_response_state'], 'request_failed')

    def test_invalid_recent_minutes_are_visible_before_normalization(self):
        owned = {'game_count': 1, 'games': [{'appid': 1, 'playtime_forever': 10}]}
        recent = {'total_count': 1, 'games': [{'appid': 1, 'playtime_2weeks': 11}]}
        entries, _ = probe.normalize_library(owned, recent)
        result = probe.playtime_diagnostics(owned, recent, entries, entries)
        self.assertEqual(result['recent_rows_with_positive_minutes'], 1)
        self.assertEqual(result['library_games_with_positive_recent_minutes'], 0)
        self.assertIsNone(entries[0]['recent_minutes'])

    def test_recent_diagnostics_reject_malformed_games_and_boolean_count(self):
        result = probe.playtime_diagnostics({}, {'total_count': False, 'games': 'invalid'}, [], [])
        self.assertEqual(result['recent_response_state'], 'invalid_games_field')
        self.assertIsNone(result['recent_reported_total_count'])

    def test_full_library_mode_includes_recent_game_missed_by_sample(self):
        entries = [{'app_id': app, 'total_minutes': 20, 'recent_minutes': None} for app in range(1, 196)]
        sampled = probe.select_sample(entries, 50, None)
        sampled_ids = {row['app_id'] for row in sampled}
        omitted = next(row for row in entries if row['app_id'] not in sampled_ids)
        omitted['recent_minutes'] = 5
        all_games = probe.select_sample(entries, 50, None, all_games=True)
        self.assertEqual(len(all_games), 195)
        self.assertEqual(sum(row['recent_minutes'] is not None for row in sampled), 0)
        self.assertEqual(sum(row['recent_minutes'] is not None for row in all_games), 1)
        self.assertEqual({row['app_id'] for row in all_games}, {row['app_id'] for row in entries})

    def test_full_library_metadata_is_batched_beyond_provider_page_size(self):
        class FakeClient:
            def __init__(self):
                self.query_sizes = []
            def igdb(self, endpoint, query):
                if endpoint == 'external_games':
                    values = re.search(r'uid = \((.*?)\)', query).group(1)
                    ids = [int(value.strip('"')) for value in values.split(',')]
                    self.query_sizes.append(len(ids))
                    return [{'uid': str(app), 'game': app + 1000} for app in ids]
                ids = [int(value) for value in re.search(r'where id = \((.*?)\)', query).group(1).split(',')]
                self.query_sizes.append(len(ids))
                return [{'id': game, 'name': 'Public title', 'genres': [{'id': 1, 'name': 'RPG'}]} for game in ids]
        client = FakeClient()
        cache = {'entries': {}, 'steam_source_id': 42}
        cache['entries']['1'] = {'version': probe.CACHE_VERSION, 'mapping_status': 'mapped', 'fetched_epoch': probe.time.time(), 'genres': [{'id': 1, 'name': 'RPG'}]}
        results = probe.resolve_metadata(client, [{'app_id': app} for app in range(1, 602)], cache)
        self.assertEqual(len(results), 601)
        self.assertEqual(results[1]['source'], 'fresh_cache')
        self.assertEqual(len(cache['entries']), 601)
        self.assertTrue(all(0 < size <= probe.METADATA_BATCH_SIZE for size in client.query_sizes))
        self.assertEqual(sum(client.query_sizes), 1200)

    def test_all_games_conflicts_with_sample_size_before_any_requests(self):
        with patch('sys.argv', ['phase2_spike.py', '--all-games', '--sample-size', '50']), patch('sys.stderr', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as error:
                probe.main()
        self.assertEqual(error.exception.code, 2)

    def test_all_games_command_writes_full_report_with_recent_minutes(self):
        class FakeClient:
            def __init__(self, *_):
                self.calls = {'steam': 0, 'twitch': 0, 'igdb': 0}
            def steam(self, method, extra=None):
                self.calls['steam'] += 1
                if method == 'GetOwnedGames':
                    return {'game_count': 195, 'games': [{'appid': app, 'playtime_forever': 20} for app in range(1, 196)]}
                return {'total_count': 1, 'games': [{'appid': 195, 'playtime_2weeks': 5}]}
        saved = {}
        def capture(path, data):
            saved[path.name] = data
        with patch('sys.argv', ['phase2_spike.py', '--all-games', '--confirm-data-use']), patch.object(probe, 'settings_from', return_value={}), patch.object(probe, 'read_cache', return_value={'entries': {}}), patch.object(probe, 'Client', FakeClient), patch.object(probe, 'resolve_metadata', return_value={}), patch.object(probe, 'write_json', side_effect=capture), patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(probe.main(), 0)
        report = saved['report.json']
        self.assertEqual(report['selection'], 'all_library_games')
        self.assertEqual(report['summary']['sample_size'], report['library_size'])
        self.assertEqual(report['summary']['sample_size'], 195)
        self.assertEqual(report['steam_diagnostics']['sample_games_with_positive_recent_minutes'], 1)
        self.assertFalse(report['steam_diagnostics']['sample_missed_all_positive_recent_games'])


if __name__ == '__main__':
    unittest.main()
