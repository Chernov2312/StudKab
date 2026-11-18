FROM python:3.12-slim AS deps
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_NO_CACHE=1
WORKDIR /srv
RUN python -m pip install --no-cache-dir uv==0.13.9
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
RUN groupadd --system puls && useradd --system --gid puls puls
COPY --from=deps /opt/venv /opt/venv
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
USER puls
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=2).close()"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
