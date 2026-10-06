FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/md2xwiki
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

WORKDIR /workspace
USER 65532:65532
ENTRYPOINT ["md2xwiki"]
