# -*- coding: utf-8 -*-
import requests
import json


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        if item.get('bot_id') is None:
            if isinstance(options, dict):
                keyword = options['keyword']
                ouser = options['user']
                user_id = item.get('user')
                username = caches.user_ids.get(user_id)
                if text == keyword and ouser == username:
                    token = options['token']
                    device = options['device']
                    # https://github.com/OpenWonderLabs/SwitchBotAPI#get-device-status
                    r = requests.get('https://api.switch-bot.com/v1.0/devices/{}/status'.format(device), headers={'Authorization': token}, timeout=10)
                    if r and r.status_code == 200:
                        j = json.loads(r.text)
                        temp = j.get('body').get('temperature')
                        humi = j.get('body').get('humidity')
                        if temp and humi:
                            client.web_client.chat_postMessage(
                                username="{}'s {}".format(ouser, keyword),
                                icon_emoji=caches.icon_emoji,
                                channel=channel,
                                text='{}C {}%'.format(temp, humi),
                                thread_ts=thread_ts,
                            )
