# -*- coding: utf-8 -*-
from modules import postMessage


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        if text.strip().replace(' ', '') in ['はむ?', 'はむ？']:
            postMessage(
                client,
                caches.username,
                caches.icon_emoji,
                channel,
                caches.doc,
                thread_ts=thread_ts,
            )
