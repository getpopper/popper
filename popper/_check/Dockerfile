FROM python:2.7-alpine
RUN apk add --no-cache curl bash && \
    curl -SL https://download.docker.com/linux/static/stable/x86_64/docker-17.06.2-ce.tgz | tar -xzv docker/docker && \
    mv docker/docker /usr/bin && \
    pip install --no-cache-dir pyaml && \
    rm -r docker/
ADD check.py /
ENTRYPOINT ["/check.py"]
