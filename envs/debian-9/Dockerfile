FROM python:2.7-slim-stretch
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install --no-install-recommends -y --no-install-suggests curl git && \
    curl -SL https://download.docker.com/linux/static/stable/x86_64/docker-18.06.0-ce.tgz | tar -xzv docker/docker && \
    mv docker/docker /usr/bin && \
    rm -r docker/ && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
ADD cli /cli
RUN pip install --no-cache-dir cli/
ENTRYPOINT ["popper"]
