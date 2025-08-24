# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import datetime as dt

import requests
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


font_prop = FontProperties(fname='/usr/share/fonts/truetype/migmix/migu-1p-regular.ttf')
mpl.rcParams["font.family"] = font_prop.get_name()

HEAT = 25
COLD = 0

prefs = {
    '11': '宗谷地方', '12': '上川・留萌地方', '13': '上川・留萌地方', '14': '石狩・空知・後志地方', '15': '石狩・空知・後志地方', '16': '石狩・空知・後志地方', '17': '網走・北見・紋別地方', '18': '釧路・根室地方', '20': '十勝地方', '21': '胆振・日高地方', '22': '胆振・日高地方', '23': '渡島・檜山地方', '24': '渡島・檜山地方', '31': '青森県', '32': '秋田県', '33': '岩手県', '34': '宮城県', '35': '山形県', '36': '福島県', '40': '茨城県', '41': '栃木県', '42': '群馬県', '43': '埼玉県', '44': '東京都', '45': '千葉県', '46': '神奈川県', '48': '長野県', '49': '山梨県', '50': '静岡県', '51': '愛知県', '52': '岐阜県', '53': '三重県', '54': '新潟県', '55': '富山県', '56': '石川県', '57': '福井県', '60': '滋賀県', '61': '京都府', '62': '大阪府', '63': '兵庫県', '64': '奈良県', '65': '和歌山県', '66': '岡山県', '67': '広島県', '68': '島根県', '69': '鳥取県', '71': '徳島県', '72': '香川県', '73': '愛媛県', '74': '高知県', '81': '山口県', '82': '福岡県', '83': '大分県', '84': '長崎県', '85': '佐賀県', '86': '熊本県', '87': '宮崎県', '88': '鹿児島県（奄美地方除く）', '91': '沖縄本島地方', '92': '大東島地方', '93': '宮古島地方', '94': '八重山地方'
}
COLORMAP = {
    HEAT + 15: '#B40068',
    HEAT + 10: '#FF2800',
    HEAT + 5: '#ff9900',
    HEAT: '#FAF500',
    COLD + 10: '#B9EBFF',
    COLD + 5: '#0096FF',
    COLD: '#0041FF',
    COLD - 5: '#002080',
}


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
            tmp = text.replace(prefix, '').strip()
            _locs = [tmp, tmp.replace('ヶ', 'ケ')]
            r = requests.get('https://www.jma.go.jp/bosai/amedas/const/amedastable.json')
            if r and r.status_code == 200:
                data = r.json()
                # dirty hack
                data['67326']['kjName'] = '広島県府中市'
                locs = []
                for k in data:
                    for _loc in set(_locs):
                        if data[k].get('kjName') == _loc:
                            loc = _loc
                            locs.append(k)

                self.now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))

                async def fetch_data(session, url, param, time_data):
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                for tim in data.keys():
                                    if param in data[tim] and data[tim][param][1] == 0:
                                        time_data[tim] = data[tim][param][0]
                            else:
                                print(f"Error: {response.status} for URL: {url}")
                    except aiohttp.ClientError as e:
                        print(f"aiohttp error for URL {url}: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred for URL {url}: {e}")

                async def prequests(code, param, time_data):
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for delta in range(16):
                            now = self.now - dt.timedelta(hours=delta * 3) - dt.timedelta(minutes=10)
                            yyyymmdd = now.strftime('%Y%m%d')
                            HH = now.strftime('%H')
                            hh = f'{int(HH) // 3 * 3:02d}'
                            url = f'https://www.jma.go.jp/bosai/amedas/data/point/{code}/{yyyymmdd}_{hh}.json'
                            task = asyncio.create_task(fetch_data(session, url, param, time_data))
                            tasks.append(task)

                        await asyncio.gather(*tasks)

                for code in locs:
                    time_data = {}
                    asyncio.run(prequests(code, param, time_data))

                    if time_data:
                        # グラフ描画
                        plt.figure(figsize=[8, 4.5], tight_layout=True)
                        # 上下左右余白なし
                        mpl.rcParams['axes.xmargin'] = 0
                        mpl.rcParams['axes.ymargin'] = 0

                        xs = sorted(time_data.keys())
                        ys = [time_data[tim] for tim in xs]
                        _ys = [v for v in ys if v is not None]  # 休止中対応
                        xmin = min(xs)
                        xmax = max(xs)
                        ymin = min(_ys) - 2
                        ymax = max(_ys) + 2

                        if param == 'humidity':
                            ymax = 100
                            ymin = 0
                        if param == 'snow':
                            if max(_ys) < 10:
                                ymax = 10
                            if min(_ys) <= 10:
                                ymin = 0
                        if param.startswith('precipitation') or param == 'snow1h':
                            ymin = 0
                            plt.bar(xs, ys)
                        else:
                            plt.plot(xs, ys)

                        if len(locs) == 1:
                            title = f'{loc}の{prefix}'
                        else:
                            pref = prefs[code[0:2]]
                            title = f'{loc}({pref})の{prefix}'

                        plt.title(title)
                        plt.grid()

                        def mmddHHMM(tim):
                            return f'{tim[4:6]}/{tim[6:8]} {tim[8:10]}:{tim[10:12]}'

                        atim = []
                        atic = []
                        for tim in xs:
                            if tim.endswith('000000') or tim.endswith('120000'):
                                plt.vlines(tim, ymin, ymax, colors='gray', linestyle='dotted')
                                if int(xmax) - int(tim) > 60000:        # 6時間?
                                    atim.append(tim)
                                    atic.append(mmddHHMM(tim))
                        atim.append(xs[-1])
                        atic.append(mmddHHMM(xs[-1]))
                        plt.xticks(atim, atic)

                        if param == 'temp':
                            for h in [HEAT + 15, HEAT + 10, HEAT + 5, HEAT]:
                                if ymax >= h:
                                    plt.hlines(h, xmin, xmax, colors=COLORMAP[h])
                            for h in [COLD + 10, COLD + 5, COLD, COLD - 5]:
                                if ymin <= h:
                                    plt.hlines(h, xmin, xmax, colors=COLORMAP[h])

                        f = f'/tmp/graph_{param}_{code}.png'
                        plt.savefig(f)
                        plt.close()

                        client.web_client.files_upload_v2(
                            username=title,
                            icon_emoji=caches.icon_emoji,
                            channel=channel,
                            file=f,
                            title=title,
                            thread_ts=thread_ts,
                        )
