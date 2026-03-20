# Fluence Match

Fluence Match is an API and worker system for influencer matching workflows.

## Prerequisites

- Python 3.12
- [Poetry](https://python-poetry.org/)
- Docker and Docker Compose (recommended for dependencies)

## Environment Setup

1. Create your environment file from the template.

```shell
# Linux/macOS
cp .env.example .env

# Windows (cmd)
copy .env.example .env
```

2. Fill required values in `.env` for your setup.

- `OPENAI_API_KEY`
- `NEO4J_BOLT_URL`
- `REDIS_URL`
- `NATS_URL`
- PostgreSQL values if your workflow uses them

For native local runs, make sure service URLs point to local endpoints when needed (for example, `localhost` instead of Docker service names).

## Run with Docker

Start the stack:

```shell
docker compose up -d
```

Services started by compose:

- API: `http://localhost:8000`
- Worker (FastStream consumer)
- Redis
- NATS

## Run Natively with Poetry

Install dependencies:

```shell
poetry install
```

You can run commands either with `poetry run` or inside `poetry shell`.

Start API:

```shell
poetry run match api
```

Start API on custom port:

```shell
poetry run match api --port 8080
```

Start worker:

```shell
poetry run match worker
```

## CLI Commands

Show main command help:

```shell
poetry run match --help
```

Generate API key:

```shell
poetry run match auth generate-api-key --name my-key --rate-limit 1000 --type DAY --ttl 259200
```

## Neo4j Commands

Install labels:

```shell
poetry run match neo4j install-labels
```

Remove labels:

```shell
poetry run match neo4j remove-labels
```

Generate diagram (arrows format):

```shell
poetry run match neo4j generate-diagram --file-type arrows
```

Generate diagram (PlantUML format):

```shell
poetry run match neo4j generate-diagram --file-type puml --output-dir .
```

More options:

```shell
poetry run match neo4j --help
```

## Makefile Shortcuts

List available targets:

```shell
make help
```

Useful targets:

- `make native.generate_api_key`
- `make docker.generate_api_key`
- `make native.generate_secret`
- `make docker.generate_secret`
- `make clean`

## Development Commands

Format code:

```shell
# If bash is available
bash scripts/format.sh
```

Lint and type-check:

```shell
# If bash is available
bash scripts/lint.sh
```

## Quick Verification

Check API health:

```shell
curl http://localhost:8000/
```

Expected response:

```json
{ "status": "running" }
```
