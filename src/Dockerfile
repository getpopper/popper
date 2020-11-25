FROM python:3.7.7-alpine3.12

COPY . /popper

RUN apk --no-cache add git && \
    apk --no-cache add gcc && \
    apk --no-cache add make && \
    apk --no-cache add linux-headers && \
    apk --no-cache add musl-dev && \
    apk --no-cache add python3-dev && \
    apk --no-cache add libffi-dev && \
    apk --no-cache add openssl-dev && \
    pip install --no-cache-dir /popper && \
    rm -r /popper

ENTRYPOINT ["popper"]
