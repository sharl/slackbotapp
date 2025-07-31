# -*- coding: utf-8 -*-
import re

import requests

DAM_URL = 'https://weathernews.jp/dam/json/dam.json'
DAM_RE = re.compile(r'ダム（?.*')
maps = {}


class call:
    """貯水率<ダム名> : ダムの貯水率を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        prefix = '貯水率'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '').strip()

            # ダム名をキャッシュ
            if not maps:
                with requests.get(DAM_URL) as r:
                    for dam in r.json()['features']:
                        _name = dam['properties']['name']
                        # 正規化
                        name = re.sub(DAM_RE, '', _name)
                        if name not in maps:
                            maps[name] = _name
                        name2 = name.replace('ヶ', 'ケ')
                        if name2 not in maps:
                            maps[name2] = _name

            if loc in maps:
                lines = []
                name = maps[loc]
                with requests.get(DAM_URL) as r:
                    for dam in r.json()['features']:
                        _dam = dam['properties']
                        if name == _dam['name']:
                            _perc = float(_dam['貯水率 (利水容量)'])
                            _total = int(_dam['利水容量'])
                            if _total != 0:
                                line = f'{loc} {name} {_perc}%'
                            else:
                                line = f'{loc} {name} 0%'
                            lines.append(line)

                if lines:
                    client.web_client.chat_postMessage(
                        username=prefix,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        text='\n'.join(lines),
                        thread_ts=thread_ts,
                    )
