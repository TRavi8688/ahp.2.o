FROM node:18-alpine

WORKDIR /app

COPY package.json ./
RUN npm install
RUN npm install -g expo-cli @expo/ngrok

COPY . .

EXPOSE 19006

CMD ["npm", "run", "web"]
