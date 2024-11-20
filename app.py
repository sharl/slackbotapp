#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import importlib
from threading import Event

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

Event().wait()
