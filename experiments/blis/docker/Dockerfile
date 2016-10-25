FROM debian:jessie

ENV DEBIAN_FRONTEND noninteractive

ADD add_path_to_usrlib.patch /tmp/

RUN apt-get update && \
    apt-get install -y \
        g++ make gfortran curl libatlas-base-dev libopenblas-dev tar patch && \
    curl -sL https://github.com/flame/blis/archive/0.2.1.tar.gz | tar xz && \
    mv /blis-* /blis && \
    cd /blis && \
    patch -p0 < /tmp/add_path_to_usrlib.patch && \
    ./configure -p /usr/ reference && \
    make -j4 && \
    make install && \
    make -j4 -C test && \
    apt-get remove -y --purge g++ make $(apt-mark showauto) && \
    apt-get install -y libgfortran-4.8-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /blis/test
ENTRYPOINT ["./runme.sh"]
