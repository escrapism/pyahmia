import argparse
import time

from rich.status import Status

from . import __pkg__, __version__
from ._api import Ahmia
from ._lib import console, check_updates, print_results, export_csv, print_banner


def cli():
    """
    Search hidden services on the Tor network.
    """
    parser = argparse.ArgumentParser(
        prog=__pkg__,
        description="Search hidden services on the Tor network.",
    )
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument(
        "-t",
        "--use-tor",
        action="store_true",
        help="Route traffic through the Tor network",
    )
    parser.add_argument(
        "-e",
        "--export",
        action="store_true",
        help="Export the output to a file",
    )
    parser.add_argument(
        "-p",
        "--period",
        type=str,
        choices=["day", "week", "month", "all"],
        default="all",
        help="Show results from a specified time period (default: all)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{__pkg__} {__version__}, by Ritchie Mwewa",
    )

    args = parser.parse_args()

    console.set_window_title(f"{__pkg__}, {__version__}")
    now: float = time.time()
    try:
        print_banner(tor_mode=args.use_tor)

        ahmia = Ahmia(
            user_agent=f"{__pkg__}-cli/{__version__}; +https://github.com/escrapism/{__pkg__}",
            use_tor=args.use_tor,
        )

        with Status(
            "[bold]Initialising[/bold][yellow]…[/yellow]", console=console
        ) as status:
            check_updates(status=status)
            search = ahmia.search(
                query=args.query, time_period=args.period, status=status
            )
            print_results(search=search)

            if args.export:
                outfile: str = export_csv(results=search["results"], path=args.query)
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
