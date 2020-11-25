FROM python:3.7.7-alpine3.12

COPY . /popper

RUN apk --no-cache add git && \
    apk --no-cache add gcc && \
    apk --no-cache add make linux-headers musl-dev python3-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir /popper && \
    rm -r /popper

ENTRYPOINT ["popper"]
