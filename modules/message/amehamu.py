# -*- coding: utf-8 -*-
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


class call:
    """あめはむ[地点] : 降水状況を表示
ゆきはむ[地点] : 降水/降雪状況を表示
サンダー[地点] : 落雷状況を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keywords = {
            'あめはむ': '',
            'ゆきはむ': 'rainsnow',
            'サンダー': 'lightning',
        }
        zoom = '10'
        param = None
        for keyword in keywords:
            if text.startswith(keyword):
                param = keywords[keyword]
                break

        if param is not None and item.get('bot_id', None) is None:
            loc = text.replace(keyword, '').strip()
            if ' ' in loc:
                loc, zoom = loc.split()
            if not loc:
                loc = '岐阜県関市'
                zoom = '4'
            loc = loc.strip()
            zoom = zoom.strip()
            title = lat = lng = None
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            headers = {
                'User-Agent': user_agent
            }
            timeout = 1
            try:
                if not (lat and lng):
                    url = 'https://geoapi.heartrails.com/api/json?method=suggest&matching=like&keyword=' + quote(loc.encode('utf8'))
                    with requests.get(url, headers=headers, timeout=timeout) as r:
                        j = r.json()['response'].get('location', [])
                        if isinstance(j, list) and len(j) > 0:
                            for p in j:
                                title = p.get('prefecture') + p.get('city')
                                lat = p.get('y')
                                lng = p.get('x')
                                if lat and lng:
                                    print(loc, title, lat, lng)
                                    break

                if not (lat and lng):
                    url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + quote(loc.encode('utf8'))
                    with requests.get(url, headers=headers, timeout=timeout) as r:
                        j = r.json()
                        if isinstance(j, list) and len(j) > 0:
                            for p in j[0], j[-1]:
                                lng, lat = p['geometry']['coordinates']
                                title = p['properties']['title']
                                print(loc, title, lat, lng)
            except Exception:
                pass

            print(loc, title, lat, lng, zoom)

            if lat and lng:
                with requests.get(f'https://weather.yahoo.co.jp/weather/zoomradar/{param}?lat={lat}&lon={lng}&z={zoom}') as r:
                    soup = BeautifulSoup(r.content, 'html.parser')
                    og_image = soup.find('meta', property='og:image')
                    if og_image is None:
                        return
                    img_url = og_image.get('content')
                    client.web_client.chat_postMessage(
                        username=keyword,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        text=text,
                        blocks=[
                            {
                                'type': 'image',
                                'title': {
                                    'type': 'plain_text',
                                    'text': title,
                                },
                                'image_url': img_url,
                                'alt_text': title,
                            }
                        ],
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
