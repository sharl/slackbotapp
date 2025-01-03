# -*- coding: utf-8 -*-
from datetime import datetime


class Caches:
    # 問い合わせを減らすためのチャンネルIDキャッシュ
    channel_ids = {}
    # 問い合わせを減らすためのユーザIDキャッシュ
    user_ids = {}
    # 問い合わせを減らすためのdisplay_nameキャッシュ
    display_names = {}
    # デフォルトチャンネル一覧
    # [{channel_id: channel_name}]
    generals = []

    username = None
    icon_emoji = None
    doc = ''

    def __init__(self):
        pass

    def updateChannels(self, client):
        r = client.web_client.conversations_list(exclude_archived=True)
        if r['ok'] is False:
            return

        for page in r:
            for channel in page['channels']:
                channel_id = channel['id']
                channel_name = channel['name']
                is_general = channel['is_general']

                self.channel_ids[channel_id] = channel_name
                if is_general:
                    self.generals.append({channel_id: channel_name})

    def parse(self, client, req):
        user_id = req.payload.get('event', {}).get('user')
        #
        # detect user
        #
        if isinstance(user_id, str) and user_id not in self.user_ids:
            user = client.web_client.users_info(user=user_id)
            if user['ok'] is True:
                user_name = user.get('user', {}).get('name')
                display_name = user.get('user', {}).get('profile', {}).get('display_name')
                if user_name:
                    self.user_ids[user_id] = user_name
                if display_name:
                    self.display_names[user_id] = display_name
                else:
                    self.display_names[user_id] = user_name

        channel_id = req.payload.get('event', {}).get('channel')
        #
        # detect channel
        #
        if isinstance(channel_id, str) and channel_id not in self.channel_ids:
            if channel_id.startswith('C') or channel_id.startswith('G'):
                # channel or group im (mpim)
                chan = client.web_client.conversations_info(channel=channel_id)
                if chan['ok'] is True:
                    channel_name = chan.get('channel', {}).get('name')
                    if channel_name is not None:
                        self.channel_ids[channel_id] = channel_name
            elif channel_id.startswith('D'):
                # im
                user_name = self.user_ids.get(user_id, '???')
                self.channel_ids[channel_id] = user_name

            if channel_id not in self.channel_ids:
                self.channel_ids[channel_id] = channel_id


class Logger:
    def __init__(self):
        pass

    def log(self, req, caches=None):
        item = req.payload.get('event')
        if item and item.get('bot_id', None) is None:
            text = item.get('text')
            user = item.get('user')
            channel = item.get('channel')
            ts = item.get('ts')
            if text and user and channel and ts:
                print('{} {}> {}: {}'.format(datetime.fromtimestamp(float(ts)).strftime('%H:%M:%S'),
                                             caches.channel_ids[channel],
                                             caches.user_ids[user],
                                             text))
