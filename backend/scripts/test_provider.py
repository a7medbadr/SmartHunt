import asyncio

from smarthunt.browser.providers.example_provider import ExampleProvider


async def main():
    provider = ExampleProvider()

    jobs = await provider.search(
        keyword="python",
        location="Riyadh",
    )

    for job in jobs:
        print(job)


asyncio.run(main())
