# -*- coding: utf-8 -*-
import re
import subprocess
import math
import datetime as dt

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt


def deg2dec(deg):
    degree, minute = deg
    return degree + minute / 60


maps = {}
NEAR_LIMIT = 10


class Amedas:
    def __init__(self):
        if not maps:
            print('>>> read amedastable')
            with requests.get('https://www.jma.go.jp/bosai/amedas/const/amedastable.json') as r:
                table = r.json()
                for code in table:
                    name = table[code]['kjName']
                    lat = deg2dec(table[code]['lat'])
                    lng = deg2dec(table[code]['lon'])
                    elem = table[code]['elems']
                    if elem[0] == '1':
                        maps[code] = (name, lat, lng)

    def getLocation(self, name):
        locs = {}
        for _name in name.split():
            for code in maps:
                if maps[code][0] == _name:
                    locs[code] = maps[code]
        return locs

    def getNearLocation(self, name):
        lines = []

        locs = self.getLocation(name)

        for code in locs:
            _, lat, lng = locs[code]
            for _code in maps:
                _name, _lat, _lng = maps[_code]
                dist = math.dist((lat, lng), (_lat, _lng))
                if dist < 1:
                    lines.append([_code, _name, dist])
        return ' '.join([loc[0] for loc in sorted(lines, key=lambda x: x[2])[:NEAR_LIMIT]])


class call:
    """アメダス[観測地点[周辺]]
アメダス気温[地方|都道府県]
アメダス降水[地方|都道府県]
アメダス雨雲[地方|都道府県]
アメダス雷[地方|都道府県]
アメダス積雪[地方|都道府県]
アメダス最高気温[低]
アメダス最低気温[高]
アメダス積雪深
アメダス衛星[日本広域|日本付近|北日本|東日本|西日本|沖縄|[1-4]日前]
アメダス赤外[日本広域|日本付近|北日本|東日本|西日本|沖縄|[1-4]日前]
アメダス可視[日本広域|日本付近|北日本|東日本|西日本|沖縄|[1-4]日前]
アメダス水蒸気[日本広域|日本付近|北日本|東日本|西日本|沖縄|[1-4]日前]
アメダスPM2.5[地方|都道府県]
アメダス[スギ|ヒノキ]花粉[地方|都道府県]
アメダス黄砂[ひまわり]"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        urls = {
            '気温': 'https://tenki.jp/amedas/',
            '降水': 'https://tenki.jp/amedas/precip.html',
            '雨雲': 'https://tenki.jp/radar/',
            '雷': 'https://tenki.jp/thunder/',
            '積雪': 'https://tenki.jp/amedas/snow.html',
            '衛星': 'https://tenki.jp/satellite/japan-near/',
            '赤外': 'https://tenki.jp/satellite/japan-near/',
            '可視': 'https://tenki.jp/satellite/japan-near/visible/',
            '水蒸気': 'https://tenki.jp/satellite/japan-near/vapor/',
            '花粉': 'https://tenki.jp/pollen/mesh/',
            'スギ花粉': 'https://tenki.jp/pollen/mesh/',
            'ヒノキ花粉': 'https://tenki.jp/pollen/mesh/cypress.html',
            'PM2.5': 'https://tenki.jp/pm25/',
            '地震': 'https://earthquake.tenki.jp/bousai/earthquake/',
            '津波': 'https://earthquake.tenki.jp/bousai/tsunami/',
        }
        prefix = 'アメダス'
        suffixes = ('周辺', '付近')
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '').strip()

            # 気温・降水・積雪用のリトライつきポスト
            @retry(stop=stop_after_attempt(3))
            def postMessage():
                print('try')
                client.web_client.chat_postMessage(
                    username=loc,
                    icon_emoji=caches.icon_emoji,
                    channel=channel,
                    text=loc,
                    blocks=[
                        {
                            'type': 'image',
                            'image_url': img_url,
                            'alt_text': loc,
                        }
                    ],
                    thread_ts=thread_ts,
                )
                print('success')

            # 地方・都道府県対応
            subloc = ''
            kvs = {
                '気温': ['common-list-entries', '#amedas-map'],
                '降水': ['common-list-entries', '#amedas-map'],
                '雨雲': ['common-list-entries', '#radar-map', 'radar-area-pref-entries-table'],
                '雷': ['common-list-entries', '#thunder-map', 'liden-area-pref-entries-table'],
                '積雪': ['common-list-entries', '#amedas-map'],
                '花粉': ['pollen-list-entries', '#pollen_mesh_image_map'],
                'PM2.5': ['common-list-entries', '#pm25-map'],
                '衛星': ['satellite-card-image-entries', '#satellite-image-map'],
                '赤外': ['satellite-card-image-entries', '#satellite-image-map'],
                '可視': ['satellite-card-image-entries', '#satellite-image-map'],
                '水蒸気': ['satellite-card-image-entries', '#satellite-image-map'],
            }
            for k in kvs:
                if k in loc and loc not in ['最高気温低', '最低気温高', '積雪深']:
                    loc, subloc = loc.split(k)
                    loc = loc.strip()
                    subloc = subloc.strip()
                    loc += k
                    list_class = kvs[k][0]
                    usemap = kvs[k][1]
                    break

            if loc in urls:
                with requests.get(urls[loc], timeout=10) as r:
                    soup = BeautifulSoup(r.content, 'html.parser')

                    print(f'loc {loc} subloc {subloc}')
                    if subloc:
                        tables = soup.find_all(class_=list_class)
                        # なぜか雨雲と衛星は3つある……
                        if len(tables) != 1:
                            for t in tables:
                                print(t.get('id'))

                            id_class = None
                            if len(kvs[loc]) > 2:
                                id_class = kvs[loc][2]
                            print(loc, len(tables), id_class)
                            tables = soup.find_all(id=id_class, class_=list_class)

                        for table in tables:
                            # 地方
                            for th in table.find_all('th'):
                                abbr = loc + th.get('abbr', th.text.replace('地方', ''))
                                href = 'https://tenki.jp' + th.a.get('href')
                                # print(abbr, href)
                                urls[abbr] = href
                                if '関東' in abbr:
                                    urls[loc + '関東'] = href
                                    urls[loc + '甲信'] = href
                                if '沖縄' in abbr:
                                    urls[abbr + '地方'] = href
                            # 都道府県
                            for li in table.find_all('li'):
                                if li.a:
                                    abbr = loc + (li.text[0:-1] if li.text[-1] in '都府県' else li.text)
                                    href = 'https://tenki.jp' + li.a.get('href')
                                    # print(abbr, href)
                                    urls[abbr] = href

                        # import json
                        # print(json.dumps(urls, indent=2, ensure_ascii=False))

                        if loc + subloc in urls:
                            with requests.get(urls[loc + subloc], timeout=10) as r:
                                soup2 = BeautifulSoup(r.content, 'html.parser')
                                if loc != '雷':
                                    og_image = soup2.find('meta', property='og:image')
                                    img_url = og_image.get('content')
                                else:
                                    og_image = soup2.find('img', usemap=usemap)
                                    img_url = og_image.get('src')
                                if og_image is None:
                                    return
                        else:
                            print(loc, subloc)
                            areas = []
                            for k in urls:
                                if loc in k:
                                    a = k.replace(loc, '')
                                    if a:
                                        areas.append(a)
                            client.web_client.chat_postMessage(
                                username=prefix,
                                icon_emoji=caches.icon_emoji,
                                channel=channel,
                                text=f'{loc} {subloc} なぜかないのだ ({" ".join(areas)})',
                                thread_ts=thread_ts,
                            )
                            return
                    else:
                        og_image = soup.find('meta', property='og:image')
                        # og_image = soup.find('img', usemap=usemap)
                        if og_image is None:
                            return
                        img_url = og_image.get('content')
                        # img_url = og_image.get('src')

                    loc += subloc
                    img_url += dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime('?%Y%m%d%H%M')
                    try:
                        postMessage()
                    except Exception as e:
                        print(e)
                    print(img_url)
            elif loc.startswith('黄砂'):
                kosa = {
                    '黄砂': 'https://www.data.jma.go.jp/env/kosa/fcst/list_js/s_jpjp_list.js',
                    '黄砂ひまわり': 'https://www.data.jma.go.jp/env/kosa/himawari/kosa_js/DSTTime.js',
                }
                img_fmts = {
                    '黄砂': 'https://www.data.jma.go.jp/env/kosa/fcst/img/surf/jp/{}_kosafcst-s_jp_jp.png',
                    '黄砂ひまわり': 'https://www.data.jma.go.jp/env/kosa/himawari/img/DST/{}_DST.jpg',
                }
                url = None
                if loc in kosa:
                    url = kosa[loc]
                    img_fmt = img_fmts[loc]

                if url:
                    with requests.get(url, timeout=10) as r:
                        content = r.content.decode('utf-8')

                        print(content)

                        slt_time = content.split('\n')[2].split()[2].replace('"', '').replace(';', '')
                        img_url = img_fmt.format(slt_time)
                        if loc == '黄砂':
                            fcst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))) + dt.timedelta(hours=3)
                            yymmdd = f'{fcst.year}{fcst.month:02d}{fcst.day:02d}'
                            hour = int(fcst.hour / 3) * 3
                            img_url = f'https://www.data.jma.go.jp/gmd/env/kosa/fcst/img/surf/jp/{yymmdd}{hour:02d}00_kosafcst-s_jp_jp.png'

                        client.web_client.chat_postMessage(
                            username=loc,
                            icon_emoji=caches.icon_emoji,
                            channel=channel,
                            text=loc,
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
                codes = None
                _loc = loc
                _keys = {
                    '積雪深': 14,
                    '最低気温高': 3,
                    '最高気温低': 2,
                    '最低気温': 1,
                    '最高気温': 0,
                }
                if loc.endswith(suffixes):
                    for s in suffixes:
                        names = loc.replace(s, '').strip()
                        if names != loc:
                            break
                    codes = Amedas().getNearLocation(names)
                if codes:
                    loc = codes
                else:
                    base_url = 'https://www.data.jma.go.jp/stats/data/mdrr/rank_daily/'

                    for key in _keys:
                        if _loc == key:
                            r = requests.get(base_url)
                            if r and r.status_code == 200:
                                soup = BeautifulSoup(r.content, 'html.parser')
                                uls = soup.find_all('ul')
                                a = uls[4].find('a')
                                r = requests.get(base_url + a['href'])
                                if r and r.status_code == 200:
                                    soup = BeautifulSoup(r.content, 'html.parser')
                                    tbls = soup.find_all('table')
                                    if _keys[key] < len(tbls):
                                        tbl = tbls[_keys[key]]
                                        trs = tbl.find_all('tr')
                                        locs = []
                                        for tr in trs[2:]:
                                            tds = tr.find_all('td')
                                            m = re.match(r'^(.*?)（', tds[3].text)
                                            if m:
                                                locs.append(m[1])
                                        loc = ' '.join(locs)
                                        break

                print('<<<', loc, _loc)

                amedas = subprocess.check_output(['amedas', loc]).decode('utf8').strip()
                if _loc in _keys:
                    lines = []
                    for _line in amedas.split('\n'):
                        cs = _line.split()
                        try:
                            if _loc.startswith('最高気温') and '最高気温' in _line:
                                lines.append(f'{cs[0]} {key} {cs[-2]} {cs[-1]}')
                            elif _loc.startswith('最低気温') and '最低気温' in _line:
                                lines.append(f'{cs[0]} {key} {cs[-5]} {cs[-4]}')
                            elif _loc == '積雪深' and '積雪' in _line:
                                for i, c in enumerate(cs):
                                    if c == '積雪':
                                        lines.append(f'{cs[0]} {cs[1]} {key} {cs[i+1]}')
                        except Exception:
                            pass
                    amedas = '\n'.join(lines)

                # modify message
                do = r'(\.\d)?度'
                # 40度以上
                ak = r' ([4-9]\d)' + do
                # 35度以上
                me = r' (3[5-9])' + do
                # 30度以上
                ho = r' (3[0-4])' + do
                # 25度以上30度未満
                te = r' (2[5-9])' + do
                # 5度未満
                mi = r' (-\d+|[0-4])' + do
                # 80% 以上
                hu = r'(8|9|10).%'
                # 10m/s 以上
                wi = r'\d\d(\.\d)?m/s'
                # 10mm/h 以上
                ra = r'\d\d(\.\d)?mm/h'
                # 100cm 以上
                sn = r'\d\d\dcm'

                emojis = {
                    ak: ':atsui_koupen:',
                    me: ':melting_face:',
                    ho: ':hot_face:',
                    te: ':fire:',
                    mi: ':ice_cube:',
                    hu: ':droplet:',
                    ra: ':umbrella_with_rain_drops:',
                    wi: ':fish_cake:',
                    sn: ':snowflake:',
                }
                for key in emojis:
                    res = []
                    for m in re.finditer(key, amedas, re.MULTILINE):
                        res.append(m[0])
                    for p in set(res):
                        amedas = amedas.replace(p, p + emojis[key])

                weathers = {
                    '晴': ':sunny:',
                    '曇': ':cloud:',
                    '雨': ':rain_cloud:',
                    '雪': ':snow_cloud:',
                    '雷': ':zap:',
                }
                for w in weathers:
                    if w in amedas:
                        amedas = amedas.replace(f'天気 {w}', weathers[w])

                if amedas:
                    client.web_client.chat_postMessage(
                        username=prefix,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        text=amedas,
                        thread_ts=thread_ts,
                    )
