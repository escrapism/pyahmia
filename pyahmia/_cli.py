import time
from contextlib import suppress

import rich_click as click
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.status import Status
from rich.table import Table

from . import __pkg__, __version__
from ._api import Ahmia, console


@click.command()
@click.argument("query", type=str)
@click.option(
    "-e",
    "--export",
    is_flag=True,
    help="Export the output to a given filename",
)
@click.option(
    "-l",
    "--limit",
    default=20,
    show_default=True,
    help="Maximum number of results to show",
)
@click.option("--use-tor", is_flag=True, help="Connect to the Tor network")
def cli(query: str, limit: int, use_tor: bool, export: bool):
    """
    Search Ahmia for hidden services matching QUERY.
    """

    console.set_window_title(f"{__pkg__}, {__version__}")

    client = Ahmia(
        user_agent=f"{__pkg__}-cli/{__version__}; +https://pypi.org/project/{__pkg__}",
        use_tor=use_tor,
    )

    table = Table(
        box=box.SIMPLE,
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

        with Status(
            "[bold]Checking for update[yellow]...[/bold][/yellow]", console=console
        ) as status:
            with suppress(Exception):
                client.check_updates()

            if use_tor:
                console.log(
                    "[bold][#c7ff70]✔ Routing traffic through Tor[/][/bold]",
                )
            else:
                console.log(
                    "[bold yellow]✘ Routing traffic through the clearnet[/bold yellow]"
                )
            status.update(
                f"[bold]Searching for [#c7ff70]{query}[/]. Please wait[yellow]...[/bold][/yellow]"
            )

            results, total_results = client.search(query=query, limit=limit)
            results_length = len(results)

            if total_results > 0:
                console.log(
                    f"[bold][#c7ff70]✔[/] Showing {results_length} of {total_results} results for [#c7ff70]{query}[/][/bold]"
                )
                for index, result in enumerate(results, start=1):
                    content_items = [
                        f"[bold][#c7ff70]{result.title}[/][/bold]",
                        Rule(style="#444444"),
                        result.about,
                        f"[blue][link=http://{result.url}]{result.url}[/link][/blue] — [bold]{result.last_seen_rel}[/]",
                    ]
                    console.print(
                        Panel(
                            Group(*content_items),
                            highlight=True,
                            border_style="dim",
                        )
                    )

                if export:
                    outfile: str = client.export_csv(results=results, path=query)
                    console.log(f"{results_length} results exported to {outfile}")

            else:
                console.log(
                    f"[bold][yellow]✘[/yellow]No results found for {query}.[/bold]"
                )

    except KeyboardInterrupt:
        console.log("\n[bold][red]✘[/red] User interruption detected[/bold]")

    except Exception as e:
        console.log(f"[bold][red]✘[/red] An error occurred:  [red]{e}[/red][/bold]")
    finally:
        elapsed: float = time.time() - now
        console.log(f"[bold][#c7ff70]✔[/] Finished in {elapsed:.2f} seconds.[/bold]")
