FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY orchestrator ./orchestrator
COPY scripts ./scripts
COPY benchmarks ./benchmarks

CMD ["python", "scripts/run_langgraph.py", "--max-iterations", "2"]
