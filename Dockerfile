FROM python:3.12-slim
WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --with=dev --no-root --no-ansi --no-interaction

COPY . .

CMD ["python", "-m", "app.main"]
