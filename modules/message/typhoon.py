# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class call:
    """台風 : 台風情報を表示
台風広域 : 広域の台風情報を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keyword = '台風'
        url = 'https://typhoon.yahoo.co.jp/weather/jp/typhoon/'
        typhoons = {
            keyword + '広域': url,
            keyword: url + '?c=1',
        }
        if text.startswith(keyword) and item.get('bot_id', None) is None:
            r = requests.get(url, timeout=10)
            if r and r.status_code == 200:
                soup = BeautifulSoup(r.content, 'html.parser')
                lis = soup.find_all('li', class_='tabView_item')
                for li in lis[2:]:
                    typhoons[keyword + li.a.text] = li.a['href']

                if text in typhoons:
                    url = typhoons[text]
                    r = requests.get(url, timeout=10)
                    if r and r.status_code == 200:
                        soup = BeautifulSoup(r.content, 'html.parser')
                        div = soup.find('div', class_='tabView_content_image')
                        client.web_client.chat_postMessage(
                            username=f"{text} {(' '.join(list(typhoons.keys())[2:])).replace('台風', '')}",
                            icon_emoji=caches.icon_emoji,
                            channel=channel,
                            text=text,
                            blocks=[
                                {
                                    'type': 'image',
                                    'image_url': div.img['src'],
                                    'alt_text': text,
                                }
                            ],
                            thread_ts=thread_ts,
                        )
