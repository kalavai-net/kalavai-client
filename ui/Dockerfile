FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 3000

ENV NEXT_PUBLIC_KALAVAI_API_URL=http://0.0.0.0:49152
ENV NEXT_PUBLIC_ACCESS_KEY=""

ENTRYPOINT ["/docker-entrypoint.sh"]
