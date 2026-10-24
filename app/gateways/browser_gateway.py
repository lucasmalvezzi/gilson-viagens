import random
from typing import List, Protocol, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth

USER_AGENTS: Tuple[str, ...] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
)

CHROMIUM_STEALTH_ARGS: List[str] = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--lang=pt-BR,pt",
]


class FlightBrowserGatewayProtocol(Protocol):
    """Interface enxuta do projeto para leitura de páginas renderizadas de voos."""

    async def fetch_rendered_flight_texts(self, url: str) -> Tuple[List[str], str]:
        """Retorna tupla (lista de textos ARIA listitem, HTML completo da página)."""
        ...


async def _navigate_with_fallback(page: Page, url: str) -> None:
    """5.4 Renderização: tenta aguardar networkidle com fallback para domcontentloaded."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)


async def _trigger_lazy_loading_and_pause(page: Page) -> None:
    """5.2 e 5.4 Scroll automático para Lazy Loading e pausa humanizada randômica."""
    try:
        await page.evaluate("window.scrollBy(0, 600)")
    except Exception:
        pass
    espera_ms = int(random.uniform(1.5, 3.5) * 1000)
    await page.wait_for_timeout(espera_ms)


async def _read_single_listitem_text(listitems_locator, index: int) -> str:
    """Lê texto visível e aria-label combinados de um item ARIA listitem."""
    item = listitems_locator.nth(index)
    try:
        visible_text = await item.inner_text(timeout=2000)
        aria_label = (await item.get_attribute("aria-label")) or ""
        return f"{visible_text} {aria_label}".strip()
    except Exception:
        return ""


async def _collect_aria_listitem_texts(page: Page, max_items: int = 15) -> List[str]:
    """5.3 Locators ARIA: coleta textos dos primeiros cards listitem renderizados."""
    try:
        listitems = page.get_by_role("listitem")
        total = min(await listitems.count(), max_items)
    except Exception:
        return []
    collected: List[str] = []
    for idx in range(total):
        combined_text = await _read_single_listitem_text(listitems, idx)
        if combined_text:
            collected.append(combined_text)
    return collected


async def _create_stealth_page(browser: Browser) -> Page:
    """Cria contexto com User-Agent rotativo e aplica máscaras Playwright Stealth."""
    context: BrowserContext = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        viewport={"width": 1366, "height": 768},
    )
    page: Page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    return page


class PlaywrightStealthGateway:
    """
    Adaptador concreto que encapsula Playwright e playwright-stealth.
    Exemplo: `texts, html = await PlaywrightStealthGateway().fetch_rendered_flight_texts(url)`
    """

    async def fetch_rendered_flight_texts(self, url: str) -> Tuple[List[str], str]:
        """
        Abre a URL em Chromium headless com Stealth e retorna (listitems, html).
        Exemplo: `items, raw_html = await gateway.fetch_rendered_flight_texts("https://...")`
        """
        if not url.startswith("http"):
            raise ValueError(f"Invalid url={url!r}; expected HTTP/HTTPS URL string.")
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=CHROMIUM_STEALTH_ARGS)
            try:
                return await self._extract_from_browser(browser, url)
            finally:
                await browser.close()

    async def _extract_from_browser(
        self, browser: Browser, url: str
    ) -> Tuple[List[str], str]:
        """Executa navegação, scroll e coleta de textos dentro de uma instância ativa."""
        page = await _create_stealth_page(browser)
        await _navigate_with_fallback(page, url)
        await _trigger_lazy_loading_and_pause(page)
        item_texts = await _collect_aria_listitem_texts(page)
        full_html = await page.content()
        return item_texts, full_html
