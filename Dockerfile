FROM python:3.13-slim-bookworm

WORKDIR /srv/pxdca
COPY requirements.txt /srv/pxdca/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY server/ /srv/pxdca/server/
COPY tools/SKILL.md /srv/pxdca/tools/SKILL.md
COPY config/pxdca.toml /srv/pxdca/config/pxdca.toml
RUN addgroup --system --gid 10001 pxdca \
    && adduser --system --uid 10001 --ingroup pxdca pxdca \
    && mkdir -p /srv/pxdca/data/state /srv/pxdca/data/artifacts /srv/pxdca/data/logs \
    && chown -R pxdca:pxdca /srv/pxdca \
    && python -m compileall -q /srv/pxdca/server

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/srv/pxdca
ENV PXDCA_CONFIG=/srv/pxdca/config/pxdca.toml
ENV PXDCA_HOST=0.0.0.0
ENV PXDCA_PORT=8000
ENV PXDCA_PATH=/mcp
ENV PXDCA_TRANSPORT=http
ENV PXDCA_STATE_ROOT=/srv/pxdca/data/state
ENV PXDCA_ARTIFACT_ROOT=/srv/pxdca/data/artifacts
ENV PXDCA_LOG_ROOT=/srv/pxdca/data/logs
EXPOSE 8000

USER pxdca
HEALTHCHECK --interval=10s --timeout=3s --retries=6 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1',8000),2); s.close()"
CMD ["python", "-m", "server.fastmcp_service"]
