# Transactions Service

A REST API for managing users, multi-currency balances, and financial transactions.
Built with FastAPI, with asynchronous analytics report generation via Dramatiq and Redis caching.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Setup](#environment-setup)
- [Running Locally](#running-locally)
- [Running with Docker Compose](#running-with-docker-compose)
- [API Documentation](#api-documentation)
- [API](#api)
- [Postman Collection](#postman-collection)
- [Tests](#tests)
- [Business Logic](#business-logic)
- [Project Structure](#project-structure)

## Features

- User registration with automatic balance initialization for all supported currencies
- List users with balances; filter by `user_id`, `email`, and `status`
- Update user status (`ACTIVE` / `BLOCKED`)
- Create transactions (`DEPOSIT` / `WITHDRAW`) with sufficient-funds checks
- Roll back transactions by creating a `REVERSAL` transaction
- List transactions with optional filtering by user
- Analytics report for the last 52 completed weeks, generated asynchronously and cached in Redis

## Tech Stack

- **Python** 3.12
- **FastAPI** - web framework
- **Pydantic v2** - data validation and serialization
- **SQLAlchemy** (async) + **Alembic** - ORM and migrations
- **PostgreSQL** - primary database
- **Redis** - cache for report generation
- **RabbitMQ** - message broker
- **Dramatiq** - background task worker
- **APScheduler** - scheduled task runner
- **Nginx** - reverse proxy (production)
- **Docker / Docker Compose** - local and production environments
- **Pytest** - automated testing
- **mypy** - static type checking
- **black / isort** - code formatting and sorting imports

## Architecture

```
                         ┌──────────────┐
                         │    Client    │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │    Nginx     │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   FastAPI    │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
             PostgreSQL       Redis      RabbitMQ
                                            ▲
                                            │
                                      ┌─────┴─────┐
                                      │  Dramatiq │
                                      │   Worker  │
                                      └─────▲─────┘
                                            │
                                      scheduled task
                                            │
                                   ┌────────┴────────┐
                                   │   APScheduler   │
                                   │    Container    │
                                   └─────────────────┘
```

The application consists of an API service, a scheduled task service,
and a background worker. FastAPI handles HTTP requests and interacts
with PostgreSQL and Redis. APScheduler runs in a separate container
and triggers report generation **every 10 minutes**. The scheduled job
sends a message to RabbitMQ through Dramatiq, which is then processed
by a dedicated worker. The worker generates the report and updates
the Redis cache.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) — for the containerized setup
- [Python](https://www.python.org/downloads/) — for the local setup without Docker
- [Poetry](https://python-poetry.org/docs/#installation) — for dependency management in the local setup
- **PostgreSQL 16+** — for the local setup without Docker (see [Running Locally](#running-locally))
- **Redis 7+** and **RabbitMQ 3+** — for the local setup without Docker (or run them in Docker, see [Running Locally](#running-locally))

## Getting Started

Clone the repository:

```bash
git clone https://github.com/leshakovalevskiy2002/internship-task.git
cd internship-task
```

Then choose one of the workflows below:

- [Running Locally](#running-locally) — run services manually with Poetry
- [Running with Docker Compose](#running-with-docker-compose) — run everything in containers

## Environment Setup

Environment files are created from the provided examples:

| File | Purpose |
|---|---|
| `.env.example` | Generic template for a local run without Docker |
| `.env.dev.example` | Docker Compose development environment |
| `.env.prod.example` | Docker Compose production environment |
| `.env.test.example` | Test environment |


## Running Locally

### 1. Install dependencies

Install Poetry (if not installed yet), then install project dependencies:

```bash
# Install Poetry (official installer)
curl -sSL https://install.python-poetry.org | python3 -

# Verify installation
poetry --version

# Install project dependencies (creates .venv automatically)
poetry install
```

> **Note:** The project runs in **package mode disabled**
> (`package-mode = false` in `pyproject.toml`), so `poetry install` installs
> only dependencies.
>
> If you see:
>
> ```
> The current project could not be installed
> ```
>
> make sure `package-mode = false` is set in `pyproject.toml`, or run:
>
> ```bash
> poetry install --no-root
> ```

All subsequent commands should be run through Poetry, e.g. `poetry run <command>`,
or inside an activated shell: `poetry shell`.

### 2. Prepare the environment

```bash
cp .env.example .env
```

### 3. Set up PostgreSQL (local instance)

Make sure PostgreSQL is installed and running locally. The `psql` client
should be available in `PATH`.

Create the application role and database once:

```bash
psql -U postgres -c "CREATE ROLE transactions WITH LOGIN PASSWORD 'transactions';"
psql -U postgres -c "CREATE DATABASE transactions_service_db OWNER transactions;"
```

Verify the connection:

```bash
psql -U transactions -d transactions_service_db -h localhost -c "SELECT 1;"
```

> The values above must match `POSTGRES_USER`, `POSTGRES_PASSWORD`, and
> `POSTGRES_DB` in `.env`.
>
> On Windows, you can do the same via pgAdmin:
> **Login/Group Roles → Create** for the role, then
> **Databases → Create** with owner `transactions`.

### 4. Start infrastructure

Start Redis (e.g. in a Docker container):

```bash
docker run -d --name my-redis -p 6379:6379 redis:8.2.0-alpine
```

Start RabbitMQ (e.g. in a Docker container):

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

### 5. Apply database migrations

```bash
poetry run alembic upgrade head
```

### 6. Start the services

Each service runs in its own terminal.

Dramatiq worker:

```bash
poetry run dramatiq app.worker --queues reports
```

Scheduled task runner:

```bash
poetry run python -m app.scheduler.main
```

FastAPI application:

```bash
poetry run python -m app.main
```

### 7. Open the API documentation

Once all services are running, the interactive API documentation is available at:

- Swagger UI: <http://127.0.0.1:7999/docs>
- ReDoc: <http://127.0.0.1:7999/redoc>
- OpenAPI JSON: <http://127.0.0.1:7999/openapi.json>

## Running with Docker Compose

### Development

### 1. Prepare the environment

```bash
cp .env.dev.example .env.dev
```

### 2. Run docker containers

```bash
docker compose --env-file .env.dev up --build -d
```

The API is available at <http://127.0.0.1:8000>, and the interactive
documentation at <http://127.0.0.1:8000/docs>.

### Production

### 1. Prepare the environment

```bash
cp .env.prod.example .env.prod
```

Set the production credentials and other secrets in `.env.prod`.

### 2. Build the images:

   ```bash
   docker compose --env-file .env.prod --file docker-compose.prod.yml build
   ```

### 3. Run migrations:

   ```bash
   docker compose --env-file .env.prod --file docker-compose.prod.yml run --rm migrate
   ```

### 4. Start the containers:

   ```bash
   docker compose --env-file .env.prod --file docker-compose.prod.yml up -d api worker scheduler nginx
   ```

The API is available through Nginx at <http://127.0.0.1>, and the
interactive documentation at <http://127.0.0.1/docs>.

## API Documentation

The interactive API documentation (Swagger UI) is available at:

| Environment | Base URL | Swagger UI |
|---|---|---|
| Local | `http://127.0.0.1:7999` | <http://127.0.0.1:7999/docs> |
| Docker (dev) | `http://127.0.0.1:8000` | <http://127.0.0.1:8000/docs> |
| Docker (prod) | `http://127.0.0.1` | <http://127.0.0.1/docs> |

For the production environment, the URL should be replaced with the actual
server hostname or domain when accessing the API remotely.

## API

All endpoints are served under the `/api/v1` prefix.

Endpoint overview:

| Method  | Path                                              | Description |
|---------|---------------------------------------------------|---|
| `GET`   | `/`                                               | Health check (service name) |
| `POST`  | `/api/v1/users`                                   | Register a new user |
| `GET`   | `/api/v1/users`                                   | List users with balances |
| `PATCH` | `/api/v1/users/{user_id}`                         | Change user status |
| `POST`  | `/api/v1/{user_id}/transactions`                  | Create a transaction |
| `PATCH` | `/api/v1/{user_id}/transactions/{transaction_id}` | Roll back a transaction |
| `GET`   | `/api/v1/transactions`                            | List transactions (filter by `user_id`) |
| `GET`   | `/api/v1/reports/analysis`                        | Analytics report for the last 52 weeks |


## Postman Collection

Import the collection into Postman:

- **File:** [`docs/postman/transactions-service.postman_collection.json`](docs/postman/transactions-service.postman_collection.json)
- **Via link:** Postman → **Import → Link** →
  ```
  https://raw.githubusercontent.com/leshakovalevskiy2002/internship-task/main/docs/postman/transactions-service.postman_collection.json
  ```
  
## Tests

Tests run against a separate database and use `.env.test`.

### 1. Prepare the test environment

```bash
cp .env.test.example .env.test
```

### 2. Create the test database (local PostgreSQL only)

If PostgreSQL runs locally (not in Docker), create the test role and database once:

```bash
psql -U postgres -c "CREATE ROLE transactions_test WITH LOGIN PASSWORD 'transactions_test';"
psql -U postgres -c "CREATE DATABASE transactions_service_db_test OWNER transactions_test;"
```

> The values above must match `POSTGRES_USER`, `POSTGRES_PASSWORD`, and
> `POSTGRES_DB` in `.env.test`.
>
> If your tests use **testcontainers**, this step is not required — an isolated
> PostgreSQL instance is started automatically.

### 3. Run the tests

Make sure Docker is running (Redis and RabbitMQ containers are started
automatically by testcontainers), then:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=app --cov-report=term-missing
```

## Business Logic

Domain rules (users, transactions, analytics) are described in
[`docs/business-logic.md`](docs/business-logic.md).

## Project Structure

```
internship-task/
├── .github/
│   └── workflows/      # CI pipelines
├── app/
│   ├── api/              # routers, handlers, response docs
│   ├── core/             # constants, enums
│   ├── config/           # settings
│   ├── docs/             # in-app docs (OpenAPI descriptions)
│   ├── models/           # SQLAlchemy models
│   ├── queries/          # SQLAlchemy queries
│   ├── repositories/     # repositories
│   ├── scheduler/        # APScheduler task runner
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # business logic (transactions, reports, users)
│   ├── tasks/            # Dramatiq actors
│   ├── dependencies.py   # FastAPI dependencies
│   ├── main.py           # FastAPI entry point
│   ├── uow.py            # unit of work
│   └── worker.py         # Dramatiq worker entry point
├── alembic/              # migrations
├── docs/                 # project documentation (business logic, Postman)
│   └── postman/          # Postman collection and environment
├── tests/
├── .dockerignore
├── .gitignore
├── alembic.ini
├── .env.dev.example
├── .env.prod.example
├── .env.example
├── .env.test.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── Dockerfile.prod
├── pytest.ini
├── poetry.lock
├── pyproject.toml
└── README.md
```
