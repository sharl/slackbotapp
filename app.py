#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import importlib
import threading

from bottle import route, run, request, response as bottleResponse
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from modules import Caches, Logger

#
# init
#
caches = Caches()
logger = Logger()

with open('config/config.json') as fd:
    config = json.load(fd)
caches.username = config.get('name', 'bot')
caches.icon_emoji = config.get('icon_emoji', ':bot:')

mods = config.get('modules', {})
modules = {}
options = {}
docs = []

for module in sorted(mods):
    m = importlib.import_module('modules.{}'.format(module))
    modules[module] = m
    options[module] = mods[module]
    _doc = m.call.__doc__
    if _doc:
        docs.append(_doc)
    caches.doc = '\n'.join(docs)


#
# main
#
client = SocketModeClient(
    app_token=os.environ.get("SLACK_APP_TOKEN"),
    web_client=WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
)


def process_message(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

        if req.payload["event"]["type"] == "message" and req.payload["event"].get("bot_id") is None:
            caches.parse(client, req)
            logger.log(req, caches)

            for module in modules:
                if module.startswith('message'):
                    modules[module].call(client, req, options=options[module], caches=caches)

        if req.payload["event"]["type"] == "reaction_added" and req.payload["event"].get("bot_id") is None:
            for module in modules:
                if module.startswith('reaction_added'):
                    modules[module].call(client, req, options=options[module], caches=caches)

        if req.payload["event"]["type"] == "emoji_changed":
            for module in modules:
                if module.startswith('emoji_changed'):
                    modules[module].call(client, req, options=options[module], caches=caches)


def process_interactive(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "interactive":
        for module in modules:
            if module.startswith('interactive'):
                modules[module].call(client, req, options=options[module], caches=caches)


client.socket_mode_request_listeners.append(process_message)
client.socket_mode_request_listeners.append(process_interactive)

client.connect()
caches.updateChannels(client)


@route('/chat_postMessage', method='POST')
def post_to_slack():
    """
    Slackの指定されたチャンネルにメッセージを投稿する API endpoint
    request body is JSON
    例:
        {
            "username": "hamu",
            "icon_emoji": "bot",
            "channel": "dev",
            "text": "Hello from API!",
            "blocks": null,
        }
    """
    try:
        data = request.json
        if not data:
            bottleResponse.status = 400
            return {'error': 'Invalid JSON payload.'}

        # print(json.dumps(data, indent=2, ensure_ascii=False))

        username = data.get('username', caches.username)
        icon_emoji = data.get('icon_emoji', caches.icon_emoji)
        # if not set channel, use general channel's first name
        channel = data.get('channel', list(caches.generals[0].values())[0] if caches.generals else None)
        text = data.get('text')
        blocks = data.get('blocks')

        if not channel:
            bottleResponse.status = 400
            return {'error': 'Required fields "channel" is missing'}

        # search channel_id
        channel_id = None
        for c_id in caches.channel_ids:
            if caches.channel_ids[c_id] == channel:
                channel_id = c_id
                break

        if not channel_id:
            bottleResponse.status = 400
            return {'error': f"Not exist {channel}'s channel_id"}

        client.web_client.chat_postMessage(
            username=username,
            icon_emoji=icon_emoji,
            channel=channel_id,
            text=text,
            blocks=blocks,
        )

        bottleResponse.status = 200
        return {'status': 'ok', 'message': 'Message successfully posted to Slack.'}
    except SlackApiError as e:
        bottleResponse.status = 500
        return {'error': f'Slack API Error: {e.response['error']}'}
    except Exception as e:
        bottleResponse.status = 500
        return {'error': f'Internal Server Error: {str(e)}'}


def run_bottle_app():
    run(host='localhost', port=16543)


bottle_thread = threading.Thread(target=run_bottle_app, daemon=True)
bottle_thread.start()

threading.Event().wait()
