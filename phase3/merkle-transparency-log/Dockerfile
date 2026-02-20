FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY src/ ./src/
ENV NODE_ENV=production
EXPOSE 8073
HEALTHCHECK --interval=30s --timeout=5s CMD wget -q --spider http://localhost:8073/health || exit 1
CMD ["node", "src/transparency-log-server.js"]
