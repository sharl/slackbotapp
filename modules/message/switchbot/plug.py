# -*- coding: utf-8 -*-
import requests


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        ts = item.get('ts')

        if item.get('bot_id', None) is None:
            if isinstance(options, dict):
                on = options['on']
                off = options['off']
                ouser = options['user']
                user_id = item.get('user')
                username = caches.user_ids.get(user_id)
                if (text == on or text == off) and ouser == username:
                    token = options['token']
                    device = options['device']
                    commands = {
                        on: 'turnOn',
                        off: 'turnOff',
                    }
                    command = commands[text]

                    # https://github.com/OpenWonderLabs/SwitchBotAPI#send-device-control-commands
                    try:
                        requests.post('https://api.switch-bot.com/v1.0/devices/{}/commands'.format(device),
                                      headers={'Authorization': token},
                                      json={
                                          'command': command,
                                          'parameter': 'default',
                                          'commandType': 'command',
                                      },
                                      timeout=10)
                        client.web_client.reactions_add(
                            channel=channel,
                            name='ok',
                            timestamp=ts,
                        )
                    except Exception:
                        client.web_client.reactions_add(
                            channel=channel,
                            name='ng',
                            timestamp=ts,
                        )
