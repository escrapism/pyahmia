import time
import typing as t

import rich_click as click
from rich.status import Status

from . import __pkg__, __version__
from ._api import Ahmia
from ._lib import console, check_updates, print_results, export_csv, print_banner


@click.command()
@click.argument("query", type=str)
@click.option(
    "-t", "--use-tor", is_flag=True, help="Route traffic through the Tor network"
)
@click.option(
    "-e",
    "--export",
    is_flag=True,
    help="Export the output to a file",
)
@click.option(
    "-p",
    "--period",
    type=click.Choice(["day", "week", "month", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Show results from a specified time period",
)
@click.version_option(__version__, "-v", "--version", prog_name=__pkg__)
def cli(
    query: str,
    use_tor: bool,
    export: bool,
    period: t.Literal["day", "week", "month", "all"],
):
    """
    Search hidden services on the Tor network.
    """

    console.set_window_title(f"{__pkg__}, {__version__}")
    now: float = time.time()
    try:
        print_banner(tor_mode=use_tor)

        ahmia = Ahmia(
            user_agent=f"{__pkg__}-cli/{__version__}; +https://github.com/escrapism/{__pkg__}",
            use_tor=use_tor,
        )

        with Status(
            "[bold]Initialising[/bold][yellow]…[/yellow]", console=console
        ) as status:
            check_updates(status=status)
            search = ahmia.search(query=query, time_period=period, status=status)
            print_results(search=search)

            if export:
                outfile: str = export_csv(results=search["results"], path=query)
                console.log(
                    f"[bold][#c7ff70]🖫[/] {search['total_count']} results exported: [link file://{outfile}]{outfile}[/bold]"
                )

    except KeyboardInterrupt:
        console.log("\n[bold][red]✘[/red] User interruption detected[/bold]")

    except OSError as e:
        console.log(f"[bold][red]✘[/red] An error occurred:  {e}[/bold]")
    finally:
        elapsed: float = time.time() - now
        console.log(f"[bold][#c7ff70]✔[/] Finished in {elapsed:.2f} seconds.[/bold]")
