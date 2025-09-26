from contextlib import suppress

import rich_click as click
from rich import print, box
from rich.table import Table

from . import Ahmia, __pkg__, __version__


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
    client = Ahmia(user_agent=f"{__pkg__}-cli/{__version__}", use_tor=use_tor)

    table = Table(
        box=box.MINIMAL,
        highlight=True,
        header_style="bold",
        border_style="dim",
    )
    table.add_column("#", style="bold")
    table.add_column("Title")
    table.add_column("About")
    table.add_column("Onion URL", style="blue", no_wrap=True)
    table.add_column("Last Seen")

    try:
        with suppress(Exception):
            client.check_updates()

        if use_tor:
            print("[bold green]Routing requests through Tor[/bold green]")
        else:
            print("[bold yellow]Not routing requests through Tor[/bold yellow]")
        print(f"[bold]Searching for '{query}'. Please wait[/]...")
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
                print(f"{results_length} results exported to {outfile}")

            print(table)

    except KeyboardInterrupt:
        print("\n[bold yellow]User interruption detected[/bold yellow]")

    except Exception as e:
        print(f"[bold red]{e}[/bold red]")
