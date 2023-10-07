# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class call:
    """実話 : 実話(うそ)を表示"""
    def __init__(self, client, req, options=None, caches={}):
        keyword = '実話'

        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        if text == keyword and item.get('bot_id', None) is None:
            url = 'http://eg.sen-nin-do.net/'

            while True:
                r = requests.get(url, timeout=10)
                if r and r.status_code == 200:
                    soup = BeautifulSoup(r.content, 'html.parser')
                    evs = soup.find_all('div', class_='main')
                    events = []
                    for ev in evs:
                        if ev.text:
                            events.append(ev.text)
                    if events:
                        status = events[0].strip()
                    if '田辺' not in status:
                        break
                else:
                    status = 'だめぽ'
                    break

            client.web_client.chat_postMessage(
                username=keyword,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=status,
                thread_ts=thread_ts,
            )
