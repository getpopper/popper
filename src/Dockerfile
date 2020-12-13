FROM alpine:20200917

COPY . /popper

RUN apk --no-cache add git py3-pip py3-paramiko && \
    pip install --no-cache-dir /popper && \
    rm -r /popper

ENTRYPOINT ["popper"]
