# -*- coding: utf-8 -*-
from datetime import datetime
import json
import subprocess

import requests

area_json = 'https://www.jma.go.jp/bosai/common/const/area.json'
fore_json = 'https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json'
weatherCodes_trans = {
    '103': 102,
    '105': 104,
    '106': 102,
    '107': 102,
    '108': 102,
    '111': 110,
    '113': 112,
    '114': 112,
    '116': 115,
    '117': 115,
    '118': 112,
    '119': 112,
    '120': 102,
    '121': 102,
    '122': 112,
    '123': 100,
    '124': 100,
    '125': 112,
    '126': 112,
    '127': 112,
    '128': 112,
    '130': 100,
    '131': 100,
    '132': 101,
    '140': 102,
    '160': 104,
    '170': 104,
    '181': 115,
    '203': 202,
    '205': 204,
    '206': 202,
    '207': 202,
    '208': 202,
    '209': 200,
    '211': 210,
    '213': 212,
    '214': 212,
    '216': 215,
    '217': 215,
    '218': 212,
    '219': 212,
    '220': 202,
    '221': 202,
    '222': 212,
    '223': 201,
    '224': 212,
    '225': 212,
    '226': 212,
    '228': 215,
    '229': 215,
    '230': 215,
    '231': 200,
    '240': 202,
    '250': 204,
    '260': 204,
    '270': 204,
    '281': 215,
    '304': 300,
    '306': 300,
    '309': 303,
    '315': 314,
    '316': 311,
    '317': 313,
    '320': 311,
    '321': 313,
    '322': 303,
    '323': 311,
    '324': 311,
    '325': 311,
    '326': 314,
    '327': 314,
    '328': 300,
    '329': 300,
    '340': 400,
    '350': 300,
    '361': 411,
    '371': 413,
    '405': 400,
    '407': 406,
    '409': 403,
    '420': 411,
    '421': 413,
    '422': 414,
    '423': 414,
    '425': 400,
    '426': 400,
    '427': 400,
    '450': 400,
}


class call:
    """天気[市区町村] : 現在からの情報を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        prefix = '天気'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '')

            r = requests.get(area_json)
            if r and r.status_code == 200:
                areas = json.loads(r.content)

                class10s = areas['class10s']
                class15s = areas['class15s']
                class20s = areas['class20s']
                offices = areas['offices']

                for c in class20s:
                    if class20s[c]['name'] == loc:
                        region = class20s[c]['parent']
                        area = class15s[region]['parent']
                        code = class10s[area]['parent']
                        area_name = offices[code]['name']

                        r = requests.get(fore_json.format(code))
                        if r and r.status_code == 200:
                            forecast = json.loads(r.content)

                            today = forecast[0]
                            # week = forecast[1]

                            w = today['timeSeries'][0]
                            p = today['timeSeries'][1]
                            t = today['timeSeries'][2]
                            for i, a in enumerate(w['areas']):
                                if a['area']['code'] == area:
                                    # date and pop
                                    pops = {}
                                    for j, d in enumerate(p['timeDefines']):
                                        pops[datetime.fromisoformat(d).strftime('%m/%d %H')] = p['areas'][i]['pops'][j]

                                    blocks = [
                                        {
                                            'type': 'context',
                                            'elements': [
                                                {
                                                    'type': 'mrkdwn',
                                                    'text': f'*{area_name} {loc}*'
                                                }
                                            ]
                                        }
                                    ]

                                    # add svg block
                                    for j, f in enumerate(a['weatherCodes']):
                                        g = weatherCodes_trans[f] if f in weatherCodes_trans else f
                                        image = f'https://www.jma.go.jp/bosai/forecast/img/{g}.png'

                                        d = datetime.fromisoformat(w['timeDefines'][j]).strftime('%m/%d')
                                        _pops = [d + '          ']

                                        for p in pops:
                                            if p.startswith(d):
                                                _pops.append(pops[p] + '%')

                                        blocks.append({
                                            'type': 'image',
                                            'title': {
                                                'type': 'plain_text',
                                                'text': '  '.join(_pops),
                                                'emoji': True
                                            },
                                            'image_url': image,
                                            'alt_text': 'weather'
                                        })

                                    # amedas challenge
                                    for a in t['areas']:
                                        _name = a['area']['name']
                                        _code = a['area']['code']
                                        if loc.startswith(_name):
                                            amedas = subprocess.check_output(['amedas', _code]).decode('utf8').strip()
                                            blocks.append({
                                                'type': 'context',
                                                'elements': [
                                                    {
                                                        'type': 'plain_text',
                                                        'text': amedas,
                                                    }
                                                ]
                                            })

                                    client.web_client.chat_postMessage(
                                        username=prefix,
                                        icon_emoji=caches.icon_emoji,
                                        channel=channel,
                                        text='気象庁発表',
                                        blocks=blocks,
                                        thread_ts=thread_ts,
                                    )
