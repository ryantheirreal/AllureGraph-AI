FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml /app/
COPY server/ /app/server/
COPY web/ /app/web/
COPY assets/ /app/assets/
RUN pip install --no-cache-dir '.[api]'
RUN useradd -m -u 10001 saveflow && mkdir -p /data && chown saveflow:saveflow /data
USER saveflow
ENV SAVEFLOW_OUTPUT_DIR=/data PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3)" || exit 1
CMD ["uvicorn", "server.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
