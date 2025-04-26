FROM ubuntu:20.04

USER root
ADD windninja /opt/src/windninja/
SHELL [ "/usr/bin/bash", "-c" ]
ENV DEBIAN_FRONTEND=noninteractive
ENV WM_PROJECT_INST_DIR=/opt
RUN dpkg-reconfigure debconf --frontend=noninteractive && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y wget gnupg2 cmake git apt-transport-https ca-certificates \
                       software-properties-common sudo build-essential \
                       pkg-config g++ libboost-program-options-dev \
                       libboost-date-time-dev libboost-test-dev && \
    cd /opt/src && \
    DEBIAN_FRONTEND=noninteractive ./windninja/scripts/build_deps_ubuntu_2004.sh && \
    rm -rf /var/lib/apt/lists

RUN cd  /opt/src/windninja && \
    mkdir build && \
    cd  /opt/src/windninja/build && \
    cmake -D SUPRESS_WARNINGS=ON -DNINJAFOAM=ON .. && \
    make -j4 && \
    make install && \
    ldconfig && \
    cd /opt/src/windninja && \
    /usr/bin/bash -c scripts/build_libs.sh

ADD app /app
ADD requirements.txt requirements.txt
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir -r requirements.txt
    
RUN mkdir -p /app/logs && \
    chmod 777 /app/logs

CMD ["python3", "/app/main.py"]
VOLUME ["/data"]
