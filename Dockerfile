FROM amazon/aws-lambda-python:3.13

RUN mkdir /hyp3
WORKDIR /hyp3

RUN mamba install -c conda-forge -y \
    awscli \
    make

RUN make install && make build

ENTRYPOINT /bin/bash

