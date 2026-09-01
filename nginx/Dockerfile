FROM nginx:1.30.4@sha256:46ccc48fbb1f5a43167f2ee2c279c122b96eec5d976e7f4e1e0780f59a51b4d6

RUN rm -f /etc/nginx/conf.d/default.conf
COPY transactions_service.conf /etc/nginx/conf.d/
