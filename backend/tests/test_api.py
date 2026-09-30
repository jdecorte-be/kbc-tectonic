"""Real HTTP contracts and restart durability, using no paid provider calls."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.banking import sparse_client
from app.config import Settings
from app.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        profiles = []
        for index in range(10):
            profile = deepcopy(sparse_client())
            profile['client_id'] = f'API-CLIENT-{index}'
            profile['compte']['transactions'][0]['transaction_id'] = f'API-TX-{index}'
            profiles.append(profile)
        source = root / 'clients.json'
        source.write_text(json.dumps(profiles))
        self.config = Settings(DATABASE_URL=f'sqlite:///{root / "bank.sqlite3"}',
                               CATEGORY_DB_PATH=str(root / 'categories.sqlite3'),
                               BANK_DATA_PATH=str(source), PRODUCTS_PATH='')

    def tearDown(self):
        self.temp.cleanup()

    def test_database_health_search_detail_and_pagination(self):
        with TestClient(create_app(self.config)) as client:
            health = client.get('/api/health')
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()['database'], 'connected')
            self.assertEqual(health.json()['storage'], 'sqlite')
            page = client.get('/api/clients', params={'q': 'API-CLIENT', 'limit': 3, 'offset': 3}).json()
            self.assertEqual(page['total'], 10)
            self.assertEqual(len(page['items']), 3)
            detail = client.get('/api/clients/API-CLIENT-0').json()
            transactions = client.get('/api/clients/API-CLIENT-0/transactions', params={'limit': 1}).json()
            self.assertEqual(transactions['items'], detail['transactions'])
            self.assertEqual(transactions['total'], 1)
            self.assertEqual(client.get('/api/clients/missing').status_code, 404)
            self.assertEqual(client.get('/api/clients', params={'offset': -1}).status_code, 422)
            self.assertEqual(client.get('/api/clients/API-CLIENT-0/transactions', params={'limit': 1001}).status_code, 422)

    def test_saved_analysis_survives_app_restart(self):
        with TestClient(create_app(self.config)) as client:
            response = client.post('/api/analyses', json={'client_id': 'API-CLIENT-0'})
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
            self.assertEqual(result['status'], 'insufficient_information')
            self.assertEqual(result['metrics']['api_calls'], 0)
            identifier = result['analysis_id']
        with TestClient(create_app(self.config)) as client:
            restored = client.get(f'/api/analyses/{identifier}')
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.json(), result)
            history = client.get('/api/analyses', params={'client_id': 'API-CLIENT-0'}).json()
            self.assertEqual(history['total'], 1)
            self.assertEqual(history['items'][0]['id'], identifier)
            self.assertEqual(client.get('/api/analyses', params={'client_id': 'API-CLIENT-1'}).json()['total'], 0)
            self.assertEqual(client.get('/api/analyses/missing').status_code, 404)

    def test_benchmark_survives_restart_with_same_metrics(self):
        with TestClient(create_app(self.config)) as client:
            response = client.post('/api/benchmarks', json={'count': 10, 'concurrency': 3})
            self.assertEqual(response.status_code, 202, response.text)
            identifier = response.json()['id']
            deadline = time.monotonic() + 5
            result = response.json()
            while result['status'] == 'running' and time.monotonic() < deadline:
                result = client.get(f'/api/benchmarks/{identifier}').json()
                time.sleep(.01)
            self.assertEqual(result['status'], 'completed', result)
            self.assertEqual(result['completed_count'], 10)
            self.assertEqual(result['metrics']['api_calls'], 0)
        with TestClient(create_app(self.config)) as client:
            restored = client.get(f'/api/benchmarks/{identifier}', params={'results_limit': 2, 'results_offset': 3}).json()
            self.assertEqual(restored['completed_count'], 10)
            self.assertEqual(len(restored['results']), 2)
            self.assertEqual(restored['metrics'], result['metrics'])
            history = client.get('/api/benchmarks').json()
            self.assertEqual(history['total'], 1)
            self.assertEqual(history['items'][0]['id'], identifier)
            self.assertEqual(client.delete(f'/api/benchmarks/{identifier}').json()['status'], 'completed')
            self.assertEqual(client.get('/api/benchmarks/missing').status_code, 404)

    def test_validation_and_missing_clients_never_start_work(self):
        with TestClient(create_app(self.config)) as client:
            for payload in ({'count': 25}, {'count': 10, 'concurrency': True}, {'count': 10, 'concurrency': 11}, {'count': 10, 'unexpected': 1}):
                self.assertEqual(client.post('/api/benchmarks', json=payload).status_code, 422)
            self.assertEqual(client.post('/api/analyses', json={'client_id': 'missing'}).status_code, 404)
            self.assertEqual(client.post('/api/analyses', json={'client_id': 'API-CLIENT-0', 'unexpected': 1}).status_code, 422)
            self.assertEqual(client.get('/api/benchmarks').json()['total'], 0)

    def test_failed_database_readiness_is_503(self):
        app = create_app(self.config)
        with TestClient(app) as client:
            with patch.object(app.state.repository, 'check_health', return_value=False):
                self.assertEqual(client.get('/api/health').status_code, 503)
