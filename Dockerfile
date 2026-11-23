FROM python:3.12-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/

RUN pip install --no-cache-dir flask pytest

CMD ["sh", "-c", "sleep infinity"]
