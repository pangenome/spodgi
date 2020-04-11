FROM debian:buster
ENV DEBIAN_VERSION=buster-20200327
ENV ODGI_COMMIT=5e18490156f08368dae0b25a69e0cf5efa5427ca
ENV SPODGI_COMMIT=f2b352e0b078018f5395cfaff36c1f044dda864e

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
    && git clone --depth 4 --shallow-submodules --recursive https://github.com/vgteam/odgi.git \
    && cd odgi \
    && git checkout "${ODGI_COMMIT}" \
    && cmake -H. -Bbuild \
    && cmake --build build -- -j 3 \
    && rm -rf deps \
    && rm -rf build \
    && rm -rf lib/*.a \
    && cp bin/odgi /usr/bin \
    && apt-get remove -y --autoremove  build-essential cmake \
    && apt-get clean

WORKDIR "/var/lib/odgi"
ENV PYTHONPATH=:/var/lib/odgi/odgi/lib
RUN DEBIAN_FRONTEND=noninteractive \
    && git clone https://github.com/pangenome/spodgi \
    && cd spodgi \
    && git checkout "${SPODGI_COMMIT}" \
    && python3 setup.py install \
    && cp sparql_odgi.py /usr/bin \
    && cp odgi_to_rdf.py /usr/bin

CMD ["bash"]
