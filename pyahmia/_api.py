import csv
import typing as t
from pathlib import Path
from types import SimpleNamespace

import requests
from bs4 import BeautifulSoup, ResultSet
from requests import Response
from requests_tor import RequestsTor
from rich.console import Console
from update_checker import UpdateChecker, UpdateResult

console = Console(log_time=False)


class Ahmia:

    def __init__(self, user_agent: str, use_tor: bool = False):
        self.user_agent = user_agent
        self.use_tor = use_tor

        if use_tor:
            self._search_url: str = (
                "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q=%s"
            )
            self.session = RequestsTor(tor_ports=(9050,), tor_cport=(9051,))
        else:
            self._search_url: str = "https://ahmia.fi/search/?q=%s"
            self.session = requests.Session()

    @staticmethod
    def check_updates():
        from . import __pkg__, __version__

        checker = UpdateChecker()
        check: t.Union[UpdateResult, None] = checker.check(
            package_name=__pkg__, package_version=__version__
        )
        if check:
            console.print(check)

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

    def search(self, query: str, limit: int = 20) -> tuple[list[SimpleNamespace], int]:
        soup: BeautifulSoup = self._get_page_source(url=self._search_url % query)
        items: ResultSet = soup.find_all("li", {"class": "result"})
        total_count = len(items)

        results: list[SimpleNamespace] = []
        for item in items[:limit]:
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

        return results, total_count

    def _get_page_source(self, url: str) -> BeautifulSoup:
        response: Response = self.session.get(
            url=url, headers={"User-Agent": self.user_agent}
        )
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        return soup
