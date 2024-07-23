# -*- coding: utf-8 -*-
import re
import subprocess

import requests
from bs4 import BeautifulSoup


class call:
    """アメダス[観測地点|気温|降水|積雪|最高気温|最低気温] : アメダスでの現在の情報を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        urls = {
            '気温': 'https://tenki.jp/amedas/',
            '降水': 'https://tenki.jp/amedas/precip.html',
            '積雪': 'https://tenki.jp/amedas/snow.html',
        }
        prefix = 'アメダス'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '').strip()

            if loc in urls:
                r = requests.get(urls[loc])
                if r and r.status_code == 200:
                    soup = BeautifulSoup(r.content, 'html.parser')
                    img = soup.find('img', id='amedas-image')
                    img_url = img.get('src')
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
            else:
                _keys = {
                    '最高気温': 0,
                    '最低気温': 1,
                }
                base_url = 'https://www.data.jma.go.jp/stats/data/mdrr/rank_daily/'

                for key in _keys:
                    if loc == key:
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
                                for tr in trs[2:5]:
                                    tds = tr.find_all('td')
                                    m = re.match(r'^(.*?)（', tds[3].text)
                                    if m:
                                        locs.append(m[1])
                                loc = ' '.join(locs)
                                break

                amedas = subprocess.check_output(['amedas', loc]).decode('utf8').strip()

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
                    wi: ':cyclone:',
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
