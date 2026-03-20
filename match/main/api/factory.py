import subprocess
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from loguru import logger

from match.api.delete_cache import router as delete_cache_router
from match.config import Settings, get_settings
from match.core.logging import init_logger
from match.presentation.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    debug = getattr(app, "debug", False)
    init_logger(debug=debug)
    yield
    state = getattr(app, "state", None)
    if state:
        dishka_container = getattr(state, "dishka_container", None)
        if dishka_container:
            await dishka_container.close()
            logger.info("Dishka container closed")


class APIFactory:
    def __init__(self, container: AsyncContainer, settings: Settings | None = None) -> None:
        if settings is None:
            self.settings = get_settings()
        else:
            self.settings = settings
        self.container = container

    def make(self) -> FastAPI:
        app = FastAPI(
            title="Fluence Match API",
            description="Endpoints for Fluence Match AI",
            lifespan=lifespan,
            debug=self.settings.debug,
        )

        # Setup Dishka Container
        setup_dishka(self.container, app)

        # Include router
        app.include_router(router)
        app.include_router(delete_cache_router)

        # Set App Version
        try:
            app.version = subprocess.check_output("git describe --always", shell=True).decode("utf-8").strip()
        except subprocess.CalledProcessError:
            logger.warning("Failed to get git version. Using default version.")

        # Status endpoint
        @app.get("/")
        async def get_status() -> dict[str, str]:
            return {"status": "running"}

        return app

    def run(self, app: FastAPI, host: str = "0.0.0.0", port: int = 8000) -> None:
        uvicorn.run(
            app=app,
            host=host,
            port=port,
        )
