# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
# from tenacity import retry, wait_fixed, stop_after_attempt

from modules import postMessage


class call:
    """天気図 : 天気図を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        url = 'https://weather.yahoo.co.jp/weather/chart/'
        if text.strip() == '天気図' and item.get('bot_id', None) is None:
            with requests.get(url, timeout=10) as r:
                soup = BeautifulSoup(r.content, 'html.parser')
                div = soup.find(id='chart-0')
                postMessage(
                    client,
                    text,
                    caches.icon_emoji,
                    channel,
                    text,
                    blocks=[
                        {
                            'type': 'image',
                            'image_url': div.img['src'],
                            'alt_text': text,
                        }
                    ],
                    thread_ts=thread_ts,
                )
