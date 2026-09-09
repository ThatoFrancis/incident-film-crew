FROM python:3.12-slim

WORKDIR /app

# Grafana MCP server binary
ADD https://github.com/grafana/mcp-grafana/releases/download/v1.3.0/mcp-grafana_Linux_x86_64.tar.gz /tmp/mcp.tar.gz
RUN tar -xzf /tmp/mcp.tar.gz -C /usr/local/bin mcp-grafana && \
    chmod +x /usr/local/bin/mcp-grafana && rm /tmp/mcp.tar.gz

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY incident_film_crew/ ./incident_film_crew/

ENV MCP_GRAFANA_CMD=/usr/local/bin/mcp-grafana
EXPOSE 8080

CMD ["sh", "-c", "adk web --host 0.0.0.0 --port ${PORT:-8080} ."]
