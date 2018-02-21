FROM python:3.6.4-alpine3.7

RUN apk add --no-cache bash curl git sed grep bc coreutils

ADD . /cli

RUN cd cli && pip install .

ENTRYPOINT ["popper"]
