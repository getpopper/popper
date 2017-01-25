FROM debian:stretch

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
      fakeroot build-essential kernel-package devscripts \
      apt-utils initramfs-tools libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ADD * /app/
WORKDIR /app
ENTRYPOINT ["/app/buildkernel.sh"]
