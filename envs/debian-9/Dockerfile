FROM python:2.7-slim-stretch

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get --no-install-recommends -y install curl git && \
    apt-get autoremove --purge -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    curl -SL https://download.docker.com/linux/static/stable/x86_64/docker-17.06.2-ce.tgz | tar -xzv docker/docker && \
    mv docker/docker /usr/bin && \
    pip install --no-cache-dir pyaml && \
    rm -r docker/
ADD check.py /
ENTRYPOINT ["/check.py"]
