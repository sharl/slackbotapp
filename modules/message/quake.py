# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from modules import postMessage

LIST_URL = 'https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/'
API_URL = 'http://192.168.0.1:15678/api'
QUAKE_CLASS = '1 2 3 4 5弱 5強 6弱 6強 7'.split()


class call:
    """地震 : 直近 5 件を表示
地震<地域名> : 最新の地域名の地震を表示
震度 : お知らせする最低震度を表示
震度<震度> : お知らせする最低震度を設定"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text'].strip()
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        # ------------------------------------------------------------
        intensity = None
        intensity_prefix = '震度'
        if text.startswith(intensity_prefix) and item.get('bot_id') is None:
            url = f'{API_URL}/intensity'
            # get current intensity
            try:
                with requests.get(url, timeout=3) as r:
                    intensity = r.json().get('state')
            except Exception:
                pass

            _intensity = text.removeprefix(intensity_prefix).strip()
            if _intensity:
                if _intensity == intensity:
                    postMessage(
                        client,
                        intensity_prefix,
                        caches.icon_emoji,
                        channel,
                        f'現在お知らせする震度は {intensity} 以上に設定済みです',
                        thread_ts=thread_ts,
                    )
                    return

                # set intensity
                user_id = item.get('user')
                username = caches.user_ids.get(user_id)
                if isinstance(options, dict):
                    ouser = options.get('user', '---')
                    if ouser != username:
                        print(intensity_prefix, ouser, username)
                        return

                    if _intensity in QUAKE_CLASS:
                        try:
                            with requests.post(
                                    url,
                                    json={'intensity': _intensity},
                                    timeout=3,
                            ) as r:
                                postMessage(
                                    client,
                                    intensity_prefix,
                                    caches.icon_emoji,
                                    channel,
                                    f'お知らせする震度を {_intensity} 以上に設定しました',
                                    thread_ts=thread_ts,
                                )
                        except Exception as e:
                            print(intensity_prefix, e)

                return
            else:
                if intensity:
                    postMessage(
                        client,
                        intensity_prefix,
                        caches.icon_emoji,
                        channel,
                        f'お知らせする震度は {intensity} 以上です',
                        thread_ts=thread_ts,
                    )
                return

        # ------------------------------------------------------------

        prefix = '地震'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.removeprefix(prefix).strip()

            trs = []
            with requests.get(LIST_URL, timeout=10) as r:
                soup = BeautifulSoup(r.content, 'html.parser')
                trs = soup.find_all('tr', bgcolor='#ffffff', valign='middle')

            limit = 5
            lines = []
            # [
            #     <td><a href="/weather/jp/earthquake/20260805180614.html">2026年8月5日 18時06分ごろ</a></td>,
            #     <td align="center">東京都２３区</td>,
            #     <td align="center">3.5</td>,
            #     <td align="center">1</td>
            # ]
            if not loc:
                for tr in trs[:limit]:
                    tds = tr.find_all('td')
                    _dt, _anm, _mag, _int = tds
                    link = 'https://typhoon.yahoo.co.jp' + _dt.a.get('href')
                    lines.append(f'{_dt.text} <{link}|{_anm.text}> M{_mag.text} 震度{_int.text}')
            else:
                for tr in trs:
                    tds = tr.find_all('td')
                    _dt, _anm, _mag, _int = tds
                    link = 'https://typhoon.yahoo.co.jp' + _dt.a.get('href')
                    if _anm.text.startswith(loc):
                        lines.append(f'{_dt.text} <{link}|{_anm.text}> M{_mag.text} 震度{_int.text}')
                        break

            # 幅揃え
            ml = len(max([line.split()[2] for line in lines]))
            _lines = []
            for line in lines:
                ps = line.split()
                ln = len(ps[2])
                s = (ml - ln) * '\u3000'
                _lines.append(f'{ps[0]} {ps[1]} {ps[2] + s} {ps[3]} {ps[4]}')
            lines = _lines

            if lines:
                quakes = '\n'.join(lines)
            else:
                quakes = '見つかりませんでした'
            postMessage(
                client,
                prefix,
                caches.icon_emoji,
                channel,
                quakes,
                thread_ts=thread_ts,
                unfurl_links=False,
            )
