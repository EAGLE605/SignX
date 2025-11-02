.PHONY: ready schema perf contract up health lint smoke all

up:
	docker compose up -d --build

ready:
	curl -fsS localhost:8000/ready | jq

health:
	curl -fsS localhost:8000/health | jq

schema:
	curl -fsS localhost:8000/schemas/envelope.v1.json | jq

perf:
	k6 run tests/perf/k6_smoke.js

contract:
	pytest -q tests/contract

smoke:
	python scripts/smoke.py

lint:
	ruff check .

all: lint contract smoke

translator.refresh:
	python svcs/agent_translator/main.py --refresh

translator.ask:
	python svcs/agent_translator/main.py --ask "$(Q)"

