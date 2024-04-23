FROM python:3.11-slim

# Install deps
RUN pip install --upgrade pip && pip install pdm
RUN apt update
RUN apt install -y gcc
RUN apt install -y uvicorn

WORKDIR /app

# Copy pdm files
COPY pyproject.toml /app/pyproject.toml
COPY pdm.lock /app/pdm.lock
COPY ./src/backend /app/backend
COPY ./.env /app/.env

RUN pdm install
EXPOSE 8000

ENTRYPOINT ["pdm", "run", "python", "-m", "uvicorn", "backend.app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
