# -*- coding: utf-8 -*-
from urllib.parse import quote
import json
import os
import re

import requests
from bs4 import BeautifulSoup

from modules import postMessage

mapfile = f'{os.environ["HOME"]}/.amehamu'


def load_config():
    data = {}
    try:
        with open(mapfile) as fd:
            data = json.loads(fd.read())
    except Exception:
        pass
    return data


def update_config(loc, lat, lng):
    data = load_config()
    data[loc] = [lat, lng]
    with open(mapfile, 'w') as fd:
        fd.write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


class call:
    """あめはむ[地点][拡大率][map URL] : 降水状況を表示/登録
ゆきはむ[地点][拡大率][map URL] : 降水/降雪状況を表示/登録
サンダー[地点][拡大率][map URL] : 落雷状況を表示/登録"""
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
        _map = None
        _ismap = False
        lat = None
        lng = None
        zoom = '10'
        param = None
        for keyword in keywords:
            if text.startswith(keyword):
                param = keywords[keyword]
                break

        if param is not None and item.get('bot_id', None) is None:
            loc = text.replace(keyword, '').strip()
            if ' ' in loc:
                tmp = loc.split()
                # URL の取り出しは <(.*?)|abbrev> からやらなければならない
                m = re.search(r'<(https://.+)\|?.*?>', tmp[-1])
                if m:
                    _map = m.group(1).split('|')[0]
                else:
                    _map = None

                # マップ指定あり
                if _map and _map.startswith('https://'):
                    # リダイレクトありの場合はそちらを使用
                    with requests.get(_map, timeout=10, allow_redirects=False) as r:
                        __map = r.headers.get('Location')
                    if __map:
                        _map = __map

                    if _map.startswith('https://www.google.co.jp/maps/'):
                        for p in _map.split('/'):
                            if p and p[0] == '@':
                                # @35.6306559,139.8636523,14z
                                _tmp = p.removeprefix('@').split(',')
                                if len(_tmp) == 3:
                                    _lat, _lng, _ = _tmp
                                    lat = round(float(_lat), 2)
                                    lng = round(float(_lng), 2)
                                    _ismap = True

                                    update_config(tmp[0], lat, lng)
                                    break

                if len(tmp) == 2:
                    if not _ismap:
                        loc, zoom = tmp
                    else:
                        loc, _ = tmp
                elif len(tmp) == 3:
                    loc, zoom, _ = tmp

            # map 処理をした時点で lat lng が準備済み _ismap = True
            if not loc:
                # lat lng も準備しちゃう
                loc = '岐阜県関市'
                lat = '35.62'
                lng = '136.88'
                zoom = '4'
                _ismap = True
            loc = loc.strip()
            zoom = zoom.strip()

            # 緯度経度決まってないので辞書引いてみる
            if not (lat and lng):
                data = load_config()
                if loc in data:
                    lat, lng = data[loc]
                    _ismap = True

            # print(f'map? {loc=} {lat} {lng} {zoom} {_ismap=}')

            if not _ismap:
                # ジオロケーション発動
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

            if _ismap:
                title = f'{loc} {zoom}'

            print(loc, title, lat, lng, zoom)

            if lat and lng:
                with requests.get(f'https://weather.yahoo.co.jp/weather/zoomradar/{param}?lat={lat}&lon={lng}&z={zoom}') as r:
                    soup = BeautifulSoup(r.content, 'html.parser')
                    og_image = soup.find('meta', property='og:image')
                    if og_image is None:
                        return
                    img_url = og_image.get('content')

                    mapFailureInfo = soup.find('div', class_='mapFailureInfo')

                    if mapFailureInfo:
                        failure = mapFailureInfo.text.strip()
                        if failure:
                            title = f'{failure} {title}'

                    postMessage(
                        client,
                        keyword,
                        caches.icon_emoji,
                        channel,
                        title or text,
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
                postMessage(
                    client,
                    keyword,
                    caches.icon_emoji,
                    channel,
                    loc + 'のスポット情報取得に失敗しました',
                    thread_ts=thread_ts,
                )
