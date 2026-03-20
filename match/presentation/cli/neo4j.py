import os
from typing import Annotated

import rich
import typer
from neomodel import AsyncStructuredNode
from neomodel.async_.core import adb
from neomodel.contrib import AsyncSemiStructuredNode
from neomodel.scripts import neomodel_generate_diagram
from neomodel.scripts.utils import load_python_module_or_file, recursive_list_classes

from match.core.async_typer import AsyncTyper

neo4j_commands = AsyncTyper(
    name="auth",
    help="[yellow]Neo4j[/yellow] Commands",
)


@neo4j_commands.command()
async def install_labels(
    ctx: typer.Context,
) -> None:
    """
    [green]Neo4j[/green] Install Labels
    """
    try:
        load_python_module_or_file("match.models")
        await adb.install_all_labels()
        rich.print("Successfully! Installed Neo4j Labels")

    except Exception as e:
        msg = getattr(e, "detail", str(e))
        rich.print(f"Failed to Install Neo4j Labels - [red]Error: {msg}[/red].")


@neo4j_commands.command()
async def remove_labels(
    ctx: typer.Context,
) -> None:
    """
    [green]Neo4j[/green] Remove Labels
    """
    try:
        await adb.remove_all_labels()
        rich.print("Successfully! Removed Neo4j Labels")

    except Exception as e:
        msg = getattr(e, "detail", str(e))
        rich.print(f"Failed to Remove Neo4j Labels - [red]Error: {msg}[/red].")


@neo4j_commands.command()
async def generate_diagram(
    ctx: typer.Context,
    file_type: Annotated[
        str,
        typer.Option("--file-type", "-T", help="File type to produce. Accepts : [arrows, puml]"),
    ] = "arrows",
    output_dir: Annotated[
        str,
        typer.Option(
            "--output-dir",
            "-O",
            help="Directory where to write output file. Default is current directory.",
        ),
    ] = ".",
) -> None:
    """
    [green]Neo4j[/green] Generate Diagram
    """
    try:
        load_python_module_or_file("match.models")
        classes = recursive_list_classes(AsyncStructuredNode, exclude_list=[AsyncSemiStructuredNode])

        filename = ""
        output = ""
        if file_type == "puml":
            filename, output = neomodel_generate_diagram.generate_plantuml(classes)
        elif file_type == "arrows":
            filename, output = neomodel_generate_diagram.generate_arrows_json(classes)
        else:
            msg = f"Unsupported file type : {file_type}"
            raise ValueError(msg)

        # Save to a file
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as file:
            file.write(output)
            rich.print(f"Successfully wrote diagram to file : [green]{file.name}[/green]")
    except Exception as e:
        msg = getattr(e, "detail", str(e))
        rich.print(f"Failed to Remove Neo4j Labels - [red]Error: {msg}[/red].")
