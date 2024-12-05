# -*- coding: utf-8 -*-
from . import Switchbot


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        if item.get('bot_id') is None:
            user_id = item.get('user')
            username = caches.user_ids.get(user_id)
            if isinstance(options, dict):
                ouser = options['user']
                if ouser != username:
                    return

                # meter parameter is 'keyword'
                for device in options['devices']:
                    keyword = device.get('keyword')
                    if keyword and keyword == text:
                        deviceID = device['device']

                        sb = Switchbot()
                        status = sb.get_device_status(deviceID)

                        client.web_client.chat_postMessage(
                            username="{}'s {}".format(ouser, keyword),
                            icon_emoji=caches.icon_emoji,
                            channel=channel,
                            text=status,
                            thread_ts=thread_ts,
                        )
