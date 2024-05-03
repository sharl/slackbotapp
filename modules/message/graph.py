# -*- coding: utf-8 -*-
import datetime as dt

import requests
import matplotlib as mpl
import matplotlib.pyplot as plt


class call:
    """[気温|降水|湿度|気圧|積雪|降雪]<観測地点> : アメダスでの推移をグラフで表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        words = {
            '気温': 'temp',
            '降水': 'precipitation10m',
            '湿度': 'humidity',
            '気圧': 'pressure',
            '積雪': 'snow',
            '降雪': 'snow1h',
        }
        prefix = None
        for p in words:
            if text.startswith(p) and item.get('bot_id') is None:
                prefix = p
                break

        if prefix:
            # グラフ種別
            param = words[prefix]
            # 地点名
            tmp = text.replace(prefix, '')
            _locs = [tmp, tmp.replace('ヶ', 'ケ')]
            r = requests.get('https://www.jma.go.jp/bosai/amedas/const/amedastable.json')
            if r and r.status_code == 200:
                data = r.json()
                locs = []
                for k in data:
                    for _loc in set(_locs):
                        if data[k].get('kjName') == _loc:
                            loc = _loc
                            locs.append(k)

                self.now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))

                for code in locs:
                    time_data = {}
                    for delta in range(9):
                        now = self.now - dt.timedelta(hours=delta * 3) - dt.timedelta(minutes=10)
                        yyyymmdd = now.strftime('%Y%m%d')
                        HH = now.strftime('%H')
                        hh = f'{int(HH) // 3 * 3:02d}'

                        # JSONデータのURL
                        url = f'https://www.jma.go.jp/bosai/amedas/data/point/{code}/{yyyymmdd}_{hh}.json'

                        # データを取得
                        response = requests.get(url)
                        data = response.json()

                        for tim in data.keys():
                            if param in data[tim]:
                                time_data[tim] = data[tim][param][0]

                    if time_data:
                        # グラフ描画
                        plt.figure(figsize=[8, 4.5], tight_layout=True)
                        # 上下左右余白なし
                        mpl.rcParams['axes.xmargin'] = 0
                        mpl.rcParams['axes.ymargin'] = 0

                        xs = sorted(time_data.keys())
                        ys = [time_data[tim] for tim in xs]
                        if param.startswith('precipitation') or param == 'snow1h':
                            plt.bar(xs, ys)
                        else:
                            plt.plot(xs, ys)
                        plt.grid()
                        plt.xticks([])
                        _ys = [v for v in ys if v is not None]  # 休止中対応
                        ymin = min(_ys)
                        ymax = max(_ys) + 1
                        for tim in xs:
                            if tim.endswith('000000') or tim.endswith('120000'):
                                plt.vlines(tim, ymin, ymax, colors='gray', linestyle='dotted')
                        f = f'/tmp/graph_{param}_{code}.png'
                        plt.savefig(f)

                        title = f'{loc}の{prefix}'
                        client.web_client.files_upload_v2(
                            username=title,
                            icon_emoji=caches.icon_emoji,
                            channel=channel,
                            file=f,
                            title=title,
                            thread_ts=thread_ts,
                        )
