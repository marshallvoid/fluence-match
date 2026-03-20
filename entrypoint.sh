#!/bin/bash

PORT=${PORT:-8000}

if [ "$1" = "worker" ]; then
    echo "Starting Fluence Match Worker..."
    faststream run match.main.worker.native:worker
else
    echo "Start Fluence Match FastAPI service..."
    uvicorn match.main.api.native:app --host 0.0.0.0 --port "${PORT}"
fi
