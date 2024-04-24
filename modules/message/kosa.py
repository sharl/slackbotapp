# -*- coding: utf-8 -*-
import datetime as dt


class call:
    """黄砂 : 黄砂情報を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        keyword = '黄砂'
        if text == keyword and item.get('bot_id', None) is None:
            fcst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))) + dt.timedelta(hours=3)
            yymmdd = f'{fcst.year}{fcst.month:02d}{fcst.day:02d}'
            hour = int(fcst.hour / 3) * 3
            img_url = f'https://www.data.jma.go.jp/gmd/env/kosa/fcst/img/surf/jp/{yymmdd}{hour:02d}00_kosafcst-s_jp_jp.png'
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
