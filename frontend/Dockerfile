FROM node:20-alpine AS base

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app
RUN mkdir -p /app/node_modules /app/.nuxt && chown -R node:node /app
USER node

COPY --chown=node:node package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./

RUN pnpm install --frozen-lockfile

COPY --chown=node:node . .

ENV HOST=0.0.0.0
ENV PORT=3000
EXPOSE 3000

# --- dev: hot reload, source is bind-mounted by docker-compose.yml ---
FROM base AS dev

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "3000"]

# --- build: compile the Nuxt app into a standalone .output ---
FROM base AS build

RUN pnpm build

# --- prod: only the self-contained Nitro server ---
FROM node:20-alpine AS prod

WORKDIR /app
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000

COPY --from=build --chown=node:node /app/.output ./.output
USER node

EXPOSE 3000

# NUXT_PUBLIC_API_BASE is read at runtime
CMD ["node", ".output/server/index.mjs"]
