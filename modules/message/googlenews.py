# -*- coding: utf-8 -*-
from urllib.parse import quote

from bs4 import BeautifulSoup
import feedparser
import requests

from modules import postMessage

BASE_URL = 'https://news.google.com'
DEF_KEY = 'journal:'
DEF_ICON = 'dog'
DEF_NOTFOUND = 'not found'
NEWS_LIMIT = 5


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
            q = quote(query.encode('utf-8'))
            search_url = f'{BASE_URL}/search?q={q}&hl=ja&gl=JP&ceid=JP%3Aja'
            with requests.get(search_url, timeout=10) as r:
                soup = BeautifulSoup(r.content, 'html.parser')
                atom = soup.find('link', type='application/atom+xml')
                _link = atom.get('href')
                full = feedparser.parse(f'{BASE_URL}{_link}')
                entries = full.entries

                lines = []
                for entry in sorted(entries, key=lambda x: x.updated, reverse=True):
                    title = entry.title
                    link = entry.link
                    lines.append(f':{emoji}: <{link}|{title}>')
                    if len(lines) >= NEWS_LIMIT:
                        break

                if not lines:
                    lines = [notfound]

                postMessage(
                    client,
                    f'『{query}』のニュース',
                    emoji,
                    channel,
                    '\n'.join(lines),
                    thread_ts=thread_ts,
                    unfurl_links=False,
                )
