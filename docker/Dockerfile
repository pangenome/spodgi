FROM jerven/odgi-python3:latest
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      git \
      python3-dev \
      python3-setuptools
RUN git clone https://github.com/pangenome/spodgi \
    && cd spodgi \
    && python3 setup.py install \
    && cp sparql_odgi.py /usr/bin \
    && cp odgi_to_rdf.py /usr/bin \
    && cp sparql_server.py /usr/bin
CMD ["bash"]
