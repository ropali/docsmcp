# docsMCP workspace

This repository uses a `uv` workspace with independently deployable modules:

- `backend`
- `mcp_server`
- `worker`

## Build each module independently

```bash
uv build --package backend
uv build --package mcp-server
uv build --package worker
```

Build artifacts are written to `./dist/`.

## Run module entrypoints

```bash
uv run --package backend backend
uv run --package mcp-server mcp-server
uv run --package worker worker
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

`mcp` and `worker` support the same actions:

```bash
make mcp add mcp
make worker add celery
```

Variable-style aliases:

```bash
make backend-add DEPS="httpx redis"
make mcp-add-dev DEPS="pytest"
make worker-build
```
