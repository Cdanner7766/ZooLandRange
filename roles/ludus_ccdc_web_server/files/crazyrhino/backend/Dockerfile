FROM node:20-alpine

RUN apk add --no-cache python3 make g++

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

RUN mkdir -p /app/data
ENV DB_PATH=/app/data/zoo_store.db

EXPOSE 5000

CMD ["node", "server.js"]
