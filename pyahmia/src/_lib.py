import csv
import typing as t
from contextlib import suppress
from pathlib import Path

from requests import RequestException
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.status import Status
from update_checker import UpdateChecker

from . import __pkg__, __version__

console = Console(log_time=False)

__all__ = [
    "print_banner",
    "print_results",
    "check_updates",
    "export_csv",
    "console",
]


def print_banner(tor_mode: bool):
    console.print(
        f"""[bold]{"[red]" if tor_mode else "[#c7ff70]"}
 ▗▄▖ ▐▌   ▄▄▄▄  ▄ ▗▞▀▜▌
▐▌ ▐▌▐▌   █ █ █ ▄ ▝▚▄▟▌
▐▛▀▜▌▐▛▀▚▖█   █ █      
▐▌ ▐▌▐▌ ▐▌      █[/bold].{"onion" if tor_mode else "fi"}{"[/red]" if tor_mode else "[/]"} {__version__}
"""
    )


def print_results(search: dict):
    is_success = search["success"]

    if is_success:
        results = search["results"]
        console.log(f"[bold][#c7ff70]✔[/] {search['message']}[/bold]")
        for index, result in enumerate(results, start=1):
            title = result["title"]
            about = result["about"]
            url = result["url"]
            last_seen = result["last_seen_rel"]

            # ----------------------------------------------------------------------- #
            content_items = [
                f"[bold][#c7ff70]{title}[/][/bold]",
                Rule(style="#444444"),
                about,
                f"[blue][link=http://{url}]{url}[/link][/blue] — [bold]{last_seen}[/]",
            ]
            console.print(
                Panel(
                    Group(*content_items),
                    highlight=True,
                    border_style="dim #c7ff70",
                    title_align="left",
                    title=f"[{index}]",
                )
            )
            # ----------------------------------------------------------------------- #
    else:
        console.log(f"[bold][yellow]✘[/yellow] {search['message']}[/bold]")


def check_updates(status: Status):
    """
    Checks for program (pyahmia) updates.

    :param status: A rich.status.Status object to show a live status message.
    """
    with suppress(RequestException):
        if isinstance(status, Status):
            status.update("[bold]Checking for updates[/bold][yellow]…[/yellow]")

        checker = UpdateChecker()
        check = checker.check(package_name=__pkg__, package_version=__version__)

        if check is not None:
            console.print(f"[bold][blue]🡅[/blue] {check}[/bold]")


def export_csv(results: t.Iterable[dict], path: str) -> str:
    """
    Exports search results to a csv file.

    :param results: A list of SimpleNamespace objects, each representing a search result.
    :param path: A path name/filename to which the results will be exported.
    :return: The pathname to the exported results file.
    """

    results_list = list(results)

    if not all(isinstance(item, dict) for item in results_list):
        raise TypeError(
            "export_csv expects an iterable of dict objects (e.g., result of Ahmia.search())"
        )

    dict_rows = [item for item in results_list]

    if not dict_rows:
        raise ValueError("No results to export")

    out: Path = Path().home() / "pyahmia" / f"{path}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open(mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=dict_rows[0].keys())
        writer.writeheader()
        writer.writerows(dict_rows)

    return str(out)
