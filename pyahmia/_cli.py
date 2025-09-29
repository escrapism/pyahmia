import time
import typing as t

import rich_click as click
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.status import Status

from . import __pkg__, __version__
from ._api import Ahmia, console


@click.command()
@click.argument("query", type=str)
@click.option(
    "-T", "--use-tor", is_flag=True, help="Route traffic through the Tor network"
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

    client = Ahmia(
        user_agent=f"{__pkg__}-cli/{__version__}; +https://pypi.org/project/{__pkg__}",
        use_tor=use_tor,
    )

    now: float = time.time()
    try:
        console.print(
            f"""[bold][#c7ff70]
 ▗▄▖ ▐▌   ▄▄▄▄  ▄ ▗▞▀▜▌
▐▌ ▐▌▐▌   █ █ █ ▄ ▝▚▄▟▌
▐▛▀▜▌▐▛▀▚▖█   █ █      
▐▌ ▐▌▐▌ ▐▌      █.fi [/][/] {__version__}
        """
        )
        with Status(
            "[bold]Initialising[/bold][yellow]...[/yellow]", console=console
        ) as status:
            client.check_updates(status=status)
            if use_tor:
                console.log(
                    f"[bold][#c7ff70]🗹 Routing traffic through Tor[/][/bold]",
                )
            else:

                console.log(
                    f"[bold][yellow]⚠ Routing traffic through the clearnet[/yellow][/bold]"
                )
            status.update(
                f"[bold]Searching for [#c7ff70]{query}[/]. Please wait[yellow]...[/bold][/yellow]"
            )

            search = client.search(query=query, time_period=period)

            if search.total_count > 0:
                results = search.results
                console.log(f"[bold][#c7ff70]✔[/] {search.summary}[/bold]")
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
                            border_style="dim #c7ff70",
                            title_align="left",
                            title=f"#{index}",
                        )
                    )

                if export:
                    outfile: str = client.export_csv(results=results, path=query)
                    console.log(
                        f"[bold][#c7ff70]🖫[/] {search.total_count} results exported: [link file://{outfile}]{outfile}[/bold]"
                    )

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
