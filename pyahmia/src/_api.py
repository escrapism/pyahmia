import typing as t

import requests
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import RequestException
from requests_tor import RequestsTor
from rich.status import Status

from ._cache import CacheManager
from ._lib import console

TIME_PERIODS = t.Literal["day", "week", "month", "all"]

__all__ = ["Ahmia"]


class Ahmia:
    def __init__(
        self, user_agent: str, use_tor: bool = False, enable_cache: bool = True
    ):
        self.user_agent = user_agent
        self.use_tor = use_tor
        self.enable_cache = enable_cache
        self.cache = CacheManager() if enable_cache else None

        if self.use_tor:
            self.base_url: str = (
                "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?"
            )
            self.session = RequestsTor(tor_ports=(9050,), tor_cport=(9051,))
        else:
            self.base_url: str = "https://ahmia.fi/search/?"
            self.session = requests.Session()

    def search(
        self,
        query: str,
        time_period: TIME_PERIODS = "all",
        status: t.Optional[Status] = None,
    ) -> dict:
        """
        Search Ahmia.fi for hidden services on the Tor network, that match with the `query`.

        :param query: Search query.
        :param time_period: Time period to get results from
          (expects either: `day`, `week`, `month`, and/or `all`)
        :param status:
        :return: A SimpleNamespace containing the search summary, total results count,
        and a list of SimpleNamespace objects, each containing info on an individual search result.
        """
        # Check cache first
        if self.enable_cache and self.cache:
            cache_key = self.cache.get_search_cache_key(
                query, time_period, self.use_tor
            )
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                if isinstance(status, Status):
                    status.update(
                        f"[bold]Retrieved [#c7ff70]{query}[/] from cache[/bold]"
                    )
                console.log("[bold][#c7ff70]✔[/] Results loaded from cache[/bold]")
                return cached_result

        token = self._get_token(status=status)

        if isinstance(status, Status):
            status.update(
                f"[bold]Searching for [#c7ff70]{query}[/]. Please wait[yellow]…[/bold][/yellow]"
            )

        results_soup = self._get_results_soup(
            query=query, time_period=time_period, token=token
        )

        items = results_soup.find_all("li", {"class": "result"})
        total_count = len(items)

        if not items:
            return {
                "success": False,
                "message": f"Sorry, but PyAhmia couldn't find results for {query}.",
            }

        message_tag = results_soup.find("div", {"class": "resultsSubheader"})
        message = " ".join(message_tag.text.split())

        results = []

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

        result = {
            "success": True,
            "message": message,
            "total_count": total_count,
            "results": results,
        }

        # Cache the successful result
        if self.enable_cache and self.cache:
            cache_key = self.cache.get_search_cache_key(
                query, time_period, self.use_tor
            )
            self.cache.set(cache_key, result)

        return result

    def _get_token(self, status: t.Optional[Status] = None) -> tuple:
        """
        Get the Ahmia homepage and capture the dynamic hidden
        anti-bot token used as additional GET parameters.

        :return: If successful, a tuple of TOKEN_NAME, TOKEN_VALUE, otherwise NONE, NONE
        """
        # Check cache for token first
        if self.enable_cache and self.cache:
            cache_key = self.cache.get_token_cache_key(self.use_tor)
            cached_token = self.cache.get(cache_key)
            if cached_token is not None:
                console.log("[bold][#c7ff70]✔[/] Token loaded from cache[/bold]")
                return tuple(cached_token)

        if isinstance(status, Status):
            status.update(
                f"[bold]Capturing session token. Please wait[yellow]…[/bold][/yellow]"
            )
        try:
            soup = self._get_page_soup(url="https://ahmia.fi/")
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
            console.log(f"[bold][#c7ff70]✔[/] Token capture successful[/bold]")
            # Cache the token with a shorter TTL (10 minutes)
            if self.enable_cache and self.cache:
                cache_key = self.cache.get_token_cache_key(self.use_tor)
                self.cache.set(cache_key, [token_name, token_value], ttl=600)
        else:
            console.log(f"[bold][red]✘[/red] Token capture failed[/bold]")

        return token_name, token_value

    def _get_page_soup(
        self, url: str, params: t.Optional[dict] = None
    ) -> BeautifulSoup:
        response: Response = self.session.get(
            url=url, timeout=10, params=params, headers={"User-Agent": self.user_agent}
        )
        response.raise_for_status()
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")

        return soup

    def _get_results_soup(self, **kwargs) -> BeautifulSoup:
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
        soup = self._get_page_soup(url=self.base_url, params=params)
        return soup
