# -*- coding: utf-8 -*-
from redis import Redis
import requests
from bs4 import BeautifulSoup

name = 'tarot'
expire = 43200


def tarots(user):
    key = name + f'.{user}'

    r = Redis(decode_responses=True)
    pre = r.get(key)
    if pre:
        return f'{user} さんはすでに引いています【{pre}】'
    else:
        res = requests.get('https://honkaku-uranai.jp/daily/tarot/one/result/', timeout=10)
        if res and res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            result1 = soup.find('p', class_='name_card').text
            result2 = soup.find('p', class_='c_keyword2').text
            result = f'{result1} {result2}'
            r.set(key, result)
            r.expire(key, expire)

            return f'{user} さんの結果は {result} です'


class call:
    """タロット : タロットを引きます (1日2回まで)"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keyword = 'タロット'
        if text == keyword and item.get('bot_id') is None:
            user_id = item.get('user')
            username = caches.display_names.get(user_id)
            result = tarots(username)

            client.web_client.chat_postMessage(
                username=keyword,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=result,
                thread_ts=thread_ts,
            )
