FROM python:slim

WORKDIR /root/git/

RUN apt-get update && apt-get install -y git nodejs npm bash cmake make g++ time && \
    git clone --recursive https://github.com/vgteam/odgi.git && \
    cd odgi && cmake -H. -Bbuild && cmake --build build -- -j 3

WORKDIR /usr/app

ADD . .

RUN pip install -r requirements.txt

ENV PATH=$PATH:/usr/app:/root/git/odgi/bin \
    PYTHONPATH=$PYTHONPATH:/root/git/odgi/lib/

ENTRYPOINT ["sparql_odgi.py"]