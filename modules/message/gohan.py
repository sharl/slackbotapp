# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class call:
    """ごはん : ランダムでごはんを表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keywords = {
            'ごはん': 'ALL',
            'エスニック': '2',
            '洋食': '3',
            '和食': '4',
            'おやつ': '5',
        }
        f = 0
        for keyword in keywords:
            if text == keyword and item.get('bot_id') is None:
                f = 1
                break
        if f == 0:
            return

        r = requests.post('https://www.kondatekun.com/recipe/roulette.php', data={'Genre': keywords[keyword]}, timeout=10)
        if r and r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            result = soup.find('h5', class_='recipename').text

            user_id = item.get('user')
            username = caches.display_names.get(user_id)

            gohan = f'{username} さんの{keyword}は {result} です'

            client.web_client.chat_postMessage(
                username=keyword,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=gohan,
                thread_ts=thread_ts,
            )
