FROM python:2.7.14-alpine3.7

RUN apk add --no-cache bash curl git sed grep bc coreutils && \
    apk add --no-cache --update g++ && \
    rm /var/cache/apk/*

ADD . /cli

RUN cd cli && pip install .

ENTRYPOINT ["popper"]

