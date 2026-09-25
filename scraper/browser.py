"""Playwright session for one Threads account: proxy + cookies (Cookie
Editor JSON) applied, ready to navigate. Actual post/reply extraction
(fetch_new_posts) is a stub - it needs real DOM structure or a HAR from
Threads before it can be implemented without guessing selectors.
"""
from __future__ import annotations

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from scraper.config import AccountConfig, load_cookies
from scraper.constants import BROWSER_NAV_TIMEOUT_MS, LOGGER
from scraper.pipeline import RawThreadsPost

THREADS_BASE_URL = "https://www.threads.net"


class ThreadsBrowserSession:
    """One Playwright browser + context per account, with proxy and
    cookies applied. Mandatory proxy per Exorde requirements.
    """

    def __init__(self, account: AccountConfig) -> None:
        self._account = account
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        if not self._account.proxy.server:
            raise ValueError(
                f"[{self._account.name}] proxy.server is required - refusing to "
                "start a browser session without a proxy"
            )

        self._playwright = await async_playwright().start()

        proxy_config = {"server": self._account.proxy.server}
        if self._account.proxy.username:
            proxy_config["username"] = self._account.proxy.username
        if self._account.proxy.password:
            proxy_config["password"] = self._account.proxy.password

        self._browser = await self._playwright.chromium.launch(
            headless=True,
            proxy=proxy_config,
        )
        self._context = await self._browser.new_context(
            user_agent=self._account.user_agent or None,
        )
        self._context.set_default_navigation_timeout(BROWSER_NAV_TIMEOUT_MS)

        cookies = load_cookies(self._account.cookie_file)
        await self._context.add_cookies(cookies)

        self._page = await self._context.new_page()
        LOGGER.info("[%s] browser session started", self._account.name)

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        LOGGER.info("[%s] browser session closed", self._account.name)

    async def fetch_new_posts(self, targets: list[dict[str, str]]) -> list[RawThreadsPost]:
        """Scrape new posts/replies for the given targets.

        STUB (v1): not implemented yet. Threads has no documented public
        read API/GraphQL endpoint confirmed here, so v1 goes through DOM
        scraping of the logged-in web UI. Implementing this without
        guessing selectors requires either:
          1. real DOM structure of a target profile/thread page (post
             container, permalink, timestamp <time> element, author
             handle, reply/parent linkage), or
          2. a HAR capture of Threads' internal API calls, if we decide
             to switch from DOM scraping to HTTP/GraphQL for v1.

        Returns a list of RawThreadsPost built ONLY from data actually
        present on the page - never fabricated ids/timestamps/content.
        """
        raise NotImplementedError(
            "fetch_new_posts is a stub - provide target page DOM structure "
            "or a HAR capture to implement real extraction (see README.md)."
        )
