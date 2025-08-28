.PHONY: init install run clean help

VENV_DIR := .venv
PYTHON := python3
PIP := $(VENV_DIR)/bin/pip
UVICORN := $(VENV_DIR)/bin/uvicorn
PORT ?= 8000

help:
	@echo "Usage: make init | install | run | clean"
	@echo "  init    Create venv, install deps, and start the server"
	@echo "  install Create venv and install dependencies"
	@echo "  run     Activate the venv and starts the FastAPI server"
	@echo "  clean   Remove virtualenv"

init: install run

install:
	@set -e; \
	if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi; \
	. $(VENV_DIR)/bin/activate; \
	$(PIP) install --upgrade pip; \
	$(PIP) install -r requirements.txt

run:
	@echo "Starting server on http://0.0.0.0:$(PORT)"; \
	. $(VENV_DIR)/bin/activate; \
	$(UVICORN) app.main:app --host 0.0.0.0 --port $(PORT)

clean:
	rm -rf $(VENV_DIR)


