FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
# No lockfile, so npm resolves an eslint-plugin-jest newer than react-scripts 5
# supports ("Environment key jest/globals is unknown"); linting is not needed.
RUN DISABLE_ESLINT_PLUGIN=true npm run build

FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
