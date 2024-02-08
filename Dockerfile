FROM python:3.11

ENV SD_PORT=9900
ENV DATA_VOLUME=/sparql-query-demo/data

RUN mkdir /sparql-query-demo
RUN mkdir /sparql-query-demo/data


COPY ./sparql-query-demo.py /sparql-query-demo/sparql-query-demo.py
COPY ./requirements.txt /sparql-query-demo/requirements.txt

RUN pip install -r /sparql-query-demo/requirements.txt

EXPOSE $SD_PORT

ENTRYPOINT [ "python", "/sparql-query-demo/sparql-query-demo.py" ]
