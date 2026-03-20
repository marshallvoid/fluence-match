# Fluence Match

### Config env

Set .env file using .env.example as template

### **Using Docker**

To start the application using Docker, run:

```shell
    docker compose up -d
```

### **Using Native (Poetry)**

#### **Install Dependencies**

Ensure you have [Poetry](https://python-poetry.org/) installed, then run:

```shell
    poetry install
```

#### **Executing Typer Commands**

You can execute Typer commands in two ways:

1. **Directly using `poetry run`**
2. **Or Activate the Poetry environment `poetry shell`**

#### **Start Services**

- Start API server with: `match api`

- Start Faststream worker with: `match worker`

### Neo4j Commands

To install labels for all models defined in the `match.models` module, run:

```shell
    match neo4j install-labels
```

To check the installed labels, generate a diagram using:

```shell
    match neo4j generate-diagram --file-type arrows
```

For more Neo4j-related commands and options:

```shell
    match neo4j --help
```

## Makefile

See `make help` for details.
