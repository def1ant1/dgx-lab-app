.PHONY: venv install install-all run run-console run-connector run-mcp-stdio stop status claude-env-local claude-env-tailscale

VENV?=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)

install: venv
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt

install-all: venv
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements-all.txt

# Backwards compatible target: run console
run: run-console

run-console: install
	@$(VENV)/bin/uvicorn dgx_ollama_console.main:app --app-dir . --host 127.0.0.1 --port 8080

run-connector: install-all
	@CONNECTOR_CHROMA_DIR=./.chroma CONNECTOR_TARGET_URL=$${CONNECTOR_TARGET_URL:-http://127.0.0.1:5173} \
	$(VENV)/bin/uvicorn apotheon_connector.app.main:app --app-dir . --host 127.0.0.1 --port 8090

run-mcp-stdio: install-all
	@MCP_ALLOWED_ROOTS=$${MCP_ALLOWED_ROOTS:-$$(pwd)} CONNECTOR_API_BASE=$${CONNECTOR_API_BASE:-http://127.0.0.1:8090} \
	$(VENV)/bin/python -m mcp_repo_connector.server

stop:
	@./stop.sh

status:
	@curl -sS http://127.0.0.1:8080/api/status | python3 -m json.tool

claude-env-local:
	@curl -sS "http://127.0.0.1:8080/api/claude-code/env?mode=local" | python3 -c 'import sys, json; print(json.load(sys.stdin)["exports"])'

claude-env-tailscale:
	@curl -sS "http://127.0.0.1:8080/api/claude-code/env?mode=tailscale" | python3 -c 'import sys, json; print(json.load(sys.stdin)["exports"])'
