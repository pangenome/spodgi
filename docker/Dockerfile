FROM ghcr.io/pangenome/pggb:202403191034527bb5b7
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      git \
      python3-dev \
      python3-setuptools \
      bash
RUN git clone https://github.com/pangenome/spodgi \
    && cd spodgi \
    && python3 setup.py install \
    && cp sparql_odgi.py /usr/bin \
    && cp odgi_to_rdf.py /usr/bin \
    && cp sparql_server.py /usr/bin
ENV PYTHONPATH="/smoothxg/deps/odgi/lib/"
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
CMD ["bash"]
