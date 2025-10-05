FROM python:3.10-slim as builder

WORKDIR /app


RUN pip install uv


RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gnupg && \
    curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /get-docker.sh


COPY pyproject.toml .
COPY . .


RUN uv pip install -e .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]