# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from modules import postMessage


class call:
    """地震[地域]"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        prefix = '地震'
        url = 'https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.removeprefix(prefix).strip()

            trs = []
            with requests.get(url, timeout=10) as r:
                soup = BeautifulSoup(r.content, 'html.parser')
                trs = soup.find_all('tr', bgcolor='#ffffff', valign='middle')

            limit = 5
            lines = []
            # [
            #     <td><a href="/weather/jp/earthquake/20260805180614.html">2026年8月5日 18時06分ごろ</a></td>,
            #     <td align="center">東京都２３区</td>,
            #     <td align="center">3.5</td>,
            #     <td align="center">1</td>
            # ]
            if not loc:
                for tr in trs[:limit]:
                    tds = tr.find_all('td')
                    _dt, _anm, _mag, _int = tds
                    link = 'https://typhoon.yahoo.co.jp' + _dt.a.get('href')
                    lines.append(f'{_dt.text} <{link}|{_anm.text}> M{_mag.text} 震度{_int.text}')
            else:
                for tr in trs:
                    tds = tr.find_all('td')
                    _dt, _anm, _mag, _int = tds
                    link = 'https://typhoon.yahoo.co.jp' + _dt.a.get('href')
                    if _anm.text.startswith(loc):
                        lines.append(f'{_dt.text} <{link}|{_anm.text}> M{_mag.text} 震度{_int.text}')
                        break

            if lines:
                quakes = '\n'.join(lines)
            else:
                quakes = '見つかりませんでした'
            postMessage(
                client,
                prefix,
                caches.icon_emoji,
                channel,
                quakes,
                thread_ts=thread_ts,
                unfurl_links=False,
            )
