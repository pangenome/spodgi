FROM debian:buster
ENV DEBIAN_VERSION=buster-20200327
ENV ODGI_COMMIT=dc76da391943a6bd6a7784e42f946dc478b865a5
ENV SPODGI_COMMIT=8a9aa7d261113b0dbc55898d9e56e29dbc13ae01

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
    && git clone --shallow-submodules --recursive https://github.com/vgteam/odgi.git \
    && cd odgi \
    && git checkout "${ODGI_COMMIT}" \
    && cmake -DBUILD_STATIC=0 -H. -Bbuild \
    && cmake --build build -- -j $(nproc) \
    && rm -rf deps \
    && rm -rf build \
    && rm -rf lib/*.a \
    && ls -s bin/odgi /usr/bin \
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
