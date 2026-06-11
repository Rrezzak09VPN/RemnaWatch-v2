FROM python:3.11-slim

RUN apt-get update && apt-get install -y wget ca-certificates && \
    wget -qO /tmp/sing-box.tar.gz \
        https://github.com/SagerNet/sing-box/releases/download/v1.11.5/sing-box-1.11.5-linux-amd64.tar.gz && \
    echo "be0c0f8d7d7feaa09821d52ab1c07c2a202a234c8c6002c1538c7d048de82f3d  /tmp/sing-box.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/sing-box.tar.gz -C /tmp && \
    mv /tmp/sing-box-1.11.5-linux-amd64/sing-box /usr/local/bin/ && \
    chmod +x /usr/local/bin/sing-box && \
    rm -rf /tmp/sing-box* && \
    apt-get remove -y wget && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p /app/data /app/logs

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, sys; sys.exit(0 if os.path.exists('/app/data/bot.db') else 1)"

CMD ["python", "-m", "src.main"]
