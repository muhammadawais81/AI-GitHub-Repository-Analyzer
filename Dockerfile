FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml ./

RUN pip install --no-cache-dir --default-timeout=180 --retries=10 -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src

RUN mkdir -p /app/app/repositories \
    /app/src/aicodingagentbackend/chroma_db \
    /root/.cache/huggingface

EXPOSE 8000

CMD ["uvicorn", "aicodingagentbackend.main:app", "--host", "0.0.0.0", "--port", "8000"]