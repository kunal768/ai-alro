FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# nginx.conf uses ${INTAKE_HOST}, ${OPTIMIZER_HOST}, ${REASONER_HOST}
# envsubst rewrites them at container start from environment variables.
# Docker Compose sets these to Docker service names; ECS sets them to Cloud Map DNS names.
COPY nginx.conf /etc/nginx/templates/default.conf.template
EXPOSE 80
