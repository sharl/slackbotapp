# -*- coding: utf-8 -*-
import random

from ddgs import DDGS

from modules import postMessage


class call:
    """<検索文字列>画像 : 画像を検索します"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        suffix = '画像'
        if text.endswith(suffix) and item.get('bot_id') is None:
            word = text.replace(suffix, '').strip()
            images = DDGS().images(
                query=word,
                region='jp-jp',
                safesearch='off',
                page=1,
                backend='auto',
            )
            if images:
                random.shuffle(images)
                link = images[0].get('image')
                postMessage(
                    client,
                    word,
                    caches.icon_emoji,
                    channel,
                    text,
                    blocks=[
                        {
                            'type': 'image',
                            'image_url': link,
                            'alt_text': word,
                        },
                    ],
                    thread_ts=thread_ts,
                )
