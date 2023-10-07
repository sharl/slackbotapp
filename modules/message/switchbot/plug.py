# -*- coding: utf-8 -*-
from . import Switchbot


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        ts = item.get('ts')

        if item.get('bot_id', None) is None:
            user_id = item.get('user')
            username = caches.user_ids.get(user_id)
            if isinstance(options, dict):
                ouser = options['user']
                if ouser != username:
                    return

                # plug parameter is 'on' and 'off'
                for device in options['devices']:
                    on = device.get('on')
                    off = device.get('off')
                    if on and off and (on == text or off == text):
                        deviceID = device['device']
                        cmds = {
                            on: 'on',
                            off: 'off',
                        }
                        sb = Switchbot()
                        reaction = 'ok' if sb.set_device_power(deviceID, cmds[text]) else 'ng'

                        client.web_client.reactions_add(
                            channel=channel,
                            name=reaction,
                            timestamp=ts,
                        )
                        return
