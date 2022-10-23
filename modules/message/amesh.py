# -*- coding: utf-8 -*-
import subprocess


class call:
    """アメッシュ : アメッシュ画像を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item["channel"]
        thread_ts = item.get('thread_ts')

        keyword = 'アメッシュ'
        if text == keyword and item.get('bot_id') is None:
            amesh = subprocess.check_output(['amesh', '-c'])
            with open('/tmp/amesh.png', 'wb') as fd:
                fd.write(amesh)
            client.web_client.files_upload_v2(
                username=keyword,
                icon_emoji=caches.icon_emoji,
                channels=channel,
                file='/tmp/amesh.png',
                title='amesh',
                thread_ts=thread_ts,
            )
