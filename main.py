import asyncio
import logging
import os
import re
from collections import namedtuple
from pathlib import Path

import aiohttp as aiohttp
import requests
from bs4 import BeautifulSoup
from slugify import slugify

URL = 'https://news.ycombinator.com/'
STORY_LINK_PATTERN = re.compile(
    r"<a class=\"storylink\" href=\"(.+?)\">(.+?)</a>"
)

NewsStory = namedtuple('NewsStory', ['link', 'title'])


def parse_baseurl(url):
    """ Fetch HTML page content from the URL provided and parses all news from it.
    :param url: base website url
    :return parsed_news: List[NewsStory]
    """

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    all_news = soup.find_all("a", {"class": "storylink"})

    parsed_news = []
    for news in all_news:
        search = STORY_LINK_PATTERN.search(str(news))
        link, title = search.groups()
        parsed_news.append(NewsStory(link=link, title=title))

    #print(parsed_news)
    logging.info(f"Found {len(parsed_news)} news.")
    return parsed_news


async def download(news, directory):
    """ Download HTML page content from the URL provided and write it to output file in directory provided.
    :param news: NewsStory named tuple
    :param directory: path to output directory
    """
    news_slug = slugify(news.title)
    news_dir = Path(os.path.join(directory, news_slug))

    if news_dir.is_dir():
        logging.info(f"Article '{news.title}' already downloaded.")
        return

    os.mkdir(news_dir)
    file_name = os.path.join(news_dir, news.title)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(news.link) as response:
                logging.info(
                    f"Status: {response.status}."
                )
               # print("Content-type:", response.headers['content-type'])

                html = await response.text()
                with open(file_name, 'wb') as f:
                    f.write(html.encode("utf-8"))
                logging.info(
                    f"Article '{news.title}' has been successfully downloaded."
                )
        except Exception as exc:
            logging.exception(
                f"URL: {news.link} unexpected error."
                f"{type(exc)} was raised."
            )


async def main(news, directory):
    """ Create tasks queue to run downloads in async mode.
    :param news: List[NewsStory]
    :param directory: path to output directory
    """
    tasks = []

    for item in news:
        tasks.append(
            asyncio.create_task(
                download(item, directory)
            )
        )
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname).1s %(message)s')
    news = parse_baseurl(URL)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(news, 'news'))
