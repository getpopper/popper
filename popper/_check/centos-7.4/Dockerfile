FROM centos:7.4.1708

RUN yum -y install git PyYAML && yum clean all && \
    curl -SL https://download.docker.com/linux/static/stable/x86_64/docker-17.06.2-ce.tgz | tar -xzv docker/docker && \
    mv docker/docker /usr/bin && \
    rm -r docker/
ADD check.py /
ENTRYPOINT ["/check.py"]
