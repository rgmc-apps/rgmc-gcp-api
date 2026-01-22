FROM python:3.11-bullseye

WORKDIR /api
COPY . /api

RUN apt-get update -y \
    && apt-get install build-essential -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip install flit \
    && FLIT_ROOT_INSTALL=1 flit install --deps production \
    && rm -rf $(pip cache dir)

CMD gunicorn src.main:api -c src/gunicorn_config.py