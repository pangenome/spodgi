FROM debian:buster
ENV DEBIAN_VERSION=buster-20200327
ENV ODGI_COMMIT=5e18490156f08368dae0b25a69e0cf5efa5427ca
ENV SPODGI_COMMIT=84a1af531e5381216eeb5035e284167ed886da21

WORKDIR "/var/lib/odgi"
RUN DEBIAN_FRONTEND=noninteractive \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      cmake \
      git \
      python3-dev \
      python3-setuptools \
      zlib1g-dev \
    && rm -fr /var/lib/apt/lists/* \
    && update-ca-certificates \
    && git clone --recursive https://github.com/vgteam/odgi.git \
    && cd odgi \
    && git checkout "${ODGI_COMMIT}" \
    && cmake -H. -Bbuild \
    && cmake --build build -- -j 3 \
    && cp bin/odgi /usr/bin

WORKDIR "/var/lib/odgi"
ENV PYTHONPATH=:/var/lib/odgi
RUN DEBIAN_FRONTEND=noninteractive \
    && git clone https://github.com/pangenome/spodgi \
    && cd spodgi \
    && git checkout "${SPODGI_COMMIT}" \
    && python3 setup.py install \
    && cp sparql_odgi.py /usr/bin \
    && cp odgi_to_rdf.py /usr/bin

CMD ["bash"]
