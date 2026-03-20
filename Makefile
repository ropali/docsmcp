SHELL := /bin/bash

UV ?= uv
UV_CACHE_DIR ?= /tmp/uv-cache
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000

SERVICES := backend mcp crawler rag

.PHONY: help \
	backend mcp crawler rag \
	backend-add backend-add-dev backend-run backend-build backend-sync backend-migrate backend-downgrade backend-revision backend-db-check \
	mcp-add mcp-add-dev mcp-run mcp-build mcp-sync \
	crawler-add crawler-add-dev crawler-run crawler-celery crawler-build crawler-sync \
	rag-add rag-add-dev rag-run rag-build rag-sync \
	build-all sync-all lock clean-dist

help:
	@echo "Workspace commands"
	@echo ""
	@echo "Shorthand (command-style):"
	@echo "  make backend add <dep1> <dep2>"
	@echo "  make backend add-dev <dep1> <dep2>"
	@echo "  make backend run"
	@echo "  make backend build"
	@echo "  make backend sync"
	@echo "  make backend migrate"
	@echo "  make backend revision \"create users table\""
	@echo "  make backend downgrade"
	@echo "  make backend db-check"
	@echo "  make backend run BACKEND_HOST=0.0.0.0 BACKEND_PORT=8080"
	@echo ""
	@echo "Supported services: backend, mcp, crawler, rag"
	@echo ""
	@echo "Explicit aliases (variable-style):"
	@echo "  make backend-add DEPS='httpx redis'"
	@echo "  make backend-add-dev DEPS='pytest ruff'"
	@echo ""
	@echo "Workspace:"
	@echo "  make build-all | make sync-all | make lock | make clean-dist"

# Command-style dispatcher:
#   make backend add dep1 dep2
#   make mcp build
#   make crawler run
#   make rag add openai qdrant-client
backend mcp crawler rag:
	@$(MAKE) service-cmd SERVICE=$@ ARGS="$(filter-out $@,$(MAKECMDGOALS))" --no-print-directory

.PHONY: service-cmd
service-cmd:
	@set -euo pipefail; \
	service="$(SERVICE)"; \
	case "$$service" in \
	  backend) pkg="backend" ;; \
	  mcp) pkg="mcp-server" ;; \
	  crawler) pkg="crawler" ;; \
	  rag) pkg="rag" ;; \
	  *) echo "Unknown service: $$service"; exit 1 ;; \
	esac; \
	set -- $(ARGS); \
	action="$${1:-help}"; \
	if [ "$$#" -gt 0 ]; then shift; fi; \
	case "$$action" in \
	  add) \
	    [ "$$#" -gt 0 ] || { echo "Usage: make $$service add <dep...>"; exit 1; }; \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package "$$pkg" "$$@" ;; \
	  add-dev) \
	    [ "$$#" -gt 0 ] || { echo "Usage: make $$service add-dev <dep...>"; exit 1; }; \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package "$$pkg" --dev "$$@" ;; \
	  run) \
	    if [ "$$service" = "backend" ]; then \
	      UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package "$$pkg" uvicorn app.main:app --reload --host "$(BACKEND_HOST)" --port "$(BACKEND_PORT)"; \
	    elif [ "$$service" = "crawler" ]; then \
	      UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package "$$pkg" celery -A crawler.celery_app:celery worker -l info -Q crawl; \
	    else \
	      cmd="$$service"; [ "$$service" = "mcp" ] && cmd="mcp-server"; \
	      UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package "$$pkg" "$$cmd"; \
	    fi ;; \
	  build) \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package "$$pkg" ;; \
	  sync) \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package "$$pkg" ;; \
	  migrate) \
	    [ "$$service" = "backend" ] || { echo "Action '$$action' is only supported for backend"; exit 1; }; \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend alembic -c backend/alembic.ini upgrade head ;; \
	  downgrade) \
	    [ "$$service" = "backend" ] || { echo "Action '$$action' is only supported for backend"; exit 1; }; \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend alembic -c backend/alembic.ini downgrade -1 ;; \
	  db-check) \
	    [ "$$service" = "backend" ] || { echo "Action '$$action' is only supported for backend"; exit 1; }; \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend python backend/scripts/db_check.py ;; \
	  revision) \
	    [ "$$service" = "backend" ] || { echo "Action '$$action' is only supported for backend"; exit 1; }; \
	    [ "$$#" -gt 0 ] || { echo "Usage: make backend revision \"message\""; exit 1; }; \
	    msg="$$(printf "%s " "$$@" | sed 's/[[:space:]]*$$//')"; \
	    UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend alembic -c backend/alembic.ini revision --autogenerate -m "$$msg" ;; \
	  help) \
	    $(MAKE) help --no-print-directory ;; \
	  *) \
	    echo "Unsupported action: $$action"; \
	    echo "Supported: add, add-dev, run, build, sync, migrate, revision, downgrade"; \
	    exit 1 ;; \
	esac

# Variable-style aliases:
#   make backend-add DEPS='httpx redis'
#   make crawler-add-dev DEPS='pytest'
#   make rag-add DEPS='openai qdrant-client'
backend-add:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package backend $(DEPS)

backend-add-dev:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package backend --dev $(DEPS)

backend-run:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend uvicorn app.main:app --reload --host "$(BACKEND_HOST)" --port "$(BACKEND_PORT)"

backend-build:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package backend

backend-sync:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package backend

backend-migrate:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend alembic -c backend/alembic.ini upgrade head

backend-downgrade:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend alembic -c backend/alembic.ini downgrade -1

backend-db-check:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend python backend/scripts/db_check.py

backend-revision:
	@test -n "$(MSG)" || (echo "Usage: make backend-revision MSG='create users table'"; exit 1)
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package backend alembic -c backend/alembic.ini revision --autogenerate -m "$(MSG)"

mcp-add:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package mcp-server $(DEPS)

mcp-add-dev:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package mcp-server --dev $(DEPS)

mcp-run:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package mcp-server mcp-server

mcp-build:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package mcp-server

mcp-sync:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package mcp-server

crawler-add:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package crawler $(DEPS)

crawler-add-dev:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package crawler --dev $(DEPS)

crawler-run:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package crawler crawler

crawler-celery:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package crawler celery -A crawler.celery_app:celery worker -l info -Q crawl

crawler-build:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package crawler

crawler-sync:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package crawler

rag-add:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package rag $(DEPS)

rag-add-dev:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) add --package rag --dev $(DEPS)

rag-run:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) run --package rag rag

rag-build:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package rag

rag-sync:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package rag

build-all:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package backend
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package mcp-server
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package crawler
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) build --package rag

sync-all:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package backend
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package mcp-server
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package crawler
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) sync --package rag

lock:
	@UV_CACHE_DIR="$(UV_CACHE_DIR)" $(UV) lock

clean-dist:
	@rm -rf dist

# Swallow extra goals in command-style calls:
# make backend add dep1 dep2
%:
	@:
