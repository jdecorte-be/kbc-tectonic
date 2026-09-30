"""Adapter contract checks without contacting TypeSafe or reading a real key.

Run from repository root: python -m unittest discover -s backend/tests -p test_jev.py
"""

import copy
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from backend.app.jev import JevClient, JevError


QUESTIONS = {
    "travel": {"type": "noul", "instructions": "Is there evidence of upcoming travel?"},
    "evidence": {
        "type": "choice",
        "instructions": "Is the transaction evidence sufficient?",
        "criteria": {"sufficient": "Several consistent observations", "insufficient": "Missing history"},
    },
}
RESPONSE = {
    "model": "jev-1.13",
    "answers": {
        "travel": {"type": "noul", "noul": 0.92},
        "evidence": {
            "type": "choice", "choice": "sufficient", "confidence": 0.89,
            "probabilities": {"sufficient": 0.93, "insufficient": 0.07},
        },
    },
    "usage": {"input_tokens": 1250, "output_tokens": 42},
}


class JevClientTests(unittest.IsolatedAsyncioTestCase):
    async def client_for(self, handler, **kwargs):
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        self.addAsyncCleanup(http.aclose)
        return JevClient(api_key="test-secret-not-real", client=http, **kwargs)

    async def test_official_request_contract_and_actual_usage(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://api.typesafe.ai/v1/systemone")
            self.assertEqual(request.headers["Authorization"], "Bearer test-secret-not-real")
            self.assertEqual(json.loads(request.content), {
                "model": "jev-latest", "state": "Synthetic customer", "questions": QUESTIONS,
            })
            return httpx.Response(200, json=RESPONSE)

        client = await self.client_for(handler)
        result = await client.decide("Synthetic customer", QUESTIONS)
        self.assertEqual(result.answers, RESPONSE["answers"])
        self.assertEqual(result.model, "jev-1.13")
        self.assertEqual(result.input_tokens, 1250)
        self.assertEqual(result.output_tokens, 42)
        self.assertEqual(result.provider_input_tokens, 1250)
        self.assertEqual(result.provider_output_tokens, 42)
        self.assertFalse(result.tokens_estimated)
        self.assertEqual(result.request_count, 1)
        self.assertEqual(result.retry_count, 0)
        self.assertAlmostEqual(result.estimated_cost_usd, 1250 * 0.042 / 1_000_000)
        self.assertGreaterEqual(result.duration_ms, 0)
        self.assertTrue(result.cost_is_estimate)

    async def test_missing_usage_is_explicitly_estimated(self):
        body = copy.deepcopy(RESPONSE)
        del body["usage"]
        client = await self.client_for(lambda _: httpx.Response(200, json=body))
        result = await client.decide("Synthetic customer", QUESTIONS)
        self.assertTrue(result.tokens_estimated)
        self.assertIsNone(result.provider_input_tokens)
        self.assertIsNone(result.provider_output_tokens)
        self.assertGreater(result.input_tokens, 0)
        self.assertGreater(result.output_tokens, 0)
        self.assertGreater(result.estimated_cost_usd, 0)

    async def test_zero_output_usage_preserved_and_custom_prices(self):
        body = copy.deepcopy(RESPONSE)
        body["usage"]["output_tokens"] = 0
        client = await self.client_for(lambda _: httpx.Response(200, json=body), input_usd_per_million=1.5, output_usd_per_million=3)
        result = await client.decide("Synthetic customer", QUESTIONS)
        self.assertEqual(result.output_tokens, 0)
        self.assertFalse(result.tokens_estimated)
        self.assertAlmostEqual(result.estimated_cost_usd, 1250 * 1.5 / 1_000_000)
        self.assertTrue(client.pricing_info["custom_rates"])

    async def test_rate_limit_retried_with_accounting(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(429, headers={"Retry-After": "0"}) if len(requests) == 1 else httpx.Response(200, json=RESPONSE)

        client = await self.client_for(handler)
        with patch("backend.app.jev.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await client.decide("Synthetic customer", QUESTIONS)
        sleep.assert_awaited_once_with(0.0)
        self.assertEqual(result.request_count, 2)
        self.assertEqual(result.retry_count, 1)
        self.assertEqual(result.provider_input_tokens, 1250)
        self.assertGreater(result.estimated_retry_cost_usd, 0)
        self.assertGreater(result.estimated_retry_input_tokens, 0)
        self.assertGreater(result.estimated_cost_usd, 1250 * 0.042 / 1_000_000)

    async def test_exhausted_timeouts_are_bounded_and_report_attempts(self):
        def handler(request):
            raise httpx.ReadTimeout("contains test-secret-not-real", request=request)

        client = await self.client_for(handler, max_retries=2)
        with patch("backend.app.jev.asyncio.sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(JevError) as raised:
                await client.decide("Synthetic customer", QUESTIONS)
        error = raised.exception
        self.assertEqual(error.code, "timeout")
        self.assertEqual(error.request_count, 3)
        self.assertEqual(error.retry_count, 2)
        self.assertEqual(sleep.await_count, 2)
        self.assertGreater(error.estimated_cost_usd, 0)
        self.assertGreater(error.estimated_input_tokens, 0)
        self.assertNotIn("test-secret", str(error))

    async def test_authentication_errors_do_not_retry_or_expose_upstream_body(self):
        client = await self.client_for(lambda _: httpx.Response(401, text="test-secret-not-real"))
        with patch("backend.app.jev.asyncio.sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(JevError) as raised:
                await client.decide("Synthetic customer", QUESTIONS)
        self.assertEqual(raised.exception.code, "authentication")
        self.assertEqual(raised.exception.request_count, 1)
        self.assertNotIn("test-secret", str(raised.exception))
        sleep.assert_not_awaited()

    async def test_redirects_are_not_followed_even_by_injected_client(self):
        calls = []

        def handler(request):
            calls.append(str(request.url))
            return httpx.Response(307, headers={"Location": "https://unrelated.example/collect"})

        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
        self.addAsyncCleanup(http.aclose)
        client = JevClient(api_key="test-secret-not-real", client=http)
        with self.assertRaises(JevError) as raised:
            await client.decide("Synthetic customer", QUESTIONS)
        self.assertEqual(raised.exception.code, "http_307")
        self.assertEqual(len(calls), 1)

    async def test_malformed_responses_cannot_become_recommendations(self):
        bodies = []
        missing_answer = copy.deepcopy(RESPONSE)
        del missing_answer["answers"]["travel"]
        bodies.append(missing_answer)
        invalid_probability = copy.deepcopy(RESPONSE)
        invalid_probability["answers"]["travel"]["noul"] = 1.4
        bodies.append(invalid_probability)
        invented_choice = copy.deepcopy(RESPONSE)
        invented_choice["answers"]["evidence"]["choice"] = "invented"
        bodies.append(invented_choice)
        negative_usage = copy.deepcopy(RESPONSE)
        negative_usage["usage"]["input_tokens"] = -12
        bodies.append(negative_usage)
        invalid_distribution = copy.deepcopy(RESPONSE)
        invalid_distribution["answers"]["evidence"]["probabilities"] = {"sufficient": 0.9, "insufficient": 0.9}
        bodies.append(invalid_distribution)
        wrong_type = copy.deepcopy(RESPONSE)
        wrong_type["answers"]["travel"] = copy.deepcopy(RESPONSE["answers"]["evidence"])
        bodies.append(wrong_type)
        nan_probability = copy.deepcopy(RESPONSE)
        nan_probability["answers"]["travel"]["noul"] = float("nan")
        bodies.append(nan_probability)
        for body in bodies:
            with self.subTest(body=body):
                client = await self.client_for(lambda _, body=body: httpx.Response(200, content=json.dumps(body)))
                with self.assertRaises(JevError) as raised:
                    await client.decide("Synthetic customer", QUESTIONS)
                self.assertEqual(raised.exception.code, "invalid_response")
                self.assertEqual(raised.exception.request_count, 1)

    async def test_invalid_json_reports_safe_validation_error(self):
        client = await self.client_for(lambda _: httpx.Response(200, text="<html>failed</html>"))
        with self.assertRaises(JevError) as raised:
            await client.decide("Synthetic customer", QUESTIONS)
        self.assertEqual(raised.exception.code, "invalid_response")

    async def test_missing_key_fails_without_network_request(self):
        client = JevClient(api_key="")
        self.assertFalse(client.configured)
        with self.assertRaises(JevError) as raised:
            await client.decide("Synthetic customer", QUESTIONS)
        self.assertEqual(raised.exception.code, "missing_api_key")
        self.assertEqual(raised.exception.request_count, 0)

    async def test_environment_configuration_and_base_url(self):
        with patch.dict("os.environ", {"JEV_API": "test-env-key", "JEV_API_URL": "https://api.typesafe.ai", "JEV_MODEL": "custom-model", "JEV_INPUT_USD_PER_MILLION": "0.25"}):
            client = JevClient()
        self.assertTrue(client.configured)
        self.assertEqual(client.endpoint, "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(client.model, "custom-model")
        self.assertEqual(client.pricing_info["input_usd_per_million"], 0.25)

    async def test_scores_keep_distribution_and_rubric(self):
        questions = {"fit": {"type": "score", "criteria": ["No fit", "Possible", "Clear fit"]}}
        body = {
            "model": "jev-1.13", "usage": {"input_tokens": 80, "output_tokens": 3},
            "answers": {"fit": {"type": "score", "score": 1.7, "confidence": 0.8,
                "legend": {"0": "No fit", "1": "Possible", "2": "Clear fit"},
                "probabilities": {"0": 0.1, "1": 0.1, "2": 0.8}}},
        }
        client = await self.client_for(lambda _: httpx.Response(200, json=body))
        result = await client.decide("Synthetic customer", questions)
        self.assertEqual(result.answers["fit"]["score"], 1.7)
        self.assertEqual(result.answers["fit"]["legend"], body["answers"]["fit"]["legend"])

    async def test_invalid_questions_fail_before_request(self):
        client = JevClient(api_key="test-key")
        for questions in ({}, {"fit": {"type": "bool"}}, {"fit": {"type": "choice", "criteria": []}}):
            with self.subTest(questions=questions):
                with self.assertRaises(JevError) as raised:
                    await client.decide("Synthetic customer", questions)
                self.assertEqual(raised.exception.request_count, 0)
                self.assertEqual(raised.exception.code, "invalid_request")


if __name__ == "__main__":
    unittest.main()
