# -*- coding: utf-8 -*-
from random import random

from redis import Redis

name = 'omikuji'
expire = 86400

results = {
    2: '大吉',
    3: '中吉',
    4: '小吉',
    5: '小吉',
    6: '吉',
    7: '吉',
    8: '吉',
    9: '末吉',
    10: '末吉',
    11: '凶',
    12: '大凶',
}


def chinchiro(user):
    key = name + f'.{user}'

    r = Redis(decode_responses=True)
    pre = r.get(key)
    if pre:
        return f'{user} さんはすでに引いています【{pre}】'
    else:
        d1 = int(random() * 6) + 1
        d2 = int(random() * 6) + 1
        result = results[d1 + d2]
        r.set(key, result)
        r.expire(key, expire)

        return f'{user} さんの結果は {result} です'


class call:
    """おみくじ : おみくじを引きます (1日2回まで)"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keyword = 'おみくじ'
        if text == keyword and item.get('bot_id') is None:
            user_id = item.get('user')
            username = caches.display_names.get(user_id)
            result = chinchiro(username)

            client.web_client.chat_postMessage(
                username=keyword,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=result,
                thread_ts=thread_ts,
            )
