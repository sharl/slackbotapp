# -*- coding: utf-8 -*-
class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        if text.strip().replace(' ', '') in ['help&gt;はむ', 'help＞はむ', 'ヘルプ&gt;はむ', 'ヘルプ＞はむ']:
            client.web_client.chat_postMessage(
                username=caches.username,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=caches.doc,
                thread_ts=thread_ts,
            )
