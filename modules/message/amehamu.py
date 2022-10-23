# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


class call:
    """あめはむ[地点] : 降水状況を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keyword = 'あめはむ'
        zoom = '10'
        if text.startswith(keyword) and item.get('bot_id', None) is None:
            loc = text.replace(keyword, '').strip()
            if ' ' in loc:
                loc, zoom = loc.split(' ')
            if not loc:
                loc = '日本'
                zoom = '4'
            loc = loc.strip()
            zoom = zoom.strip()
            url = 'https://www.geocoding.jp/api/?q=' + quote(loc.encode('utf8'))
            r = requests.get(url, timeout=10, verify=False)
            if r and r.status_code == 200:
                print(r.text.strip())
                root = ET.fromstring(r.text)
                lat = None
                lng = None
                if root.find('./error') is None and root.find('./result/error') is None:
                    lat = root.find('./coordinate/lat').text
                    lng = root.find('./coordinate/lng').text

                if lat and lng:
                    r = requests.get('https://weather.yahoo.co.jp/weather/zoomradar/?lat={}&lon={}&z={}'.format(lat, lng, zoom))
                    if r and r.status_code == 200:
                        soup = BeautifulSoup(r.content, 'html.parser')
                        og_images = soup.find_all('meta', property="og:image")
                        if len(og_images) == 0:
                            return
                        img_url = og_images[0].get('content')
                        print(img_url)
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
                    else:
                        client.web_client.chat_postMessage(
                            username=keyword,
                            icon_emoji=caches.icon_emoji,
                            channel=channel,
                            text=loc + 'は見つからなかったよ',
                            thread_ts=thread_ts,
                        )
                else:
                    client.web_client.chat_postMessage(
                        username=keyword,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        text=loc + 'のスポット情報取得に失敗しました',
                        thread_ts=thread_ts,
                    )
