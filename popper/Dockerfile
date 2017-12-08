FROM golang:1.9

ADD . /go/src/github.com/systemslab/popper

WORKDIR /go/src/github.com/systemslab/popper

RUN go get ./ && \
    go build

ENTRYPOINT ["/go/bin/popper"]
