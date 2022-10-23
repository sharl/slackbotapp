# -*- coding: utf-8 -*-
import subprocess


class call:
    """アメダス[観測地点] : アメダスでの現在の情報を表示"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item["channel"]
        thread_ts = item.get('thread_ts')

        prefix = 'アメダス'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '')
            amedas = subprocess.check_output(['amedas', loc]).decode('utf8').strip()
            client.web_client.chat_postMessage(
                username=prefix,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=amedas,
                thread_ts=thread_ts,
            )
