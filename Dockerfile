FROM amazon/aws-lambda-python:3.13

RUN microdnf update && \
    microdnf install -y make && \
    microdnf clean all

RUN make --version

RUN mkdir /hyp3
WORKDIR /hyp3

COPY . /hyp3/

RUN python3 -m pip install --no-cache-dir --upgrade wheel

RUN make install && make build

CMD ["/bin/bash"]
