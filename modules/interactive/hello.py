# -*- coding: utf-8 -*-
from slack_sdk.socket_mode.response import SocketModeResponse


class call:
    def __init__(self, client, req, options=None, caches={}):
        _type = req.payload.get('type')
        if _type == 'shortcut':
            if req.payload['callback_id'] == 'socket-mode-shortcut':
                # Acknowledge the request anyway
                response = SocketModeResponse(envelope_id=req.envelope_id)
                client.send_socket_mode_response(response)

                # Open a welcome modal
                client.web_client.views_open(
                    trigger_id=req.payload['trigger_id'],
                    view={
                        'type': 'modal',
                        'callback_id': 'hello-modal',
                        'title': {
                            'type': 'plain_text',
                            'text': 'Greetings!'
                        },
                        'submit': {
                            'type': 'plain_text',
                            'text': 'Good Bye'
                        },
                        'blocks': [
                            {
                                'type': 'section',
                                'text': {
                                    'type': 'mrkdwn',
                                    'text': 'Hello!'
                                }
                            }
                        ]
                    }
                )

        if _type == 'view_submission':
            if req.payload['view']['callback_id'] == 'hello-modal':
                # Acknowledge the request anyway
                response = SocketModeResponse(envelope_id=req.envelope_id)
                client.send_socket_mode_response(response)

                print('view_submission', req.payload)
