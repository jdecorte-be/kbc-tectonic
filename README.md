# KBC Signal · Jev + OpenAI

A hackathon demo that profiles synthetic banking customers, matches supported interests to the products in `products.json`, and measures the cost and latency of real batch runs. Insufficient information and no suitable advert are valid outcomes.

## Run the demo

Keep `JEV_API` and `OPENAI_API_KEY` in your shell environment or the root `.env` file. Copy `.env.example` for configuration. Credentials are used only on the server.

### Docker

```sh
make up
```

Open **http://localhost:3000**. Interactive API documentation: http://localhost:8000/api/docs. Customers are generated automatically; SQLite categories persist in a Docker volume. PostgreSQL is not required.

### Local development

Requirements: Python 3.11+, Node.js 22+ and pnpm 12.6.0.

```sh
make install
make backend
```

In another terminal at the repository root:

```sh
make frontend
```

Nuxt proxies browser requests from `/api` to `NUXT_API_BASE`, which defaults to `http://127.0.0.1:8000`.

## Demo flow

1. Select a synthetic customer, inspect their balance and transactions, and run the analysis.
2. Review their inferred category, supported behavioral signals, evidence, and relevant product adverts.
3. The initial category question offers **Student**, **Worker**, and **UNKNOWN**. If Jev chooses UNKNOWN, OpenAI can identify a supported missing category, such as **Retired** from recurring pension payments.
4. The new category, its definition, question history, and customer assignment are saved in SQLite. The next Jev run reads the updated choices directly from the database. This expands the available choices; it does not retrain Jev.
5. Inspect learned categories in the category registry. If neither model has sufficient evidence, the result stays UNKNOWN.
6. Select **SYN-SPARSE** to show abstention when there is too little history.
7. Run a benchmark with **10, 100, or 1,000 customers** and 1–10 concurrent workflows. Inspect progress, individual results and adverts, wall time, throughput, p50/p95 latency, calls, tokens and estimated cost.

## How decisions work

- `generate_bank_profiles.py` supplies deterministic fake accounts, transactions, counterparties, categories, and balances. The app generates 1,000 customers plus a sparse example. Set `BANK_DATA_PATH` to load an existing JSON array of explicitly synthetic profiles. The generator's hidden `scenario_simulation` label is excluded from inference.
- Financial facts are calculated in integer cents. Evidence includes transaction identifiers, category aggregates, recurring payments, cash flow, and changes against each customer's own history. Order line items are absent and remain unknown.
- Every categorical Jev choice includes **UNKNOWN**. OpenAI's fallback returns a strict JSON structure and may reuse a known category, propose a new one, or abstain. Category definitions are persisted with provenance. Evidence must reference supplied transactions before a learned category is accepted.
- Jev validates behavioral signals and scores relevant catalogue products. Current balance is not treated as total wealth or disposable budget; past travel does not establish a future holiday; observed insurance prevents presenting a duplicate as missing cover.
- Adverts use the supplied product descriptions and factual templates. No rates, investment returns, coverage details, or eligibility promises are invented.
- Customers who disabled personalization receive no adverts and trigger no AI requests. Provider failures are reported as errors, separately from abstentions. Missing keys never trigger a silent fake AI result.

## Benchmark and estimated cost

The benchmark executes the real workflow for each selected customer; it does not extrapolate a small run to pretend that 1,000 customers were processed. It uses bounded concurrency and a monotonic server clock. A cancelled run drains in-flight work so its usage can still be counted.

Cost is an **estimate in USD for Jev and OpenAI API calls**, excluding hosting and infrastructure. Provider token usage is used when available. Missing usage and failed attempts are explicitly estimated. Call counts include retries. The provider invoice remains authoritative.

| Provider | Default model | Input / 1M tokens | Output / 1M tokens | Source |
| --- | --- | --- | --- | --- |
| TypeSafe | `jev-latest` | $0.042 | $0 | [Official announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev) |
| OpenAI | `gpt-4.1-mini` | $0.40 | $1.60 | [Official model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini) |

Override rates with `JEV_INPUT_USD_PER_MILLION`, `JEV_OUTPUT_USD_PER_MILLION`, `OPENAI_INPUT_USD_PER_MILLION`, and `OPENAI_OUTPUT_USD_PER_MILLION`. OpenAI cached input is conservatively charged at the regular input rate in the estimate. When changing the model, configure matching prices.

The customer rate includes opt-outs and abstentions, which are shown separately. Category discovery can add OpenAI latency to an initial run; subsequent runs can reuse learned categories through Jev. Compare runs with the registry state and error counts in mind. Benchmark jobs have bounded in-memory retention and are lost on backend restart; the category registry persists. Use one backend process for this demo.

## Persistence and API

`CATEGORY_DB_PATH` sets the SQLite registry location; the default is `data/categories.sqlite3`. The database is ignored by Git. Docker stores it in `category_data`.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Configuration, models, prices, dataset size |
| `GET /api/clients?q=&limit=50&offset=0` | Search customers |
| `GET /api/clients/{id}` | Customer facts and transactions |
| `GET /api/products` | Product catalogue |
| `GET /api/categories` | Persisted categories and question definitions |
| `POST /api/analyses` | Run `{"client_id":"…"}` |
| `POST /api/benchmarks` | Start `{"count":10,"concurrency":5}` |
| `GET /api/benchmarks/{id}` | Progress, metrics and results |
| `DELETE /api/benchmarks/{id}` | Request benchmark cancellation |

Provider contracts: [TypeSafe OpenAPI](https://api.typesafe.ai/openapi.json) and [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs). OpenAI requests use the Responses API with `store: false`.

## Verification

```sh
make test
cd frontend
pnpm typecheck
pnpm build
```

Backend unit tests use simulated providers and make no paid API requests. They cover abstention, opt-outs, typed response validation, failure accounting, batch metrics, and persistence of learned category choices.
