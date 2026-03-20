import rich
import typer

from match.core.async_typer import AsyncTyper
from match.infrastructure.api_key_manager.api_key_manager import APIKeyManager
from match.infrastructure.api_key_manager.encrypt_api_key import RateLimitType

auth_commands = AsyncTyper(
    name="auth",
    help="[yellow]Manage[/yellow] Authentication",
)


@auth_commands.command()
async def generate_api_key(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name of the API key.",
    ),
    rate_limit: int = typer.Option(
        1000,
        "--rate-limit",
        "-r",
        help="Rate limit for the API key.",
    ),
    rate_limit_type: RateLimitType = typer.Option(
        RateLimitType.DAY.value,
        "--type",
        "-t",
        help="Rate limit type for the API key.",
    ),
    ttl: int = typer.Option(
        3 * 24 * 60 * 60,
        "--ttl",
        "-t",
        help="Time to live for the API key.",
    ),
) -> None:
    """
    [green]Generate[/green] a new API key.
    """

    container = ctx.obj["container"]

    async with container() as request_container:
        api_key_manager: APIKeyManager = await request_container.get(APIKeyManager)

        try:
            api_key = await api_key_manager.create(
                name=name,
                rate_limit=rate_limit,
                rate_limit_type=rate_limit_type,
                ttl=ttl,
            )
            rich.print(f"Successfully! Generated API Key: [green]{api_key}[/green]")

        except Exception as e:
            msg = getattr(e, "detail", str(e))
            rich.print(f"Failed to Generate API Key - [red]Error: {msg}[/red].")
