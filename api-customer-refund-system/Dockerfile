FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies first, separately from the app code, so this layer is
# only rebuilt when pyproject.toml/uv.lock actually change. `uv sync` doesn't
# install the "dev" extra (pytest, ruff) unless asked to, so this stays a lean
# production image without needing to say so explicitly.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
# uv_build (the project's build backend) reads pyproject.toml's `readme`
# field and fails without the file actually being present, even though
# nothing at runtime reads it.
COPY README.md ./
RUN uv sync --frozen

EXPOSE 8000

# Apply any pending migrations, then start the API. In a real deployment
# migrations would run as a separate release step rather than on every
# container start, but for a single-instance local/demo setup this keeps
# `docker compose up` a genuine one-command start.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn api_customer_refund_system.main:app --host 0.0.0.0 --port 8000"]
