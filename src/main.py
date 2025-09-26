import typing as t
from types import SimpleNamespace

import requests
from bs4 import BeautifulSoup, ResultSet
from requests import Response
from requests_tor import RequestsTor


class Ahmia:

    def __init__(self, user_agent: str, use_tor: bool = False):
        """
        Initialise an Ahmia search client.

        :param user_agent: The User-Agent string that will be sent with all requests.
        :param use_tor: If True, requests will be routed through the Tor network using
                        the Ahmia .onion hidden service. If False, the clearnet version
                        of Ahmia (https://ahmia.fi) will be used instead.
        """

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

        self.session.headers.update({"User-Agent": self.user_agent})

    def search(
        self, query: str, limit: int = 20
    ) -> t.Generator[SimpleNamespace, None, None]:
        """
        Search Ahmia for hidden services matching the given query.

        :param query: The search term to look up on Ahmia.
        :param limit: Maximum number of results to yield. Defaults to 20.
        :return: A generator yielding SimpleNamespace objects, each representing a search result.
        """

        soup: BeautifulSoup = self._get_source(url=self._search_url % query)
        items: ResultSet = soup.find_all("li", {"class": "result"})

        for item in items[:limit]:
            last_seen_tag = item.find("span", {"class": "lastSeen"})
            last_seen_text = (
                last_seen_tag.get_text(strip=True) if last_seen_tag else "NaN"
            )
            last_seen_timestamp = (
                last_seen_tag.get("data-timestamp") if last_seen_tag else "NaN"
            )

            yield SimpleNamespace(
                **{
                    "title": " ".join(item.find("h4").text.split()),
                    "about": " ".join(item.find("p").text.split()),
                    "url": " ".join(item.find("cite").text.split()),
                    "last_seen_rel": last_seen_text.replace("\xa0", " "),
                    "last_seen_ts": last_seen_timestamp,
                }
            )

    def _get_source(self, url: str) -> BeautifulSoup:
        """
        Fetch the given URL using the configured session and parse the response.

        :param url: The full URL to request.
        :return: A BeautifulSoup object containing the parsed HTML content
                 of the response.
        """

        response: Response = self.session.get(url=url)
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        return soup
