FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# System deps: arp-scan (raw packets), gcc+python3-dev (netifaces C extension), iputils-ping
RUN apt-get update && apt-get install -y --no-install-recommends \
        arp-scan gcc python3-dev iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy everything (source + deps) so pip can build the wheel
COPY . .

# Install (regular install, not editable — source already in image)
RUN pip install --no-cache-dir .

# Persistent data dir
RUN mkdir -p /var/lib/network-scanner

# Defaults — override with env vars at runtime
ENV NETWORK_SCANNER_DATA_DIR=/var/lib/network-scanner \
    LOG_LEVEL=INFO \
    LOG_TO_FILE=false \
    MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

# MCP server — stdio for Claude Desktop, http for remote access
CMD ["python", "-m", "network_scanner_mcp.server"]
