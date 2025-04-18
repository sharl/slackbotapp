# -*- coding: utf-8 -*-
import re
import json
from urllib.parse import quote
# from datetime import datetime

import requests
from bs4 import BeautifulSoup

DEF_KEY = 'journal:'
DEF_ICON = 'dog'
DEF_NOTFOUND = 'not found'
NEWS_LIMIT = 5
DATE_LIMIT = 3


class BreakException(Exception):
    pass


class call:
    """いぬ、<ニュース> : 関連するニュースの候補を表示します"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keyword = DEF_KEY
        emoji = DEF_ICON
        notfound = DEF_NOTFOUND
        if isinstance(options, dict):
            keyword = options.get('keyword', DEF_KEY)
            emoji = options.get('emoji', DEF_ICON)
            notfound = options.get('notfound', DEF_NOTFOUND)

        if text.startswith(keyword) and item.get('bot_id', None) is None:
            query = text.replace(keyword, '')
            q = quote(query.encode('utf8'))
            search_url = f'https://news.google.com/search?q={q}&hl=ja&gl=JP&ceid=JP%3Aja'
            with requests.get(search_url) as r:
                soup = BeautifulSoup(r.content, 'html.parser')
                p = soup.find('script', class_='ds:2')
                if p:
                    # {key: 'ds:2', hash: '3', data:["gsrre
                    # , sideChannel: {}}
                    j = p.text.replace('AF_initDataCallback(', '').replace(');', '')
                    m = re.search('^{.*?data:(.*),.*$', j)
                    data = json.loads(m.group(1))

                    # make body list
                    lines = []
                    # now = int(datetime.timestamp(datetime.now()))
                    if data[1]:
                        try:
                            for n in data[1][0]:
                                if isinstance(n, list):
                                    for m in n:
                                        if isinstance(m, list):
                                            if isinstance(m[2], str):
                                                # timestamp = m[4][0]
                                                # if now - timestamp > DATE_LIMIT * 86400:
                                                #     continue
                                                title = m[2]
                                                url = m[6]
                                                line = f':{emoji}: <{url}|{title}>'
                                                lines.append(line)
                                                if len(lines) >= NEWS_LIMIT:
                                                    raise BreakException
                        except BreakException:
                            pass

                    if not lines:
                        lines = [notfound]

                    client.web_client.chat_postMessage(
                        username=f'『{query}』のニュース',
                        icon_emoji=emoji,
                        channel=channel,
                        unfurl_links=False,
                        text='\n'.join(lines),
                        thread_ts=thread_ts,
                    )
