import asyncio
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from app.banking import BankData, cents, extract_facts
from app.jev import JevError, JevResult
from app.workflow import Workflow, candidate_products, supported_signals


def profile(identifier='TEST-1', consent=True):
    transactions = []
    balance = 100000
    for month in (7, 8, 9):
        for category, direction, amount in [('salaire', 'credit', 300000), ('transfert_epargne', 'debit', 20000), ('carburant', 'debit', 5500), ('assurance_auto', 'debit', 5500)]:
            balance += amount if direction == 'credit' else -amount
            transactions.append({'transaction_id': f'{identifier}-TX-{len(transactions)}', 'date': f'2026-{month:02}-15',
                'sens': direction, 'montant': amount / 100, 'categorie': category, 'type': 'ordre_permanent',
                'contrepartie': 'Synthetic merchant', 'pays_contrepartie': 'Belgique', 'solde_apres': balance / 100})
    return {'client_id': identifier, 'synthetique': True, 'scenario_simulation': 'SECRET_GROUND_TRUTH',
        'prenom': 'Test', 'age': 30, 'ville': 'Bruxelles', 'pays': 'Belgique',
        'preferences': {'personnalisation_commerciale': consent},
        'compte': {'debut_historique': '2026-07-01', 'fin_historique': '2026-09-30',
                   'solde_initial': 1000, 'solde_final': balance / 100, 'transactions': transactions}}


class FakeRegistry:
    def snapshot(self):
        return {'items': [{'id': 'worker', 'label': 'Worker'}], 'questions': []}


class FakeCategories:
    def __init__(self, unknown=False):
        self.calls = []
        self.unknown = unknown
        self.registry = FakeRegistry()

    async def classify(self, client_id, state, evidence_ids):
        self.calls.append(state)
        return {'category': {'id': 'UNKNOWN' if self.unknown else 'worker', 'label': 'UNKNOWN' if self.unknown else 'Worker',
                            'source': 'jev', 'confidence': .95, 'evidence': evidence_ids[:2], 'created': False},
                'metrics': {'api_calls': 1, 'input_tokens': 20, 'output_tokens': 5, 'estimated_cost_usd': .001,
                            'tokens_estimated': False, 'openai_calls': 0,
                            'providers': {'jev': {'api_calls': 1, 'input_tokens': 20, 'output_tokens': 5, 'estimated_cost_usd': .001}}},
                'stages': [{'name': 'Jev category', 'status': 'completed', 'duration_ms': 1, 'detail': 'Worker'}], 'error': None}


class FakeJev:
    configured = True
    def __init__(self, confidence=.95, fail_at=None):
        self.confidence = confidence
        self.fail_at = fail_at
        self.calls = []

    async def decide(self, state, questions):
        self.calls.append((state, questions))
        if len(self.calls) == self.fail_at:
            raise JevError('Test provider failure.', request_count=2, estimated_cost_usd=.002, estimated_input_tokens=200)
        return JevResult(answers={key: {'type': 'noul', 'noul': self.confidence} for key in questions},
                         model='test', input_tokens=100, output_tokens=10, tokens_estimated=False,
                         request_count=1, retry_count=0, duration_ms=5, estimated_cost_usd=.0005)


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        path = Path(self.temp.name) / 'data.json'
        path.write_text(json.dumps([profile(), profile('OPT-OUT', consent=False)]))
        self.data = BankData(data_path=str(path))

    def tearDown(self):
        self.temp.cleanup()

    async def test_opt_out_and_sparse_do_not_call_providers(self):
        jev, categories = FakeJev(), FakeCategories()
        workflow = Workflow(self.data, jev, category_service=categories)
        for identifier, status in [('OPT-OUT', 'opt_out'), ('SYN-SPARSE', 'insufficient_information')]:
            result = await workflow.analyse(identifier)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['metrics']['api_calls'], 0)
            self.assertEqual(result['metrics']['estimated_cost_usd'], 0)
            self.assertEqual(result['ads'], [])
        self.assertEqual(jev.calls, [])
        self.assertEqual(categories.calls, [])

    async def test_full_workflow_uses_jev_and_exact_catalogue_copy(self):
        jev, categories = FakeJev(), FakeCategories()
        result = await Workflow(self.data, jev, category_service=categories).analyse('TEST-1')
        self.assertEqual(result['status'], 'recommended')
        self.assertEqual(result['category']['label'], 'Worker')
        self.assertEqual(result['metrics']['api_calls'], 3)
        self.assertEqual(result['metrics']['input_tokens'], 220)
        self.assertAlmostEqual(result['metrics']['estimated_cost_usd'], .002)
        self.assertEqual(result['metrics']['providers']['jev']['api_calls'], 3)
        catalogue = {item['id']: item['description'] for item in self.data.products}
        for ad in result['ads']:
            self.assertEqual(ad['body'], catalogue[ad['product_id']])
            self.assertIn('TX-', ' '.join(ad['evidence']))
        self.assertNotIn('SECRET_GROUND_TRUTH', json.dumps(jev.calls) + json.dumps(categories.calls))
        self.assertNotIn('scenario_simulation', json.dumps(jev.calls) + json.dumps(categories.calls))
        self.assertIn('customer_category', json.loads(jev.calls[1][0]))

    async def test_unknown_and_low_support_abstain(self):
        jev = FakeJev()
        result = await Workflow(self.data, jev, category_service=FakeCategories(unknown=True)).analyse('TEST-1')
        self.assertEqual(result['status'], 'insufficient_information')
        self.assertEqual(jev.calls, [])
        result = await Workflow(self.data, FakeJev(confidence=.2), category_service=FakeCategories()).analyse('TEST-1')
        self.assertEqual(result['status'], 'insufficient_information')
        self.assertEqual(result['ads'], [])

    async def test_provider_failure_keeps_prior_and_retry_costs(self):
        result = await Workflow(self.data, FakeJev(fail_at=2), category_service=FakeCategories()).analyse('TEST-1')
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['ads'], [])
        self.assertEqual(result['metrics']['api_calls'], 4)
        self.assertEqual(result['metrics']['input_tokens'], 320)
        self.assertAlmostEqual(result['metrics']['estimated_cost_usd'], .0035)
        self.assertEqual(result['metrics']['usage_source'], 'estimated')
        self.assertEqual(result['metrics']['providers']['jev']['usage_source'], 'estimated')
        self.assertTrue(result['metrics']['providers']['jev']['tokens_estimated'])

    async def test_missing_key_is_an_explicit_error(self):
        jev = FakeJev()
        jev.configured = False
        result = await Workflow(self.data, jev, category_service=FakeCategories()).analyse('TEST-1')
        self.assertEqual(result['status'], 'error')
        self.assertIn('JEV_API', result['error'])
        self.assertEqual(result['metrics']['api_calls'], 0)

    def test_facts_use_exact_cents_and_do_not_confuse_saving_with_spending(self):
        facts = self.data.facts('TEST-1')
        self.assertEqual(cents('1.10'), 110)
        self.assertEqual(facts['total_credit_cents'], 900000)
        self.assertEqual(facts['total_debit_cents'], 93000)
        self.assertEqual(facts['consumption_debit_cents'], 33000)
        self.assertEqual(facts['balance_cents'], 907000)
        self.assertEqual(facts['existing_insurance'], ['assurance_auto'])
        self.assertEqual(len(facts['monthly_cashflow']), 3)
        self.assertNotIn('scenario_simulation', self.data.get('TEST-1'))

    def test_existing_insurance_and_unknown_future_plans_do_not_get_advertised(self):
        facts = self.data.facts('TEST-1')
        profiles = [{**item, 'confidence': .99} for item in supported_signals(facts)]
        candidates = candidate_products(self.data.products, profiles, facts)
        names = [item['name'] for item in candidates]
        self.assertTrue(any('Start2Save' in name for name in names))
        self.assertFalse(any('Insurance' in name or 'Loan' in name for name in names))
        facts['habits']['negative_balance_observation_count'] = 1
        self.assertEqual(candidate_products(self.data.products, profiles, facts), [])
