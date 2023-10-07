# -*- coding: utf-8 -*-
import os
import json
import time
import hashlib
import hmac
import base64
import uuid

import requests


class Switchbot:
    base_url = 'https://api.switch-bot.com'
    charset = 'utf-8'
    token = None
    secret = None

    def __init__(self):
        conf = (os.environ.get('HOME') or '.') + '/.switchbot'
        try:
            with open(conf) as fd:
                j = json.load(fd)
                self.token = j['token']
                self.secret = j['secret']
        except Exception as e:
            raise e

    def make_headers(self):
        nonce = uuid.uuid4()
        t = int(round(time.time() * 1000))
        string_to_sign = '{}{}{}'.format(self.token, t, nonce)

        string_to_sign = bytes(string_to_sign, self.charset)
        secret = bytes(self.secret, self.charset)
        sign = base64.b64encode(hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())

        return {
            'Content-Type': 'application/json; charset={}'.format(self.charset),
            'Authorization': self.token,
            'sign': str(sign, self.charset),
            't': str(t),
            'nonce': str(nonce),
        }

    def get_device_list(self):
        headers = self.make_headers()
        r = requests.get(self.base_url + '/v1.1/devices', headers=headers, timeout=10)
        if r and r.status_code == 200:
            j = json.loads(str(r.content, 'utf-8'))
            print(json.dumps(j, indent=2, ensure_ascii=False))

    def parse(self, data):
        deviceType = data.get('deviceType')

        # have power status (lighting unit)
        if deviceType in ['Color Bulb']:
            return data['power']

        # have temp and humi sensors
        if deviceType in ['Meter', 'MeterPlus', 'WoIOSensor']:
            temperature = data['temperature']
            humidity = data['humidity']
            return '{}C {}%'.format(temperature, humidity)

        # have power status (not lighting unit)
        if deviceType in ['Bot', 'Plug Mini (US)', 'Plug Mini (JP)', 'Plug']:
            return data['power']

    def get_device_status(self, deviceID):
        headers = self.make_headers()
        r = requests.get(self.base_url + '/v1.1/devices/{}/status'.format(deviceID), headers=headers, timeout=10)
        if r and r.status_code == 200:
            j = json.loads(str(r.content, 'utf-8')).get('body', [])
            return self.parse(j)
        else:
            return []

    def set_device_power(self, deviceID, cmd):
        commands = {
            'on': 'turnOn',
            'off': 'turnOff',
        }
        headers = self.make_headers()
        try:
            command = commands[cmd]
            requests.post(self.base_url + '/v1.1/devices/{}/commands'.format(deviceID),
                          headers=headers,
                          json={
                              'command': command,
                              'parameter': 'default',
                              'commandType': 'command',
                          },
                          timeout=10)
            return True
        except Exception as e:
            print(e)
            return False
