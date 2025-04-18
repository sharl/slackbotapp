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
        return ' '.join([loc[0] for loc in sorted(lines, key=lambda x: x[2])[:5]])


class call:
    """アメダス[観測地点[周辺]]
アメダス気温
アメダス降水
アメダス積雪
アメダス最高気温[低]
アメダス最低気温[高]
アメダス積雪深
アメダス[スギ|ヒノキ]花粉
アメダス黄砂[ひまわり]"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        urls = {
            '気温': 'https://tenki.jp/amedas/',
            '降水': 'https://tenki.jp/amedas/precip.html',
            '積雪': 'https://tenki.jp/amedas/snow.html',
            '花粉': 'https://tenki.jp/pollen/mesh/',
            'スギ花粉': 'https://tenki.jp/pollen/mesh/',
            'ヒノキ花粉': 'https://tenki.jp/pollen/mesh/cypress.html',
        }
        prefix = 'アメダス'
        suffix = '周辺'
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

            if loc in urls:
                with requests.get(urls[loc], timeout=10) as r:
                    soup = BeautifulSoup(r.content, 'html.parser')
                    img = soup.find('img', id='amedas-image')
                    if img:
                        img_url = img.get('src')
                    else:
                        # 花粉
                        og_images = soup.find_all('img', usemap="#pollen_mesh_image_map")
                        if len(og_images) == 0:
                            return
                        img_url = og_images[0].get('src')

                    print(img)
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
                if loc.endswith(suffix):
                    names = loc.replace(suffix, '').strip()
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
                                    tbl = soup.find_all('table')[_keys[key]]
                                    trs = tbl.find_all('tr')
                                    locs = []
                                    for tr in trs[2:7]:
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
                        if _loc.startswith('最高気温'):
                            lines.append(f'{cs[0]} {key} {cs[-2]} {cs[-1]}')
                        elif _loc.startswith('最低気温'):
                            lines.append(f'{cs[0]} {key} {cs[-5]} {cs[-4]}')
                        elif _loc == '積雪深':
                            for i, c in enumerate(cs):
                                if c == '積雪':
                                    lines.append(f'{cs[0]} {cs[1]} {key} {cs[i+1]}')
                    amedas = '\n'.join(lines)

                # modify message
                # 35度以上
                ho = r' (3[5-9]|[4-9].)(\..)?度'
                # 30度以上
                me = r' (3[0-4])(\..)?度'
                # 25度以上30度未満
                te = r' (2[5-9])(\..)?度'
                # 5度未満
                mi = r' (-\d+|[0-4])(\..)?度'
                # 80% 以上
                hu = r'(8|9|10).%'
                # 10m/s 以上
                wi = r'\d\d(\.\d)?m/s'
                # 10mm/h 以上
                ra = r'\d\d(\.\d)?mm/h'
                # 100cm 以上
                sn = r'\d\d\dcm'

                emojis = {
                    ho: ':melting_face:',
                    me: ':hot_face:',
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

                client.web_client.chat_postMessage(
                    username=prefix,
                    icon_emoji=caches.icon_emoji,
                    channel=channel,
                    text=amedas,
                    thread_ts=thread_ts,
                )
