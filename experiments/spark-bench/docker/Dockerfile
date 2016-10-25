FROM ivotron/openssh

RUN apt-get update && apt-get install -y scala wget && \
    wget --no-check-certificate http://apache.mirrors.tds.net/spark/spark-2.0.1/spark-2.0.1-bin-hadoop2.7.tgz -O - | tar xz && \
    mv spark* spark && \
    rm /spark/conf/* && \
    apt-get remove --purge -y wget && \
    apt-get autoremove --purge -y wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV SPARK_HOME=/spark
ENV PATH=$PATH:$SPARK_HOME/bin

ADD entrypoint.sh /root

ENTRYPOINT ["/root/entrypoint.sh"]
