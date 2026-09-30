"""OpenAI fallback request/response checks without sending real credentials."""

import json
import unittest
import httpx

from backend.app.openai_classifier import OpenAIClassifier, OpenAIError


DECISION = {"action": "unknown", "category_id": "UNKNOWN", "label": "UNKNOWN", "description": "Insufficient evidence.",
            "confidence": 0.9, "evidence_ids": [], "support_kind": "none", "reason": "No income observations provided."}


class OpenAIClassifierTests(unittest.IsolatedAsyncioTestCase):
    async def build(self, handler):
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        self.addAsyncCleanup(http.aclose)
        return OpenAIClassifier(api_key="fake-secret", client=http, max_retries=0)

    async def test_strict_responses_api_and_provider_usage(self):
        def handler(request):
            self.assertEqual(str(request.url), "https://api.openai.com/v1/responses")
            payload = json.loads(request.content)
            self.assertFalse(payload["store"])
            self.assertTrue(payload["text"]["format"]["strict"])
            self.assertEqual(payload["text"]["format"]["type"], "json_schema")
            self.assertFalse(payload["text"]["format"]["schema"]["additionalProperties"])
            self.assertNotIn("UNKNOWN", [item["id"] for item in json.loads(payload["input"])["existing_categories"]])
            self.assertIn("CREATE it", payload["instructions"])
            return httpx.Response(200, json={"status": "completed", "model": "gpt-4.1-mini",
                "usage": {"input_tokens": 200, "output_tokens": 80}, "output": [
                    {"type": "message", "content": [{"type": "output_text", "text": json.dumps(DECISION)}]}]})
        result = await (await self.build(handler)).classify('{"evidence":[]}', [{"id": "UNKNOWN", "label": "UNKNOWN"}], [])
        self.assertEqual(result.decision, DECISION)
        self.assertEqual(result.input_tokens, 200)
        self.assertFalse(result.tokens_estimated)
        self.assertAlmostEqual(result.estimated_cost_usd, (200 * .4 + 80 * 1.6) / 1_000_000)

    async def test_refusal_retains_actual_billed_usage(self):
        client = await self.build(lambda _: httpx.Response(200, json={"status": "completed", "model": "gpt-4.1-mini",
            "usage": {"input_tokens": 200, "output_tokens": 14}, "output": [
                {"type": "message", "content": [{"type": "refusal", "refusal": "No."}]}]}))
        with self.assertRaises(OpenAIError) as raised:
            await client.classify('{"evidence":[]}', [], [])
        error = raised.exception
        self.assertEqual(error.code, "refusal")
        self.assertEqual(error.input_tokens, 200)
        self.assertEqual(error.output_tokens, 14)
        self.assertFalse(error.tokens_estimated)

    async def test_invalid_structured_output_retains_usage(self):
        client = await self.build(lambda _: httpx.Response(200, json={"status": "completed", "model": "gpt-4.1-mini",
            "usage": {"input_tokens": 200, "output_tokens": 14}, "output": [
                {"type": "message", "content": [{"type": "output_text", "text": '{"action":"invented"}'}]}]}))
        with self.assertRaises(OpenAIError) as raised:
            await client.classify('{"evidence":[]}', [], [])
        self.assertEqual(raised.exception.code, "invalid_response")
        self.assertEqual(raised.exception.input_tokens, 200)

    async def test_http_error_is_safe_and_redirects_are_rejected(self):
        for status in (401, 302):
            client = await self.build(lambda _, status=status: httpx.Response(status, text="fake-secret", headers={"Location": "https://unrelated.example"}))
            with self.assertRaises(OpenAIError) as raised:
                await client.classify('{"evidence":[]}', [], [])
            self.assertNotIn("fake-secret", str(raised.exception))
            self.assertEqual(raised.exception.request_count, 1)


if __name__ == "__main__":
    unittest.main()
