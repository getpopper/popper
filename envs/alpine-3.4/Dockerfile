FROM python:2.7-alpine3.4
RUN apk add --no-cache curl bash git && \
    curl -SL https://download.docker.com/linux/static/stable/x86_64/docker-18.06.0-ce.tgz | tar -xzv docker/docker && \
    mv docker/docker /usr/bin && \
    rm -r docker/
ADD cli /cli
RUN pip install --no-cache-dir /cli
ENTRYPOINT ["popper"]
