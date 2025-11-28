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

        if self.use_tor:
            self.base_url: str = (
                "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?"
            )
            self.session = RequestsTor(tor_ports=(9050,), tor_cport=(9051,))
        else:
            self.base_url: str = "https://ahmia.fi/search/?"
            self.session = requests.Session()

    @staticmethod
    def check_updates(status: Status):
        """
        Checks for program (pyahmia) updates.

        :param status: A rich.status.Status object to show a live status message.
        """
        from . import __pkg__, __version__

        with suppress(RequestException):
            if isinstance(status, Status):
                status.update("[bold]Checking for updates[/bold][yellow]...[/yellow]")

            checker = UpdateChecker()
            check: t.Union[UpdateResult, None] = checker.check(
                package_name=__pkg__, package_version=__version__
            )

            if check is not None:
                console.print(f"[bold][blue]🡅[/blue] {check}[/bold]")

    @staticmethod
    def export_csv(results: t.Iterable[SimpleNamespace], path: str) -> str:
        """
        Exports search results to a csv file.

        :param results: A list of SimpleNamespace objects, each representing a search result.
        :param path: A path name/filename to which the results will be exported.
        :return: The pathname to the exported results file.
        """

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
        token: t.Tuple[str, str],
        time_period: TIME_PERIODS = "all",
    ) -> SimpleNamespace:
        """
        Search Ahmia.fi for hidden services on the Tor network, that match with the `query`.

        :param token: Session token containing token_name, token_value
        :param query: Search query.
        :param time_period: Time period to get results from
          (expects either: `day`, `week`, `month`, and/or `all`)
        :return: A SimpleNamespace containing the search summary, total results count,
        and a list of SimpleNamespace objects, each containing info on an individual search result.
        """

        soup: BeautifulSoup = self._results_soup(
            query=query, time_period=time_period, token=token
        )

        items: ResultSet = soup.find_all("li", {"class": "result"})
        total_count: int = len(items)

        if not items:
            return SimpleNamespace(
                success=False,
                message=f"[bold]Sorry, but PyAhmia couldn't find results for [#c7ff70]{query}.[/][/bold]",
            )

        message_tag: PageElement = soup.find("div", {"class": "resultsSubheader"})
        message: t.Union[t.LiteralString, str] = " ".join(message_tag.text.split())

        results: list[dict] = []

        for item in items:
            last_seen_tag = item.find("span", {"class": "lastSeen"})
            last_seen_text = (
                last_seen_tag.get_text(strip=True) if last_seen_tag else "NaN"
            )
            last_seen_timestamp = (
                last_seen_tag.get("data-timestamp") if last_seen_tag else "NaN"
            )

            results.append(
                {
                    "title": " ".join(item.find("h4").text.split()),
                    "about": " ".join(item.find("p").text.split()),
                    "url": " ".join(item.find("cite").text.split()),
                    "last_seen_rel": last_seen_text.replace("\xa0", " "),
                    "last_seen_ts": last_seen_timestamp,
                }
            )

        return self._dict_to_namespace(
            obj={
                "success": True,
                "message": message,
                "total_count": total_count,
                "results": results,
            }
        )

    def _dict_to_namespace(
        self, obj: t.Union[t.Dict, t.List[t.Dict], t.Any]
    ) -> t.Union[SimpleNamespace, t.List[SimpleNamespace], t.Any]:
        """
        Converts a dict or list of dicts to a/list of SimpleNamespace objects.

        :param obj: A dict or list of dicts to be converted.
        :return: A SimpleNamespace object or a list of those.
        """
        if isinstance(obj, dict):
            return SimpleNamespace(
                **{key: self._dict_to_namespace(value) for key, value in obj.items()}
            )
        elif isinstance(obj, list):
            return [self._dict_to_namespace(obj=item) for item in obj]
        else:
            return obj

    def _results_soup(self, **kwargs) -> BeautifulSoup:
        """
        Parses a web response's HTML into a BeautifulSoup object.

        :return: A BeautifulSoup object with parsed HTML markup.
        """

        token = kwargs.get("token")

        if token[0] and token[1] is None:
            print(
                f"Token appears to be invalid ({token}), this might return empty results."
            )
            return BeautifulSoup("", "html.parser")

        query: str = kwargs.get("query")
        time_period: TIME_PERIODS = kwargs.get("time_period")

        params: dict = {"q": query}

        period_to_days: dict = {
            "day": "1",
            "week": "7",
            "month": "30",
        }

        if time_period in period_to_days:
            params["d"] = period_to_days[time_period]

        params[f"{token[0]}"] = token[1]
        soup = self.get_soup(url=self.base_url, params=params)
        return soup

    def token(self) -> t.Tuple[t.Optional[str], t.Optional[str]]:
        """
        Fetch the Ahmia homepage and capture the dynamic hidden
        anti-bot token used as additional GET parameters.

        :return: If successful, a tuple of TOKEN_NAME, TOKEN_VALUE, otherwise NONE, NONE
        """
        try:
            soup = self.get_soup(url="https://ahmia.fi/")
        except ConnectionError:
            return None, None
        except RequestException:
            return None, None

        hidden_input = soup.find("input", {"type": "hidden"})

        if hidden_input is None:
            return None, None

        token_name: t.Optional[str] = hidden_input.get("name")
        token_value: t.Optional[str] = hidden_input.get("value")

        # We only check if token_name and token_value are not None because the tokens come in pairs
        if token_name and token_value is not None:
            console.log(
                f"[bold][#c7ff70]✔[/] Token capture successful[/bold]"
            )  #  {token_name}, {token_value}")
        else:
            console.log(
                f"[bold][red]✘[/red] Token capture failed"
            )  # {token_name}, {token_value}")

        return token_name, token_value

    def get_soup(self, url: str, params: t.Optional[dict] = None) -> BeautifulSoup:
        response: Response = self.session.get(
            url=url, timeout=10, params=params, headers={"User-Agent": self.user_agent}
        )
        response.raise_for_status()
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")

        return soup
