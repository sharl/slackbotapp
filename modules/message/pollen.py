# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class call:
    """[スギ|ヒノキ]花粉 : 花粉飛散予測マップを表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keywords = {
            '花粉': 'https://tenki.jp/pollen/mesh/',
            'スギ花粉': 'https://tenki.jp/pollen/mesh/',
            'ヒノキ花粉': 'https://tenki.jp/pollen/mesh/cypress.html',
        }
        bot_id = item.get('bot_id', None)
        for keyword in keywords:
            if keyword == text and bot_id is None:
                url = keywords[keyword]
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.4472.114 Safari/537.36'
                headers = {
                    'User-Agent': user_agent,
                }
                r = requests.get(url, headers=headers, timeout=10)
                if r and r.status_code == 200:
                    soup = BeautifulSoup(r.content, 'html.parser')
                    og_images = soup.find_all('img', usemap="#pollen_mesh_image_map")
                    if len(og_images) == 0:
                        return
                    img_url = og_images[0].get('src')
                    client.web_client.chat_postMessage(
                        username=keyword,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        text=text,
                        blocks=[
                            {
                                'type': 'image',
                                'image_url': img_url,
                                'alt_text': text,
                            }
                        ],
                        thread_ts=thread_ts,
                    )
