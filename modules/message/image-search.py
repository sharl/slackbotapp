# -*- coding: utf-8 -*-
import random

from ddgs import DDGS
from ddgs.exceptions import DDGSException

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
            word = text.removesuffix(suffix).strip()
            images = []
            try:
                images = DDGS().images(
                    query=word,
                    region='jp-jp',
                    safesearch='off',
                    page=1,
                    backend='auto',
                )
            except DDGSException:
                pass

            if images:
                random.shuffle(images)
                link = images[0].get('image')
                blocks = [
                    {
                        'type': 'image',
                        'image_url': link,
                        'alt_text': word,
                    },
                ]
                message = word
            else:
                blocks = []
                message = '今回は見つからなかったのだ'

            postMessage(
                client,
                word,
                caches.icon_emoji,
                channel,
                message,
                blocks=blocks,
                thread_ts=thread_ts,
            )
