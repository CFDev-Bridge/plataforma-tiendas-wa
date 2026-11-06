# syntax=docker/dockerfile:1

ARG NODE_IMAGE=node:24-alpine
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.29-alpine

# Construcción con el usuario sin privilegios `node` incluido en la imagen oficial.
FROM ${NODE_IMAGE} AS build
ENV NG_CLI_ANALYTICS=false
RUN mkdir /build && chown node:node /build
WORKDIR /build
USER node
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY --chown=node:node . .
RUN npm run build

# Verificaciones del panel (formato, lint y pruebas) sin Node en la máquina anfitriona.
FROM build AS check
CMD ["sh", "-c", "npm run format:check && npm run lint && npm run test:ci"]

# nginx sin privilegios (puerto 8080, usuario no root).
FROM ${NGINX_IMAGE} AS runtime
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /build/dist/frontend/browser /usr/share/nginx/html
EXPOSE 8080
