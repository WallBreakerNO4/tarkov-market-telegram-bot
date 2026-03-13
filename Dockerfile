FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock /app/
ENV UV_NO_DEV=1
RUN uv sync --locked --no-install-project

COPY bot.py /app/bot.py
COPY libs /app/libs

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "bot.py"]
