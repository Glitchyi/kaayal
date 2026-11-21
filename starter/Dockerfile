FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
COPY scripts ./scripts

ENV DATABASE_URL="sqlite:////data/kaayal.db"
EXPOSE 8000
VOLUME /data
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
