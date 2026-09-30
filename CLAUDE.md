# CLAUDE.md

Hackathon project (KBC). Speed and a working demo matter more than polish. Prefer simple solutions, mock data over real integrations, and finish end-to-end flows before adding features.

## Product idea

An app that analyses the **transactions of KBC clients** to infer a **customer profile / life-stage segment**, so the bank can understand who a client is and act on it (personalised offers, advice, alerts).

### Habit tracking

The goal is also to **track clients' habits over time**, not only label them. Profiles are derived from habits.

Habits to detect:
- **Spending rhythm** – when they spend (payday spike, weekends, nights), average basket size, frequency per category.
- **Recurring payments** – subscriptions, rent, insurance, gym; new/cancelled/changed ones.
- **Saving & investing behaviour** – regularity and size of transfers to savings/brokerage.
- **Merchant/category loyalty** – favourite shops, eating out vs. groceries, online vs. in-store.
- **Mobility** – fuel, transit, travel, spending abroad.
- **Cash vs. card** – ATM withdrawal frequency and amounts.
- **Income pattern** – regular salary vs. irregular income, payday date.
- **Balance behaviour** – end-of-month balance, overdraft frequency.

Habit changes are the most valuable signal (e.g. sudden travel spend, new baby-shop purchases, stopped student-canteen payments): detect **drift vs. the client's own baseline** and surface it as an event/alert, and use it to trigger profile changes.

### Target profiles (segments)

Core:
- **Student** – small recurring income/allowance, tuition, cheap food, public transport, streaming.
- **Young investor** – first salary, regular transfers to brokerage/savings, crypto/ETF purchases.
- **Investor** – large/recurring investment flows, brokerage fees, diversified holdings.
- **Going on holiday soon** – travel bookings (flights, hotels, Airbnb), FX/ATM abroad, travel insurance, luggage/outdoor shops.

Extra ideas:
- **New parent / family** – baby shops, childcare, pharmacies, larger groceries.
- **Homebuyer / mover** – notary, agency, furniture/DIY, mortgage simulations, rent stops.
- **Car owner / commuter** – fuel, tolls, parking, car insurance, leasing.
- **Freelancer / self-employed** – irregular incoming payments, VAT, coworking, software subscriptions.
- **Saver** – steady outflows to savings, low discretionary spend.
- **Financial stress** – overdraft, rejected payments, payday loans, rising fixed costs (handle sensitively).
- **Retiree / pre-retiree** – pension income, healthcare, pension savings.
- **Wedding / big event** – venues, jewelry, catering.

Design notes:
- A client can have **multiple profiles with a confidence score**, and profiles change over time (trend, not a one-off label).
- Classification is **explainable**: always show *which transactions/signals* led to a profile.
- Start rule-based (merchant category / MCC, recurring patterns, amounts); ML is optional.
- Privacy/GDPR: use synthetic or anonymised data only. Never commit real client data.

## Repo layout

- `frontend/` – Nuxt 4 app (Vue 3, TypeScript). Currently a dashboard template.
  - `app/pages/` – routes (`index.vue`, `dashboard/`)
  - `app/components/` – app components; `components/ui/` holds shadcn-vue components
  - `app/lib/utils.ts` – `cn()` helper
  - `app/assets/css/main.css` – Tailwind v4 + theme variables
- `backend/` – empty so far (API, transaction data, profiling logic will go here).
- `frontend/my-app/` – stray `.nuxt` artefact; ignore it.

## Frontend stack

Nuxt 4, Nuxt UI 4, shadcn-vue (`reka-nova` style, config in `frontend/components.json`), Tailwind CSS v4, reka-ui, TanStack Vue Table, Unovis (charts), dnd-kit, VueUse, Zod, Lucide / Tabler icons.

Path aliases: `@/components`, `@/lib`, `@/components/ui`, `@/composables`.

## Commands (run in `frontend/`)

Package manager is **pnpm** (don't use npm; `package-lock.json` is stale).

```bash
pnpm install
pnpm dev          # dev server
pnpm build
pnpm lint
pnpm typecheck
pnpm gen:api     # regenerate app/types/api.gen.ts from the backend OpenAPI spec (backend must be running)
npx shadcn-vue@latest add <component>   # add a UI component
```

API types come only from the backend OpenAPI spec (`/api/openapi.json`, docs at `/api/docs`): add a Pydantic `response_model` in `backend/app/schemas.py`, run `pnpm gen:api`, and import aliases from `@/types/api`. Fetch via composables in `app/composables/useApi.ts`.

## KBC theme

Brand colors (Belgian KBC Bank & Verzekering; verify against the [brand guidelines](https://kbcbrand.lovable.app/) if exact match matters):
- **Dark mode is the default** (`colorMode.preference: 'dark'` in `nuxt.config.ts`); near-black backgrounds, navy-tinted cards/sidebar. Light mode keeps black as primary.
- **KBC teal / accent**: `#1DBCC2` (RGB 29, 188, 194) – primary buttons/highlights in dark mode, focus rings, charts, active states (Nuxt UI primary = `kbc`)
- **Deep navy** `#052D58` (RGB 5, 45, 88) – optional secondary accent
- Alt (KBC Bank Ireland): blue `#003768`, light blue `#00AEEF`
- Neutrals: white backgrounds, light gray surfaces; blue = stability/trust.

Apply by overriding `--primary`, `--ring`, sidebar and chart variables in `frontend/app/assets/css/main.css` (currently neutral grayscale shadcn defaults), not with ad-hoc hex values in components. Tone: clean, friendly, trustworthy; handle sensitive profiles (e.g. financial stress) calmly.

## Conventions

- Vue `<script setup lang="ts">`, Composition API.
- Validate API payloads with Zod; share types between pages/components.
- Use existing shadcn-vue/Nuxt UI components before writing custom ones.
- Use Tailwind utility classes and theme variables from `main.css`; no ad-hoc CSS.
- Put fake/demo data in clearly named mock files (e.g. `server/` routes or `app/data/`) so they're easy to swap for a real API.
- Keep commits small and frequent; work on branch `jdecorte`, main branch is `master`.

## Suggested MVP for the demo

1. Synthetic transaction generator (several clients, one per profile).
2. Habit engine: transactions -> habits (recurring payments, spending rhythm, baselines) + change detection.
3. Profiling engine: habits/signals -> profile + confidence + reasons.
4. Dashboard: client list, profile badges, segment distribution chart, client detail with transaction timeline, habit trends, and "why this profile".
5. One actionable output per profile (e.g. holiday -> travel insurance / FX card offer; student -> youth account; young investor -> ETF savings plan).
