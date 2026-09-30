FROM node:20-alpine AS base

WORKDIR /app
RUN mkdir -p /app/node_modules && chown -R node:node /app
USER node

COPY --chown=node:node package.json package-lock.json* ./

RUN npm install

COPY --chown=node:node . .

EXPOSE 3001

# --- dev: Vite dev server, source is bind-mounted by docker-compose.yml ---
FROM base AS dev

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]

# --- build: static bundle in /app/dist ---
FROM base AS build

RUN npm run build

# --- prod: nginx serves the bundle and proxies /api to the backend ---
FROM nginx:1.27-alpine AS prod

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 3001

CMD ["nginx", "-g", "daemon off;"]
