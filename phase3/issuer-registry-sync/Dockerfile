FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY src/ ./src/
COPY sql/ ./sql/
ENV NODE_ENV=production
EXPOSE 8071
HEALTHCHECK --interval=30s --timeout=5s CMD wget -q --spider http://localhost:8071/health || exit 1
CMD ["node", "src/hub-sync-server.js"]
