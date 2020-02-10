FROM python:3.7

COPY . /opt/EnrichServer
WORKDIR /opt/EnrichServer/

EXPOSE 8080

ENTRYPOINT [ "/usr/local/bin/python3", "/opt/EnrichServer/EnrichServer.py" ]
