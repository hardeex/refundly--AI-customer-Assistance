FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* variables are inlined into the client JS bundle at build
# time - unlike BACKEND_API_URL/BACKEND_API_KEY (read server-side at request
# time, so they don't need to be here), these have to be passed as build
# args, not just set on the running container, or the compiled bundle falls
# back to whatever default the source code has.
ARG NEXT_PUBLIC_APP_NAME
ARG NEXT_PUBLIC_BACKEND_DOCS_URL
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# The standalone output only includes what next.config.ts's output:
# "standalone" traced as actually used - a normal node_modules copy isn't
# needed alongside it.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
