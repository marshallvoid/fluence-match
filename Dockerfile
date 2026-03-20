# Build stage
FROM python:3.12.8-slim AS builder

# Install poetry
RUN pip install poetry==1.8.5

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY ./match match
COPY poetry.lock pyproject.toml /app/

# Export dependencies to requirements.txt and install
RUN pip install build && python3 -m build --wheel

# Final stage
FROM python:3.12.8-slim

WORKDIR /app

COPY --from=builder ./app/dist ./
RUN $(printf "pip install %s[match]" match*.whl) && pip cache purge && rm ./*.whl

COPY ./match /app/match
COPY ./entrypoint.sh /app

CMD ["sh", "entrypoint.sh"]
