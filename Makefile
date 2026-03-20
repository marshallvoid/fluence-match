# Flags and settings
DOCKER_COMPOSE_FILE = -f docker-compose.yml
NATIVE_RUN = poetry run
DOCKER_RUN = docker compose ${DOCKER_COMPOSE_FILE} exec -t fluence-match_api

# Targets separation
NATIVE_PREFIX = native.
DOCKER_PREFIX = docker.

# Define Makefile arguments
ARGS := $(filter-out $(KNOWN_TARGETS),$(MAKECMDGOALS))
KNOWN_TARGETS = native.generate_api_key docker.generate_api_key native.generate_secret docker.generate_secret

ifneq ($(ARGS),$(MAKECMDGOALS))
$(eval $(ARGS):;@:)
endif

# Default target (help command)
.PHONY: help
help: ## Show this help information
	@echo "Available commands:"
	@grep -E '^[a-zA-Z0-9._-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'
	@echo "\nUse 'make <target>' to execute a command."


.PHONY: native.generate_api_key
native.generate_api_key: ## Generate an API key (Native)
	@read -p "Enter API Key Name: " API_KEY_NAME; \
	read -p "Enter Rate Limit (default: 1000): " RATE_LIMIT; \
	read -p "Enter Rate Limit Type (default: DAY): " RATE_LIMIT_TYPE; \
	read -p "Enter TTL in seconds (default: 259200): " TTL; \
	${NATIVE_RUN} match auth generate-api-key --name "$$API_KEY_NAME" --rate-limit "$${RATE_LIMIT:-1000}" --type "$${RATE_LIMIT_TYPE:-DAY}" --ttl "$${TTL:-259200}"

.PHONY: docker.generate_api_key
docker.generate_api_key: ## Generate an API key (Docker)
	@read -p "Enter API Key Name: " API_KEY_NAME; \
	read -p "Enter Rate Limit (default: 1000): " RATE_LIMIT; \
	read -p "Enter Rate Limit Type (default: DAY): " RATE_LIMIT_TYPE; \
	read -p "Enter TTL in seconds (default: 259200): " TTL; \
	${DOCKER_RUN} match auth generate-api-key --name "$$API_KEY_NAME" --rate-limit "$${RATE_LIMIT:-1000}" --type "$${RATE_LIMIT_TYPE:-DAY}" --ttl "$${TTL:-259200}"


# -------------------------------
# Generate Secret Key
# -------------------------------
.PHONY: native.generate_secret
native.generate_secret: ## Generate a Base64 URL-safe secret key (Native)
	@python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"

.PHONY: docker.generate_secret
docker.generate_secret: ## Generate a Base64 URL-safe secret key (Docker)
	${DOCKER_RUN} /bin/bash -c "python -c 'import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())'"

.PHONY: clean
clean: ## Remove Python cache files and directories
	@echo "Removing all __pycache__ directories and .pyc files…"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
