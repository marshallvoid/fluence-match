import typer
from neomodel import config

from match.config import get_settings
from match.config.settings import Settings
from match.core.async_typer import AsyncTyper
from match.main.api.app import run_api
from match.main.worker.app import run_worker
from match.presentation.cli.auth import auth_commands
from match.presentation.cli.neo4j import neo4j_commands
from match.providers.factory import make_container


class CLIFactory:
    def make(self) -> typer.Typer:
        settings = get_settings()
        container = make_container(settings)

        app = AsyncTyper(
            rich_markup_mode="rich",
            context_settings={
                "obj": {
                    "container": container,
                    "settings": settings,
                },
            },
        )

        # Setup Neo4j Driver
        self.neoj4_driver_config(settings)

        # Add commands
        self.add_api_command(app)
        self.add_worker_command(app)
        self.add_app_commands(app)
        return app

    def add_api_command(self, app: AsyncTyper) -> None:
        @app.command(name="api")
        def api(
            ctx: typer.Context, port: int = typer.Option(8000, "--port", "-p", help="Port to run the API Sever")
        ) -> None:
            """
            [green]Run[/green] api.
            """
            ctx_container = ctx.obj.get("container")
            ctx_settings = ctx.obj.get("settings")
            run_api(ctx_settings, ctx_container, port=port)

    def add_worker_command(self, app: AsyncTyper) -> None:
        @app.command(name="worker")
        def worker(ctx: typer.Context) -> None:
            """
            [green]Run[/green] worker.
            """
            ctx_container = ctx.obj.get("container")
            ctx_settings = ctx.obj.get("settings")
            run_worker(ctx_settings, ctx_container)

    def add_app_commands(self, app: AsyncTyper) -> None:
        app.add_typer(auth_commands, name="auth")
        app.add_typer(neo4j_commands, name="neo4j")

    def neoj4_driver_config(self, settings: Settings) -> None:
        assert settings.neo4j_bolt_url, "Neo4j URL is required"

        config.DATABASE_URL = settings.neo4j_bolt_url
        config.MAX_CONNECTION_POOL_SIZE = settings.neo4j_max_connections
        config.CONNECTION_TIMEOUT = settings.neo4j_connection_timeout
        config.MAX_CONNECTION_LIFETIME = settings.neo4j_max_connection_lifetime
