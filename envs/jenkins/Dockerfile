FROM jenkins/jenkins:lts
USER root
RUN  curl -SL https://download.docker.com/linux/static/stable/x86_64/docker-17.06.2-ce.tgz | tar -xzv docker/docker && \
     mv docker/docker /usr/bin && \
     rm -r docker/
USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN  /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
