# DocsMCP - Turn any webpage into LLM-ready context.

This repository uses a `uv` workspace with independently deployable modules:

- `backend`
- `mcp_server`
- `crawler`

## Architecture

```text
+-------------------+          HTTP /api/v1           +----------------------+
| Client / Consumer | -----------------------------> | backend (FastAPI)    |
+-------------------+                                |----------------------|
                                                     | routes               |
                                                     | repositories         |
                                                     | celery producer      |
                                                     | storage service      |
                                                     +----------+-----------+
                                                                |
                         +--------------------------------------+----------------------------------+
                         |                                      |                                  |
                         v                                      v                                  v
               +-------------------+                  +-------------------+              +-------------------+
               | PostgreSQL        |                  | Redis             |              | S3 / Storage      |
               |-------------------|                  |-------------------|              |-------------------|
               | sources           |                  | Celery broker     |              | uploaded files    |
               | pages             |                  | result backend    |              | crawled HTML      |
               | crawl_jobs        |                  +---------+---------+              +---------+---------+
               +-------------------+                            |                                  ^
                                                                |                                  |
                                                                v                                  |
                                                     +----------------------+                      |
                                                     | crawler (Celery)     | ---------------------+
                                                     |----------------------|
                                                     | crawl_source_task    |
                                                     | crawler pipeline     |
                                                     | httpx / Playwright   |
                                                     | shared DB models     |
                                                     +----------+-----------+
                                                                |
                                                                v
                                                     +----------------------+
                                                     | External websites    |
                                                     |----------------------|
                                                     | source URLs crawled  |
                                                     +----------------------+

```

## Build each module independently

```bash
uv build --package backend
uv build --package mcp-server
uv build --package crawler
```

Build artifacts are written to `./dist/`.

## Run module entrypoints

```bash
uv run --package backend backend
uv run --package mcp-server mcp-server
uv run --package crawler crawler
```

## Makefile shortcuts

Command-style:

```bash
make backend add httpx redis
make backend add-dev pytest ruff
make backend run
make backend build
```

`make backend run` starts the FastAPI dev server with reload:

```bash
make backend run BACKEND_HOST=0.0.0.0 BACKEND_PORT=8080
```

`mcp` and `crawler` support the same actions:

```bash
make mcp add mcp
make crawler add celery
```

Variable-style aliases:

```bash
make backend-add DEPS="httpx redis"
make mcp-add-dev DEPS="pytest"
make crawler-build
```

## Backend migrations (Alembic)

Alembic is configured in `backend/alembic.ini` with scripts in `backend/migrations`.

```bash
make backend migrate
make backend revision "create users table"
make backend downgrade
make backend db-check
```
