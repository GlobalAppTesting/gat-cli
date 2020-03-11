FROM python:3.7-alpine AS dev

# hadolint ignore=DL3018
RUN apk --no-cache add gcc musl-dev libffi-dev openssl-dev && \
  rm -rf /var/cache/apk
# hadolint ignore=DL3013
RUN pip3 install poetry

COPY poetry.lock \
  pyproject.toml \
  /app/

WORKDIR /app
RUN /usr/local/bin/poetry install --no-dev

FROM python:3.7-alpine
WORKDIR /app
COPY --from=dev /usr/local /usr/local
COPY --from=dev /app /app
COPY --from=dev /root/.cache/pypoetry/virtualenvs /root/.cache/pypoetry/virtualenvs
COPY gat-cli.py LICENSE README.md /app/
COPY gat /app/gat/

ENTRYPOINT ["/usr/local/bin/poetry", "run", "python", "gat-cli.py"]
