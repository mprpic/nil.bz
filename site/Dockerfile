FROM registry.fedoraproject.org/fedora:latest

RUN dnf install -y nginx python3-markdown python3-jinja2 && \
    dnf clean all && \
    mkdir -p /var/www/html

COPY ./nginx.conf /etc/nginx/

EXPOSE 8080

CMD ["nginx"]
