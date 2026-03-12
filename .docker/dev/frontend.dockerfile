FROM node:25.8-alpine

WORKDIR /app

# install dependencies (will be overridden by mount, but cached for fallback)
COPY frontend/package*.json ./
RUN npm install

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
