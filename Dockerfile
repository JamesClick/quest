FROM node:18

WORKDIR /home/node/app

COPY package*.json ./

RUN npm install

COPY ./src/ ./
COPY ./bin/ ./bin/

EXPOSE 3000

CMD [ "node", "000.js" ]