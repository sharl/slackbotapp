# -*- coding: utf-8 -*-
import json
import os
import subprocess

import requests
from bs4 import BeautifulSoup as bs

from modules import postMessage


class call:
    """天気<観測地点> [tenki.jpの2週間天気URL] : 天気予報を表示 [登録]"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        prefix = '天気'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '').strip()
            tenkijp = ''
            if ' ' in loc:
                loc, url = loc.split()
                url = url.strip('<>')
                print(loc, url)
                tenkijp = subprocess.check_output(['tenkijp', loc, url]).decode('utf8').strip()
            else:
                tenkijp = subprocess.check_output(['tenkijp', loc]).decode('utf8').strip()

            if not tenkijp:
                return

            f = os.path.join(os.environ['HOME'], '.tenkijp')
            if os.path.exists(f):
                j = {}
                with open(f) as fd:
                    j = json.load(fd)
                if loc in j:
                    u = j[loc].removesuffix('10days.html')

                    ld_data = None
                    with requests.get(u, timeout=10) as r:
                        soup = bs(r.content.decode('utf-8'), 'html.parser')
                        for s in soup.find_all('script', type='application/ld+json'):
                            if s.string:
                                try:
                                    data = json.loads(s.string)
                                    if data.get('@id') == u + '#indexes':
                                        ld_data = data
                                        break
                                except json.JSONDecodeError:
                                    pass

                    lines = []
                    f = ''
                    if ld_data:
                        cols = ld_data.get('mainEntity', {}).get('csvw:tableSchema', {}).get('csvw:columns', [])
                        for col in cols:
                            line = f"{col['csvw:name']} {col['csvw:cells'][0]['csvw:value']}"
                            lines.append(line.replace('今日の', '').replace('指数', ''))
                        f = ' '.join(lines)
                    tail = tenkijp.splitlines()
                    head = [tail[0]]
                    if f:
                        head.append(f)
                    tenkijp = '\n'.join(head + tail[1:])

            postMessage(
                client,
                f'{loc}の{prefix}',
                caches.icon_emoji,
                channel,
                tenkijp,
                thread_ts=thread_ts,
            )
