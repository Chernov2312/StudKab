FROM node:22-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine AS runtime
RUN addgroup -S puls && adduser -S -G puls puls && chown -R puls:puls /data /config
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist /srv
USER puls
EXPOSE 80 443 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=8s CMD wget -q -T 2 -O /dev/null http://127.0.0.1:8081/api/v1/health/live || exit 1
