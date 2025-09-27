import time
from contextlib import suppress

import rich_click as click
from rich import box
from rich.table import Table

from . import __pkg__, __version__
from .main import Ahmia, console, log


@click.command()
@click.argument("query", type=str)
@click.option(
    "--export",
    help="Export the output to a given filename",
)
@click.option(
    "--limit",
    default=20,
    show_default=True,
    help="Maximum number of results to show",
)
@click.option("--use-tor", is_flag=True, help="Connect to the Tor network")
def cli(query: str, limit: int, use_tor: bool, export: str):
    """
    Search Ahmia for hidden services matching QUERY.
    """

    console.set_window_title(f"{__pkg__}, {__version__}")

    client = Ahmia(
        user_agent=f"{__pkg__}-cli/{__version__}; +https://pypi.org/project/{__pkg__}",
        use_tor=use_tor,
    )

    table = Table(
        box=box.MINIMAL,
        highlight=True,
        header_style="bold",
        border_style="dim",
    )
    table.add_column("#", style="bold")
    table.add_column("title")
    table.add_column("about")
    table.add_column("url", style="blue", no_wrap=True)
    table.add_column("last seen")

    now: float = time.time()
    try:
        with suppress(Exception):
            client.check_updates()

        if use_tor:
            log.info("[bold green]Routing traffic through Tor[/bold green]")
        else:
            log.warning(
                "[bold yellow]Routing traffic through the clearnet[/bold yellow]"
            )
        log.info(f"[bold]Searching for '{query}'. Please wait[/]...")
        results = list(client.search(query=query, limit=limit))
        results_length = len(results)

        if results:
            for index, result in enumerate(results, start=1):
                table.add_row(
                    str(index),
                    result.title,
                    result.about,
                    result.url,
                    result.last_seen_rel,
                )

            if export:
                outfile: str = client.export_csv(results=results, path=export)
                log.info(f"{results_length} results exported to {outfile}")

            console.print(table)
        else:
            log.warning(f"[bold]No results found for {query}.[/bold]")

    except KeyboardInterrupt:
        log.warning("\n[bold]User interruption detected[/bold]")

    except Exception as e:
        console.log(f"[bold red]{e}[/bold red]")
    finally:
        elapsed: float = time.time() - now
        log.info(f"[bold]Finished in {elapsed:.2f} seconds.[/]")
