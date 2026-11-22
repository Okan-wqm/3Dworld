# One entry point for humans, LLM sessions and CI. CI runs these same targets.
#   make setup          model-free Python env (.venv) + geom_core bindings
#   make setup-models   + PyTorch (CPU), MoGe, SAM 2   (add GPU=1 for CUDA PyTorch)
#   make ci             everything CI checks: lint, test, schema, licenses

VENV ?= .venv
PY := $(VENV)/bin/python
SETUP_FLAGS := $(if $(GPU),--gpu,)

.PHONY: setup setup-models bindings lint lint-rust lint-python test test-rust test-python \
        schema licenses ci

setup:
	VENV=$(VENV) scripts/setup_env.sh

setup-models:
	VENV=$(VENV) scripts/setup_env.sh --models $(SETUP_FLAGS)

# Rebuild the Python bindings after changing Rust code.
bindings:
	$(VENV)/bin/maturin develop --release -q -m crates/geom-py/Cargo.toml

lint: lint-rust lint-python

lint-rust:
	cargo fmt --all --check
	cargo clippy --locked --workspace --all-targets -- -D warnings

lint-python:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	$(PY) -m mypy

test: test-rust test-python

test-rust:
	cargo test --locked
	cargo test --locked -p geom-core --no-default-features

test-python:
	$(PY) -m pytest -q

# Regenerates the JSON Schema and the Python-built fixture, then fails if either was
# out of date (the committed files are the cross-language contract).
schema:
	cargo run --locked -q -p scene-schema --bin export-schema schema/scene.schema.json
	$(PY) -m workers.tests.scene_example
	git diff --exit-code schema/

licenses:
	cargo deny --locked check licenses bans sources
	$(PY) scripts/check_blacklist.py

ci: lint test schema licenses
