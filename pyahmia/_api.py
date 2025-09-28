import csv
import typing as t
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace

import requests
from bs4 import BeautifulSoup, ResultSet, PageElement
from requests import Response
from requests.exceptions import RequestException
from requests_tor import RequestsTor
from rich.console import Console
from rich.status import Status
from update_checker import UpdateChecker, UpdateResult

console = Console(log_time=False)

TIME_PERIODS = t.Literal["day", "week", "month", "all"]


class Ahmia:

    def __init__(self, user_agent: str, use_tor: bool = False):
        self.user_agent = user_agent
        self.use_tor = use_tor

        if use_tor:
            self.base_url: str = (
                "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q=%s"
            )
            self.session = RequestsTor(tor_ports=(9050,), tor_cport=(9051,))
        else:
            self.base_url: str = "https://ahmia.fi/search/?q=%s"
            self.session = requests.Session()

    @staticmethod
    def check_updates(status: Status):
        from . import __pkg__, __version__

        with suppress(RequestException):
            if isinstance(status, Status):
                status.update("[bold]Checking for update[yellow]...[/bold][/yellow]")

            checker = UpdateChecker()
            check: t.Union[UpdateResult, None] = checker.check(
                package_name=__pkg__, package_version=__version__
            )

            if check is not None:
                console.print(f"[bold][blue]🡅[/blue] {check}[/bold]")

    @staticmethod
    def export_csv(results: t.Iterable[SimpleNamespace], path: str) -> str:
        results_list = list(results)

        if not all(isinstance(item, SimpleNamespace) for item in results_list):
            raise TypeError(
                "export_csv expects an iterable of SimpleNamespace objects (e.g., result of Ahmia.search())"
            )

        dict_rows = [item.__dict__ for item in results_list]

        if not dict_rows:
            raise ValueError("No results to export")

        out: Path = Path().home() / "pyahmia" / f"{path}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)

        with out.open(mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=dict_rows[0].keys())
            writer.writeheader()
            writer.writerows(dict_rows)

        return str(out)

    def search(
        self,
        query: str,
        time_period: TIME_PERIODS = "all",
    ) -> tuple[list[SimpleNamespace], str, int]:
        soup: BeautifulSoup = self._get_page_source(
            query=query, time_period=time_period
        )
        summary_tag: PageElement = soup.find("div", {"class": "resultsSubheader"})
        summary: t.Union[t.LiteralString, str] = " ".join(summary_tag.text.split())

        items: ResultSet = soup.find_all("li", {"class": "result"})
        total_count: int = len(items)

        results: list[SimpleNamespace] = []
        for item in items:
            last_seen_tag = item.find("span", {"class": "lastSeen"})
            last_seen_text = (
                last_seen_tag.get_text(strip=True) if last_seen_tag else "NaN"
            )
            last_seen_timestamp = (
                last_seen_tag.get("data-timestamp") if last_seen_tag else "NaN"
            )

            results.append(
                SimpleNamespace(
                    **{
                        "title": " ".join(item.find("h4").text.split()),
                        "about": " ".join(item.find("p").text.split()),
                        "url": " ".join(item.find("cite").text.split()),
                        "last_seen_rel": last_seen_text.replace("\xa0", " "),
                        "last_seen_ts": last_seen_timestamp,
                    }
                )
            )

        return results, summary, total_count

    def _get_page_source(self, query: str, time_period: TIME_PERIODS) -> BeautifulSoup:
        params: dict = {"q": query}

        period_to_days: dict = {
            "day": "1",
            "week": "7",
            "month": "30",
        }

        if time_period in period_to_days:
            params["d"] = period_to_days[time_period]

        response: Response = self.session.get(
            url=self.base_url, params=params, headers={"User-Agent": self.user_agent}
        )
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        return soup
