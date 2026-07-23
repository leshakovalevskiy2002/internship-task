FROM nginx:1.25

RUN rm -f /etc/nginx/conf.d/default.conf
COPY transactions_service.conf /etc/nginx/conf.d/
