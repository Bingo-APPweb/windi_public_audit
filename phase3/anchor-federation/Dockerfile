FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY src/ ./src/
ENV NODE_ENV=production
EXPOSE 8072
HEALTHCHECK --interval=30s --timeout=5s CMD wget -q --spider http://localhost:8072/health || exit 1
CMD ["node", "src/hub-anchor-receiver.js"]
