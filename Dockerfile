FROM python:3.11-slim

WORKDIR /srv/logicmcp
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY server ./server
RUN python -m compileall -q server

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/srv/logicmcp
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_PATH=/mcp
ENV MCP_TRANSPORT=http
ENV MCP_OUTPUT_ROOT=/srv/logicmcp/output
EXPOSE 8000

CMD ["python", "-m", "server.fastmcp_service"]
