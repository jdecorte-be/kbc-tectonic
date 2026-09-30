import asyncio
from types import SimpleNamespace
import unittest

from app.benchmark import BenchmarkBusy, BenchmarkManager, aggregate_metrics


class FakeWorkflow:
    def __init__(self, fail=False, delay=.001):
        self.data = SimpleNamespace(benchmark_clients=lambda count: [str(index) for index in range(count)])
        self.active = 0
        self.peak = 0
        self.calls = []
        self.fail = fail
        self.delay = delay

    async def analyse(self, identifier):
        self.calls.append(identifier)
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            await asyncio.sleep(self.delay)
            if self.fail and identifier == '0':
                raise RuntimeError('Unexpected worker failure')
            status = ['recommended', 'no_match', 'opt_out', 'error'][int(identifier) % 4]
            calls = 0 if status == 'opt_out' else 2
            return {'client': {'id': identifier}, 'status': status, 'facts': {}, 'ads': [],
                    'metrics': {'duration_ms': 10 + int(identifier), 'api_calls': calls, 'input_tokens': calls * 100,
                                'output_tokens': calls * 10, 'estimated_cost_usd': calls * .001,
                                'usage_source': 'provider' if calls else 'none'}}
        finally:
            self.active -= 1


class BenchmarkTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_10_100_1000_runs_and_bounded_concurrency(self):
        for count in (10, 100, 1000):
            workflow = FakeWorkflow(delay=0)
            manager = BenchmarkManager(workflow)
            initial = manager.start(count, 3)
            self.assertEqual(initial['status'], 'running')
            with self.assertRaises(BenchmarkBusy):
                manager.start(10, 2)
            await manager.tasks[initial['id']]
            result = manager.snapshot(initial['id'])
            self.assertEqual(result['status'], 'completed')
            self.assertEqual(result['completed_count'], count)
            self.assertEqual(len(workflow.calls), count)
            self.assertEqual(len(set(workflow.calls)), count)
            self.assertEqual(workflow.peak, 3)
            self.assertEqual(result['metrics']['api_calls'], sum(item['metrics']['api_calls'] for item in result['results']))
            self.assertEqual(result['metrics']['recommended_count'] + result['metrics']['abstained_count'] + result['metrics']['opt_out_count'] + result['metrics']['error_count'], count)
            self.assertGreater(result['elapsed_ms'], 0)
            self.assertEqual(len(manager.snapshot(initial['id'], results_limit=2)['results']), 2)
            self.assertEqual(manager.snapshot(initial['id'], results_limit=2)['completed_count'], count)
            await manager.close()

    async def test_cancel_finishes_inflight_work_and_records_cost(self):
        workflow = FakeWorkflow(delay=.01)
        manager = BenchmarkManager(workflow)
        initial = manager.start(10, 2)
        task = manager.tasks[initial['id']]
        while workflow.active < 2:
            await asyncio.sleep(0)
        pending = manager.cancel(initial['id'])
        self.assertTrue(pending['cancel_requested'])
        self.assertEqual(pending['status'], 'running')
        await task
        result = manager.snapshot(initial['id'])
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(result['completed_count'], 2)
        self.assertEqual(result['metrics']['api_calls'], 4)
        self.assertAlmostEqual(result['metrics']['estimated_cost_usd'], .004)
        self.assertEqual(workflow.active, 0)

    async def test_unexpected_worker_failure_waits_for_siblings_before_finalizing(self):
        workflow = FakeWorkflow(fail=True, delay=.001)
        manager = BenchmarkManager(workflow)
        initial = manager.start(10, 3)
        await manager.tasks[initial['id']]
        result = manager.snapshot(initial['id'])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['completed_count'], 9)
        self.assertEqual(workflow.active, 0)
        elapsed = result['elapsed_ms']
        await asyncio.sleep(.005)
        final = manager.snapshot(initial['id'])
        self.assertEqual(final['completed_count'], 9)
        self.assertEqual(final['elapsed_ms'], elapsed)

    def test_percentiles_costs_and_abstention_are_distinct(self):
        rows = [{'status': status, 'metrics': {'duration_ms': latency, 'api_calls': calls, 'input_tokens': 10,
                  'output_tokens': 2, 'estimated_cost_usd': .001, 'usage_source': source}}
                for status, latency, calls, source in [('recommended', 10, 2, 'provider'), ('opt_out', 2, 0, 'none'),
                    ('insufficient_information', 4, 0, 'none'), ('error', 100, 3, 'estimated')]]
        metric = aggregate_metrics(rows, 200)
        self.assertEqual(metric['p50_latency_ms'], 4)
        self.assertEqual(metric['p95_latency_ms'], 100)
        self.assertEqual(metric['average_latency_ms'], 29)
        self.assertEqual(metric['clients_per_second'], 20)
        self.assertEqual(metric['api_calls'], 5)
        self.assertEqual(metric['usage_source'], 'estimated')
        self.assertEqual(metric['opt_out_count'], 1)
        self.assertEqual(metric['abstained_count'], 1)
        self.assertAlmostEqual(metric['estimated_cost_usd'], .004)
