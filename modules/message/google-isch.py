# -*- coding: utf-8 -*-
import random

import requests
from bs4 import BeautifulSoup as bs


class call:
    """<検索文字列>画像 : Google で画像を検索"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        suffix = '画像'
        if text.endswith(suffix) and item.get('bot_id') is None:
            word = text.replace(suffix, '').strip()

            # tbm=isch, tbm=vid
            with requests.get(f'https://www.google.com/search?q={word}&tbm=isch&biw=1920&bih=1080&sa=X&dpr=1') as r:
                soup = bs(r.content, 'html.parser')
                imgs = soup.find_all('img')
                links = []
                for img in imgs:
                    if not img.get('alt'):
                        links.append(img.get('src'))
                if links:
                    random.shuffle(links)
                    link = links[0]

                    client.web_client.chat_postMessage(
                        username=word,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        text=text,
                        blocks=[
                            {
                                'type': 'image',
                                'image_url': link,
                                'alt_text': word,
                            },
                        ],
                        thread_ts=thread_ts,
                    )
