# Makefile для llmstart_hw_intensive_072025

.PHONY: build run test lint deploy local-deploy run-local

build:
	docker build -t llm-tg-bot .

run:
	docker run --env-file .env -p 8080:8080 llm-tg-bot

test:
	conda run -n llm-tg-bot pytest tests/

lint:
	conda run -n llm-tg-bot ruff src/

deploy: build
	@if [ -f .env ]; then export $$(grep -v '^#' .env | grep -v '^[[:space:]]*$$' | xargs); fi && railway up 

local-deploy: build
	@if [ -f .env ]; then export $$(grep -v '^#' .env | grep -v '^[[:space:]]*$$' | xargs); fi && docker run --env-file .env -p 8080:8080 llm-tg-bot 

run-local: build
	docker run --env-file .env llm-tg-bot 