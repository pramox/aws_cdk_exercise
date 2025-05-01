#### STAGE 1: BUILD ###
FROM node:20.11.1-alpine AS build
WORKDIR /usr/local/app
COPY . /usr/local/app/

RUN npm install
RUN npm run build

### STAGE 2: RUN ###
FROM nginx:1.25.3-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /usr/local/app/dist/angular/browser /usr/share/nginx/html
