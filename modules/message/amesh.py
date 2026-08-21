# -*- coding: utf-8 -*-
import subprocess
import time

from redis import Redis

from modules import postMessage, uploadFile


KEY_PREFIX = 'amesh'
EXPIRES = 60 * 5


class call:
    """アメッシュ : アメッシュ画像を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item["channel"]
        thread_ts = item.get('thread_ts')

        keyword = 'アメッシュ'
        if text == keyword and item.get('bot_id') is None:
            r = Redis(decode_responses=True)
            key = f'{KEY_PREFIX}.{caches.channel_ids.get(channel, 'dummy')}'
            pre = r.get(key)
            # すでに出力していたら無視
            if pre:
                before = int(time.time() - float(pre))
                message = ''
                if before < 60:
                    message = f'{before}秒くらい前に'
                else:
                    message = f'{int(before / 60)}分くらい前に'

                postMessage(
                    client,
                    keyword,
                    caches.icon_emoji,
                    channel,
                    message,
                    thread_ts=thread_ts,
                )

                return
            else:
                r.set(key, time.time())         # store: str
                r.expire(key, EXPIRES)

            amesh = subprocess.check_output(['amesh', '-c'])
            with open('/tmp/amesh.png', 'wb') as fd:
                fd.write(amesh)
            uploadFile(
                client,
                keyword,
                caches.icon_emoji,
                channel,
                'amesh',
                '/tmp/amesh.png',
                thread_ts=thread_ts,
            )
