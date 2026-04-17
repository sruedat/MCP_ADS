# Imagen de referencia para ejecutar el servidor MCP con pyads (adslib en Linux).
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcp_ads ./mcp_ads

RUN pip install --no-cache-dir --break-system-packages .

# Directorio por defecto para montar plc.json y variables.json
ENV MCP_ADS_CONFIG_DIR=/config

VOLUME ["/config"]

ENTRYPOINT ["python3", "-m", "mcp_ads"]
