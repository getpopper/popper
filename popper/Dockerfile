# Before building, execute the following from the root folder of the project:
#
# docker run --rm -v `pwd`/popper:/app -w /app treeder/go vendor
# docker run --rm -v `pwd`/popper:/app -w /app treeder/go build

FROM iron/base
WORKDIR /app
COPY app /app/popper
ENTRYPOINT ["./popper"]
