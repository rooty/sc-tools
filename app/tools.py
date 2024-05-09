import time
import logging
from typing import Annotated

# import json

import requests
import aiohttp
# import asyncio

from fastapi import (FastAPI, Path)
from fastapi.responses import HTMLResponse

import sentry_sdk

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(funcName)s(), line %(lineno)d)  %(message)s"
)


sentry_sdk.init(
    dsn="",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)
app = FastAPI(
    title="utils for dls scripts", openapi_url="/api/v1/openapi.json"
)


@app.on_event("startup")
async def app_start():
    pass


@app.on_event("shutdown")
async def app_stop():
    pass


@app.get("/")
async def home_page():
    return {"message": "HOME page"}


@app.get("/xplatform/prx/{prx}/offset/{offset}/dom/{dom}")
async def xplatform(
        prx: Annotated[int, Path(description="Proxy port(cISO)", title="Proxy port(cISO)")],
        offset: Annotated[int, Path(description="Offset", title="Offset")],
        dom: Annotated[str, Path(description="DOM hostname", title="DOM hostname")],
):
    tic = time.perf_counter()

    url = f"https://{dom}/thirdparty/games/slots?limit=300&offset={offset}"

    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'
    }
    proxies = {
        'http': f"http://proxy:{prx}",
        'https': f"http://proxy:{prx}",
    }
    games = list()
    retgames = {
        'URL_prx': url,
        'games': games
    }
    cnt = 1
    while cnt > 0:
        url = f"https://{dom}/thirdparty/games/slots?limit=3000&offset={offset}"
        r = requests.get(url, headers=headers, proxies=proxies)
        ret_json = r.json()
        if 'success' in ret_json:
            items = ret_json["games"]
            cnt = len(items)
            games += items
            offset += 300
            logging.debug(f"games {len(items)}")
        else:
            break

    toc = time.perf_counter()
    logging.debug(f"Runtime = {toc - tic:0.4f} seconds")

    return retgames


@app.get("/videoslots/prx/{prx}/qnt/{qnt}", response_class=HTMLResponse)
async def videoslots(
        prx: Annotated[int, Path(description="Proxy port(cISO)", title="Proxy port(cISO)")],
        qnt: Annotated[int, Path(description="Page count(count)", title="Page count(count)")]
):
    page = 1
    pages = list()
    html = ""
    tic = time.perf_counter()
    while page <= qnt:
        url = (f"https://www.videoslots.com/phive/modules/BoxHandler/html/ajaxActions.php?func=printGameList&boxid=744"
               f"&action=GetBoxHtml&page={page}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'
        }
        timeout = aiohttp.ClientTimeout(total=900)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, proxy=f"http://proxy:{prx}") as resp:
                result = await resp.text()
                if resp.status != 200:
                    break
                pages.append(result.strip())
        logging.debug(f"Page:{page}")
        page += 1

    toc = time.perf_counter()
    logging.debug(f"Runtime for {page-1} pages = {toc - tic:0.4f} seconds")
    html = html.join(map(str, pages))

    return f"""
        <html>
            <head>
                <title>Some HTML in here</title>
            </head>
            <body>
                <h1>Look ma! HTML!</h1>
                {html}
            </body>
        </html>
        """


@app.get("/lionspin/prx/{prx}")
async def lionspin(prx: Annotated[int, Path(description="Proxy port(cISO)", title="Proxy port(cISO)")]):
    print(f"Proxy port:{prx}")
    cur_page: int = 1
    total_pages: int = 1

    url: str = "https://www.lionspin.com/api/games_filter"

    headers: dict[str, str] = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'
    }
    proxies = {
        'http': f"http://proxy:{prx}",
        'https': f"http://proxy:{prx}",
    }
    all_pages = list()
    while cur_page <= total_pages:
        pdata = {
            "device": "desktop",
            "page": cur_page,
            "pageSize": 100,
            "filter": {
                "categories": {"identifiers": ["all"], "strategy": "OR"},
                "providers": []
            },
            "sort": {"type": "global", "direction": "ASC"},
            "page_size": 100
        }
        r = requests.post(url, json=pdata, headers=headers, proxies=proxies)
        ret_json = r.json()
        all_pages += ret_json["data"]
        if cur_page == 1:
            total_pages = ret_json['pagination']['total_pages']
            logging.debug(f" Port: {prx}, total_pages:{total_pages}")
        cur_page += 1

    return all_pages
    