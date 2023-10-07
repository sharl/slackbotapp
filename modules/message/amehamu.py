# -*- coding: utf-8 -*-
import re
import json
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
                loc = '長野県麻績村日'
                zoom = '3.5'
            loc = loc.strip()
            zoom = zoom.strip()
            url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + quote(loc.encode('utf8'))
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            headers = {
                'User-Agent': user_agent
            }
            r = requests.get(url, headers=headers, timeout=10)
            if r and r.status_code == 200:
                j = json.loads(r.text)
                lat = None
                lng = None
                pat = re.compile(r'^.*[都道府県]')
                if isinstance(j, list) and len(j) > 0:
                    for p in j:
                        title = p['properties']['title']
                        lat = p['geometry']['coordinates'][1]
                        lng = p['geometry']['coordinates'][0]
                        m = pat.search(title)
                        if m:
                            print(loc, title)
                            break

                if lat and lng:
                    r = requests.get('https://weather.yahoo.co.jp/weather/zoomradar/?lat={}&lon={}&z={}'.format(lat, lng, zoom))
                    if r and r.status_code == 200:
                        soup = BeautifulSoup(r.content, 'html.parser')
                        og_images = soup.find_all('meta', property="og:image")
                        if len(og_images) == 0:
                            return
                        img_url = og_images[0].get('content').replace('600x600', '600x400')
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
