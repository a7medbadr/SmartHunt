import asyncio

from smarthunt.browser.core import BrowserManager


async def main():
    browser = await BrowserManager().start()

    page = await browser.new_page()

    await page.goto(
        "https://example.com",
        wait_until="networkidle",
    )

    print(await page.title())

    await browser.stop()


asyncio.run(main())
