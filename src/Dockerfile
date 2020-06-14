FROM python:3.7.7-alpine3.12

COPY . /popper

RUN apk --no-cache add git && \
    pip install --no-cache-dir /popper && \
    rm -r /popper

ENTRYPOINT ["popper"]
