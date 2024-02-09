FROM python:3.11

ENV SD_PORT=9900
ENV DATA_VOLUME=/sparql-query-demo/data
ENV ROOT_PATH="/"

RUN git clone https://github.com/Ibaii99/sparql-query-demo.git --branch v1.1

RUN pip install -r /sparql-query-demo/requirements.txt

EXPOSE $SD_PORT

ENTRYPOINT [ "python", "/sparql-query-demo/sparql-query-demo.py" ]
