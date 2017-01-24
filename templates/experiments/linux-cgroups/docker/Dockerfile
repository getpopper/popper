FROM debian:stretch
MAINTAINER Sam McLeod

ENV DEBIAN_FRONTEND noninteractive

# Install Debian packages
RUN apt-get -y update && \
    apt-get -y install \
      openssh-client coreutils fakeroot build-essential \
      kernel-package wget xz-utils gnupg bc devscripts \
      apt-utils initramfs-tools aria2 curl libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ADD * /app/
WORKDIR /app
ENTRYPOINT ["/app/buildkernel.sh"]
